# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestAuditorAccess(GovooProcurementTestBase):
    """Issue #293: the Auditor role must be able to read, but never write,
    create, or delete, tenders and purchase orders."""

    def test_auditor_can_read_tender_and_purchase_order(self):
        auditor = new_test_user(
            self.env, login='test_procurement_auditor',
            groups='govoo_base.group_govoo_auditor',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        tender.with_user(auditor).check_access('read')
        bid.with_user(auditor).check_access('read')

    def test_auditor_can_read_bid_vendor_bids_fields_without_access_error(self):
        """Issue #354: same gap as the Legal Officer's (see
        test_legal_officer_access.py) -- opening a vendor bid via the
        tender's "Vendor Bids" smart button falls back to the core
        Purchase module's own views, which read invoice_ids and
        order_line. The Auditor had no ACL on account.move/
        account.move.line/purchase.order.line either."""
        auditor = new_test_user(
            self.env, login='test_procurement_auditor_bid_fields',
            groups='govoo_base.group_govoo_auditor',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        bid.with_user(auditor).read(['invoice_ids', 'order_line'])

    def test_auditor_cannot_write_create_or_unlink(self):
        auditor = new_test_user(
            self.env, login='test_procurement_auditor_2',
            groups='govoo_base.group_govoo_auditor',
            company_id=self.company.id,
        )
        tender = self._make_tender()
        bid = self._make_bid(tender, self.vendor_a)

        with self.assertRaises(AccessError):
            tender.with_user(auditor).write({'name': 'Hacked'})
        with self.assertRaises(AccessError):
            bid.with_user(auditor).write({'partner_id': self.vendor_b.id})
        with self.assertRaises(AccessError):
            self.env['govoo.tender'].with_user(auditor).create({
                'name': 'New Tender',
                'company_id': self.company.id,
            })
        with self.assertRaises(AccessError):
            tender.with_user(auditor).unlink()
