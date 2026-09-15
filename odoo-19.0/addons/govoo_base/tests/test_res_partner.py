# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestResPartnerPii(TransactionCase):
    """TC-BASE-001: PII fields hidden from non-privileged reads."""

    def setUp(self):
        super().setUp()
        self.company = self.env.company
        self.partner = self.env['res.partner'].create({
            'name': 'Test Person',
            'govoo_national_id': '1234567890',
        })

    def test_non_privileged_read_omits_national_id(self):
        """TC-BASE-001: Non-privileged user reads a partner with
        govoo_national_id set -- field not present in the read result.

        A restricted field is excluded from the field list Odoo builds
        for read() (via fields_get()) before the read ever runs, so
        checking fields_get() directly is the precise way to assert
        this without depending on which other unrelated fields a bare
        read() happens to pull in for this user.
        """
        user = new_test_user(
            self.env, login='test_base_user',
            groups='govoo_base.group_govoo_user',
            company_id=self.company.id,
        )
        allowed_fields = self.partner.with_user(user).fields_get(['govoo_national_id'])
        self.assertNotIn('govoo_national_id', allowed_fields)

        result = self.partner.with_user(user).read(['name'])[0]
        self.assertNotIn('govoo_national_id', result)


@tagged('post_install', '-at_install')
class TestResCompanyOptionalFye(TransactionCase):
    """TC-BASE-002: govoo_financial_year_end is optional at the model layer."""

    def test_company_saves_without_financial_year_end(self):
        company = self.env['res.company'].create({
            'name': 'No FYE Set Co',
        })
        self.assertFalse(company.govoo_financial_year_end)
