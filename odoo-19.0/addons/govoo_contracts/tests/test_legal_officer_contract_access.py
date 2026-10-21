# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, UserError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install', 'govoo_contracts')
class TestLegalOfficerContractAccess(GovooContractsTestBase):
    """Issue #354: the Legal Officer can read and draft (create/edit
    only while still in Draft) the contract resulting from an Awarded
    tender, narrowed the same way #352 narrowed the Procurement
    Officer's own read-only grant -- but with its own, stricter
    condition (Awarded tenders only, consistent with this role's
    tender/purchase.order/minutes record rules in govoo_procurement),
    and its own write restriction (Draft only) enforced in Python since
    ir.rule can't narrow a single rule's domain differently per
    operation without re-triggering the OR-combination gotcha #352
    documented."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.legal_officer = new_test_user(
            cls.env, login='test_legal_officer_contracts',
            groups='govoo_procurement.group_govoo_legal_officer',
            company_id=cls.company.id,
        )

    def test_legal_officer_can_read_contract_on_an_awarded_tender(self):
        tender = self._make_evaluation_ready_tender(evaluation_stage='awarded')
        contract = self._make_contract(tender_id=tender.id)
        contract.with_user(self.legal_officer).check_access('read')

    def test_legal_officer_cannot_read_contract_on_a_tender_not_yet_awarded(self):
        """The Legal Officer's own tender/minutes access is already
        Awarded-only (#329); the contract they'd draft from an earlier
        stage shouldn't be reachable either, even though #330's own
        gate would already block creating it in that state."""
        tender = self._make_evaluation_ready_tender(evaluation_stage='financial_evaluation')
        contract = self._make_contract(tender_id=tender.id)
        with self.assertRaises(AccessError):
            contract.with_user(self.legal_officer).check_access('read')

    def test_legal_officer_cannot_read_contract_without_a_tender(self):
        contract = self._make_contract()
        with self.assertRaises(AccessError):
            contract.with_user(self.legal_officer).check_access('read')

    def test_legal_officer_can_draft_a_new_contract_for_an_awarded_tender(self):
        tender = self._make_evaluation_ready_tender(evaluation_stage='awarded')
        contract = self.env['govoo.contract'].with_user(self.legal_officer).create({
            'name': 'CTR-DRAFT-0001',
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': self.company.id,
            'tender_id': tender.id,
            'value': 5000.0,
        })
        self.assertEqual(contract.state, 'draft')

    def test_legal_officer_cannot_edit_contract_once_past_draft(self):
        tender = self._make_evaluation_ready_tender(evaluation_stage='awarded')
        contract = self._make_contract(tender_id=tender.id)
        contract.action_submit()
        self.assertEqual(contract.state, 'in_approval')
        with self.assertRaises(UserError):
            contract.with_user(self.legal_officer).write({'value': 1.0})

    def test_legal_officer_can_still_edit_while_in_draft(self):
        tender = self._make_evaluation_ready_tender(evaluation_stage='awarded')
        contract = self._make_contract(tender_id=tender.id)
        contract.with_user(self.legal_officer).write({'value': 7500.0})
        self.assertEqual(contract.value, 7500.0)

    def test_legal_officer_with_broader_contract_role_is_not_narrowed(self):
        """A Legal Officer who also holds a broader contract role (e.g.
        Contract Manager) keeps that role's own, broader access and is
        not held to the Draft-only write restriction either."""
        dual_role_user = new_test_user(
            self.env, login='test_legal_officer_and_contract_manager',
            groups='govoo_procurement.group_govoo_legal_officer,'
                   'govoo_base.group_govoo_contract_manager',
            company_id=self.company.id,
        )
        contract = self._make_contract()
        contract.with_user(dual_role_user).check_access('read')
        contract.action_submit()
        contract.with_user(dual_role_user).write({'value': 1.0})
