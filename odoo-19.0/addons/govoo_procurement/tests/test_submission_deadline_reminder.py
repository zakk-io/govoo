# Part of Govoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install')
class TestTenderSubmissionDeadlineReminder(GovooProcurementTestBase):
    """Issue #236: tender submission deadline reminder -- not a legal
    threshold (ordinary per-tender operational data, like a contract's
    own End Date), so no [CONFIRM] config gate, just the field being set."""

    def setUp(self):
        super().setUp()
        self.secretary = new_test_user(
            self.env, login='test_procurement_reminder_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
            email='secretary.procurement.reminder.test@example.com',
        )
        self.officer = new_test_user(
            self.env, login='test_procurement_reminder_officer',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
            email='officer.procurement.reminder.test@example.com',
        )

    def test_no_reminder_when_deadline_unset(self):
        tender = self._make_tender()
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.tender']._cron_send_submission_deadline_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_reminder_sent_within_lead_window(self):
        tender = self._make_tender()
        tender.write({
            'submission_deadline': datetime.date.today() + datetime.timedelta(days=2),
            'reminder_lead_days': 3,
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.tender']._cron_send_submission_deadline_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)
        self.assertTrue(tender.message_ids.filtered(
            lambda m: 'submission deadline' in (m.body or ''),
        ))

    def test_no_reminder_outside_lead_window(self):
        tender = self._make_tender()
        tender.write({
            'submission_deadline': datetime.date.today() + datetime.timedelta(days=10),
            'reminder_lead_days': 3,
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.tender']._cron_send_submission_deadline_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_no_reminder_past_pre_evaluation_stage(self):
        tender = self._make_tender()
        tender.write({
            'submission_deadline': datetime.date.today() + datetime.timedelta(days=2),
            'reminder_lead_days': 3,
        })
        tender.action_start_technical_evaluation()
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.tender']._cron_send_submission_deadline_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)
