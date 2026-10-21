# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase
from odoo.tests.common import new_test_user


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

    def _make_approved_evaluation_meeting(self, name, company=None):
        """Issue #330: a committee meeting whose minutes have reached
        'approved' -- the completion bar the contract-drafting gate
        checks. Builds the govoo.meeting/govoo.minutes chain directly
        rather than depending on govoo_procurement's own test fixtures,
        since this module's tests don't import that module's test
        code."""
        company = company or self.company
        committee = self.env['govoo.committee'].create({
            'name': 'Tender Evaluation Committee',
            'company_id': company.id,
        })
        meeting = self.env['govoo.meeting'].create({
            'name': name,
            'meeting_type': 'committee',
            'committee_id': committee.id,
            'date': '2026-03-01 10:00:00',
            'company_id': company.id,
            'state': 'minuted',
        })
        minutes = self.env['govoo.minutes'].create({'meeting_id': meeting.id})
        minutes.action_submit_for_approval()
        # govoo_board's minutes_require_different_approver gate (live
        # Governance Settings configuration, not reset by this test
        # base) can be on, so approve as a different user from whoever
        # submitted -- same reasoning govoo_procurement's own _award()
        # helper already documents for an analogous gate.
        approver = new_test_user(
            self.env, login='test_minutes_approver_%d' % minutes.id,
            groups='govoo_base.group_govoo_secretary',
            company_id=company.id,
        )
        minutes.with_user(approver).action_approve()
        meeting.minutes_id = minutes.id
        return meeting

    def _make_evaluation_ready_tender(self, **overrides):
        """Issue #330: a tender whose Technical and Financial Evaluation
        minutes are both approved -- the state a contract is actually
        allowed to start drafting against."""
        vals = {
            'name': 'IT Services Tender 2026',
            'company_id': self.company.id,
            'technical_evaluation_meeting_id': self._make_approved_evaluation_meeting(
                'Technical Evaluation Meeting',
            ).id,
            'financial_evaluation_meeting_id': self._make_approved_evaluation_meeting(
                'Financial Evaluation Meeting',
            ).id,
        }
        vals.update(overrides)
        return self.env['govoo.tender'].create(vals)

    def _grant_delegation(self, user_id=None, max_value=1000000.0, contract_type_id=False):
        """Test convenience: give a user delegated authority to execute
        contracts (BR-CM-002), so tests unrelated to the
        delegation-of-authority gate itself don't need to construct one
        by hand. docs/spec-facing tests of the gate live in
        test_delegation_of_authority.py."""
        return self.env['govoo.contract.delegation'].create({
            'company_id': self.company.id,
            'user_id': user_id or self.env.uid,
            'contract_type_id': contract_type_id,
            'max_value': max_value,
        })
