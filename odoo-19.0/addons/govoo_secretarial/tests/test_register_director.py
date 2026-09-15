# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestRegisterDirector(TransactionCase):
    """TC-SEC-STAT-001: Register of Directors reflects resignation."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Director'})
        self.company = self.env.company

    def test_appointment_auto_creates_register_row(self):
        """TC-SEC-STAT-001: a director-role appointment auto-creates a
        govoo.register.director row."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        register = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment.id),
        ])
        self.assertEqual(len(register), 1)
        self.assertEqual(register.partner_id, self.partner)
        self.assertEqual(register.state, 'active')

    def test_resignation_reflected_on_register(self):
        """TC-SEC-STAT-001: resigning the appointment reflects on the
        register row's date_resigned/state, and logs a 'cease' audit entry."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        register = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment.id),
        ])

        appointment.date_resigned = '2026-06-30'

        self.assertEqual(register.date_resigned, appointment.date_resigned)
        self.assertEqual(register.state, 'resigned')

        entries = self.env['govoo.register.entry'].search([
            ('register_model', '=', 'govoo.register.director'),
            ('res_id', '=', register.id),
            ('change_type', '=', 'cease'),
        ])
        self.assertTrue(entries, 'A cease audit entry should be logged on resignation.')

    def test_non_register_role_does_not_create_row(self):
        """A committee_member appointment (not director/chair/md/secretary)
        does not appear on the Register of Directors."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'committee_member',
            'date_appointed': '2024-01-01',
        })
        register = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment.id),
        ])
        self.assertFalse(register)
