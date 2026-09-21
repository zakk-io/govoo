# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase


class GovooContractsTestBase(TransactionCase):
    """Shared setup for govoo_contracts module tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.counterparty = cls.env['res.partner'].create({
            'name': 'Acme Supplies Ltd',
            'company_id': cls.company.id,
        })
        cls.contract_type = cls.env['govoo.contract.type'].create({
            'name': 'Supply Agreement',
            'company_id': cls.company.id,
        })

    def _make_contract(self, **overrides):
        vals = {
            'name': 'CTR-0001',
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': self.company.id,
            'value': 10000.0,
        }
        vals.update(overrides)
        return self.env['govoo.contract'].create(vals)
