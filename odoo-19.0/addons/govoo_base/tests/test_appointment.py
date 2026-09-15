# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
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
