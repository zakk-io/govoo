# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date

from dateutil.relativedelta import relativedelta

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_rw')
class TestRwConfig(TransactionCase):
    """TC-RW-001..003: Rwanda configuration tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

    def test_001_currency_rwf_active(self):
        """TC-RW-001: RWF currency is active with 0 decimal places after install."""
        rwf = self.env.ref('base.RWF')
        self.assertTrue(rwf.active, 'RWF currency should be active after govoo_rw install.')
        self.assertEqual(rwf.decimal_places, 0, 'RWF should have 0 decimal places.')
        self.assertEqual(rwf.rounding, 1, 'RWF rounding should be 1.')

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

    def test_005_accounts_retention_uses_accounting_date_not_create_date(self):
        """Issue #42: accounts/auditor_reports retention must use
        date/invoice_date as the reference, not create_date (when the DB
        row was inserted, which can lag the accounting date by months
        during month-end close)."""
        if 'account.move' not in self.env:
            self.skipTest('account module not installed.')

        journal = self.env['account.journal'].search([
            ('company_id', '=', self.company.id),
            ('type', '=', 'general'),
        ], limit=1)
        accounts = self.env['account.account'].search([
            ('company_ids', 'in', self.company.id),
        ], limit=2)
        if not journal or len(accounts) < 2:
            self.skipTest('No general journal/accounts available to create a test account.move.')

        rule = self.env.ref('govoo_rw.retention_accounts', raise_if_not_found=False)
        if not rule:
            self.skipTest('No seeded accounts retention rule found.')

        # create_date is "now" (recent); the accounting date is well past
        # the 10-accounting-period (~10 month) retention window, so only
        # the correct reference date should mark it expired.
        old_accounting_date = date.today() - relativedelta(years=2)
        move = self.env['account.move'].create({
            'journal_id': journal.id,
            'date': old_accounting_date,
            'move_type': 'entry',
            'line_ids': [
                (0, 0, {'account_id': accounts[0].id, 'debit': 100.0, 'credit': 0.0}),
                (0, 0, {'account_id': accounts[1].id, 'debit': 0.0, 'credit': 100.0}),
            ],
        })
        move.action_post()

        expired = self.env['govoo.rw.retention']._get_expired_records(rule, date.today())
        self.assertIn(
            move, expired,
            'A posted move with an old accounting date should be expired '
            'even though its create_date is today.',
        )

    def test_004_retention_categories_configured(self):
        """TC-RW-005: All five retention categories are configured.

        Previously mislabeled TC-RW-004 -- that ID belongs to the CMA
        governance checklist model (FR-RW-004, see #44/#64), which this
        test has nothing to do with.
        """
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

    def test_default_date_format_applies_to_res_lang(self):
        """Issue #43: saving govoo_default_date_format updates the
        selected language's res.lang.date_format, since that's the
        only mechanism Odoo uses to actually render dates."""
        en_lang = self.env['res.lang'].search([('code', '=', 'en_US')], limit=1)
        self.assertTrue(en_lang, 'en_US should be installed in a fresh instance.')
        original_format = en_lang.date_format
        try:
            settings = self.env['res.config.settings'].create({
                'govoo_default_language': 'en_US',
                'govoo_default_date_format': 'YYYY-MM-DD',
            })
            settings.execute()
            en_lang.invalidate_recordset(['date_format'])
            self.assertEqual(en_lang.date_format, '%Y-%m-%d')
        finally:
            en_lang.date_format = original_format
