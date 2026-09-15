# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooRegisterBeneficialOwner(models.Model):
    _name = 'govoo.register.beneficial.owner'
    _description = 'Register of Beneficial Owners'
    _inherit = ['mail.thread']
    _order = 'date_became_registrable desc'

    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Beneficial Owner',
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
    # [CONFIRM] exact selection values per Rwanda law — thresholds not hard-coded
    nature_of_control = fields.Selection(
        selection=[
            ('shares_25', 'Ownership of more than 25% of shares'),
            ('voting_25', 'Entitlement to more than 25% of voting rights'),
            ('board_appoint', 'Right to appoint majority of board members'),
            ('significant', 'Significant influence or control'),
        ],
        string='Nature of Control',
        required=True,
        tracking=True,
    )
    date_became_registrable = fields.Date(
        string='Date Became Registrable',
        tracking=True,
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    evidence_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Evidence Document',
    )
    is_provisional = fields.Boolean(
        string='Provisional',
        compute='_compute_is_provisional',
        store=True,
        help='True if nature_of_control uses an unconfirmed threshold category (BR-SEC-STAT-003)',
    )

    @api.depends('nature_of_control')
    def _compute_is_provisional(self):
        # All current selections are provisional until confirmed by legal advisor
        # [CONFIRM] which categories become authoritative once confirmed
        for rec in self:
            rec.is_provisional = True

    @api.constrains('nature_of_control')
    def _check_nature_of_control(self):
        for rec in self:
            if not rec.nature_of_control:
                raise ValidationError(
                    _('Nature of Control is required before this record can be marked complete.')
                )

    def _audit_log(self, change_type, effective_date):
        self.env['govoo.register.entry']._log_entry(
            register_model='govoo.register.beneficial.owner',
            res_id=self.id,
            change_type=change_type,
            effective_date=effective_date,
        )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec._audit_log(
                'create',
                rec.date_became_registrable or fields.Date.context_today(rec),
            )
        return records

    def write(self, vals):
        res = super().write(vals)
        for rec in self:
            rec._audit_log('update', fields.Date.context_today(rec))
        return res
