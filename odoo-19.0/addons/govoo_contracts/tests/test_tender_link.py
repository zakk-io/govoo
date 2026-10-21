# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
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
        tender = self._make_evaluation_ready_tender()
        contract = self._make_contract(tender_id=tender.id)
        self.assertEqual(contract.tender_id, tender)

    def test_tender_contract_count_and_smart_button_domain(self):
        tender = self._make_evaluation_ready_tender()
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


@tagged('post_install', '-at_install', 'govoo_contracts')
class TestLockContractDraftingGate(GovooContractsTestBase):
    """Issue #330: drafting a contract from an awarded tender stays
    locked until Technical Evaluation and Financial Evaluation are both
    complete (their minutes approved) for that tender."""

    def _make_tender(self):
        return self.env['govoo.tender'].create({
            'name': 'IT Services Tender 2026',
            'company_id': self.company.id,
        })

    def test_blocked_when_both_evaluations_missing(self):
        tender = self._make_tender()
        with self.assertRaises(ValidationError) as ctx:
            self._make_contract(tender_id=tender.id)
        self.assertIn('Technical Evaluation', str(ctx.exception))
        self.assertIn('Financial Evaluation', str(ctx.exception))

    def test_blocked_when_only_technical_evaluation_present(self):
        tender = self._make_tender()
        tender.technical_evaluation_meeting_id = self._make_approved_evaluation_meeting(
            'Technical Evaluation Meeting',
        ).id
        with self.assertRaises(ValidationError) as ctx:
            self._make_contract(tender_id=tender.id)
        self.assertNotIn('Technical Evaluation', str(ctx.exception))
        self.assertIn('Financial Evaluation', str(ctx.exception))

    def test_blocked_when_minutes_exist_but_not_yet_approved(self):
        """Draft/for_approval minutes don't count as complete -- same
        approved/signed bar already used for portal visibility (#344)."""
        tender = self._make_tender()
        committee = self.env['govoo.committee'].create({
            'name': 'Tender Evaluation Committee', 'company_id': self.company.id,
        })
        meeting = self.env['govoo.meeting'].create({
            'name': 'Technical Evaluation Meeting', 'meeting_type': 'committee',
            'committee_id': committee.id, 'date': '2026-03-01 10:00:00',
            'company_id': self.company.id, 'state': 'minuted',
        })
        minutes = self.env['govoo.minutes'].create({'meeting_id': meeting.id})
        meeting.minutes_id = minutes.id
        tender.technical_evaluation_meeting_id = meeting.id
        tender.financial_evaluation_meeting_id = self._make_approved_evaluation_meeting(
            'Financial Evaluation Meeting',
        ).id

        with self.assertRaises(ValidationError) as ctx:
            self._make_contract(tender_id=tender.id)
        self.assertIn('Technical Evaluation', str(ctx.exception))

    def test_succeeds_once_both_evaluations_complete(self):
        tender = self._make_evaluation_ready_tender()
        contract = self._make_contract(tender_id=tender.id)
        self.assertEqual(contract.tender_id, tender)

    def test_gate_not_triggered_for_contracts_without_a_tender(self):
        """No regression: a contract that never links to a tender must
        never hit this gate at all."""
        contract = self._make_contract()
        self.assertFalse(contract.tender_id)
