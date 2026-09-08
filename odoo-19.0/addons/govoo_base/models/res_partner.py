# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    govoo_is_director = fields.Boolean(
        string='Director',
        tracking=True,
        help='Whether this person is a director of the company',
    )
    govoo_is_shareholder = fields.Boolean(
        string='Shareholder',
        tracking=True,
        help='Whether this person is a shareholder of the company',
    )
    govoo_is_officer = fields.Boolean(
        string='Officer',
        tracking=True,
        help='Whether this person is an officer (e.g. company secretary) of the company',
    )
    govoo_is_beneficial_owner = fields.Boolean(
        string='Beneficial Owner',
        tracking=True,
        help='Whether this person is a beneficial owner of the company',
    )
    govoo_national_id = fields.Char(
        string='National ID',
        tracking=True,
        groups='govoo_base.group_govoo_secretary,govoo_base.group_govoo_admin',
    )
    govoo_date_of_birth = fields.Date(
        string='Date of Birth',
        tracking=True,
        groups='govoo_base.group_govoo_secretary,govoo_base.group_govoo_admin',
    )
    govoo_nationality_id = fields.Many2one(
        comodel_name='res.country',
        string='Nationality',
        tracking=True,
    )
    govoo_appointment_ids = fields.One2many(
        comodel_name='govoo.appointment',
        inverse_name='partner_id',
        string='Appointments',
    )

    @api.constrains('govoo_date_of_birth')
    def _check_govoo_date_of_birth(self):
        for rec in self:
            if rec.govoo_date_of_birth and rec.govoo_date_of_birth >= fields.Date.today():
                raise ValidationError(
                    _('Date of Birth must be in the past.')
                )
