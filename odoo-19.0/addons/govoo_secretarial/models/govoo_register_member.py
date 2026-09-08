# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooRegisterMember(models.Model):
    """Register of Members — curated from share holdings (govoo_shares)."""
    _name = 'govoo.register.member'
    _description = 'Register of Members'
    _inherit = ['mail.thread']
    _order = 'date_entered desc'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Shareholder',
        required=True,
        ondelete='restrict',
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    date_entered = fields.Date(
        string='Date Entered',
    )
    date_ceased = fields.Date(
        string='Date Ceased',
        help='Set when aggregate holding reaches zero',
    )

    @api.constrains('date_ceased', 'date_entered')
    def _check_dates(self):
        for rec in self:
            if rec.date_ceased and rec.date_entered:
                if rec.date_ceased < rec.date_entered:
                    raise ValidationError(
                        _('Date Ceased must be on or after Date Entered.')
                    )

    def _audit_log(self, change_type, effective_date):
        self.env['govoo.register.entry']._log_entry(
            register_model='govoo.register.member',
            res_id=self.id,
            change_type=change_type,
            effective_date=effective_date,
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._audit_log('create', rec.date_entered or fields.Date.context_today(rec))
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'date_ceased' in vals and rec.date_ceased:
                rec._audit_log('cease', rec.date_ceased)
            else:
                rec._audit_log('update', fields.Date.context_today(rec))
        return res
