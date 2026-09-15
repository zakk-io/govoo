# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestRegisterMemberHoldings(GovooShareTestBase):
    """Issue #54: govoo.register.member.holding_ids links back to the
    member's actual per-share-class holdings."""

    def test_holding_ids_reflects_allotments(self):
        self._make_allotment(self.partner_a, 10)
        self.env['govoo.share.holding']._recompute_holdings(self.share_class.id)

        member = self.env['govoo.register.member'].search([
            ('partner_id', '=', self.partner_a.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEqual(len(member), 1)

        holding = self.env['govoo.share.holding'].search([
            ('partner_id', '=', self.partner_a.id),
            ('share_class_id', '=', self.share_class.id),
        ])
        self.assertEqual(member.holding_ids, holding)
        self.assertEqual(member.holding_ids.quantity, 10)
