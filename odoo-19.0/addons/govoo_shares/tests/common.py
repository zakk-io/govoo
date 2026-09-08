# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase


class GovooShareTestBase(TransactionCase):
    """Shared setup for share module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner_a = cls.env['res.partner'].create({
            'name': 'Shareholder A',
            'company_id': cls.company.id,
        })
        cls.partner_b = cls.env['res.partner'].create({
            'name': 'Shareholder B',
            'company_id': cls.company.id,
        })
        cls.partner_c = cls.env['res.partner'].create({
            'name': 'Shareholder C',
            'company_id': cls.company.id,
        })
        cls.share_class = cls.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 100,
            'company_id': cls.company.id,
        })

    def _make_allotment(self, partner, qty):
        """Create an allotment and trigger holding recomputation."""
        return self.env['govoo.share.allotment'].create({
            'share_class_id': self.share_class.id,
            'partner_id': partner.id,
            'quantity': qty,
            'date_allotted': '2026-01-01',
        })
