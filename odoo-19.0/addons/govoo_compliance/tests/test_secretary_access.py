# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooComplianceTestBase


@tagged('post_install', '-at_install', 'govoo_compliance')
class TestSecretaryComplianceInstanceAccess(GovooComplianceTestBase):
    """Issue #80: Secretary has full RWCD on govoo.compliance.instance,
    per access-control.md §2."""

    def test_secretary_can_delete_instance(self):
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Test Obligation',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 31,
            'fixed_month': 3,
            'active': True,
            'company_id': self.company.id,
        })
        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': self.company.id,
            'due_date': '2026-03-31',
        })
        instance.with_user(self.user_secretary).unlink()
        self.assertFalse(instance.exists())
