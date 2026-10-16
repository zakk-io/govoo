# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestTenderBidPrice(GovooProcurementTestBase):
    """A competitive tender bid must never suggest a price to the vendor --
    confirms Unit Price defaults to 0.00 on a tender-linked bid even when
    the product has a non-zero Cost, while normal (non-tender) purchasing
    keeps the native auto-suggested price."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Switch',
            'type': 'consu',
            'purchase_ok': True,
            'standard_price': 280000,
        })

    def test_tender_bid_line_price_defaults_to_zero(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        line = self.env['purchase.order.line'].create({
            'order_id': bid.id,
            'product_id': self.product.id,
            'product_qty': 1,
        })
        self.assertEqual(line.price_unit, 0.0)

    def test_manual_price_on_tender_bid_line_still_sticks(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        line = self.env['purchase.order.line'].create({
            'order_id': bid.id,
            'product_id': self.product.id,
            'product_qty': 1,
        })
        line.price_unit = 850000
        self.assertEqual(line.price_unit, 850000)

    def test_normal_non_tender_po_keeps_native_price_suggestion(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.vendor_a.id,
            'company_id': self.company.id,
        })
        line = self.env['purchase.order.line'].create({
            'order_id': po.id,
            'product_id': self.product.id,
            'product_qty': 1,
        })
        self.assertEqual(line.price_unit, 280000)
