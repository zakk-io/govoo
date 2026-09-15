# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestShareClassAdminAccess(GovooShareTestBase):
    """access-control.md: Board Administrator gets RW on share.class, not C/D."""

    def test_admin_cannot_create_or_delete_share_class(self):
        admin = new_test_user(
            self.env, login='test_share_class_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        self.share_class.with_user(admin).write({'name': 'Renamed by Admin'})
        with self.assertRaises(AccessError):
            self.env['govoo.share.class'].with_user(admin).create({
                'name': 'New Class',
                'nominal_value': 1000,
                'total_authorised': 100,
                'company_id': self.company.id,
            })
        with self.assertRaises(AccessError):
            self.share_class.with_user(admin).unlink()
