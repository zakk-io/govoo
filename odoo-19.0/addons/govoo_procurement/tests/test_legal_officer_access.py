# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestLegalOfficerAccess(GovooProcurementTestBase):
    """Issue #329: the Legal Officer can read minutes/scores on an
    Awarded tender, never write anywhere, and cannot see a tender still
    in an earlier evaluation stage."""

    def _make_legal_officer(self, login):
        return new_test_user(
            self.env, login=login,
            groups='govoo_procurement.group_govoo_legal_officer',
            company_id=self.company.id,
        )

    def _make_awarded_tender(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = meeting.id
        self._qualify_a_bid(tender)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        self._award(tender, bid)
        return tender, bid

    def test_legal_officer_can_read_minutes_and_scores_on_awarded_tender(self):
        legal_officer = self._make_legal_officer('test_legal_officer_read')
        tender, bid = self._make_awarded_tender()

        minutes = self.env['govoo.minutes'].create({
            'meeting_id': tender.technical_evaluation_meeting_id.id,
        })
        tender.technical_evaluation_meeting_id.minutes_id = minutes.id
        bid.write({'govoo_technical_score': 85.0, 'govoo_financial_score': 90.0})

        tender_as_legal = tender.with_user(legal_officer)
        tender_as_legal.check_access('read')
        self.assertEqual(tender_as_legal.technical_evaluation_minutes_id, minutes)

        bid_as_legal = bid.with_user(legal_officer)
        bid_as_legal.check_access('read')
        self.assertEqual(bid_as_legal.govoo_technical_score, 85.0)
        self.assertEqual(bid_as_legal.govoo_financial_score, 90.0)

    def test_legal_officer_cannot_write(self):
        legal_officer = self._make_legal_officer('test_legal_officer_write')
        tender, bid = self._make_awarded_tender()

        with self.assertRaises(AccessError):
            tender.with_user(legal_officer).write({'name': 'Hacked'})
        with self.assertRaises(AccessError):
            bid.with_user(legal_officer).write({'govoo_technical_score': 1.0})

    def test_legal_officer_cannot_read_tender_in_earlier_stage(self):
        legal_officer = self._make_legal_officer('test_legal_officer_early_stage')
        tender = self._make_tender()
        self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            tender.with_user(legal_officer).check_access('read')

    def test_legal_officer_can_read_bid_vendor_bids_fields_without_access_error(self):
        """Issue #354: opening a vendor bid via the tender's "Vendor
        Bids" smart button (action_view_bids) falls back to the core
        Purchase module's own list/form views, which read invoice_ids
        and order_line -- the Legal Officer had no ACL on
        account.move/account.move.line/purchase.order.line at all, so
        this crashed with an Access Error instead of rendering."""
        legal_officer = self._make_legal_officer('test_legal_officer_bid_fields')
        tender, bid = self._make_awarded_tender()
        bid.with_user(legal_officer).read(['invoice_ids', 'order_line'])

    def test_evaluation_tender_id_sync(self):
        """Issue #329: setting technical/financial_evaluation_meeting_id
        on a tender back-populates govoo.meeting.evaluation_tender_id --
        the record rule's own back-reference. Self-healing: replacing a
        meeting clears the old link rather than leaving it stale."""
        tender = self._make_tender()
        technical_meeting = self._make_committee_meeting()
        financial_meeting = self._make_committee_meeting()

        tender.technical_evaluation_meeting_id = technical_meeting.id
        self.assertEqual(technical_meeting.evaluation_tender_id, tender)

        tender.financial_evaluation_meeting_id = financial_meeting.id
        self.assertEqual(financial_meeting.evaluation_tender_id, tender)

        other_meeting = self._make_committee_meeting()
        tender.technical_evaluation_meeting_id = other_meeting.id
        self.assertFalse(technical_meeting.evaluation_tender_id)
        self.assertEqual(other_meeting.evaluation_tender_id, tender)
