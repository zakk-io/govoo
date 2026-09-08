# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


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
        """TC-BASE-003: Appointment state is 'resigned' when date_resigned is in the past."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
            'date_resigned': '2024-06-30',
        })
        self.assertEqual(appointment.state, 'resigned')

    def test_appointment_date_resigned_before_date_appointed_raises(self):
        """TC-BASE-003: Constraint raises when date_resigned < date_appointed."""
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
