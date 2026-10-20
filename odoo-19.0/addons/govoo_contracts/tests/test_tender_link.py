# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install', 'govoo_contracts')
class TestTenderLink(GovooContractsTestBase):
    """Issue #304: a contract can optionally trace back to the tender it
    originated from, and a tender can navigate forward to the contract(s)
    it produced."""

    def _make_tender(self):
        return self.env['govoo.tender'].create({
            'name': 'IT Services Tender 2026',
            'company_id': self.company.id,
        })

    def test_contract_links_to_its_originating_tender(self):
        tender = self._make_tender()
        contract = self._make_contract(tender_id=tender.id)
        self.assertEqual(contract.tender_id, tender)

    def test_tender_contract_count_and_smart_button_domain(self):
        tender = self._make_tender()
        self.assertEqual(tender.contract_count, 0)
        contract = self._make_contract(tender_id=tender.id)
        self.assertEqual(tender.contract_count, 1)
        self.assertEqual(tender.contract_ids, contract)
        action = tender.action_view_contracts()
        self.assertEqual(action['domain'], [('tender_id', '=', tender.id)])

    def test_contract_without_a_tender_is_unaffected(self):
        """No regression: most contracts don't originate from a
        competitive tender at all -- tender_id must stay optional."""
        contract = self._make_contract()
        self.assertFalse(contract.tender_id)
