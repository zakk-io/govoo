# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestGovooAppointment(TransactionCase):
    """TC-BASE-003: Appointment state computes correctly from dates."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Director',
        })
        self.company = self.env.company

    def test_appointment_state_active_when_no_resignation(self):
        """TC-BASE-003: Appointment state is 'active' when date_resigned is not set."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        self.assertEqual(appointment.state, 'active')

    def test_appointment_state_resigned_when_date_resigned_in_past(self):
        """TC-BASE-003b: Appointment state is 'resigned' when date_resigned is in the past."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
            'date_resigned': '2024-06-30',
        })
        self.assertEqual(appointment.state, 'resigned')

    def test_appointment_date_resigned_before_date_appointed_raises(self):
        """TC-BASE-003c: Constraint raises when date_resigned < date_appointed."""
        with self.assertRaises(ValidationError):
            self.env['govoo.appointment'].create({
                'partner_id': self.partner.id,
                'company_id': self.company.id,
                'role': 'secretary',
                'date_appointed': '2024-06-30',
                'date_resigned': '2024-01-01',
            })

    def test_appointment_role_selection(self):
        """TC-BASE-003: Valid role selections work."""
        for role in ['director', 'secretary', 'chair', 'md', 'committee_member']:
            appointment = self.env['govoo.appointment'].create({
                'partner_id': self.partner.id,
                'company_id': self.company.id,
                'role': role,
                'date_appointed': '2024-01-01',
            })
            self.assertEqual(appointment.role, role)

    def test_document_field_falls_back_to_attachment_without_documents_app(self):
        """TC-BASE-005: Documents app not installed; a workflow needing
        appointment_document_id runs and falls back to ir.attachment
        without an unhandled exception."""
        documents_installed = self.env['ir.module.module'].search_count([
            ('name', '=', 'documents'),
            ('state', '=', 'installed'),
        ])
        self.assertFalse(documents_installed, 'This dev environment should not have Documents installed.')

        attachment = self.env['ir.attachment'].create({
            'name': 'Appointment Letter.pdf',
            'type': 'binary',
            'datas': b'',
        })
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
            'appointment_document_id': attachment.id,
        })
        self.assertEqual(appointment.appointment_document_id, attachment)

    def test_admin_has_read_only_access(self):
        """Admin group has read access to govoo.appointment, but not
        write/create/unlink (access-control.md §2: Admin: R)."""
        admin = new_test_user(
            self.env, login='test_appt_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        appointment.with_user(admin).check_access('read')
        with self.assertRaises(Exception):
            self.env['govoo.appointment'].with_user(admin).check_access('create')
        for operation in ('write', 'unlink'):
            with self.assertRaises(Exception):
                appointment.with_user(admin).check_access(operation)

    def test_end_date_before_date_appointed_raises(self):
        """End Date must be >= Date Appointed, same discipline as Date
        Resigned (issue #200)."""
        with self.assertRaises(ValidationError):
            self.env['govoo.appointment'].create({
                'partner_id': self.partner.id,
                'company_id': self.company.id,
                'role': 'director',
                'date_appointed': '2024-06-30',
                'end_date': '2024-01-01',
            })


@tagged('post_install', '-at_install')
class TestGovooAppointmentSuccessionReminders(TransactionCase):
    """Succession-Planning Reminders (issue #200): reminder fires within
    the configured lead window, not outside it, and not when End Date
    is unset -- same mail.activity-staging discipline as the
    govoo_contracts key-date reminder cron."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({
            'name': 'Test Director',
        })
        self.company = self.env.company

    def _active_appointment(self, end_date=False, reminder_lead_months=3):
        return self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
            'end_date': end_date,
            'reminder_lead_months': reminder_lead_months,
        })

    def test_reminder_staged_within_lead_window(self):
        appointment = self._active_appointment(
            end_date=Date.today() + timedelta(days=60),
            reminder_lead_months=3,  # 90-day window covers 60 days out
        )
        self.env['govoo.appointment']._cron_send_succession_reminders()
        self.assertTrue(appointment.activity_ids)

    def test_no_reminder_outside_lead_window(self):
        appointment = self._active_appointment(
            end_date=Date.today() + timedelta(days=200),
            reminder_lead_months=3,  # 90-day window does not cover 200 days out
        )
        self.env['govoo.appointment']._cron_send_succession_reminders()
        self.assertFalse(appointment.activity_ids)

    def test_no_reminder_when_end_date_unset(self):
        appointment = self._active_appointment(end_date=False)
        self.env['govoo.appointment']._cron_send_succession_reminders()
        self.assertFalse(appointment.activity_ids)

    def test_no_reminder_when_lead_months_not_positive(self):
        appointment = self._active_appointment(
            end_date=Date.today() + timedelta(days=10),
            reminder_lead_months=0,
        )
        self.env['govoo.appointment']._cron_send_succession_reminders()
        self.assertFalse(appointment.activity_ids)

    def test_no_reminder_for_resigned_appointment(self):
        appointment = self._active_appointment(
            end_date=Date.today() + timedelta(days=60),
            reminder_lead_months=3,
        )
        appointment.date_resigned = Date.today() - timedelta(days=1)
        self.assertEqual(appointment.state, 'resigned')
        self.env['govoo.appointment']._cron_send_succession_reminders()
        self.assertFalse(appointment.activity_ids)
