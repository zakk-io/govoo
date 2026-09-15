# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_rw')
class TestRetentionMultiCompany(TransactionCase):
    """Issue #81: Secretary is covered by the multi-company scoping
    rule on govoo.rw.retention, not just Admin."""

    def test_secretary_cannot_read_other_company_retention_rule(self):
        company_a = self.env.company
        company_b = self.env['res.company'].create({'name': 'Other Co'})
        secretary = new_test_user(
            self.env, login='test_retention_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=company_a.id,
        )
        rule_b = self.env['govoo.rw.retention'].create({
            'name': 'Other Co Rule',
            'retention_category': 'minutes',
            'basis': 'years',
            'retention_years': 10,
            'company_id': company_b.id,
        })
        with self.assertRaises(Exception):
            rule_b.with_user(secretary).check_access('read')
