# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestRelatedPartyChecks(GovooContractsTestBase):
    """Related-Party Checks (issue #171): BR-CM-003, TC-CM-003."""

    def test_ordinary_counterparty_is_not_related_party(self):
        contract = self._make_contract()
        self.assertFalse(contract.is_related_party)

    def test_director_counterparty_is_related_party(self):
        self.counterparty.govoo_is_director = True
        contract = self._make_contract()
        self.assertTrue(contract.is_related_party)

    def test_shareholder_counterparty_is_related_party(self):
        self.counterparty.govoo_is_shareholder = True
        contract = self._make_contract()
        self.assertTrue(contract.is_related_party)

    def test_officer_counterparty_is_related_party(self):
        self.counterparty.govoo_is_officer = True
        contract = self._make_contract()
        self.assertTrue(contract.is_related_party)

    def test_beneficial_owner_counterparty_is_related_party(self):
        self.counterparty.govoo_is_beneficial_owner = True
        contract = self._make_contract()
        self.assertTrue(contract.is_related_party)

    def test_is_related_party_recomputes_on_counterparty_change(self):
        other_partner = self.env['res.partner'].create({
            'name': 'Related Party Partner',
            'company_id': self.company.id,
            'govoo_is_director': True,
        })
        contract = self._make_contract()
        self.assertFalse(contract.is_related_party)
        contract.counterparty_id = other_partner
        self.assertTrue(contract.is_related_party)

    def test_approval_blocked_for_related_party_without_declaration(self):
        self.counterparty.govoo_is_director = True
        contract = self._make_contract()
        contract.action_submit()
        with self.assertRaises(ValidationError):
            contract.action_approve()

    def test_approval_succeeds_for_related_party_with_declaration(self):
        self.counterparty.govoo_is_director = True
        contract = self._make_contract(conflict_declared=True)
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')

    def test_approval_unaffected_for_non_related_party(self):
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')
