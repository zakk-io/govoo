# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestPartnerAccess(TransactionCase):
    """access-control.md §2 (res.partner): U:R(non-PII), SEC:RWCD,
    A:RWC, DP:R(own), SP:R(own), AU:R."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.other_partner = self.env['res.partner'].create({
            'name': 'Other Partner',
            'company_id': self.company.id,
        })

    def test_user_has_read_only_access(self):
        user = new_test_user(
            self.env, login='test_partner_user',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        self.other_partner.with_user(user).check_access('read')
        for operation in ('write', 'unlink'):
            with self.assertRaises(Exception):
                self.other_partner.with_user(user).check_access(operation)
        with self.assertRaises(Exception):
            self.env['res.partner'].with_user(user).check_access('create')

    def test_auditor_has_read_only_access(self):
        auditor = new_test_user(
            self.env, login='test_partner_auditor',
            groups='govoo_base.group_govoo_auditor',
            company_id=self.company.id,
        )
        self.other_partner.with_user(auditor).check_access('read')
        for operation in ('write', 'unlink'):
            with self.assertRaises(Exception):
                self.other_partner.with_user(auditor).check_access(operation)

    def test_admin_has_rwc_no_unlink(self):
        admin = new_test_user(
            self.env, login='test_partner_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        self.other_partner.with_user(admin).check_access('read')
        self.other_partner.with_user(admin).check_access('write')
        self.env['res.partner'].with_user(admin).check_access('create')
        with self.assertRaises(Exception):
            self.other_partner.with_user(admin).check_access('unlink')

    def test_secretary_has_full_rwcd(self):
        secretary = new_test_user(
            self.env, login='test_partner_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        partner = self.env['res.partner'].with_user(secretary).create({
            'name': 'Secretary-created Partner',
            'company_id': self.company.id,
        })
        partner.with_user(secretary).check_access('read')
        partner.with_user(secretary).write({'name': 'Renamed'})
        partner.with_user(secretary).unlink()

    def test_director_portal_sees_only_own_partner(self):
        director = new_test_user(
            self.env, login='test_partner_director',
            groups='govoo_base.group_govoo_director_portal',
            company_id=self.company.id,
        )
        director.partner_id.with_user(director).check_access('read')
        with self.assertRaises(Exception):
            self.other_partner.with_user(director).check_access('read')

    def test_shareholder_portal_sees_only_own_partner(self):
        shareholder = new_test_user(
            self.env, login='test_partner_shareholder',
            groups='govoo_base.group_govoo_shareholder_portal',
            company_id=self.company.id,
        )
        shareholder.partner_id.with_user(shareholder).check_access('read')
        with self.assertRaises(Exception):
            self.other_partner.with_user(shareholder).check_access('read')
