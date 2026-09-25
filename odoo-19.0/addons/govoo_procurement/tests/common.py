# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase


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

    def _make_committee_meeting(self):
        return self.env['govoo.meeting'].create({
            'name': 'Tender Evaluation Meeting',
            'meeting_type': 'committee',
            'committee_id': self.committee.id,
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
