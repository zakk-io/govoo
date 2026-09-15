# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooShareAllotment(models.Model):
    _name = 'govoo.share.allotment'
    _description = 'Share Allotment (Issuance)'
    _inherit = ['mail.thread']
    _order = 'date_allotted desc'

    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        tracking=True,
        ondelete='cascade',
    )
    share_class_id = fields.Many2one(
        comodel_name='govoo.share.class',
        string='Share Class',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Allottee',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    quantity = fields.Integer(
        string='Number of Shares',
        required=True,
        tracking=True,
    )
    price_per_share = fields.Monetary(
        string='Price per Share',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='share_class_id.currency_id',
        readonly=True,
    )
    date_allotted = fields.Date(
        string='Date Allotted',
        tracking=True,
    )
    certificate_no = fields.Char(
        string='Certificate Number',
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    certificate_document_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Share Certificate',
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_('Allotment quantity must be greater than zero.'))

    @api.constrains('share_class_id', 'quantity')
    def _check_authorised_limit(self):
        for rec in self:
            if rec.share_class_id:
                existing = sum(
                    rec.share_class_id.allotment_ids
                    .filtered(lambda a: a.id != rec.id)
                    .mapped('quantity'),
                )
                if existing + rec.quantity > rec.share_class_id.total_authorised:
                    raise ValidationError(
                        _('Allotment would exceed total authorised shares for this class (BR-SHARE-001).')
                    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            self.env['govoo.share.holding']._recompute_holdings(rec.share_class_id.id)
        return records

    def unlink(self):
        classes = self.mapped('share_class_id')
        res = super().unlink()
        for cls in classes:
            self.env['govoo.share.holding']._recompute_holdings(cls.id)
        return res
