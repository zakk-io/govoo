# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class GovooMeeting(models.Model):
    _name = 'govoo.meeting'
    _description = 'Board / Committee Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date desc'

    name = fields.Char(
        string='Meeting Name',
        required=True,
        tracking=True,
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    committee_id = fields.Many2one(
        comodel_name='govoo.committee',
        string='Committee',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    meeting_type = fields.Selection(
        selection=[
            ('board', 'Board Meeting'),
            ('committee', 'Committee Meeting'),
            ('agm', 'Annual General Meeting'),
            ('egm', 'Extraordinary General Meeting'),
            ('executive', 'Executive Management Meeting'),
            ('departmental', 'Departmental Meeting'),
        ],
        string='Meeting Type',
        required=True,
        tracking=True,
        help='Issue #202: "executive" and "departmental" meetings are '
             'confidentiality-partitioned by committee_id.member_ids -- '
             'see govoo_meeting_confidential_comp_rule -- unlike board/'
             'committee/agm/egm meetings, which remain visible to every '
             'internal governance user as before.',
    )
    calendar_event_id = fields.Many2one(
        comodel_name='calendar.event',
        string='Calendar Event',
        tracking=True,
    )
    date = fields.Datetime(
        string='Start Date',
        required=True,
        tracking=True,
    )
    date_end = fields.Datetime(
        string='End Date',
        tracking=True,
    )
    location = fields.Char(
        string='Location',
    )
    virtual_link = fields.Char(
        string='Virtual Meeting Link',
    )
    attendee_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Invited Attendees',
    )
    confirmed_attendee_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='govoo_meeting_confirmed_attendee_rel',
        column1='meeting_id',
        column2='partner_id',
        string='Attendees Present',
        help='Issue #271 item 4: who actually attended, distinct from '
             'attendee_ids (who was invited). Quorum is computed from this '
             'list once it has been populated; left empty, quorum falls '
             'back to the invite list exactly as before this field '
             'existed.',
    )
    quorum_required = fields.Integer(
        string='Quorum Required',
        required=True,
        default=1,
        tracking=True,
    )
    quorum_met = fields.Boolean(
        string='Quorum Met',
        compute='_compute_quorum_met',
        store=True,
    )
    agenda_ids = fields.One2many(
        comodel_name='govoo.agenda.item',
        inverse_name='meeting_id',
        string='Agenda Items',
    )
    pack_id = fields.Many2one(
        comodel_name='govoo.board.pack',
        string='Board Pack',
    )
    minutes_id = fields.Many2one(
        comodel_name='govoo.minutes',
        string='Minutes',
    )
    resolution_ids = fields.One2many(
        comodel_name='govoo.resolution',
        inverse_name='meeting_id',
        string='Resolutions',
    )
    agenda_count = fields.Integer(
        string='Agenda Items',
        compute='_compute_agenda_count',
    )
    pack_count = fields.Integer(
        string='Pack',
        compute='_compute_pack_count',
    )
    minutes_count = fields.Integer(
        string='Minutes',
        compute='_compute_minutes_count',
    )
    resolution_count = fields.Integer(
        string='Resolutions',
        compute='_compute_resolution_count',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('held', 'Held'),
            ('minuted', 'Minuted'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )
    cancel_reason = fields.Char(
        string='Cancellation Reason',
        copy=False,
    )
    rescheduled_from_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Rescheduled From',
        readonly=True,
        copy=False,
    )
    rescheduled_to_id = fields.Many2one(
        comodel_name='govoo.meeting',
        string='Rescheduled To',
        readonly=True,
        copy=False,
    )

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/meetings/%s' % rec.id

    @api.depends('agenda_ids')
    def _compute_agenda_count(self):
        for rec in self:
            rec.agenda_count = len(rec.agenda_ids)

    @api.depends('pack_id')
    def _compute_pack_count(self):
        for rec in self:
            rec.pack_count = 1 if rec.pack_id else 0

    @api.depends('minutes_id')
    def _compute_minutes_count(self):
        for rec in self:
            rec.minutes_count = 1 if rec.minutes_id else 0

    @api.depends('resolution_ids')
    def _compute_resolution_count(self):
        for rec in self:
            rec.resolution_count = len(rec.resolution_ids)

    def action_view_agenda(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Agenda Items',
            'res_model': 'govoo.agenda.item',
            'view_mode': 'list,form',
            'domain': [('meeting_id', '=', self.id)],
            'context': {'default_meeting_id': self.id},
        }

    def action_view_pack(self):
        self.ensure_one()
        if not self.pack_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Board Pack',
            'res_model': 'govoo.board.pack',
            'view_mode': 'form',
            'res_id': self.pack_id.id,
        }

    def action_view_minutes(self):
        self.ensure_one()
        if not self.minutes_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'name': 'Minutes',
            'res_model': 'govoo.minutes',
            'view_mode': 'form',
            'res_id': self.minutes_id.id,
        }

    def action_create_pack(self):
        """Create the board pack for this meeting and open it -- the Pack
        tab's empty state's call-to-action (issue #152). govoo.board.pack's
        own create() links itself back onto meeting.pack_id.
        """
        self.ensure_one()
        pack = self.env['govoo.board.pack'].create({'meeting_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Board Pack',
            'res_model': 'govoo.board.pack',
            'view_mode': 'form',
            'res_id': pack.id,
        }

    def action_create_minutes(self):
        """Create the minutes for this meeting and open it -- the Minutes
        tab's empty state's call-to-action (issue #152).
        """
        self.ensure_one()
        minutes = self.env['govoo.minutes'].create({'meeting_id': self.id})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Minutes',
            'res_model': 'govoo.minutes',
            'view_mode': 'form',
            'res_id': minutes.id,
        }

    def action_create_resolution(self):
        """Resolutions' empty-state call-to-action (issue #273), matching
        action_create_pack()/action_create_minutes() above. Unlike those
        two, govoo.resolution has required fields (title, resolution_type)
        that can't be meaningfully defaulted, so this opens a blank create
        form pre-seeded with meeting_id via context instead of
        pre-creating a placeholder record."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resolution',
            'res_model': 'govoo.resolution',
            'view_mode': 'form',
            'context': {'default_meeting_id': self.id},
        }

    def action_view_resolutions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Resolutions',
            'res_model': 'govoo.resolution',
            'view_mode': 'list,form,kanban',
            'domain': [('meeting_id', '=', self.id)],
            'context': {'default_meeting_id': self.id},
        }

    @api.depends('attendee_ids', 'confirmed_attendee_ids', 'quorum_required')
    def _compute_quorum_met(self):
        for rec in self:
            attendees = rec.confirmed_attendee_ids if rec.confirmed_attendee_ids else rec.attendee_ids
            rec.quorum_met = len(attendees) >= rec.quorum_required

    @api.constrains('quorum_required')
    def _check_quorum_required(self):
        for rec in self:
            if rec.quorum_required <= 0:
                raise ValidationError(_('Quorum Required must be greater than zero.'))

    def _validate_state_transition(self, target_state):
        """Enforce strictly forward, one-step state transitions (BR-BOARD-002).

        Issue #271 item 2: 'cancelled' is reachable from 'draft'/'scheduled'
        only -- a meeting already 'held' is history, not cancellable. It is
        otherwise a dead end (no transition out of it), same as the other
        terminal states.
        """
        allowed = {
            'draft': ['scheduled', 'cancelled'],
            'scheduled': ['held', 'cancelled'],
            'held': ['minuted'],
            'minuted': ['closed'],
        }
        for rec in self:
            if target_state not in allowed.get(rec.state, []):
                raise ValidationError(
                    _('Cannot transition from "%s" to "%s". '
                      'State transitions must be strictly forward, one step at a time.')
                    % (rec.state, target_state),
                )

    def _meeting_notice_period_days(self):
        """Issue #271 item 3: minimum days between scheduling a meeting and
        its date. Unset (0) = disabled, matching the resolution notice
        period convention from #269."""
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.meeting_notice_period_days', '0',
        )
        try:
            return int(raw or '0')
        except (TypeError, ValueError):
            return 0

    def _close_requires_minutes_approved(self):
        """Issue #271 item 8: unset/False preserves the original behavior
        (action_minute()'s 'for_approval' precondition is enough to close)."""
        return self.env['ir.config_parameter'].sudo().get_param(
            'govoo_board.meeting_close_requires_minutes_approved', 'False',
        ) in ('True', '1')

    def action_schedule(self):
        self._validate_state_transition('scheduled')
        notice_days = self._meeting_notice_period_days()
        if notice_days:
            for rec in self:
                if rec.date:
                    days_remaining = (rec.date - fields.Datetime.now()).days
                    if days_remaining < notice_days:
                        raise ValidationError(_(
                            'Cannot schedule: only %d day(s) notice before '
                            'the meeting; the configured notice period '
                            '("govoo_board.meeting_notice_period_days") '
                            'requires at least %d day(s).'
                        ) % (max(days_remaining, 0), notice_days))
        alarm = self.env.ref('govoo_board.alarm_meeting_email_1_day', raise_if_not_found=False)
        for rec in self:
            if not rec.calendar_event_id and rec.date:
                stop = rec.date_end or rec.date
                event = self.env['calendar.event'].create({
                    'name': rec.name,
                    'start': rec.date,
                    'stop': stop,
                    'partner_ids': [(6, 0, rec.attendee_ids.ids)],
                    'user_id': self.env.user.id,
                    # Issue #236: without an alarm, Odoo's own calendar
                    # reminder engine never fires for this event -- there
                    # was previously no "your meeting is in N days"
                    # notification of any kind for board/committee
                    # meetings.
                    'alarm_ids': [(6, 0, alarm.ids)] if alarm else False,
                })
                rec.calendar_event_id = event
        self.write({'state': 'scheduled'})

    def action_hold(self):
        """Whether a Secretary override should be able to bypass this
        block is an open decision [CONFIRM] (state-machines.md,
        open-decisions.md #9) -- until confirmed, this transition is
        hard-blocked with no override path.
        """
        self._validate_state_transition('held')
        for rec in self:
            if not rec.quorum_met:
                attendees = rec.confirmed_attendee_ids if rec.confirmed_attendee_ids else rec.attendee_ids
                raise UserError(
                    _('Cannot mark meeting as held: quorum not met '
                      '(%d of %d required).')
                    % (len(attendees), rec.quorum_required)
                )
        self.write({'state': 'held'})

    def action_minute(self):
        self._validate_state_transition('minuted')
        for rec in self:
            if not rec.minutes_id:
                raise ValidationError(_('Minutes must be created before marking meeting as minuted.'))
            if rec.minutes_id.state not in ('for_approval', 'approved', 'signed'):
                raise ValidationError(
                    _('Minutes must be at least "For Approval" before marking meeting as minuted.')
                )
        self.write({'state': 'minuted'})

    def action_close(self):
        self._validate_state_transition('closed')
        requires_minutes_approved = self._close_requires_minutes_approved()
        for rec in self:
            terminal_states = ('passed', 'failed', 'withdrawn')
            non_terminal = rec.resolution_ids.filtered(
                lambda r: r.state not in terminal_states,
            )
            if non_terminal:
                raise ValidationError(
                    _('Cannot close meeting: %d resolution(s) are not yet in a terminal state.')
                    % len(non_terminal),
                )
            if requires_minutes_approved and rec.minutes_id.state not in ('approved', 'signed'):
                raise ValidationError(_(
                    'Cannot close meeting: minutes must be "Approved" or '
                    '"Signed" first ("govoo_board.meeting_close_requires_minutes_approved").'
                ))
        self.write({'state': 'closed'})

    def action_cancel(self, reason=None):
        """Issue #271 item 2: cancel a meeting before it's held -- a
        meeting already 'held' is history, not cancellable (enforced by
        _validate_state_transition). Blocks on any non-terminal resolution,
        the same guard action_close() already applies, so an in-progress
        vote is never silently orphaned against a cancelled meeting (the
        #269 auto-close cron would otherwise still find and tally it
        later)."""
        self._validate_state_transition('cancelled')
        for rec in self:
            terminal_states = ('passed', 'failed', 'withdrawn')
            non_terminal = rec.resolution_ids.filtered(
                lambda r: r.state not in terminal_states,
            )
            if non_terminal:
                raise ValidationError(_(
                    'Cannot cancel meeting: %d resolution(s) are not yet in '
                    'a terminal state. Withdraw them first.'
                ) % len(non_terminal))
        self.write({'state': 'cancelled', 'cancel_reason': reason or False})

    def action_reschedule(self, new_date):
        """Issue #271 item 2: cancel this meeting and create a new, linked
        one at new_date, carrying over committee/attendees/quorum setup.
        Deliberately does NOT copy agenda items or resolutions -- deep-
        copying linked resolutions could affect vote state and needs its
        own design pass (explicitly out of scope, see issue #271)."""
        self.ensure_one()
        self.action_cancel(reason=_('Rescheduled'))
        new_meeting = self.copy({
            'name': self.name,
            'date': new_date,
            'date_end': False,
            'state': 'draft',
            'calendar_event_id': False,
            'pack_id': False,
            'minutes_id': False,
            'agenda_ids': [],
            'resolution_ids': [],
            'confirmed_attendee_ids': [(6, 0, [])],
            'rescheduled_from_id': False,
            'rescheduled_to_id': False,
            'cancel_reason': False,
        })
        self.rescheduled_to_id = new_meeting
        new_meeting.rescheduled_from_id = self
        return new_meeting
