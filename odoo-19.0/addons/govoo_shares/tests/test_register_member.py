# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestRegisterMember(GovooShareTestBase):
    """TC-SEC-STAT-002: Register of Members auto-population and date_ceased."""

    def test_allotment_creates_register_member_row(self):
        """TC-SEC-STAT-002: allotting shares creates a govoo.register.member
        row with date_entered set."""
        self._make_allotment(self.partner_a, 10)
        self.env['govoo.share.holding']._recompute_holdings(self.share_class.id)

        member = self.env['govoo.register.member'].search([
            ('partner_id', '=', self.partner_a.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEqual(len(member), 1)
        self.assertTrue(member.date_entered)
        self.assertFalse(member.date_ceased)

    def test_holding_reduced_to_zero_sets_date_ceased(self):
        """TC-SEC-STAT-002: transferring all shares away (holding reaches
        zero) sets date_ceased on the register.member row."""
        self._make_allotment(self.partner_a, 10)
        self.env['govoo.share.holding']._recompute_holdings(self.share_class.id)

        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 10,
            'date_transferred': '2026-03-01',
        })
        transfer.action_approve()
        transfer.action_register()
        self.env['govoo.share.holding']._recompute_holdings(self.share_class.id)

        holding_a = self.env['govoo.share.holding'].search([
            ('partner_id', '=', self.partner_a.id),
            ('share_class_id', '=', self.share_class.id),
        ], limit=1)
        self.assertEqual(holding_a.quantity, 0)

        member_a = self.env['govoo.register.member'].search([
            ('partner_id', '=', self.partner_a.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEqual(len(member_a), 1)
        self.assertTrue(member_a.date_ceased, 'date_ceased should be set once holding reaches zero.')
