# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooResolution(models.Model):
    _name = 'govoo.resolution'
    _description = 'Resolution'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'
    _rec_name = 'title'

    meeting_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Meeting',
        ondelete='restrict',
    )
    agenda_item_id = fields.Many2one(
        comodel_name='govoo.agenda.item',
        string='Agenda Item',
        ondelete='set null',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        compute='_compute_company_id',
        store=True,
        readonly=True,
    )
    title = fields.Char(
        string='Resolution Title',
        required=True,
        tracking=True,
    )
    text = fields.Html(
        string='Resolution Text',
    )
    resolution_type = fields.Selection(
        selection=[
            ('ordinary', 'Ordinary'),
            ('special', 'Special'),
            ('written', 'Written'),
        ],
        string='Resolution Type',
        required=True,
        tracking=True,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('open', 'Open for Voting'),
            ('passed', 'Passed'),
            ('failed', 'Failed'),
            ('withdrawn', 'Withdrawn'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    vote_ids = fields.One2many(
        comodel_name='govoo.vote',
        inverse_name='resolution_id',
        string='Votes',
    )
    vote_count = fields.Integer(
        string='Votes',
        compute='_compute_vote_count',
    )
    voter_notification_ids = fields.One2many(
        comodel_name='govoo.resolution.voter',
        inverse_name='resolution_id',
        string='Voting Notifications',
    )
    unreachable_voter_count = fields.Integer(
        string='Voters Without Portal Access',
        compute='_compute_unreachable_voter_count',
        help='Eligible voters portal access could not be auto-created for '
             '(issue #234) because they have no usable email on file -- '
             'everyone else is auto-enrolled and notified automatically.',
    )
    requires_my_vote = fields.Boolean(
        string='Requires My Vote',
        compute='_compute_requires_my_vote',
        search='_search_requires_my_vote',
        help='Open resolution with no vote yet cast by the current user '
             '(dashboards.md §1: "absence of own vote row").',
    )
    result = fields.Selection(
        selection=[
            ('passed', 'Passed'),
            ('failed', 'Failed'),
        ],
        string='Result',
        compute='_compute_result',
        store=True,
    )
    effective_date = fields.Date(
        string='Effective Date',
        tracking=True,
    )
    vote_deadline = fields.Datetime(
        string='Voting Deadline',
        tracking=True,
        help='Issue #269: set automatically at action_open() from the '
             '"govoo_board.resolution_voting_window_days" parameter, when '
             'configured. Blank (the default) means no deadline -- a '
             'Secretary must still manually tally, matching behavior '
             'before this field existed.',
    )
    tie_break_pending = fields.Boolean(
        string='Tie-Break Pending',
        tracking=True,
        help='Issue #269: set by action_tally() when a simple-majority '
             'vote ties and "govoo_board.resolution_tie_break_enabled" is '
             'on, instead of auto-failing. Cleared by '
             'action_chair_casting_vote().',
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a signing document is generated for this field, check
    # self.env['govoo.feature.flags'].is_sign_app_installed() to use
    # sign.request instead, falling back to ir.attachment on Community.
    sign_request_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Sign Request',
    )

    @api.onchange('agenda_item_id')
    def _onchange_agenda_item_id(self):
        for rec in self:
            if rec.agenda_item_id and not rec.meeting_id:
                rec.meeting_id = rec.agenda_item_id.meeting_id

    @api.constrains('meeting_id', 'agenda_item_id')
    def _check_meeting_agenda_consistency(self):
        """A resolution linked via agenda_item_id must have a matching
        meeting_id, so it's visible via meeting.resolution_ids -- and
        therefore included in action_close's terminal-state check
        (BR-BOARD-002)."""
        for rec in self:
            if rec.agenda_item_id and rec.meeting_id != rec.agenda_item_id.meeting_id:
                raise ValidationError(
                    _('This resolution\'s meeting must match its agenda item\'s '
                      'meeting (%s).') % rec.agenda_item_id.meeting_id.name
                )

    @api.constrains('sign_request_id')
    def _check_esignature_legally_confirmed(self):
        """BR-BOARD-008: gate sign_request_id usage on confirmed legal
        validity of e-signature under Rwandan law -- still an open
        decision (docs/spec/decisions/open-decisions.md #3), so this
        defaults to unconfirmed/blocked.
        """
        confirmed = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.e_signature_legally_confirmed', 'False',
        ) in ('True', '1')
        if confirmed:
            return
        for rec in self:
            if rec.sign_request_id:
                raise ValidationError(_(
                    'E-signature is not yet confirmed as legally valid '
                    'under Rwandan law (BR-BOARD-008); Sign Request cannot '
                    'be used. Store the executed resolution document '
                    'separately instead.'
                ))

    @api.depends('meeting_id.company_id')
    def _compute_company_id(self):
        """Meeting-linked resolutions take the meeting's company; standalone
        written resolutions (meeting_id null -- nullable per
        docs/spec/modules/govoo_board.md) fall back to the acting user's
        company. A plain `related='meeting_id.company_id'` field left this
        False whenever meeting_id was unset, which then failed the
        multi-company ir.rule (govoo_resolution_comp_rule: company_id in
        company_ids) for every user with no configured group able to fix
        it -- surfaced as a generic Access Error that named no group."""
        for rec in self:
            rec.company_id = rec.meeting_id.company_id if rec.meeting_id else self.env.company

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/votes/%s' % rec.id

    def _quorum_met(self):
        """BR-BOARD-005: quorum for meeting-linked resolutions reuses the
        meeting's own (already-correct) quorum computation. Standalone/
        written resolutions (meeting_id is null) have no quorum concept
        defined anywhere in spec -- [CONFIRM]; treated as always-met unless
        'govoo_board.written_resolution_quorum_percentage' is explicitly
        configured (issue #269 item 7), in which case that fraction of
        _get_eligible_voters() must have cast a non-conflicted vote.
        """
        self.ensure_one()
        if self.meeting_id:
            return self.meeting_id.quorum_met
        threshold = self._written_resolution_quorum_percentage()
        if threshold is None:
            return True
        eligible_count = len(self._get_eligible_voters())
        if eligible_count <= 0:
            return True
        votes_cast = len(self.vote_ids.filtered(lambda v: not v.is_conflicted))
        return votes_cast >= threshold * eligible_count

    def _voting_window_days(self):
        """Issue #269 item 3: days after action_open() a resolution's vote
        auto-closes via cron. Unset (0) = no deadline, the exact behavior
        before this field existed -- a Secretary must manually tally."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.resolution_voting_window_days', '0',
        )
        try:
            return int(raw or '0')
        except (TypeError, ValueError):
            return 0

    def _notice_period_days(self):
        """Issue #269 item 5: minimum days between action_open() and a
        linked meeting's date. Unset (0) = disabled, matching the "no
        hard-coded legal values" convention -- standalone resolutions have
        no meeting date to measure against and are never gated by this."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.resolution_notice_period_days', '0',
        )
        try:
            return int(raw or '0')
        except (TypeError, ValueError):
            return 0

    def _meeting_state_gate_enabled(self):
        """Issue #269 item 6: when enabled, action_open() refuses to open
        voting on a resolution whose meeting is still in 'draft'. Defaults
        to disabled: govoo.meeting itself defaults to 'draft' and existing
        workflows (and this module's own test suite) routinely open
        resolutions before the meeting is formally scheduled, so enabling
        this by default would silently change behavior rather than add an
        opt-in governance policy."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.resolution_meeting_state_gate_enabled', 'False',
        ) in ('True', '1')

    def _tie_break_enabled(self):
        """Issue #269 item 4: whether a tied simple-majority vote should
        wait for a chair's casting vote (tie_break_pending) instead of
        auto-failing. Unset/False preserves the original "a tie fails"
        behavior."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.resolution_tie_break_enabled', 'False',
        ) in ('True', '1')

    def _written_resolution_quorum_percentage(self):
        """Issue #269 item 7: fraction (0-1) of eligible voters a standalone
        (meeting-less) resolution needs voting for quorum to be considered
        met. Unset (None) preserves the original always-met behavior --
        the exact figure is a [CONFIRM] legal/governance-policy question,
        same discipline as _special_majority_threshold."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.written_resolution_quorum_percentage',
        )
        if not raw:
            return None
        try:
            return float(raw)
        except (TypeError, ValueError):
            return None

    def _get_eligible_voters(self):
        """Return [(partner, voter_type)] -- 'director' or 'shareholder'
        -- for this resolution, consolidating the eligibility logic
        otherwise duplicated across govoo_portal's director.py/
        shareholder.py controllers and govoo_vote.create()'s own
        weight-sourcing (issue #234). Used to decide who gets the
        voting-invite email in action_open(); a partner eligible both
        ways (e.g. a director who also holds shares) is only returned
        once, as 'director' -- the more specific relationship for a
        meeting-linked resolution.
        """
        self.ensure_one()
        voters = {}
        # Shareholder branch: same gating govoo_vote.create() already uses
        # to decide whether to source vote weight from holdings at all.
        is_shareholder_eligible_type = self.resolution_type in ('ordinary', 'special')
        is_shareholder_meeting_context = (
            not self.meeting_id or self.meeting_id.meeting_type in ('agm', 'egm')
        )
        if is_shareholder_eligible_type and is_shareholder_meeting_context:
            company_id = self.company_id.id or self.env.company.id
            holdings = self.env['govoo.share.holding'].search([
                ('company_id', '=', company_id),
                ('quantity', '>', 0),
            ])
            for partner in holdings.partner_id:
                voters[partner.id] = (partner, 'shareholder')
        # Director branch: active, non-secretary appointees of the
        # meeting's own committee -- only meaningful for a meeting-linked
        # resolution.
        if self.meeting_id:
            appointments = self.env['govoo.appointment'].search([
                ('committee_id', '=', self.meeting_id.committee_id.id),
                ('role', '!=', 'secretary'),
                ('state', '=', 'active'),
            ])
            for partner in appointments.partner_id:
                voters[partner.id] = (partner, 'director')
        return list(voters.values())

    def _compute_vote_weight_for(self, partner):
        """Issue #269 item 2: the single source of truth for what weight a
        vote by `partner` on this resolution gets -- shared by
        govoo.vote.create() (which actually sets it) and the portal's
        weight-disclosure preview (which must show the voter the exact
        same number before they submit, never an approximation)."""
        self.ensure_one()
        is_shareholder_eligible_type = self.resolution_type in ('ordinary', 'special')
        is_shareholder_meeting_context = (
            not self.meeting_id or self.meeting_id.meeting_type in ('agm', 'egm')
        )
        if is_shareholder_eligible_type and is_shareholder_meeting_context:
            company_id = self.company_id.id or self.env.company.id
            holding = self.env['govoo.share.holding'].search([
                ('partner_id', '=', partner.id),
                ('company_id', '=', company_id),
            ], limit=1)
            if holding:
                return holding.voting_power
        return 1.0

    @api.depends('vote_ids')
    def _compute_vote_count(self):
        for rec in self:
            rec.vote_count = len(rec.vote_ids)

    @api.depends('voter_notification_ids.has_portal_access')
    def _compute_unreachable_voter_count(self):
        for rec in self:
            rec.unreachable_voter_count = len(
                rec.voter_notification_ids.filtered(lambda v: not v.has_portal_access)
            )

    @api.depends_context('uid')
    @api.depends('state', 'vote_ids.voter_id')
    def _compute_requires_my_vote(self):
        partner = self.env.user.partner_id
        for rec in self:
            rec.requires_my_vote = (
                rec.state == 'open' and partner not in rec.vote_ids.voter_id
            )

    def _search_requires_my_vote(self, operator, value):
        # Boolean domain leaves are normalized by the ORM to 'in'/'not in'
        # with a set (e.g. ('requires_my_vote', 'in', {True})), not just
        # plain '='/'!=' with a scalar -- handle both forms.
        if isinstance(value, (list, tuple, set, frozenset)):
            wants_true = True in value
        else:
            wants_true = bool(value)
        if operator in ('!=', 'not in'):
            wants_true = not wants_true
        partner = self.env.user.partner_id
        matching_ids = self.search([('state', '=', 'open')]).filtered(
            lambda rec: partner not in rec.vote_ids.voter_id
        ).ids
        if wants_true:
            return [('id', 'in', matching_ids)]
        return [('id', 'not in', matching_ids)]

    def action_view_votes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Votes',
            'res_model': 'govoo.vote',
            # Issue #251: kanban added so the Votes smart button -- the only
            # UI path to this model for most users -- can actually reach the
            # new per-voter kanban card, not just the list.
            'view_mode': 'kanban,list,form',
            'domain': [('resolution_id', '=', self.id)],
            'context': {'default_resolution_id': self.id},
        }

    def _special_majority_threshold(self, raise_if_unset=False):
        """Fraction (0-1) of for+against votes a 'special' resolution must
        clear. Exact value is a genuinely open legal question
        (open-decisions.md item 11, BR-BOARD-005) -- no default is set, per
        the "no hard-coded legal values / defaults to disabled until
        confirmed" rule (architecture/technology-standards.md rule 4).
        """
        self.ensure_one()
        threshold = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.special_resolution_majority_threshold',
        )
        if not threshold:
            if raise_if_unset:
                raise ValidationError(_(
                    'Special resolution majority threshold is not configured '
                    '(BR-BOARD-005; see docs/spec/decisions/open-decisions.md '
                    'item 11 -- exact percentage pending company articles / '
                    'Rwandan law confirmation). Set the '
                    '"govoo_board.special_resolution_majority_threshold" '
                    'system parameter before tallying special resolutions.'
                ))
            return None
        return float(threshold)

    def _passes_majority(self, for_votes, against_votes, raise_if_unconfigured=False):
        self.ensure_one()
        if self.resolution_type != 'special':
            return for_votes > against_votes
        threshold = self._special_majority_threshold(raise_if_unset=raise_if_unconfigured)
        if threshold is None:
            return False
        total = for_votes + against_votes
        return total > 0 and for_votes >= threshold * total

    @api.depends(
        'vote_ids.choice', 'vote_ids.weight', 'vote_ids.is_conflicted',
        'resolution_type', 'meeting_id.quorum_met',
    )
    def _compute_result(self):
        """Compute result from vote tally (BR-BOARD-005: quorum + majority
        threshold for resolution_type). Result is only set when state is
        'passed' or 'failed'. Never raises here (unlike action_tally) --
        this compute can be triggered by unrelated writes (e.g. a vote's
        is_conflicted flag, which remains writable after immutability
        locks in), so an unconfigured special-resolution threshold falls
        back to `False` rather than blocking an unrelated write.
        """
        for rec in self:
            if rec.state not in ('passed', 'failed'):
                rec.result = False
                continue
            votes = rec.vote_ids.filtered(lambda v: not v.is_conflicted)
            for_votes = sum(votes.filtered(lambda v: v.choice == 'for').mapped('weight'))
            against_votes = sum(votes.filtered(lambda v: v.choice == 'against').mapped('weight'))
            if rec._quorum_met() and rec._passes_majority(for_votes, against_votes):
                rec.result = 'passed'
            else:
                rec.result = 'failed'

    def _validate_state_transition(self, target_state):
        """Enforce allowed state transitions."""
        allowed = {
            'draft': ['open', 'withdrawn'],
            'open': ['passed', 'failed', 'withdrawn'],
        }
        for rec in self:
            if target_state not in allowed.get(rec.state, []):
                raise ValidationError(
                    _('Cannot transition from "%s" to "%s".') % (rec.state, target_state),
                )

    def action_open(self):
        """Open resolution for voting; notify eligible voters.

        Issue #234: in addition to the existing internal activity, every
        eligible voter (see _get_eligible_voters) gets the same two-channel
        notification govoo_board_pack.py's action_distribute() uses for
        board packs -- an in-app message_post plus an actual email. A
        voter with no portal account yet is auto-granted one first (see
        govoo.resolution.voter.action_grant_portal_access -- Odoo's own
        "Grant Portal Access" flow, so they also get the standard
        set-your-password invite email) and still gets the voting-invite
        email right after; only a voter with no usable email at all stays
        flagged instead (visible via unreachable_voter_count).
        """
        self._validate_state_transition('open')
        notice_days = self._notice_period_days()
        gate_meeting_state = self._meeting_state_gate_enabled()
        for rec in self:
            if not rec.resolution_type:
                raise ValidationError(_('Resolution type must be set before opening.'))
            if gate_meeting_state and rec.meeting_id and rec.meeting_id.state == 'draft':
                raise ValidationError(_(
                    'Cannot open voting: meeting "%s" has not been scheduled '
                    'yet (still in Draft).'
                ) % rec.meeting_id.name)
            if rec.meeting_id and rec.meeting_id.state == 'cancelled':
                # Issue #271: 'cancelled' is a new meeting state this check
                # predates (#269) -- this branch is unconditional (not
                # gated by resolution_meeting_state_gate_enabled), since a
                # cancelled meeting is never a valid place to vote
                # regardless of that policy switch.
                raise ValidationError(_(
                    'Cannot open voting: meeting "%s" has been cancelled.'
                ) % rec.meeting_id.name)
            if notice_days and rec.meeting_id and rec.meeting_id.date:
                days_remaining = (rec.meeting_id.date - fields.Datetime.now()).days
                if days_remaining < notice_days:
                    raise ValidationError(_(
                        'Cannot open voting: only %d day(s) notice before the '
                        'meeting; the configured notice period '
                        '("govoo_board.resolution_notice_period_days") '
                        'requires at least %d day(s).'
                    ) % (max(days_remaining, 0), notice_days))
        self.write({'state': 'open'})
        window_days = self._voting_window_days()
        if window_days:
            self.write({'vote_deadline': fields.Datetime.now() + timedelta(days=window_days)})
        template = self.env.ref(
            'govoo_board.mail_template_resolution_voting_invite',
            raise_if_not_found=False,
        )
        for rec in self:
            # Create activity for eligible voters notification
            rec.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Vote on resolution: %s' % rec.title,
                user_id=self.env.user.id,
            )
            rec.voter_notification_ids = [
                (0, 0, {'partner_id': partner.id, 'voter_type': voter_type})
                for partner, voter_type in rec._get_eligible_voters()
            ]
            for voter in rec.voter_notification_ids.filtered(lambda v: not v.has_portal_access):
                voter.action_grant_portal_access()
            for voter in rec.voter_notification_ids.filtered('has_portal_access'):
                rec.message_post(
                    body=_('A resolution is open for your vote: %s') % rec.title,
                    partner_ids=voter.partner_id.ids,
                    subtype_xmlid='mail.mt_comment',
                )
                if template:
                    template.send_mail(voter.id, force_send=True)
                voter.notified_date = fields.Datetime.now()

    def action_tally(self):
        """Tally votes and set result (BR-BOARD-005): quorum + majority
        threshold for resolution_type. A 'special' resolution with no
        configured majority threshold raises rather than silently applying
        plain majority.

        Issue #269 item 4: a tied simple-majority vote (for == against)
        does not auto-fail when 'govoo_board.resolution_tie_break_enabled'
        is on -- there is no "chair" field anywhere in govoo.meeting to
        resolve it automatically, so the resolution is flagged
        tie_break_pending and stays open until action_chair_casting_vote()
        is called. With the flag off (the default), a tie fails exactly as
        before.
        """
        for rec in self:
            if rec.state != 'open':
                raise ValidationError(_('Can only tally an open resolution.'))
            eligible_votes = rec.vote_ids.filtered(lambda v: not v.is_conflicted)
            if not eligible_votes:
                raise ValidationError(_('No eligible votes to tally.'))
            for_votes = sum(eligible_votes.filtered(lambda v: v.choice == 'for').mapped('weight'))
            against_votes = sum(eligible_votes.filtered(lambda v: v.choice == 'against').mapped('weight'))
            if (
                rec.resolution_type != 'special'
                and for_votes == against_votes
                and rec._tie_break_enabled()
            ):
                rec.tie_break_pending = True
                continue
            if rec._quorum_met() and rec._passes_majority(
                for_votes, against_votes, raise_if_unconfigured=True,
            ):
                rec.state = 'passed'
                rec.result = 'passed'
            else:
                rec.state = 'failed'
                rec.result = 'failed'
            rec.tie_break_pending = False
            # Otherwise action_open's "Vote on resolution" activity nags as
            # overdue forever on a resolution that no longer needs a vote
            # (issue #154).
            rec.activity_feedback(['mail.mail_activity_data_todo'])

    def action_chair_casting_vote(self, decision):
        """Issue #269 item 4: resolve a tie flagged by action_tally() via
        tie_break_pending. Restricted to Secretary/Admin rather than a
        dedicated "chair" role, since no chair-role field exists anywhere
        on govoo.meeting yet -- [CONFIRM] whether a dedicated role should
        replace this group check once that's decided (same deferral
        already applied to the special-resolution majority threshold)."""
        if decision not in ('passed', 'failed'):
            raise ValidationError(_('Casting vote decision must be "passed" or "failed".'))
        if not (
            self.env.user.has_group('govoo_base.group_govoo_secretary')
            or self.env.user.has_group('govoo_base.group_govoo_admin')
        ):
            raise ValidationError(_(
                'Only the Company Secretary or Board Administrator may '
                "record a chair's casting vote."
            ))
        for rec in self:
            if not rec.tie_break_pending:
                raise ValidationError(_('This resolution has no pending tie-break.'))
            rec.state = decision
            rec.result = decision
            rec.tie_break_pending = False
            rec.activity_feedback(['mail.mail_activity_data_todo'])

    def action_chair_casting_vote_passed(self):
        """Button-friendly wrapper -- form buttons cannot pass a Python
        argument to action_chair_casting_vote()."""
        self.action_chair_casting_vote('passed')

    def action_chair_casting_vote_failed(self):
        """Button-friendly wrapper -- form buttons cannot pass a Python
        argument to action_chair_casting_vote()."""
        self.action_chair_casting_vote('failed')

    def action_withdraw(self):
        self._validate_state_transition('withdrawn')
        self.write({'state': 'withdrawn'})
        self.activity_feedback(['mail.mail_activity_data_todo'])
