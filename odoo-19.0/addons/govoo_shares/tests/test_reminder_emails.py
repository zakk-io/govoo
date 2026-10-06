# Part of Govoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooShareTestBase


@tagged('post_install', '-at_install')
class TestSharesReminderEmails(GovooShareTestBase):
    """Issue #236: certificate issuance and transfer registration
    reminders -- both disabled by default (unconfirmed [CONFIRM] legal
    thresholds), both real emails (not just internal activities) to
    Company Secretaries once their governing config parameter is set."""

    def setUp(self):
        super().setUp()
        self.secretary = new_test_user(
            self.env, login='test_shares_reminder_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
            email='secretary.shares.reminder.test@example.com',
        )

    def test_certificate_reminder_noop_when_config_unset(self):
        allotment = self._make_allotment(self.partner_a, 10)
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_certificate_issuance_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_certificate_reminder_sent_within_window(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_shares.certificate_issuance_deadline_days', '60',
        )
        allotment = self.env['govoo.share.allotment'].create({
            'share_class_id': self.share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 10,
            'date_allotted': datetime.date.today() - datetime.timedelta(days=55),
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_certificate_issuance_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_certificate_reminder_skipped_once_issued(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_shares.certificate_issuance_deadline_days', '60',
        )
        attachment = self.env['ir.attachment'].create({
            'name': 'cert.pdf', 'datas': b'ZmFrZSBwZGY=',
        })
        allotment = self.env['govoo.share.allotment'].create({
            'share_class_id': self.share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 10,
            'date_allotted': datetime.date.today() - datetime.timedelta(days=55),
            'certificate_document_id': attachment.id,
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_certificate_issuance_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_transfer_reminder_noop_when_config_unset(self):
        self._make_allotment(self.partner_a, 20)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': '2026-01-01',
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_transfer_registration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_transfer_reminder_sent_within_window(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_shares.transfer_registration_deadline_days', '30',
        )
        self._make_allotment(self.partner_a, 20)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': datetime.date.today() - datetime.timedelta(days=25),
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_transfer_registration_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_transfer_reminder_skipped_once_registered(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_shares.transfer_registration_deadline_days', '30',
        )
        self._make_allotment(self.partner_a, 20)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': datetime.date.today() - datetime.timedelta(days=25),
        })
        transfer.action_approve()
        transfer.action_register()
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.shares.cron']._cron_send_transfer_registration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)
