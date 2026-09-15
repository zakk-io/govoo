# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class GovooShareTransfer(models.Model):
    _name = 'govoo.share.transfer'
    _description = 'Share Transfer'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

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
    transferor_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transferor (Seller)',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    transferee_id = fields.Many2one(
        comodel_name='res.partner',
        string='Transferee (Buyer)',
        required=True,
        tracking=True,
        ondelete='restrict',
    )
    quantity = fields.Integer(
        string='Number of Shares',
        required=True,
        tracking=True,
    )
    price = fields.Monetary(
        string='Price',
        currency_field='currency_id',
        tracking=True,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        related='share_class_id.currency_id',
        readonly=True,
    )
    date_transferred = fields.Date(
        string='Date Transferred',
        tracking=True,
    )
    stamp_duty = fields.Monetary(
        string='Stamp Duty',
        currency_field='currency_id',
        tracking=True,
    )
    # Always ir.attachment (Many2one comodel is fixed at class-definition
    # time); when a document is generated for this field, check
    # self.env['govoo.feature.flags'].is_documents_app_installed() to
    # additionally file a copy into the Documents workspace.
    transfer_instrument_id = fields.Many2one(
        comodel_name='ir.attachment',
        string='Transfer Instrument',
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('registered', 'Registered'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
    )

    @api.constrains('quantity')
    def _check_quantity(self):
        for rec in self:
            if rec.quantity <= 0:
                raise ValidationError(_('Transfer quantity must be greater than zero.'))

    @api.constrains('transferor_id', 'transferee_id')
    def _check_parties_differ(self):
        for rec in self:
            if rec.transferor_id == rec.transferee_id:
                raise ValidationError(_('Transferor and Transferee must be different parties.'))

    def _check_transferor_holding(self):
        """Validate transfer quantity against transferor's current holding (BR-SHARE-002)."""
        for rec in self:
            holding = self.env['govoo.share.holding'].search([
                ('partner_id', '=', rec.transferor_id.id),
                ('share_class_id', '=', rec.share_class_id.id),
            ], limit=1)
            if holding and holding.quantity < rec.quantity:
                raise ValidationError(
                    _('Transfer quantity exceeds transferor\'s current holding (BR-SHARE-002).')
                )

    def action_approve(self):
        self._check_transferor_holding()
        self.write({'state': 'approved'})

    def action_register(self):
        self._check_transferor_holding()
        self.write({'state': 'registered'})
        for rec in self:
            self.env['govoo.share.holding']._recompute_holdings(rec.share_class_id.id)

    def action_draft(self):
        for rec in self:
            if rec.state == 'registered':
                raise ValidationError(_('Cannot reset a registered transfer to draft.'))
        self.write({'state': 'draft'})
