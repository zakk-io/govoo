# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooResolution(models.Model):
    _name = 'govoo.resolution'
    _description = 'Resolution'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'

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
        related='meeting_id.company_id',
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
    # Feature-flagged: ir.attachment (Community) / sign.request (Enterprise)
    sign_request_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Sign Request',
    )

    def _compute_access_url(self):
        super()._compute_access_url()
        for rec in self:
            rec.access_url = '/my/votes/%s' % rec.id

    @api.depends('vote_ids')
    def _compute_vote_count(self):
        for rec in self:
            rec.vote_count = len(rec.vote_ids)

    def action_view_votes(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Votes',
            'res_model': 'govoo.vote',
            'view_mode': 'list,form',
            'domain': [('resolution_id', '=', self.id)],
            'context': {'default_resolution_id': self.id},
        }

    @api.depends('vote_ids.choice', 'vote_ids.weight', 'vote_ids.is_conflicted')
    def _compute_result(self):
        """Compute result from vote tally.

        Result is only set when state is 'passed' or 'failed'.
        """
        for rec in self:
            if rec.state not in ('passed', 'failed'):
                rec.result = False
                continue
            votes = rec.vote_ids.filtered(lambda v: not v.is_conflicted)
            for_votes = sum(votes.filtered(lambda v: v.choice == 'for').mapped('weight'))
            against_votes = sum(votes.filtered(lambda v: v.choice == 'against').mapped('weight'))
            # Majority threshold: more for than against (ordinary);
            # higher threshold for special — [CONFIRM exact percentage per articles]
            if for_votes > against_votes:
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
        """Open resolution for voting; notify eligible voters."""
        self._validate_state_transition('open')
        for rec in self:
            if not rec.resolution_type:
                raise ValidationError(_('Resolution type must be set before opening.'))
        self.write({'state': 'open'})
        for rec in self:
            # Create activity for eligible voters notification
            rec.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                summary='Vote on resolution: %s' % rec.title,
                user_id=self.env.user.id,
            )

    def action_tally(self):
        """Tally votes and set result (BR-BOARD-005).

        System-computed from vote rows; quorum + majority threshold
        depends on resolution_type. [CONFIRM exact thresholds per articles].
        """
        for rec in self:
            if rec.state != 'open':
                raise ValidationError(_('Can only tally an open resolution.'))
            eligible_votes = rec.vote_ids.filtered(lambda v: not v.is_conflicted)
            if not eligible_votes:
                raise ValidationError(_('No eligible votes to tally.'))
            for_votes = sum(eligible_votes.filtered(lambda v: v.choice == 'for').mapped('weight'))
            against_votes = sum(eligible_votes.filtered(lambda v: v.choice == 'against').mapped('weight'))
            if for_votes > against_votes:
                rec.state = 'passed'
                rec.result = 'passed'
            else:
                rec.state = 'failed'
                rec.result = 'failed'

    def action_withdraw(self):
        self._validate_state_transition('withdrawn')
        self.write({'state': 'withdrawn'})
