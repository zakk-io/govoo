# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import date, timedelta

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class TestComplianceFullWorkflow(GovooComplianceTestBase):
    """TC-WF-COMP-001: obligation activated -> cron generates instance ->
    reminders staged -> instance goes late -> filed. Escalation fires once
    per overdue instance, not repeatedly on every cron run."""

    def test_full_lifecycle(self):
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Full Workflow Filing',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'lead_time_days': 30,
            'active': True,
            'company_id': self.company.id,
        })

        # 1. Cron generates an instance
        self.env['govoo.compliance.cron']._cron_generate_instances()
        instance = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ], limit=1)
        self.assertTrue(instance)
        self.assertEqual(instance.state, 'upcoming')
        instance.responsible_id = self.user_responsible

        # 2. Move the due date within the reminder lead-time window and
        # confirm the reminder cron stages an activity.
        instance.due_date = date.today() + timedelta(days=10)
        self.env['govoo.compliance.cron']._cron_send_reminders()
        reminder = self.env['mail.activity'].search([
            ('res_model', '=', 'govoo.compliance.instance'),
            ('res_id', '=', instance.id),
        ])
        self.assertTrue(reminder, 'A reminder activity should be staged within lead time.')

        instance.action_start()
        self.assertEqual(instance.state, 'in_progress')

        # 3. Push the instance overdue and escalate
        instance.due_date = date.today() - timedelta(days=1)
        self.env['govoo.compliance.cron']._cron_escalate_late()
        instance.invalidate_recordset(['state'])
        self.assertEqual(instance.state, 'late')

        message_count_after_first_escalation = len(instance.message_ids)

        # Escalation must not duplicate on a second cron run for the same
        # (now-late) instance -- the cron only touches upcoming/in_progress.
        self.env['govoo.compliance.cron']._cron_escalate_late()
        instance.invalidate_recordset(['state'])
        self.assertEqual(instance.state, 'late')
        self.assertEqual(len(instance.message_ids), message_count_after_first_escalation)

        # 4. File it
        instance.write({
            'reference_no': 'REF-001',
            'filed_date': date.today(),
        })
        instance.action_file()
        self.assertEqual(instance.state, 'filed')

    def test_reminder_and_escalation_also_email_company_secretaries(self):
        """Issue #236: both _cron_send_reminders and _cron_escalate_late
        previously only ever produced an internal activity/chatter note
        that reached no one -- every active Company Secretary now also
        gets a real email for each."""
        secretary = new_test_user(
            self.env, login='test_compliance_reminder_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
            email='secretary.compliance.reminder.test@example.com',
        )
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Email Reminder Filing',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 1,
            'fixed_month': 1,
            'lead_time_days': 30,
            'active': True,
            'company_id': self.company.id,
        })
        self.env['govoo.compliance.cron']._cron_generate_instances()
        instance = self.env['govoo.compliance.instance'].search([
            ('obligation_id', '=', obligation.id),
            ('company_id', '=', self.company.id),
        ], limit=1)

        instance.due_date = date.today() + timedelta(days=10)
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.compliance.cron']._cron_send_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)

        instance.due_date = date.today() - timedelta(days=1)
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.compliance.cron']._cron_escalate_late()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)
