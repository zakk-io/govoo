# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestAdminRegisterAccess(TransactionCase):
    """Issue #77: Board Administrator has read access to
    register.director/.member/.charge, per access-control.md §2."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({'name': 'Test Person'})

    def test_admin_has_read_access_to_director_member_charge_registers(self):
        admin = new_test_user(
            self.env, login='test_sec_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        appointment = self.env['govoo.appointment'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'role': 'director',
            'date_appointed': '2024-01-01',
        })
        director_register = self.env['govoo.register.director'].search([
            ('appointment_id', '=', appointment.id),
        ])
        member_register = self.env['govoo.register.member'].create({
            'partner_id': self.partner.id,
            'company_id': self.company.id,
            'date_entered': '2024-01-01',
        })
        charge = self.env['govoo.register.charge'].create({
            'company_id': self.company.id,
            'amount': 1000000,
            'date_created': '2024-01-01',
        })

        director_register.with_user(admin).check_access('read')
        member_register.with_user(admin).check_access('read')
        charge.with_user(admin).check_access('read')
