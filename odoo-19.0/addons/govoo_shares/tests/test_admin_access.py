# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooShareTestBase


@tagged('post_install', '-at_install', 'govoo_shares')
class TestAdminShareAccess(GovooShareTestBase):
    """Issue #77: Board Administrator has read access to share.allotment/
    .transfer/.holding, per access-control.md §2."""

    def test_admin_has_read_access_to_allotment_transfer_holding(self):
        admin = new_test_user(
            self.env, login='test_shares_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        allotment = self._make_allotment(self.partner_a, 10)
        transfer = self.env['govoo.share.transfer'].create({
            'share_class_id': self.share_class.id,
            'transferor_id': self.partner_a.id,
            'transferee_id': self.partner_b.id,
            'quantity': 5,
            'date_transferred': '2026-03-01',
        })
        holding = self.env['govoo.share.holding'].search([
            ('partner_id', '=', self.partner_a.id),
            ('share_class_id', '=', self.share_class.id),
        ], limit=1)

        allotment.with_user(admin).check_access('read')
        transfer.with_user(admin).check_access('read')
        holding.with_user(admin).check_access('read')
