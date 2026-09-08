# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class GovooShareHoldingTC(GovooShareTestBase):
    """TC-SHARE-003, 004 — Holding recomputation and multi-party scenarios."""

    def test_multi_party_allotments(self):
        """Three allotments, verify each holding computed correctly."""
        self._make_allotment(self.partner_a, 10)
        self._make_allotment(self.partner_b, 10)
        self._make_allotment(self.partner_c, 10)

        holdings = self.env['govoo.share.holding'].search([
            ('share_class_id', '=', self.share_class.id),
        ])
        self.assertEqual(len(holdings), 3)

        for h in holdings:
            self.assertEqual(h.quantity, 10)
            self.assertAlmostEqual(h.percentage, 33.33, places=1)
            self.assertEqual(h.voting_power, 10.0)

    def test_holding_percentage_sum(self):
        """Percentages across all holders sum to 100%."""
        self._make_allotment(self.partner_a, 7)
        self._make_allotment(self.partner_b, 3)

        holdings = self.env['govoo.share.holding'].search([
            ('share_class_id', '=', self.share_class.id),
        ])
        total_pct = sum(holdings.mapped('percentage'))
        self.assertAlmostEqual(total_pct, 100.0, places=1)

    def test_voting_power_computed(self):
        """Voting power = quantity * votes_per_share."""
        self.share_class.votes_per_share = 2.0
        self._make_allotment(self.partner_a, 10)

        holding = self.env['govoo.share.holding'].search([
            ('partner_id', '=', self.partner_a.id),
            ('share_class_id', '=', self.share_class.id),
        ], limit=1)
        self.assertEqual(holding.voting_power, 20.0)
