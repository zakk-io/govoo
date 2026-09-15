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

    @api.constrains('date_resigned', 'date_appointed')
    def _check_dates(self):
        for rec in self:
            if rec.date_resigned and rec.date_appointed:
                if rec.date_resigned < rec.date_appointed:
                    raise ValidationError(
                        _('Date Resigned must be greater than or equal to Date Appointed.')
                    )
