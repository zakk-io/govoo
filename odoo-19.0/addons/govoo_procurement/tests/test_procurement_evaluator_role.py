# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestProcurementEvaluatorRole(GovooProcurementTestBase):
    """Issue #316: a Procurement Evaluator can see everything relevant to
    judge a bid, but can only write a score through the narrow wizard --
    never any other field, never create a tender or a bid."""

    def _make_evaluator(self, login):
        return new_test_user(
            self.env, login=login,
            groups='govoo_procurement.group_govoo_procurement_evaluator',
            company_id=self.company.id,
        )

    def test_evaluator_can_read_tender_and_bids(self):
        evaluator = self._make_evaluator('test_procurement_evaluator_read')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        tender.with_user(evaluator).check_access('read')
        bid.with_user(evaluator).check_access('read')

    def test_evaluator_can_submit_score_via_wizard(self):
        evaluator = self._make_evaluator('test_procurement_evaluator_submit')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        wizard = self.env['govoo.bid.score.wizard'].with_user(evaluator).create({
            'bid_id': bid.id,
            'govoo_technical_score': 85,
            'govoo_financial_score': 70,
        })
        wizard.action_submit()

        self.assertEqual(bid.govoo_technical_score, 85)
        self.assertEqual(bid.govoo_financial_score, 70)

    def test_evaluator_cannot_write_score_directly(self):
        evaluator = self._make_evaluator('test_procurement_evaluator_direct_write')
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            bid.with_user(evaluator).write({'govoo_technical_score': 50})

    def test_evaluator_cannot_create_tender_or_bid(self):
        evaluator = self._make_evaluator('test_procurement_evaluator_create')
        tender = self._make_tender()

        with self.assertRaises(AccessError):
            self.env['govoo.tender'].with_user(evaluator).create({
                'name': 'New Tender',
                'company_id': self.company.id,
            })
        with self.assertRaises(AccessError):
            self.env['purchase.order'].with_user(evaluator).create({
                'partner_id': self.vendor_a.id,
                'govoo_tender_id': tender.id,
                'company_id': self.company.id,
            })

    def test_non_evaluator_cannot_use_score_wizard(self):
        """A plain governance user has no ACL row at all on this wizard
        (it's scoped to the Evaluator group only), so it's blocked at
        create() already -- the has_group() check inside action_submit()
        is defense in depth for anyone who somehow got a wizard record
        another way (e.g. a direct ORM call bypassing the UI)."""
        plain_user = new_test_user(
            self.env, login='test_procurement_plain_user_score',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            self.env['govoo.bid.score.wizard'].with_user(plain_user).create({
                'bid_id': bid.id,
                'govoo_technical_score': 50,
                'govoo_financial_score': 50,
            })

        wizard = self.env['govoo.bid.score.wizard'].create({
            'bid_id': bid.id,
            'govoo_technical_score': 50,
            'govoo_financial_score': 50,
        })
        with self.assertRaises(AccessError):
            wizard.with_user(plain_user).action_submit()
