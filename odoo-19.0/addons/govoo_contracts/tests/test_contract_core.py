# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestContractCore(GovooContractsTestBase):
    """Contract Register & Core Models (issue #167): model, state
    machine, write-once executed document, and multi-company isolation."""

    def setUp(self):
        super().setUp()
        # Execution is gated by delegation-of-authority (BR-CM-002, issue
        # #170); grant the test user a broad one here so these core-model
        # tests aren't coupled to that gate. The gate itself is exercised
        # in test_delegation_of_authority.py.
        self._grant_delegation()

    def test_contract_creation_defaults(self):
        contract = self._make_contract()
        self.assertEqual(contract.state, 'draft')
        self.assertEqual(contract.renewal_type, 'fixed')
        self.assertEqual(contract.currency_id, self.company.currency_id)

    def test_date_end_before_date_start_rejected(self):
        with self.assertRaises(ValidationError):
            self._make_contract(date_start='2026-06-01', date_end='2026-01-01')

    def test_state_transitions_happy_path(self):
        contract = self._make_contract()
        contract.action_submit()
        self.assertEqual(contract.state, 'in_approval')
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')
        contract.action_execute()
        self.assertEqual(contract.state, 'executed')
        contract.action_activate()
        self.assertEqual(contract.state, 'active')
        contract.action_expire()
        self.assertEqual(contract.state, 'expired')

    def test_state_transition_terminate_branch(self):
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()
        contract.action_terminate()
        self.assertEqual(contract.state, 'terminated')

    def test_state_transition_cannot_skip(self):
        contract = self._make_contract()
        with self.assertRaises(ValidationError):
            contract.action_approve()

    def test_state_transition_cannot_go_backward(self):
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        with self.assertRaises(ValidationError):
            contract.action_submit()

    def test_terminal_states_reject_transition(self):
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()
        contract.action_expire()
        with self.assertRaises(ValidationError):
            contract.action_terminate()

    def test_executed_document_write_once(self):
        """TC-CM-004 / BR-CM-004: once a contract is executed, the executed
        document cannot be replaced or cleared in place."""
        attachment_1 = self.env['ir.attachment'].create({
            'name': 'contract-v1.pdf', 'raw': b'v1',
        })
        attachment_2 = self.env['ir.attachment'].create({
            'name': 'contract-v2.pdf', 'raw': b'v2',
        })
        contract = self._make_contract(executed_document_id=attachment_1.id)
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        with self.assertRaises(UserError):
            contract.write({'executed_document_id': attachment_2.id})
        with self.assertRaises(UserError):
            contract.write({'executed_document_id': False})

    def test_executed_document_editable_before_executed(self):
        """The write-once lock only applies from 'executed' onward -- it
        must not block ordinary drafting before that."""
        attachment_1 = self.env['ir.attachment'].create({
            'name': 'draft-v1.pdf', 'raw': b'v1',
        })
        attachment_2 = self.env['ir.attachment'].create({
            'name': 'draft-v2.pdf', 'raw': b'v2',
        })
        contract = self._make_contract(executed_document_id=attachment_1.id)
        contract.write({'executed_document_id': attachment_2.id})
        self.assertEqual(contract.executed_document_id, attachment_2)

    def test_executed_contract_cannot_be_deleted(self):
        """TC-SEC-011 / BR-CM-004: an executed+ contract cannot be
        unlink()'d by any group, mirroring the register.entry pattern."""
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        with self.assertRaises(UserError):
            contract.unlink()

    def test_draft_contract_can_be_deleted(self):
        contract = self._make_contract()
        contract.unlink()


@tagged('post_install', '-at_install')
class TestContractMultiCompanyIsolation(GovooContractsTestBase):
    """Same multi-company isolation discipline as every other govoo_*
    model (BR-SEC-001), applied to govoo.contract/govoo.contract.type."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_b = cls.env['res.company'].create({'name': 'Other Company'})
        cls.contract_manager = new_test_user(
            cls.env, login='test_contract_manager',
            groups='govoo_base.group_govoo_contract_manager',
            company_id=cls.company.id,
        )
        cls.contract_type_b = cls.env['govoo.contract.type'].create({
            'name': 'Company B Type',
            'company_id': cls.company_b.id,
        })
        cls.counterparty_b = cls.env['res.partner'].create({
            'name': 'Company B Counterparty',
            'company_id': cls.company_b.id,
        })
        cls.contract_a = cls.env['govoo.contract'].create({
            'name': 'CTR-A-0001',
            'contract_type_id': cls.contract_type.id,
            'counterparty_id': cls.counterparty.id,
            'company_id': cls.company.id,
            'value': 10000.0,
        })
        cls.contract_b = cls.env['govoo.contract'].create({
            'name': 'CTR-B-0001',
            'contract_type_id': cls.contract_type_b.id,
            'counterparty_id': cls.counterparty_b.id,
            'company_id': cls.company_b.id,
            'value': 5000.0,
        })

    def test_contract_manager_cannot_read_other_company_contract(self):
        contracts = self.env['govoo.contract'].with_user(self.contract_manager).search([])
        self.assertIn(self.contract_a, contracts)
        self.assertNotIn(self.contract_b, contracts)

    def test_contract_manager_cannot_browse_other_company_contract_by_id(self):
        contract_b_as_manager = self.contract_b.with_user(self.contract_manager)
        with self.assertRaises(AccessError):
            contract_b_as_manager.check_access('read')

    def test_contract_approver_cannot_create(self):
        approver = new_test_user(
            self.env, login='test_contract_approver',
            groups='govoo_base.group_govoo_contract_approver',
            company_id=self.company.id,
        )
        with self.assertRaises(AccessError):
            self.env['govoo.contract'].with_user(approver).create({
                'name': 'CTR-0002',
                'contract_type_id': self.contract_type.id,
                'counterparty_id': self.counterparty.id,
                'company_id': self.company.id,
            })
