# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooContractsTestBase


def _make_passed_resolution(env):
    resolution = env['govoo.resolution'].create({
        'title': 'Approve the supply agreement',
        'resolution_type': 'ordinary',
    })
    resolution.write({'state': 'passed'})
    return resolution


@tagged('post_install', '-at_install')
class TestApprovalRoutingBoardLinkage(GovooContractsTestBase):
    """Approval Routing & Board-Approval Linkage (issue #169): BR-CM-001."""

    def test_approval_blocked_without_resolution_when_type_requires_it(self):
        self.contract_type.requires_board_approval = True
        contract = self._make_contract()
        contract.action_submit()
        with self.assertRaises(ValidationError):
            contract.action_approve()

    def test_approval_blocked_with_non_passed_resolution(self):
        self.contract_type.requires_board_approval = True
        resolution = self.env['govoo.resolution'].create({
            'title': 'Still open',
            'resolution_type': 'ordinary',
        })
        contract = self._make_contract(resolution_id=resolution.id)
        contract.action_submit()
        with self.assertRaises(ValidationError):
            contract.action_approve()

    def test_approval_succeeds_with_passed_resolution(self):
        self.contract_type.requires_board_approval = True
        resolution = _make_passed_resolution(self.env)
        contract = self._make_contract(resolution_id=resolution.id)
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')

    def test_approval_blocked_when_value_meets_threshold(self):
        self.contract_type.approval_threshold = 5000.0
        contract = self._make_contract(value=10000.0)
        contract.action_submit()
        with self.assertRaises(ValidationError):
            contract.action_approve()

    def test_approval_allowed_below_threshold_without_resolution(self):
        self.contract_type.approval_threshold = 50000.0
        contract = self._make_contract(value=10000.0)
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')

    def test_approval_succeeds_when_value_meets_threshold_with_resolution(self):
        self.contract_type.approval_threshold = 5000.0
        resolution = _make_passed_resolution(self.env)
        contract = self._make_contract(value=10000.0, resolution_id=resolution.id)
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')

    def test_no_gate_for_ordinary_contract(self):
        """A contract whose type does not require board approval and
        whose value is below any threshold approves without a resolution."""
        contract = self._make_contract()
        contract.action_submit()
        contract.action_approve()
        self.assertEqual(contract.state, 'approved')
