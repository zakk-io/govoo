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
