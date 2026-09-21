# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestRetentionAlignment(GovooContractsTestBase):
    """Retention Alignment (issue #179): FR-CM-18.

    docs/spec/decisions/assumptions.md: unlike govoo.minutes.
    retention_until, no statutory default is assumed if
    contract_type_id.retention_years is unset -- contract retention has
    no established default in this project, so it computes no date
    rather than guessing one.
    """

    def test_no_retention_until_when_type_unconfigured(self):
        contract = self._make_contract()
        self.assertFalse(contract.retention_until)

    def test_retention_until_computed_from_type_retention_years(self):
        self.contract_type.retention_years = 6
        contract = self._make_contract()
        expected_year = contract.create_date.year + 6
        self.assertEqual(contract.retention_until.year, expected_year)

    def test_retention_until_recomputes_when_type_changes(self):
        contract = self._make_contract()
        self.assertFalse(contract.retention_until)
        self.contract_type.retention_years = 3
        self.assertTrue(contract.retention_until)
        self.assertEqual(
            contract.retention_until.year, contract.create_date.year + 3,
        )

    def test_different_types_can_have_different_retention(self):
        long_retention_type = self.env['govoo.contract.type'].create({
            'name': 'Long Retention Type',
            'company_id': self.company.id,
            'retention_years': 10,
        })
        short_contract = self._make_contract()
        self.contract_type.retention_years = 2
        long_contract = self._make_contract(
            name='CTR-0002', contract_type_id=long_retention_type.id,
        )
        self.assertEqual(
            short_contract.retention_until.year,
            short_contract.create_date.year + 2,
        )
        self.assertEqual(
            long_contract.retention_until.year,
            long_contract.create_date.year + 10,
        )
