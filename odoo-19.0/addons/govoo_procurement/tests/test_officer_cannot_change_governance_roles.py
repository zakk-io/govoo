# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooProcurementTestBase


@tagged('post_install', '-at_install', 'govoo_procurement')
class TestOfficerCannotChangeGovernanceRoles(GovooProcurementTestBase):
    """A Procurement Officer can manage a vendor's ordinary contact
    details (#314), but must never change a company's governance role
    classification (Director/Shareholder/Officer/Beneficial Owner) --
    that's the Company Secretary/Board Administrator's call."""

    def test_officer_cannot_set_governance_role_on_existing_company(self):
        officer = new_test_user(
            self.env, login='test_officer_governance_write',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        with self.assertRaises(AccessError):
            self.vendor_a.with_user(officer).write({'govoo_is_director': True})

    def test_officer_cannot_set_governance_role_on_create(self):
        officer = new_test_user(
            self.env, login='test_officer_governance_create',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        with self.assertRaises(AccessError):
            self.env['res.partner'].with_user(officer).create({
                'name': 'New Vendor Co',
                'is_company': True,
                'company_id': self.company.id,
                'govoo_is_shareholder': True,
            })

    def test_officer_can_still_edit_ordinary_contact_fields(self):
        officer = new_test_user(
            self.env, login='test_officer_governance_ordinary',
            groups='govoo_procurement.group_govoo_procurement_officer',
            company_id=self.company.id,
        )
        self.vendor_a.with_user(officer).write({'phone': '+250 788 000 000'})
        self.assertEqual(self.vendor_a.phone, '+250 788 000 000')

    def test_non_officer_can_still_set_governance_role(self):
        """No regression: this restriction is specific to the Officer
        role, every other governance user keeps editing these as before."""
        secretary = new_test_user(
            self.env, login='test_secretary_governance_write',
            groups='govoo_base.group_govoo_secretary',
            company_id=self.company.id,
        )
        self.vendor_a.with_user(secretary).write({'govoo_is_director': True})
        self.assertTrue(self.vendor_a.govoo_is_director)
