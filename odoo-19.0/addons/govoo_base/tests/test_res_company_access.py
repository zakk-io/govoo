# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestResCompanyAccess(TransactionCase):
    """Company Secretary must have write access to res.company's govoo_*
    governance fields (access-control.md §2: S=RW)."""

    def test_secretary_can_write_entity_type(self):
        company = self.env.company
        secretary = new_test_user(
            self.env, login='test_company_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=company.id,
        )
        company.with_user(secretary).write({'govoo_entity_type': 'llc'})
        self.assertEqual(company.govoo_entity_type, 'llc')

    def test_admin_has_create_and_unlink_rights_on_company(self):
        """access-control.md: company creation/deletion restricted to Admin
        (implying Admin can do it).

        Checks the res.company access grant directly via check_access()
        rather than a full create(), since res.company.create() triggers
        an internal res.partner creation as a side effect -- Admin's
        access to res.partner is a separate, already-tracked gap (#70),
        not part of this issue's scope.
        """
        admin = new_test_user(
            self.env, login='test_company_admin',
            groups='govoo_base.group_govoo_admin',
        )
        self.env['res.company'].with_user(admin).browse().check_access('create')
        self.env.company.with_user(admin).check_access('unlink')
