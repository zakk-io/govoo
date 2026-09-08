# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_rw')
class TestRwConfig(TransactionCase):
    """TC-RW-001..003: Rwanda configuration tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_001_currency_rwf_active(self):
        """TC-RW-001: RWF currency is active with 2 decimal places after install."""
        rwf = self.env.ref('base.RWF')
        self.assertTrue(rwf.active, 'RWF currency should be active after govoo_rw install.')
        self.assertEqual(rwf.decimal_places, 2, 'RWF should have 2 decimal places.')
        self.assertEqual(rwf.rounding, 0.01, 'RWF rounding should be 0.01.')

    def test_002_retention_config_minutes(self):
        """TC-RW-002: Retention config for minutes returns correct retention date."""
        rule = self.env.ref('govoo_rw.retention_minutes')
        self.assertTrue(rule.active, 'Minutes retention rule should be active.')
        self.assertEqual(rule.retention_category, 'minutes')
        self.assertEqual(rule.basis, 'years')
        self.assertEqual(rule.retention_years, 10)

        reference_date = date(2020, 1, 1)
        retention_date = rule.get_retention_date(reference_date)
        expected = date(2030, 1, 1)
        self.assertEqual(retention_date, expected,
                         'Retention date should be 10 years from reference.')

    def test_003_obligation_templates_inactive(self):
        """TC-RW-003: All Rwanda-seeded obligation templates have active=False."""
        obligation_ids = [
            'govoo_rw.obligation_vat_monthly',
            'govoo_rw.obligation_paye_monthly',
            'govoo_rw.obligation_wht_monthly',
            'govoo_rw.obligation_rssb_monthly',
            'govoo_rw.obligation_vat_small_taxpayers',
            'govoo_rw.obligation_cit_instalment_1',
            'govoo_rw.obligation_cit_instalment_2',
            'govoo_rw.obligation_cit_instalment_3',
            'govoo_rw.obligation_cit_annual',
            'govoo_rw.obligation_annual_return_accounts',
            'govoo_rw.obligation_cma_governance_self_assessment',
        ]
        for xml_id in obligation_ids:
            obligation = self.env.ref(xml_id)
            self.assertFalse(
                obligation.active,
                f'Obligation template {xml_id} should be active=False '
                'until advisor confirmation (BR-COMP-001).',
            )

    def test_004_retention_categories_configured(self):
        """TC-RW-004: All five retention categories are configured."""
        expected_categories = ['minutes', 'resolutions', 'accounts', 'auditor_reports', 'board_reports']
        for category in expected_categories:
            rules = self.env['govoo.rw.retention'].search([
                ('retention_category', '=', category),
                ('active', '=', True),
            ])
            self.assertTrue(
                rules,
                f'No active retention rule found for category: {category}',
            )
