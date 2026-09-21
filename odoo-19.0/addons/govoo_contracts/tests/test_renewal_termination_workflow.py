# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestRenewalTerminationWorkflow(GovooContractsTestBase):
    """Renewal/Termination Workflow (issue #175): TC-CM-010, FR-CM-14."""

    def _active_contract(self, **overrides):
        self._grant_delegation()
        contract = self._make_contract(**overrides)
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()
        return contract

    def test_fixed_term_contract_expires_past_date_end(self):
        contract = self._active_contract(
            renewal_type='fixed', date_end=Date.today() - timedelta(days=1),
        )
        self.env['govoo.contract.cron']._cron_expire_fixed_term_contracts()
        self.assertEqual(contract.state, 'expired')

    def test_evergreen_contract_stays_active_past_date_end(self):
        contract = self._active_contract(
            renewal_type='auto', date_end=Date.today() - timedelta(days=1),
        )
        self.env['govoo.contract.cron']._cron_expire_fixed_term_contracts()
        self.assertEqual(contract.state, 'active')

    def test_fixed_term_contract_not_yet_due_stays_active(self):
        contract = self._active_contract(
            renewal_type='fixed', date_end=Date.today() + timedelta(days=30),
        )
        self.env['govoo.contract.cron']._cron_expire_fixed_term_contracts()
        self.assertEqual(contract.state, 'active')

    def test_terminate_requires_reason(self):
        contract = self._active_contract()
        with self.assertRaises(ValidationError):
            contract.action_terminate()

    def test_terminate_succeeds_with_reason(self):
        contract = self._active_contract()
        contract.termination_reason = 'Counterparty insolvency.'
        contract.action_terminate()
        self.assertEqual(contract.state, 'terminated')

    def test_evergreen_contract_can_still_be_explicitly_terminated(self):
        contract = self._active_contract(renewal_type='auto')
        contract.termination_reason = 'Mutual agreement to end early.'
        contract.action_terminate()
        self.assertEqual(contract.state, 'terminated')
