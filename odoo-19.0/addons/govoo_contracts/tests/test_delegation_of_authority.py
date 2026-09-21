# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestDelegationOfAuthority(GovooContractsTestBase):
    """Delegation-of-Authority Matrix (issue #170): BR-CM-002.

    Per docs/spec/data-model/state-machines.md and business-rules.md,
    delegation-of-authority is enforced at execution (approved ->
    executed), not at approval -- corrected here from the GitHub issue's
    paraphrase, which is now the aspirational description while this
    test suite and the state machine spec are the source of truth.
    """

    def _approved_contract(self, **overrides):
        contract = self._make_contract(**overrides)
        contract.action_submit()
        contract.action_approve()
        return contract

    def test_execution_blocked_with_no_delegation(self):
        contract = self._approved_contract()
        with self.assertRaises(ValidationError):
            contract.action_execute()

    def test_execution_blocked_below_required_limit(self):
        self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': self.env.uid,
            'contract_type_id': self.contract_type.id,
            'max_value': 5000.0,
        })
        contract = self._approved_contract(value=10000.0)
        with self.assertRaises(ValidationError):
            contract.action_execute()

    def test_execution_allowed_within_type_specific_limit(self):
        self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': self.env.uid,
            'contract_type_id': self.contract_type.id,
            'max_value': 20000.0,
        })
        contract = self._approved_contract(value=10000.0)
        contract.action_execute()
        self.assertEqual(contract.state, 'executed')

    def test_execution_allowed_within_any_type_limit(self):
        self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': self.env.uid,
            'max_value': 20000.0,
        })
        contract = self._approved_contract(value=10000.0)
        contract.action_execute()
        self.assertEqual(contract.state, 'executed')

    def test_execution_blocked_for_delegation_scoped_to_other_type(self):
        other_type = self.env['govoo.contract.type'].create({
            'name': 'Lease Agreement',
            'company_id': self.company.id,
        })
        self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': self.env.uid,
            'contract_type_id': other_type.id,
            'max_value': 20000.0,
        })
        contract = self._approved_contract(value=10000.0)
        with self.assertRaises(ValidationError):
            contract.action_execute()

    def test_execution_uses_delegation_of_executing_user_not_creator(self):
        approver = new_test_user(
            self.env, login='test_delegated_approver',
            groups='govoo_base.group_govoo_contract_approver',
            company_id=self.company.id,
        )
        self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': approver.id,
            'max_value': 20000.0,
        })
        contract = self._approved_contract(value=10000.0)
        with self.assertRaises(ValidationError):
            contract.action_execute()
        contract.with_user(approver).action_execute()
        self.assertEqual(contract.state, 'executed')
