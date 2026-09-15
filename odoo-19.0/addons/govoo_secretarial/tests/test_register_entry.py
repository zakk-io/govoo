# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged('post_install', '-at_install')
class TestRegisterEntry(TransactionCase):
    """TC-SEC-STAT-005: govoo.register.entry is append-only."""

    def setUp(self):
        super().setUp()
        self.partner = self.env['res.partner'].create({'name': 'Test Person'})
        self.company = self.env.company

    def test_entry_created_on_director_register(self):
        """Audit entry is created when a director register record is created."""
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        # Director register is curated from appointment — create a register record
        register = self.env['govoo.register.director'].create({
            'appointment_id': appointment.id,
        })
        entries = self.env['govoo.register.entry'].search([
            ('register_model', '=', 'govoo.register.director'),
            ('res_id', '=', register.id),
        ])
        self.assertTrue(entries, 'Audit entry should be created on register creation')
        self.assertEqual(entries[0].change_type, 'create')

    def test_entry_write_rejected(self):
        """TC-SEC-STAT-005 / TC-ACC-008: Any user, including Board
        Administrator, cannot write on register.entry (append-only ledger)."""
        entry = self.env['govoo.register.entry'].create({
            'register_model': 'test.model',
            'res_id': 1,
            'change_type': 'create',
            'effective_date': '2024-01-01',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            entry.write({'notes': 'tamper attempt'})

    def test_entry_unlink_rejected(self):
        """TC-SEC-STAT-005 / TC-ACC-008: Any user, including Board
        Administrator, cannot unlink register.entry (append-only ledger)."""
        entry = self.env['govoo.register.entry'].create({
            'register_model': 'test.model',
            'res_id': 1,
            'change_type': 'create',
            'effective_date': '2024-01-01',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            entry.unlink()
