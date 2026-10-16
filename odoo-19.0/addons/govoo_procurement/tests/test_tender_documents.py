# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestTenderDocuments(GovooProcurementTestBase):
    """Issue #306: internal, pre-publication document workspace on a tender."""

    def _make_document(self, tender, name='Draft RFP.pdf'):
        return self.env['ir.attachment'].create({
            'name': name,
            'res_model': 'govoo.tender',
            'res_id': tender.id,
            'datas': b'ZmFrZSBwZGY=',
        })

    def test_officer_can_create_and_read_document(self):
        officer = new_test_user(
            self.env, login='test_tender_doc_officer',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        document = self._make_document(tender)

        document.with_user(officer).check_access('read')
        self.assertIn(document, tender.document_ids)

    def test_document_scoped_to_its_own_tender_only(self):
        tender_a = self._make_tender()
        tender_b = self.env['govoo.tender'].create({
            'name': 'Vehicle Fleet Tender 2026',
            'company_id': self.company.id,
            'tender_category_id': self.tender_category.id,
        })
        document_a = self._make_document(tender_a, 'Tender A Spec.pdf')

        self.assertIn(document_a, tender_a.document_ids)
        self.assertNotIn(document_a, tender_b.document_ids)

    def test_portal_user_cannot_read_tender_documents(self):
        """Regression: govoo.tender has zero portal access, so ir.attachment's
        own res_model/res_id access delegation must keep documents
        internal-only too, exactly as it does for the tender record itself."""
        portal_user = new_test_user(
            self.env, login='test_tender_doc_portal',
            groups='base.group_portal',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        document = self._make_document(tender)

        with self.assertRaises(AccessError):
            tender.with_user(portal_user).check_access('read')
        with self.assertRaises(AccessError):
            document.with_user(portal_user).check_access('read')

    def test_documents_locked_once_awarded(self):
        """Issue #306 follow-up: documents cannot be added or removed once
        a tender is Awarded -- they are part of its permanent record."""
        tender = self._make_tender()
        document = self._make_document(tender)
        bid = self._make_bid(tender, self.vendor_a)
        tender.action_start_technical_evaluation()
        tender.action_start_financial_evaluation()
        tender.awarded_bid_id = bid.id
        tender.action_award()

        with self.assertRaises(ValidationError):
            self._make_document(tender, 'Late Addition.pdf')
        with self.assertRaises(ValidationError):
            document.unlink()

    def test_documents_still_editable_before_award(self):
        """Confirms the lock in test_documents_locked_once_awarded is
        scoped to the Awarded stage only -- documents stay freely editable
        while a tender is still under evaluation."""
        tender = self._make_tender()
        self._make_document(tender)
        tender.action_start_technical_evaluation()
        # Should not raise.
        self._make_document(tender, 'Still Editable.pdf')
        self.assertEqual(len(tender.document_ids), 2)
