# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError, UserError


class GovooMeeting(models.Model):
    _name = 'govoo.meeting'
    _description = 'Board / Committee Meeting'
    _inherit = ['mail.thread', 'mail.activity.mixin']
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
        ],
        string='Meeting Type',
        required=True,
        tracking=True,
    )
    calendar_event_id = fields.Many2one(
        comodel_name='calendar.event',
        string='Calendar Event',
        tracking=True,
    )
    date = fields.Datetime(
        string='Meeting Date',
        required=True,
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
        string='Attendees',
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
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('scheduled', 'Scheduled'),
            ('held', 'Held'),
            ('minuted', 'Minuted'),
            ('closed', 'Closed'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    @api.depends('attendee_ids', 'quorum_required')
    def _compute_quorum_met(self):
        for rec in self:
            rec.quorum_met = len(rec.attendee_ids) >= rec.quorum_required

    @api.constrains('quorum_required')
    def _check_quorum_required(self):
        for rec in self:
            if rec.quorum_required <= 0:
                raise ValidationError(_('Quorum Required must be greater than zero.'))

    def _validate_state_transition(self, target_state):
        """Enforce strictly forward, one-step state transitions (BR-BOARD-002)."""
        allowed = {
            'draft': ['scheduled'],
            'scheduled': ['held'],
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

    def action_schedule(self):
        self._validate_state_transition('scheduled')
        for rec in self:
            if not rec.calendar_event_id and rec.date:
                event = self.env['calendar.event'].create({
                    'name': rec.name,
                    'start': rec.date,
                    'stop': rec.date,
                    'partner_ids': [(6, 0, rec.attendee_ids.ids)],
                    'user_id': self.env.user.id,
                })
                rec.calendar_event_id = event
        self.write({'state': 'scheduled'})

    def action_hold(self):
        self._validate_state_transition('held')
        for rec in self:
            if not rec.quorum_met:
                raise UserError(
                    _('Warning: Quorum not met (%d of %d required). '
                      'Proceed anyway?')
                    % (len(rec.attendee_ids), rec.quorum_required)
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
        self.write({'state': 'closed'})
