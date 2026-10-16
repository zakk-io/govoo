# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.depends('order_id.govoo_tender_id')
    def _compute_price_unit_and_date_planned_and_name(self):
        """A competitive tender bid must never suggest a price to the
        vendor -- native Odoo auto-fills Unit Price from the product's
        Cost (or a vendor-specific price, if one exists) the moment a
        product is added to a line, which both leaks the company's
        internal cost basis to the officer and anchors what should be an
        independent vendor quote. Force it back to 0.00 for any line on a
        tender-linked bid, whether the product already existed or was just
        created inline -- both paths set product_id on the line, which
        triggers this same compute.

        A manually-typed price still sticks: native _reset_price_unit()
        sets price_unit and technical_price_unit to the same value, and
        the base method's own guard (`technical_price_unit != price_unit`)
        skips recomputing once a human edits price_unit directly, leaving
        the two fields unequal. Calling _reset_price_unit(0.0) here keeps
        them equal again, so a later recompute trigger (e.g. a different
        product or a quantity change) will still re-run and get reset back
        to 0.00, exactly like a fresh, never-touched line.
        """
        super()._compute_price_unit_and_date_planned_and_name()
        for line in self:
            if line.order_id.govoo_tender_id and line.product_id and line.price_unit:
                line._reset_price_unit(0.0)
