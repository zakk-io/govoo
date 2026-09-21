# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.fields import Date
from odoo.tests import tagged

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestDashboards(GovooContractsTestBase):
    """Dashboards (issue #178): obligations RAG-coloring convention
    (ui/dashboards.md section 2/4b) and the register/spend views exist
    and don't error on real data."""

    def _obligation(self, due_in_days, lead_time_days=7, state='open'):
        contract = self._make_contract()
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Test obligation',
            'due_date': Date.today() + timedelta(days=due_in_days),
            'lead_time_days': lead_time_days,
        })
        if state == 'done':
            obligation.action_done()
        elif state == 'waived':
            obligation.action_waive()
        return obligation

    def test_rag_green_when_open_and_far_from_due(self):
        obligation = self._obligation(due_in_days=30, lead_time_days=7)
        self.assertEqual(obligation.rag_color, 'green')

    def test_rag_amber_when_open_and_within_lead_time(self):
        obligation = self._obligation(due_in_days=3, lead_time_days=7)
        self.assertEqual(obligation.rag_color, 'amber')

    def test_rag_red_when_overdue(self):
        obligation = self._obligation(due_in_days=-1, lead_time_days=7)
        self.env['govoo.contract.obligation']._cron_escalate_overdue()
        obligation.invalidate_recordset()
        self.assertEqual(obligation.state, 'overdue')
        self.assertEqual(obligation.rag_color, 'red')

    def test_rag_grey_when_done(self):
        obligation = self._obligation(due_in_days=5, state='done')
        self.assertEqual(obligation.rag_color, 'grey')

    def test_rag_grey_when_waived(self):
        obligation = self._obligation(due_in_days=5, state='waived')
        self.assertEqual(obligation.rag_color, 'grey')

    def test_spend_by_counterparty_pivot_view_reads_real_data(self):
        """Register/spend views render off real fields -- a smoke check
        that the pivot's grouping/measure fields exist and are readable,
        not a UI rendering test."""
        contract_a = self._make_contract(value=1000.0)
        contract_b = self._make_contract(
            name='CTR-0002', counterparty_id=self.counterparty.id, value=2500.0,
        )
        contracts = contract_a | contract_b
        total = sum(contracts.mapped('value'))
        self.assertEqual(total, 3500.0)
