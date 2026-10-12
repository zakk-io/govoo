# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta
from lxml import etree

from odoo.fields import Date
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval
from dateutil.relativedelta import relativedelta

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestContractViewRendering(GovooContractsTestBase):
    """Issue #253: ribbons on terminal states and the new search filters
    need their underlying views/domains to actually be correct, not just
    present. get_views() exercises the same field/widget validation Odoo
    runs on module upgrade (catches a typo'd field or widget name); the
    filter tests re-evaluate the real domain string straight out of the
    view, the same way the web client would, rather than duplicating it by
    hand in the test."""

    def _active_contract(self, **overrides):
        self._grant_delegation()
        contract = self._make_contract(**overrides)
        contract.action_submit()
        contract.action_approve()
        contract.action_execute()
        contract.action_activate()
        return contract

    def _get_filter_domain(self, view_xmlid, filter_name):
        view = self.env.ref(view_xmlid)
        arch = etree.fromstring(view.arch)
        node = arch.find(f".//filter[@name='{filter_name}']")
        self.assertIsNotNone(node, f"filter '{filter_name}' not found in {view_xmlid}")
        eval_context = {
            'context_today': lambda: Date.context_today(self.env.user),
            'relativedelta': relativedelta,
            'uid': self.env.uid,
        }
        return safe_eval(node.get('domain'), eval_context)

    def test_contract_form_view_loads_for_every_terminal_state(self):
        """get_views() must not raise for the ribbon-bearing form, e.g. if
        a ribbon's invisible= referenced a field/value that doesn't exist."""
        contract = self._active_contract()
        contract.termination_reason = 'Counterparty insolvency.'
        contract.action_terminate()
        self.assertEqual(contract.state, 'terminated')
        views = contract.get_views([(False, 'form')])
        self.assertIn('form', views['views'])

        expired = self._active_contract(renewal_type='fixed', date_end=Date.today() - timedelta(days=1))
        self.env['govoo.contract.cron']._cron_expire_fixed_term_contracts()
        self.assertEqual(expired.state, 'expired')
        views = expired.get_views([(False, 'form')])
        self.assertIn('form', views['views'])

    def test_contract_type_form_view_loads(self):
        self.contract_type.get_views([(False, 'form')])

    def test_expiring_soon_filter_matches_active_contracts_within_60_days(self):
        in_window = self._active_contract(date_end=Date.today() + timedelta(days=30))
        outside_window = self._active_contract(date_end=Date.today() + timedelta(days=90))
        no_date = self._active_contract(date_end=False)

        domain = self._get_filter_domain('govoo_contracts.govoo_contract_view_search', 'filter_expiring_soon')
        matches = self.env['govoo.contract'].search(domain)

        self.assertIn(in_window, matches)
        self.assertNotIn(outside_window, matches)
        self.assertNotIn(no_date, matches)

    def test_my_obligations_filter_matches_only_own_obligations(self):
        from odoo.tests.common import new_test_user

        other_user = new_test_user(
            self.env, login='test_obligation_other_user',
            groups='base.group_user',
            company_id=self.company.id,
        )
        contract = self._active_contract()
        mine = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'File renewal notice',
            'due_date': Date.today() + timedelta(days=10),
            'responsible_id': self.env.uid,
        })
        not_mine = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Pay annual fee',
            'due_date': Date.today() + timedelta(days=10),
            'responsible_id': other_user.id,
        })

        domain = self._get_filter_domain(
            'govoo_contracts.govoo_contract_obligation_view_search', 'filter_mine')
        matches = self.env['govoo.contract.obligation'].search(domain)

        self.assertIn(mine, matches)
        self.assertNotIn(not_mine, matches)
