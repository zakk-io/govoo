# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooRegisterCharge(models.Model):
    """Register of Charges. Charges are never deleted, only marked satisfied (BR-SEC-STAT-004)."""
    _name = 'govoo.register.charge'
    _description = 'Register of Charges'
    _inherit = ['mail.thread']
    _order = 'date_created desc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        ondelete='cascade',
    )
    chargee_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Chargee',
        ondelete='restrict',
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
    )
    date_created = fields.Date(
        string='Date Created',
    )
    date_registered = fields.Date(
        string='Date Registered',
    )
    property_description = fields.Text(
        string='Property Description',
    )
    satisfied = fields.Boolean(
        string='Satisfied',
        default=False,
        tracking=True,
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    charge_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Charge Document',
    )

    @api.constrains('amount')
    def _check_amount(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_('Charge amount must be greater than zero.'))

    @api.constrains('date_registered', 'date_created')
    def _check_dates(self):
        for rec in self:
            if rec.date_registered and rec.date_created:
                if rec.date_registered < rec.date_created:
                    raise ValidationError(
                        _('Date Registered must be on or after Date Created.')
                    )

    def _audit_log(self, change_type, effective_date):
        self.env['govoo.register.entry']._log_entry(
            register_model='govoo.register.charge',
            res_id=self.id,
            change_type=change_type,
            effective_date=effective_date,
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._audit_log('create', rec.date_created or fields.Date.context_today(rec))
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            if 'satisfied' in vals and rec.satisfied:
                rec._audit_log('cease', fields.Date.context_today(rec))
            else:
                rec._audit_log('update', fields.Date.context_today(rec))
        return res

    def unlink(self):
        """Charges are never deleted, only satisfied (BR-SEC-STAT-004)."""
        raise ValidationError(_('Charges cannot be deleted. Mark as satisfied instead.'))
