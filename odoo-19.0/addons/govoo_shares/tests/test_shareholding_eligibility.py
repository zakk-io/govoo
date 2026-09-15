# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestShareholdingEligibility(GovooShareTestBase):
    """Issue #86: shareholding_company_ids (and therefore shareholder
    resolution eligibility) excludes holdings in a non-voting share
    class."""

    def test_non_voting_holding_excluded_from_shareholding_company_ids(self):
        non_voting_class = self.env['govoo.share.class'].create({
            'name': 'Non-Voting Preference Shares',
            'total_authorised': 1000,
            'votes_per_share': 0,
            'company_id': self.company.id,
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': non_voting_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 100,
            'date_allotted': '2026-01-01',
        })
        self.partner_a.invalidate_recordset(['shareholding_company_ids'])
        self.assertNotIn(self.company, self.partner_a.shareholding_company_ids)

    def test_voting_holding_included_in_shareholding_company_ids(self):
        self._make_allotment(self.partner_a, 10)  # self.share_class has votes_per_share=1.0
        self.partner_a.invalidate_recordset(['shareholding_company_ids'])
        self.assertIn(self.company, self.partner_a.shareholding_company_ids)
