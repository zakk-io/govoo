# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model_create_multi
    def create(self, vals_list):
        """Issue found while manually testing a 5-vendor tender: retyping
        the same line items on every vendor bid is tedious and risks the
        items silently drifting between vendors, which breaks a fair
        comparison. When a new bid is added to a tender that already has a
        sibling bid with items, copy the items (product/qty/description)
        onto it automatically -- never the price, since each vendor's
        price must stay independently theirs (the price_unit=0.0
        guarantee in purchase_order_line.py already covers any line linked
        to a tender, so this is safe with no extra code). Forward-only: if
        no sibling has items yet, the new bid just starts empty, same as
        before this existed.

        Also blocks adding a brand-new, unscored bid to a tender that's
        already been Awarded, matching the same "Awarded = locked" rule
        already applied to a tender's documents (ir_attachment.py).
        """
        for vals in vals_list:
            tender_id = vals.get('govoo_tender_id')
            if tender_id:
                tender = self.env['govoo.tender'].browse(tender_id)
                if tender.evaluation_stage == 'awarded':
                    raise ValidationError(_(
                        'A new vendor bid cannot be added once a tender '
                        'is Awarded.'
                    ))
        orders = super().create(vals_list)
        for order in orders:
            if order.govoo_tender_id and not order.order_line:
                sibling = order.govoo_tender_id.bid_ids.filtered(
                    lambda b: b.id != order.id and b.order_line
                )[:1]
                if sibling:
                    order.order_line = [
                        Command.create({
                            'product_id': line.product_id.id,
                            'name': line.name,
                            'product_qty': line.product_qty,
                            'product_uom_id': line.product_uom_id.id,
                        })
                        for line in sibling.order_line
                        if not line.display_type
                    ]
        return orders

    govoo_tender_id = fields.Many2one(
        comodel_name='govoo.tender',
        string='Tender',
        ondelete='set null',
        tracking=True,
        help='Links this vendor bid (a normal RFQ/purchase order) to the '
             "governance-tracked tender case file it's part of.",
    )
    govoo_technical_score = fields.Float(
        string='Technical Score',
        tracking=True,
        help='[CONFIRM] The scoring scale and technical-vs-financial '
             'weighting for tender evaluation are not specified (issue '
             '#205 sub-task). Recorded here as a plain 0-100 score per '
             'the committee\'s own methodology; no combined/weighted '
             'score is computed until that weighting is confirmed.',
    )
    govoo_financial_score = fields.Float(
        string='Financial Score',
        tracking=True,
        help='[CONFIRM] See govoo_technical_score -- weighting not yet confirmed.',
    )

    @api.constrains('govoo_technical_score', 'govoo_financial_score')
    def _check_govoo_scores_range(self):
        for rec in self:
            for field_name in ('govoo_technical_score', 'govoo_financial_score'):
                value = rec[field_name]
                if value and not (0 <= value <= 100):
                    raise ValidationError(_(
                        '%s must be between 0 and 100.'
                    ) % rec._fields[field_name].string)
