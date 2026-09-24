# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooAppointment(models.Model):
    _name = 'govoo.appointment'
    _description = 'Appointment (role-over-time)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_appointed desc'
    _check_company_auto = True

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Person',
        required=True,
        tracking=True,
        ondelete='cascade',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    role = fields.Selection(
        selection=[
            ('director', 'Director'),
            ('secretary', 'Company Secretary'),
            ('chair', 'Chairperson'),
            ('md', 'Managing Director'),
            ('committee_member', 'Committee Member'),
        ],
        string='Role',
        required=True,
        tracking=True,
    )
    committee_id = fields.Many2one(
        comodel_name='govoo.committee',
        string='Committee',
        tracking=True,
        ondelete='set null',
        check_company=True,
    )
    date_appointed = fields.Date(
        string='Date Appointed',
        required=True,
        tracking=True,
    )
    date_resigned = fields.Date(
        string='Date Resigned',
        tracking=True,
    )
    end_date = fields.Date(
        string='End Date',
        tracking=True,
        help='Planned end of this appointment\'s tenure, used to trigger '
             'succession-planning reminders. Distinct from Date Resigned, '
             'which records an actual departure after the fact.',
    )
    reminder_lead_months = fields.Integer(
        string='Reminder Lead Time (Months)',
        default=3,
        tracking=True,
        help='How many months before End Date to stage a succession-'
             'planning reminder (e.g. 1-6 months). No reminder is staged '
             'if End Date is not set.',
    )
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('resigned', 'Resigned'),
        ],
        string='Status',
        compute='_compute_state',
        store=True,
        tracking=True,
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    appointment_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Appointment Document',
    )

    @api.depends('date_appointed', 'date_resigned')
    def _compute_state(self):
        for rec in self:
            if rec.date_resigned and rec.date_resigned <= fields.Date.context_today(rec):
                rec.state = 'resigned'
            else:
                rec.state = 'active'

    @api.constrains('date_resigned', 'date_appointed', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.date_resigned and rec.date_appointed:
                if rec.date_resigned < rec.date_appointed:
                    raise ValidationError(
                        _('Date Resigned must be greater than or equal to Date Appointed.')
                    )
            if rec.end_date and rec.date_appointed:
                if rec.end_date < rec.date_appointed:
                    raise ValidationError(
                        _('End Date must be greater than or equal to Date Appointed.')
                    )

    @api.model
    def _cron_send_succession_reminders(self):
        """Succession-planning reminders (issue #200): reuses the exact
        same mail.activity-staging technique as govoo_contracts' key-date
        reminders (govoo_contracts.models.govoo_contract_cron) -- not a
        new/parallel reminder engine. Only active appointments with an
        End Date and a positive reminder lead time are considered;
        open-ended appointments (no End Date) never generate a reminder.
        """
        today = fields.Date.context_today(self)
        appointments = self.search([
            ('state', '=', 'active'),
            ('end_date', '!=', False),
        ])
        for appointment in appointments:
            lead_months = appointment.reminder_lead_months or 0
            if lead_months <= 0:
                continue
            days_to_end = (appointment.end_date - today).days
            lead_days = lead_months * 30
            if 0 < days_to_end <= lead_days:
                appointment.activity_schedule(
                    activity_type_id=self.env.ref(
                        'mail.mail_activity_data_todo',
                    ).id,
                    summary='Succession planning: %s\'s appointment ends '
                            'in %d days' % (
                                appointment.partner_id.name, days_to_end,
                            ),
                    user_id=appointment.create_uid.id,
                )

    @api.depends('partner_id.name', 'role')
    def _compute_display_name(self):
        # No plain-text field on this model (a Many2one can't be used as
        # _rec_name -- its default display conversion is str(recordset),
        # not the related record's display name), so display_name would
        # otherwise fall back to the raw "govoo.appointment,<id>" string.
        role_labels = dict(self._fields['role']._description_selection(self.env))
        for rec in self:
            role_label = role_labels.get(rec.role, rec.role)
            rec.display_name = '%s — %s' % (rec.partner_id.name, role_label) \
                if rec.partner_id else role_label
