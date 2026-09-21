# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.exceptions import ValidationError
from odoo.fields import Date
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestObligationMilestoneTracking(GovooContractsTestBase):
    """Obligation/Milestone Tracking (issue #174)."""

    def test_obligation_scoped_to_contract_and_company(self):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Deliver first shipment',
            'due_date': Date.today() + timedelta(days=30),
        })
        self.assertEqual(obligation.company_id, contract.company_id)
        self.assertIn(obligation, contract.obligation_ids)
        self.assertEqual(contract.obligation_count, 1)

    def test_milestone_scoped_to_contract_and_company(self):
        contract = self._make_contract()
        milestone = self.env['govoo.contract.milestone'].create({
            'contract_id': contract.id,
            'name': 'First payment',
            'date': Date.today() + timedelta(days=15),
            'value': 2500.0,
        })
        self.assertEqual(milestone.company_id, contract.company_id)
        self.assertIn(milestone, contract.milestone_ids)
        self.assertEqual(contract.milestone_count, 1)

    def test_obligation_terminal_state_blocks_further_change(self):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Final report',
            'due_date': Date.today(),
        })
        obligation.action_done()
        self.assertEqual(obligation.state, 'done')
        with self.assertRaises(ValidationError):
            obligation.write({'state': 'open'})

    def test_obligation_waive_blocked_when_already_terminal(self):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Final report',
            'due_date': Date.today(),
        })
        obligation.action_done()
        with self.assertRaises(ValidationError):
            obligation.action_waive()

    def test_cron_escalates_overdue_obligation(self):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Overdue item',
            'due_date': Date.today() - timedelta(days=1),
        })
        self.env['govoo.contract.obligation']._cron_escalate_overdue()
        self.assertEqual(obligation.state, 'overdue')

    def test_cron_does_not_escalate_future_obligation(self):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Future item',
            'due_date': Date.today() + timedelta(days=10),
        })
        self.env['govoo.contract.obligation']._cron_escalate_overdue()
        self.assertEqual(obligation.state, 'open')

    def test_obligation_reminder_staged_within_lead_time(self):
        contract = self._make_contract()
        responsible = self.env.user
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Reminder-eligible item',
            'due_date': Date.today() + timedelta(days=3),
            'lead_time_days': 7,
            'responsible_id': responsible.id,
        })
        self.env['govoo.contract.cron']._cron_send_obligation_reminders()
        self.assertTrue(obligation.activity_ids)
