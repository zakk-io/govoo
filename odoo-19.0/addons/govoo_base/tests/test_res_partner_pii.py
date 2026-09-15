# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase, new_test_user


@tagged('post_install', '-at_install')
class TestResPartnerPii(TransactionCase):
    """TC-SEC-003 / TC-BASE-001: govoo_national_id/govoo_date_of_birth are
    restricted to Secretary/Admin via the field-level groups= parameter
    (RPC-level restriction, not just view-hiding)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.partner = cls.env['res.partner'].create({
            'name': 'PII Test Person',
            'govoo_national_id': '1234567890',
            'govoo_date_of_birth': '1980-01-01',
        })
        cls.governance_user = new_test_user(
            cls.env, login='test_pii_governance_user',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company.id,
        )
        cls.secretary = new_test_user(
            cls.env, login='test_pii_secretary',
            groups='govoo_base.group_govoo_secretary',
            company_id=cls.company.id,
        )

    def test_governance_user_cannot_read_pii_fields(self):
        """Per Odoo's field-group semantics (odoo.exceptions.AccessError
        docstring on _check_field_access): explicitly requesting a
        restricted field raises; the field is also absent from
        fields_get() for this group, so it never appears via a normal
        (no explicit field list) read/form load either."""
        with self.assertRaises(AccessError):
            self.partner.with_user(self.governance_user).read(['govoo_national_id'])
        with self.assertRaises(AccessError):
            self.partner.with_user(self.governance_user).read(['govoo_date_of_birth'])

        fields = self.env['res.partner'].with_user(self.governance_user).fields_get()
        self.assertNotIn('govoo_national_id', fields)
        self.assertNotIn('govoo_date_of_birth', fields)

    def test_secretary_can_read_pii_fields(self):
        result = self.partner.with_user(self.secretary).read(
            ['name', 'govoo_national_id', 'govoo_date_of_birth'],
        )[0]
        self.assertEqual(result['govoo_national_id'], '1234567890')
        self.assertEqual(str(result['govoo_date_of_birth']), '1980-01-01')
