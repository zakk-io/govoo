# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestTenderBidCopy(GovooProcurementTestBase):
    """A new vendor bid on a tender should inherit an existing sibling
    bid's line items (never its price), so every vendor quotes on the
    identical scope without retyping it by hand."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Test Switch',
            'type': 'consu',
            'purchase_ok': True,
            'standard_price': 280000,
        })

    def test_new_bid_copies_items_from_sibling_bid(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        self.env['purchase.order.line'].create({
            'order_id': bid_a.id,
            'product_id': self.product.id,
            'product_qty': 20,
        })

        bid_b = self._make_bid(tender, self.vendor_b)

        self.assertEqual(len(bid_b.order_line), 1)
        self.assertEqual(bid_b.order_line.product_id, self.product)
        self.assertEqual(bid_b.order_line.product_qty, 20)
        self.assertEqual(bid_b.order_line.price_unit, 0.0)

    def test_new_bid_stays_empty_when_no_sibling_has_items(self):
        tender = self._make_tender()
        self._make_bid(tender, self.vendor_a)
        bid_b = self._make_bid(tender, self.vendor_b)
        self.assertFalse(bid_b.order_line)

    def test_cannot_add_bid_to_an_awarded_tender(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        self._qualify_a_bid(tender)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        self._award(tender, bid)

        with self.assertRaises(ValidationError):
            self._make_bid(tender, self.vendor_b)
