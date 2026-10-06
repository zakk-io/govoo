# Part of Govoo. See LICENSE file for full copyright and licensing details.

import datetime

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestSecretarialReminderEmails(TransactionCase):
    """Issue #236: charge registration and beneficial-owner declaration
    reminders -- both disabled by default (unconfirmed [CONFIRM] legal
    thresholds), both real emails (not just internal activities) to
    Company Secretaries once their governing config parameter is set."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.secretary = new_test_user(
            cls.env, login='test_secretarial_reminder_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=cls.company.id,
            email='secretary.reminder.test@example.com',
        )
        cls.partner = cls.env['res.partner'].create({'name': 'Test Chargee/BO'})

    def test_charge_reminder_noop_when_config_unset(self):
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'chargee_partner_id': self.partner.id,
            'amount': 1000,
            'date_created': '2026-01-01',
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_charge_registration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)
        self.assertFalse(charge.message_ids.filtered(
            lambda m: 'must be registered' in (m.body or ''),
        ))

    def test_charge_reminder_sent_within_window(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_secretarial.charge_registration_deadline_days', '14',
        )
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'chargee_partner_id': self.partner.id,
            'amount': 1000,
            'date_created': datetime.date.today() - datetime.timedelta(days=10),
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_charge_registration_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)
        self.assertTrue(charge.message_ids.filtered(
            lambda m: 'must be registered' in (m.body or ''),
        ))

    def test_charge_reminder_skipped_once_registered(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_secretarial.charge_registration_deadline_days', '14',
        )
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'chargee_partner_id': self.partner.id,
            'amount': 1000,
            'date_created': datetime.date.today() - datetime.timedelta(days=10),
            'date_registered': datetime.date.today(),
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_charge_registration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_beneficial_owner_reminder_noop_when_config_unset(self):
        owner = self.env['govoo.register.beneficial.owner'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'nature_of_control': 'shares_25',
            'date_became_registrable': '2026-01-01',
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_beneficial_owner_declaration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_beneficial_owner_reminder_sent_within_window(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_secretarial.beneficial_owner_declaration_deadline_days', '14',
        )
        owner = self.env['govoo.register.beneficial.owner'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'nature_of_control': 'shares_25',
            'date_became_registrable': datetime.date.today() - datetime.timedelta(days=10),
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_beneficial_owner_declaration_reminders()
        self.assertGreater(self.env['mail.mail'].search_count([]), mail_count_before)

    def test_beneficial_owner_reminder_skipped_once_evidence_filed(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_secretarial.beneficial_owner_declaration_deadline_days', '14',
        )
        attachment = self.env['ir.attachment'].create({
            'name': 'evidence.pdf', 'datas': b'ZmFrZSBwZGY=',
        })
        owner = self.env['govoo.register.beneficial.owner'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'nature_of_control': 'shares_25',
            'date_became_registrable': datetime.date.today() - datetime.timedelta(days=10),
            'evidence_document_id': attachment.id,
        })
        mail_count_before = self.env['mail.mail'].search_count([])
        self.env['govoo.secretarial.cron']._cron_send_beneficial_owner_declaration_reminders()
        self.assertEqual(self.env['mail.mail'].search_count([]), mail_count_before)
