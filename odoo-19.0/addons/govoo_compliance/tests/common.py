# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase


class GovooComplianceTestBase(TransactionCase):
    """Shared setup for compliance module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'govoo_financial_year_end': '0630',  # 30 June
        })
        cls.user_secretary = cls.env['res.users'].create({
            'login': 'test_secretary',
            'name': 'Test Secretary',
            'company_id': cls.company.id,
        })
        cls.user_secretary.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_secretary').id)],
        })
        cls.user_responsible = cls.env['res.users'].create({
            'login': 'test_responsible',
            'name': 'Test Responsible',
            'company_id': cls.company.id,
        })
        cls.user_responsible.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_user').id)],
        })
