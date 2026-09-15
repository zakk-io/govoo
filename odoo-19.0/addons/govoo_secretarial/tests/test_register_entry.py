# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


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
        """TC-SEC-STAT-005: Any user cannot write on register.entry."""
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
        """TC-SEC-STAT-005: Any user cannot unlink register.entry."""
        entry = self.env['govoo.register.entry'].create({
            'register_model': 'test.model',
            'res_id': 1,
            'change_type': 'create',
            'effective_date': '2024-01-01',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            entry.unlink()

    def test_entry_write_rejected_even_for_admin(self):
        """TC-SEC-006: write()/unlink() are rejected for ANY user, including
        Board Administrator -- not just the default test superuser."""
        admin = new_test_user(
            self.env, login='test_register_entry_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        entry = self.env['govoo.register.entry'].create({
            'register_model': 'test.model',
            'res_id': 1,
            'change_type': 'create',
            'effective_date': '2024-01-01',
            'company_id': self.company.id,
        })
        with self.assertRaises(UserError):
            entry.with_user(admin).write({'notes': 'tamper attempt'})
        with self.assertRaises(UserError):
            entry.with_user(admin).unlink()

    def test_governance_user_cannot_read_register_entry(self):
        """access-control.md: Governance User has NO access to the
        statutory audit ledger, not even read."""
        entry = self.env['govoo.register.entry'].create({
            'register_model': 'test.model',
            'res_id': 1,
            'change_type': 'create',
            'effective_date': '2024-01-01',
            'company_id': self.company.id,
        })
        governance_user = new_test_user(
            self.env, login='test_governance_user',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        with self.assertRaises(AccessError):
            entry.with_user(governance_user).check_access('read')
