# Part of Govoo. See LICENSE file for full copyright and licensing details.


from odoo.tests import tagged

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class GovooComplianceInstanceGenerationTC(GovooComplianceTestBase):
    """TC-COMP-001..003 — Instance generation from obligations."""

    def test_fixed_date_generates_instance(self):
        """TC-COMP-001: Active obligation, basis=fixed_date, cron runs → instance created."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Annual Return',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 31,
            'fixed_month': 3,
            'active': True,
            'company_id': self.company.id,
        })

        # Run cron
        self.env['govoo.compliance.cron']._cron_generate_instances()

        instance = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.assertTrue(instance)
        self.assertEqual(instance.state, 'upcoming')
        self.assertTrue(instance.due_date)

    def test_fye_relative_no_fye_no_instance(self):
        """TC-COMP-002: basis=fye_relative, company has no FYE → no instance, logged."""
        # Clear the FYE setting
        self.company.govoo_financial_year_end = False
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Tax Return',
            'authority': 'RRA',
            'frequency': 'annual',
            'basis': 'fye_relative',
            'fye_offset_months': 6,
            'active': True,
            'company_id': self.company.id,
        })

        self.env['govoo.compliance.cron']._cron_generate_instances()

        instance = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertFalse(instance)

    def test_fye_relative_with_fye_generates_instance(self):
        """TC-COMP-003: basis=fye_relative, FYE=30 June, offset=6 months → due_date=30 Dec."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Tax Return',
            'authority': 'RRA',
            'frequency': 'annual',
            'basis': 'fye_relative',
            'fye_offset_months': 6,
            'active': True,
            'company_id': self.company.id,
        })

        self.env['govoo.compliance.cron']._cron_generate_instances()

        instance = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.assertTrue(instance)
        # FYE 30 June + 6 months = 30 December
        self.assertEqual(instance.due_date.month, 12)
        self.assertEqual(instance.due_date.day, 30)

    def test_no_duplicate_instance(self):
        """Cron does not create duplicate instances for same period."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Quarterly Filing',
            'frequency': 'quarterly',
            'basis': 'fixed_date',
            'fixed_day': 15,
            'fixed_month': 4,
            'active': True,
            'company_id': self.company.id,
        })

        self.env['govoo.compliance.cron']._cron_generate_instances()
        self.env['govoo.compliance.cron']._cron_generate_instances()

        instances = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ])
        self.assertEqual(len(instances), 1)
