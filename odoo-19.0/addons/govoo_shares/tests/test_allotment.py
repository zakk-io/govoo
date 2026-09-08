# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class GovooShareAllotmentTC(GovooShareTestBase):
    """TC-SHARE-001..004 — Allotment, transfer, holding recomputation."""

    def test_allotment_exceeds_authorised_raises(self):
        """TC-SHARE-001: Allotment + existing allotments exceed total_authorised."""
        self._make_allotment(self.partner_a, 50)
        with self.assertRaises(ValidationError):
            self.env['govoo.share.allotment'].create({
                'share_class_id': self.share_class.id,
                'partner_id': self.partner_b.id,
                'quantity': 60,  # total_authorised=100, existing=50
            })

    def test_transfer_exceeds_holding_raises(self):
        """TC-SHARE-002: Transfer quantity > transferor's current holding."""
        self._make_allotment(self.partner_a, 10)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 15,
            'date_transferred': '2026-01-15',
        })
        with self.assertRaises(ValidationError):
            transfer.action_approve()

    def test_allotment_creates_holding(self):
        """TC-SHARE-003: Allotment creates / updates holding record."""
        self._make_allotment(self.partner_a, 10)
        holding = self.env['govoo.share.holding'].search([
            ('partner_id', '=', self.partner_a.id),
            ('share_class_id', '=', self.share_class.id),
        ], limit=1)
        self.assertTrue(holding)
        self.assertEqual(holding.quantity, 10)
        self.assertEqual(holding.percentage, 100.0)
        self.assertEqual(holding.voting_power, 10.0)

    def test_transfer_updates_holdings_sum_to_100(self):
        """TC-SHARE-004: Allotments + transfer → percentages sum to 100%."""
        self._make_allotment(self.partner_a, 10)
        self._make_allotment(self.partner_b, 10)
        self._make_allotment(self.partner_c, 10)

        # Transfer 5 from A to C
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_c.id,
            'quantity': 5,
            'date_transferred': '2026-02-01',
        })
        transfer.action_approve()
        transfer.action_register()

        holdings = self.env['govoo.share.holding'].search([
            ('share_class_id', '=', self.share_class.id),
        ])
        total_qty = sum(holdings.mapped('quantity'))
        total_pct = sum(holdings.mapped('percentage'))

        self.assertEqual(total_qty, 30)
        self.assertAlmostEqual(total_pct, 100.0, places=1)

        holding_a = holdings.filtered(lambda h: h.partner_id == self.partner_a)
        holding_c = holdings.filtered(lambda h: h.partner_id == self.partner_c)
        self.assertEqual(holding_a.quantity, 5)
        self.assertEqual(holding_c.quantity, 15)
