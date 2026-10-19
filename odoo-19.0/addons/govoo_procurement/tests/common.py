# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase
from odoo.tests.common import new_test_user


class GovooProcurementTestBase(TransactionCase):
    """Shared setup for procurement module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.vendor_a = cls.env['res.partner'].create({
            'name': 'Vendor A',
            'company_id': cls.company.id,
            'supplier_rank': 1,
        })
        cls.vendor_b = cls.env['res.partner'].create({
            'name': 'Vendor B',
            'company_id': cls.company.id,
            'supplier_rank': 1,
        })
        cls.tender_category = cls.env['res.partner.category'].create({
            'name': 'IT Services Tender',
        })
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Tender Evaluation Committee',
            'company_id': cls.company.id,
        })

    def _make_tender(self):
        return self.env['govoo.tender'].create({
            'name': 'IT Services Tender 2026',
            'company_id': self.company.id,
            'tender_category_id': self.tender_category.id,
        })

    def _make_bid(self, tender, vendor):
        return self.env['purchase.order'].create({
            'partner_id': vendor.id,
            'govoo_tender_id': tender.id,
            'company_id': self.company.id,
        })

    def _award(self, tender, bid):
        """Award `tender` to `bid` as a user other than whoever created
        the tender. Issue #300/#317: a tender's own creator can never be
        the one who awards it, so any test that only incidentally needs
        an Awarded tender (not testing that rule itself) goes through
        this helper instead of calling action_award() directly."""
        tender.write({'awarded_bid_id': bid.id})
        other_officer = new_test_user(
            self.env, login='test_award_officer_%d' % tender.id,
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        tender.with_user(other_officer).action_award()

    def _make_committee_meeting(self):
        return self.env['govoo.meeting'].create({
            'name': 'Tender Evaluation Meeting',
            'meeting_type': 'committee',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
