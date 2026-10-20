# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestBidQualification(GovooProcurementTestBase):
    """Issue #328: the Officer's own compliance screening of each bid,
    required before Technical Evaluation can start."""

    def _disqualify(self, bid, reason='Certificate of experience shows 4 years; tender requires 10.'):
        wizard = self.env['govoo.bid.disqualify.wizard'].create({
            'bid_id': bid.id,
            'reason': reason,
        })
        wizard.action_submit()
        return wizard

    def test_officer_can_mark_bid_qualified(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        self.assertEqual(bid.govoo_qualification_status, 'pending')
        bid.action_mark_qualified()
        self.assertEqual(bid.govoo_qualification_status, 'qualified')

    def test_disqualify_wizard_records_reason(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        self._disqualify(bid, 'Missing company registration certificate.')
        self.assertEqual(bid.govoo_qualification_status, 'disqualified')
        self.assertEqual(bid.govoo_disqualification_reason, 'Missing company registration certificate.')

    def test_disqualifying_without_a_reason_is_blocked(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        with self.assertRaises(ValidationError):
            bid.write({'govoo_qualification_status': 'disqualified'})

    def test_start_technical_evaluation_blocked_without_a_qualified_bid(self):
        tender = self._make_tender()
        self._make_bid(tender, self.vendor_a)
        with self.assertRaises(ValidationError):
            tender.action_start_technical_evaluation()

    def test_start_technical_evaluation_succeeds_with_at_least_one_qualified_bid(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        bid_b = self._make_bid(tender, self.vendor_b)
        bid_a.action_mark_qualified()
        self._disqualify(bid_b)
        # Should not raise, even though bid_b is Disqualified.
        tender.action_start_technical_evaluation()
        self.assertEqual(tender.evaluation_stage, 'technical_evaluation')

    def test_score_wizard_blocks_a_disqualified_bid(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        bid_b = self._make_bid(tender, self.vendor_b)
        bid_a.action_mark_qualified()
        self._disqualify(bid_b)
        tender.action_start_technical_evaluation()

        evaluator = new_test_user(
            self.env, login='test_bid_qual_evaluator',
            groups='govoo_procurement.group_govoo_procurement_evaluator',
            company_id=self.company.id,
        )
        wizard = self.env['govoo.bid.score.wizard'].with_user(evaluator).create({
            'bid_id': bid_b.id, 'govoo_technical_score': 80,
        })
        with self.assertRaises(ValidationError):
            wizard.action_submit()

    def test_cannot_mark_qualified_after_pre_evaluation(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        bid_a.action_mark_qualified()
        tender.action_start_technical_evaluation()
        bid_b = self._make_bid(tender, self.vendor_b)
        with self.assertRaises(ValidationError):
            bid_b.action_mark_qualified()
