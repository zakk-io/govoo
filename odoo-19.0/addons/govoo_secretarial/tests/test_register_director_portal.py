# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestRegisterDirectorPortalAccess(TransactionCase):
    """Issue #78: Director Portal sees only their own
    govoo.register.director entry."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company

    def test_director_portal_sees_only_own_register_entry(self):
        director_a = new_test_user(
            self.env, login='test_reg_director_a',
            groups='govoo_base.group_govoo_director_portal',
            company_id=self.company.id,
        )
        director_b = new_test_user(
            self.env, login='test_reg_director_b',
            groups='govoo_base.group_govoo_director_portal',
            company_id=self.company.id,
        )
        appointment_a = self.env['govoo.appointment'].create({
            'partner_id': director_a.partner_id.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        appointment_b = self.env['govoo.appointment'].create({
            'partner_id': director_b.partner_id.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        register_a = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment_a.id),
        ])
        register_b = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment_b.id),
        ])

        register_a.with_user(director_a).check_access('read')
        with self.assertRaises(Exception):
            register_b.with_user(director_a).check_access('read')
