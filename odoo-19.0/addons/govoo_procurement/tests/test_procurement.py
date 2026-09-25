# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestTenderCategory(GovooProcurementTestBase):

    def test_vendor_and_tender_share_the_same_category_vocabulary(self):
        """Issue #205: vendor categorization by tender type reuses the
        native Contact Tags model (res.partner.category) instead of a
        parallel category model."""
        self.vendor_a.category_id = [(4, self.tender_category.id)]
        tender = self._make_tender()
        self.assertEqual(tender.tender_category_id, self.tender_category)
        self.assertIn(self.tender_category, self.vendor_a.category_id)


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestEvaluationStages(GovooProcurementTestBase):

    def test_default_stage_is_pre_evaluation(self):
        tender = self._make_tender()
        self.assertEqual(tender.evaluation_stage, 'pre_evaluation')

    def test_stages_advance_sequentially(self):
        tender = self._make_tender()
        tender.action_start_technical_evaluation()
        self.assertEqual(tender.evaluation_stage, 'technical_evaluation')
        tender.action_start_financial_evaluation()
        self.assertEqual(tender.evaluation_stage, 'financial_evaluation')
        bid = self._make_bid(tender, self.vendor_a)
        tender.awarded_bid_id = bid.id
        tender.action_award()
        self.assertEqual(tender.evaluation_stage, 'awarded')

    def test_cannot_skip_a_stage(self):
        tender = self._make_tender()
        with self.assertRaises(ValidationError):
            tender.action_start_financial_evaluation()

    def test_cannot_advance_past_awarded(self):
        tender = self._make_tender()
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        bid = self._make_bid(tender, self.vendor_a)
        tender.awarded_bid_id = bid.id
        tender.action_award()
        with self.assertRaises(ValidationError):
            tender.action_award()

    def test_cannot_award_without_selecting_a_bid(self):
        tender = self._make_tender()
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        with self.assertRaises(ValidationError):
            tender.action_award()


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestBidScoring(GovooProcurementTestBase):

    def test_bids_from_multiple_vendors_can_be_scored(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        bid_b = self._make_bid(tender, self.vendor_b)
        bid_a.write({'govoo_technical_score': 80, 'govoo_financial_score': 70})
        bid_b.write({'govoo_technical_score': 60, 'govoo_financial_score': 90})
        self.assertEqual(tender.bid_count, 2)
        self.assertEqual(bid_a.govoo_technical_score, 80)
        self.assertEqual(bid_b.govoo_financial_score, 90)

    def test_score_out_of_range_raises(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        with self.assertRaises(ValidationError):
            bid.write({'govoo_technical_score': 150})

    def test_negative_score_raises(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        with self.assertRaises(ValidationError):
            bid.write({'govoo_financial_score': -5})

    def test_awarded_bid_must_belong_to_the_tender(self):
        tender = self._make_tender()
        other_tender = self._make_tender()
        foreign_bid = self._make_bid(other_tender, self.vendor_a)
        with self.assertRaises(ValidationError):
            tender.awarded_bid_id = foreign_bid.id


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestEvaluationMinutes(GovooProcurementTestBase):

    def test_evaluation_meeting_links_to_tender(self):
        tender = self._make_tender()
        meeting = self._make_committee_meeting()
        tender.evaluation_meeting_id = meeting.id
        self.assertEqual(tender.evaluation_meeting_id, meeting)

    def test_evaluation_minutes_reuses_govoo_minutes_not_a_new_model(self):
        """Issue #205 sub-task: committee evaluation minutes must reuse
        govoo.minutes via the linked meeting, not a parallel model."""
        tender = self._make_tender()
        meeting = self._make_committee_meeting()
        tender.evaluation_meeting_id = meeting.id
        self.assertFalse(tender.evaluation_minutes_id)

        minutes = self.env['govoo.minutes'].create({'meeting_id': meeting.id})
        meeting.minutes_id = minutes.id
        self.assertEqual(tender.evaluation_minutes_id, minutes)
