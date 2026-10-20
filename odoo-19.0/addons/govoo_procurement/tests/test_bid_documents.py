# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestBidDocuments(GovooProcurementTestBase):
    """Issue #338: each vendor bid's own submitted documents, scoped to
    that bid only -- distinct from the tender's shared document_ids."""

    def _make_document(self, bid, name='Certificate of Experience.pdf'):
        return self.env['ir.attachment'].create({
            'name': name,
            'res_model': 'purchase.order',
            'res_id': bid.id,
            'datas': b'ZmFrZSBwZGY=',
        })

    def test_officer_can_create_and_read_bid_document(self):
        officer = new_test_user(
            self.env, login='test_bid_doc_officer',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        document = self._make_document(bid)

        document.with_user(officer).check_access('read')
        self.assertIn(document, bid.document_ids)

    def test_document_scoped_to_its_own_bid_only(self):
        tender = self._make_tender()
        bid_a = self._make_bid(tender, self.vendor_a)
        bid_b = self._make_bid(tender, self.vendor_b)
        document_a = self._make_document(bid_a, 'Vendor A Proposal.pdf')

        self.assertIn(document_a, bid_a.document_ids)
        self.assertNotIn(document_a, bid_b.document_ids)

    def test_bid_documents_distinct_from_tender_documents(self):
        """A bid's document_ids and the tender's own document_ids are two
        separate stores -- a bid document never leaks into the tender's
        shared RFQ/TOR bucket, or vice versa."""
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        bid_document = self._make_document(bid)
        tender_document = self.env['ir.attachment'].create({
            'name': 'RFQ Pack.pdf',
            'res_model': 'govoo.tender',
            'res_id': tender.id,
            'datas': b'ZmFrZSBwZGY=',
        })

        self.assertIn(bid_document, bid.document_ids)
        self.assertNotIn(tender_document, bid.document_ids)
        self.assertIn(tender_document, tender.document_ids)
        self.assertNotIn(bid_document, tender.document_ids)

    def test_portal_user_cannot_read_bid_documents(self):
        portal_user = new_test_user(
            self.env, login='test_bid_doc_portal',
            groups='base.group_portal',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        document = self._make_document(bid)

        with self.assertRaises(AccessError):
            document.with_user(portal_user).check_access('read')

    def test_bid_documents_locked_once_tender_awarded(self):
        """Issue #338: a bid's documents are part of the same tender case
        file and lock on the same Awarded trigger as the tender's own."""
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        document = self._make_document(bid)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        self._award(tender, bid)

        with self.assertRaises(ValidationError):
            self._make_document(bid, 'Late Addition.pdf')
        with self.assertRaises(ValidationError):
            document.unlink()

    def test_bid_documents_still_editable_before_award(self):
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)
        self._make_document(bid)
        tender.action_start_technical_evaluation()
        # Should not raise.
        self._make_document(bid, 'Still Editable.pdf')
        self.assertEqual(len(bid.document_ids), 2)
