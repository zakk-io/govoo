# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestShareLifecycle(GovooShareTestBase):
    """TC-WF-SHARE-001: class -> allot 600/400 -> transfer 200 -> register.
    Final holdings 400/400/200, percentages sum to 100%."""

    def test_full_share_lifecycle(self):
        share_class = self.env['govoo.share.class'].create({
            'name': 'Lifecycle Ordinary Shares',
            'nominal_value': 1000,
            'total_authorised': 1000,
            'company_id': self.company.id,
        })
        partner_third = self.env['res.partner'].create({'name': 'Shareholder D'})

        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 600,
            'date_allotted': '2026-01-01',
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_b.id,
            'quantity': 400,
            'date_allotted': '2026-01-01',
        })

        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': partner_third.id,
            'quantity': 200,
            'date_transferred': '2026-02-01',
        })
        transfer.action_approve()
        transfer.action_register()

        holdings = self.env['govoo.share.holding'].search([
            ('share_class_id', '=', share_class.id),
        ])
        holdings_by_partner = {h.partner_id: h.quantity for h in holdings}
        self.assertEqual(holdings_by_partner[self.partner_a], 400)
        self.assertEqual(holdings_by_partner[self.partner_b], 400)
        self.assertEqual(holdings_by_partner[partner_third], 200)

        total_pct = sum(holdings.mapped('percentage'))
        self.assertAlmostEqual(total_pct, 100.0, places=1)
