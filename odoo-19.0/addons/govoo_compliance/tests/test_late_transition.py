# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date, timedelta

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class GovooComplianceLateTransitionTC(GovooComplianceTestBase):
    """TC-COMP-004 — Late transition on overdue instances."""

    def test_overdue_instance_becomes_late(self):
        """TC-COMP-004: Instance due_date in past, not filed/waived → cron sets to late."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Overdue Filing',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'active': True,
            'company_id': self.company.id,
        })

        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'period': '2025',
            'due_date': date.today() - timedelta(days=5),
            'state': 'upcoming',
        })

        self.env['govoo.compliance.cron']._cron_escalate_late()

        instance.invalidate_recordset(['state'])
        self.assertEqual(instance.state, 'late')

    def test_filed_instance_not_escalated(self):
        """Filed instance is not affected by escalation cron."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Filed Filing',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'active': True,
            'company_id': self.company.id,
        })

        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'period': '2025',
            'due_date': date.today() - timedelta(days=5),
            'state': 'filed',
        })

        self.env['govoo.compliance.cron']._cron_escalate_late()

        instance.invalidate_recordset(['state'])
        self.assertEqual(instance.state, 'filed')

    def test_terminal_state_blocks_transition(self):
        """Cannot change state from filed/waived."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Terminal Filing',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'active': True,
            'company_id': self.company.id,
        })

        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'period': '2025',
            'due_date': '2025-01-01',
            'state': 'filed',
        })

        with self.assertRaises(ValidationError):
            instance.state = 'upcoming'

    def test_file_requires_reference_and_date(self):
        """action_file requires reference_no and filed_date."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Incomplete Filing',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'active': True,
            'company_id': self.company.id,
        })

        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'period': '2025',
            'due_date': '2025-01-01',
            'state': 'in_progress',
        })

        with self.assertRaises(ValidationError):
            instance.action_file()

    def test_waive_from_upcoming(self):
        """Can waive from upcoming state."""
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Waivable Filing',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'active': True,
            'company_id': self.company.id,
        })

        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'period': '2025',
            'due_date': '2025-01-01',
            'state': 'upcoming',
        })

        instance.action_waive()
        self.assertEqual(instance.state, 'waived')
