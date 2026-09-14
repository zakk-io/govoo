# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestAuditorMultiCompanyIsolation(TransactionCase):
    """An Auditor assigned to one company must not see another company's
    governance records -- the multi-company *_comp_rule records only
    apply if Auditor is (implied) a member of group_govoo_user."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env.company
        cls.company_b = cls.env['res.company'].create({'name': 'Other Company'})

        cls.auditor = new_test_user(
            cls.env, login='test_auditor',
            groups='govoo_base.group_govoo_auditor',
            company_id=cls.company_a.id,
        )

        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'Company A Committee',
            'company_id': cls.company_a.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Company B Committee',
            'company_id': cls.company_b.id,
        })

    def test_auditor_cannot_read_other_company_committee(self):
        committees = self.env['govoo.committee'].with_user(self.auditor).search([])
        self.assertIn(self.committee_a, committees)
        self.assertNotIn(self.committee_b, committees)

    def test_auditor_cannot_browse_other_company_committee_by_id(self):
        committee_b_as_auditor = self.committee_b.with_user(self.auditor)
        with self.assertRaises(AccessError):
            committee_b_as_auditor.check_access('read')
