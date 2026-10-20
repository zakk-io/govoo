# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import Command, _, api, fields, models
from odoo.exceptions import AccessError, ValidationError

_GOVOO_SCORE_FIELDS = ('govoo_technical_score', 'govoo_financial_score')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _check_officer_not_scoring(self, vals):
        """Issue #318: the Procurement Officer role no longer gets to enter
        a bid score directly, full stop, now that a dedicated Evaluator
        role exists for it. Checked via has_group() rather than relying on
        this model's own ACL, since this needs to hold even when the call
        comes in through a sudo()-elevated path (sudo() never changes
        self.env.user, only bypasses access rights) -- the Evaluator's own
        scoring wizard still works because the real calling user there is
        the Evaluator, not the Officer.
        """
        if any(field_name in vals for field_name in _GOVOO_SCORE_FIELDS):
            if self.env.user.has_group('govoo_procurement.group_govoo_procurement_officer'):
                raise AccessError(_(
                    'Procurement Officers can no longer enter a Technical/'
                    'Financial score directly. Ask a Procurement Evaluator '
                    'to submit the score instead.'
                ))

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
            self._check_officer_not_scoring(vals)
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

    def write(self, vals):
        self._check_officer_not_scoring(vals)
        return super().write(vals)

    govoo_tender_id = fields.Many2one(
        comodel_name='govoo.tender',
        string='Tender',
        ondelete='set null',
        tracking=True,
        help='Links this vendor bid (a normal RFQ/purchase order) to the '
             "governance-tracked tender case file it's part of.",
    )
    tender_evaluation_stage = fields.Selection(
        related='govoo_tender_id.evaluation_stage',
        string='Tender Evaluation Stage',
        help='Read-only passthrough so the Documents tab below can be '
             'made readonly once the parent tender is Awarded -- view '
             'readonly/invisible conditions can only reference a field on '
             'this record itself, not a dotted path through a Many2one.',
    )
    # Issue #338: the tender itself already has its own document_ids
    # (govoo.tender.document_ids) for the RFQ pack / TOR shared by every
    # bidder; this is the bidder's own submitted documents (certificates,
    # proposals, registration, etc.), scoped to this one bid only. Same
    # shape as govoo.tender.document_ids, same lock-once-Awarded
    # discipline (ir_attachment.py), reusing that discipline rather than
    # a parallel one.
    document_ids = fields.One2many(
        comodel_name='ir.attachment',
        inverse_name='res_id',
        domain=[('res_model', '=', 'purchase.order')],
        string='Bid Documents',
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
