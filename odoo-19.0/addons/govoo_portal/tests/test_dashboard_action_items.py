# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo.fields import Date
from odoo.tests import TransactionCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_portal')
class TestDashboardActionItems(TransactionCase):
    """Issue #266: the unified "My Action Items" Dashboard replaces the
    old role-based board.board Dashboard (issue #252) with a per-user
    action list aggregated across 5 models. Every query here runs as the
    calling user (never sudo()), so these tests also double as the
    record-rule/multi-company regression guard the issue asked for."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.other_company = cls.env['res.company'].create({'name': 'Other Co (266)'})

        cls.director = new_test_user(
            cls.env, login='test_266_director',
            groups='govoo_base.group_govoo_user',
            company_id=cls.company.id,
        )
        cls.approver = new_test_user(
            cls.env, login='test_266_approver',
            groups='govoo_base.group_govoo_user,govoo_base.group_govoo_contract_approver',
            company_id=cls.company.id,
        )

        cls.committee = cls.env['govoo.committee'].create({
            'name': 'Committee 266',
            'company_id': cls.company.id,
        })
        cls.env['govoo.appointment'].create({
            'partner_id': cls.director.partner_id.id,
            'company_id': cls.company.id,
            'role': 'director',
            'committee_id': cls.committee.id,
            'date_appointed': '2025-01-01',
        })

        cls.contract_type = cls.env['govoo.contract.type'].create({
            'name': 'Supply Agreement 266',
            'company_id': cls.company.id,
        })
        cls.counterparty = cls.env['res.partner'].create({
            'name': 'Acme 266 Ltd',
            'company_id': cls.company.id,
        })

    def _make_resolution(self, company, partner=False):
        meeting = self.env['govoo.meeting'].create({
            'name': 'Meeting 266',
            'meeting_type': 'board',
            'committee_id': self.committee.id if company == self.company else False,
            'date': '2026-04-01 10:00:00',
            'company_id': company.id,
            'attendee_ids': [(6, 0, [partner.id])] if partner else [],
        })
        resolution = self.env['govoo.resolution'].create({
            'title': 'Resolution 266',
            'text': '<p>Resolved.</p>',
            'resolution_type': 'ordinary',
            'meeting_id': meeting.id,
        })
        resolution.action_open()
        return resolution, meeting

    def _make_obligation(self, responsible, company, due_in_days, state='open'):
        contract = self.env['govoo.contract'].create({
            'name': 'CTR-266-%s' % responsible.login,
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': company.id,
            'value': 1000.0,
        })
        obligation = self.env['govoo.contract.obligation'].create({
            'contract_id': contract.id,
            'name': 'Obligation 266',
            'due_date': Date.today() + timedelta(days=due_in_days),
            'responsible_id': responsible.id,
        })
        if state != 'open':
            obligation.state = state
        return obligation

    def _make_compliance_instance(self, responsible, company, due_in_days, state='upcoming'):
        obligation = self.env['govoo.compliance.obligation'].create({
            'name': 'Compliance Obligation 266',
            'authority': 'RDB',
            'frequency': 'annual',
            'basis': 'fixed_date',
            'fixed_day': 31,
            'fixed_month': 3,
            'active': True,
            'company_id': company.id,
        })
        instance = self.env['govoo.compliance.instance'].create({
            'obligation_id': obligation.id,
            'company_id': company.id,
            'due_date': Date.today() + timedelta(days=due_in_days),
            'responsible_id': responsible.id,
        })
        if state != 'upcoming':
            instance.state = state
        return instance

    def _get_items(self, user):
        return self.env['govoo.dashboard.action.items'].with_user(user).get_my_action_items()

    def test_vote_item_appears_for_eligible_voter(self):
        resolution, meeting = self._make_resolution(self.company, self.director.partner_id)
        data = self._get_items(self.director)
        vote_items = [i for i in data['items'] if i['type'] == 'vote' and i['res_id'] == resolution.id]
        self.assertEqual(len(vote_items), 1)
        self.assertEqual(vote_items[0]['group'], 'week')
        # Not assertEqual: this runs against seeded demo data, which may
        # already have other open resolutions this new test user hasn't
        # voted on either -- the exact count isn't this test's concern,
        # only that our own fixture resolution is correctly included.
        self.assertGreaterEqual(data['counts']['votes'], 1)

    def test_vote_item_absent_once_user_has_voted(self):
        resolution, meeting = self._make_resolution(self.company, self.director.partner_id)
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.director.partner_id.id,
            'choice': 'for',
        })
        data = self._get_items(self.director)
        vote_items = [i for i in data['items'] if i['type'] == 'vote' and i['res_id'] == resolution.id]
        self.assertEqual(len(vote_items), 0)

    def test_overdue_obligation_appears_under_overdue_bucket(self):
        obligation = self._make_obligation(self.approver, self.company, due_in_days=-3, state='overdue')
        data = self._get_items(self.approver)
        matches = [i for i in data['items'] if i['type'] == 'obligation' and i['res_id'] == obligation.id]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['group'], 'overdue')
        self.assertIn('Overdue', matches[0]['due_label'])
        self.assertEqual(data['counts']['overdue'], 1)

    def test_obligation_absent_for_user_without_contract_access(self):
        """govoo.contract.obligation has no access row for plain
        group_govoo_user -- this must degrade to zero items, not raise."""
        self._make_obligation(self.director, self.company, due_in_days=5)
        data = self._get_items(self.director)
        self.assertFalse([i for i in data['items'] if i['type'] == 'obligation'])

    def test_contract_in_approval_appears_only_for_approver_group(self):
        contract = self.env['govoo.contract'].create({
            'name': 'CTR-266-approval',
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': self.company.id,
            'value': 5000.0,
            'state': 'in_approval',
        })
        approver_data = self._get_items(self.approver)
        self.assertIn(
            contract.id,
            [i['res_id'] for i in approver_data['items'] if i['type'] == 'contract'],
        )

        director_data = self._get_items(self.director)
        self.assertFalse([i for i in director_data['items'] if i['type'] == 'contract'])

    def test_late_compliance_instance_appears_under_overdue_bucket(self):
        instance = self._make_compliance_instance(self.director, self.company, due_in_days=-2, state='late')
        data = self._get_items(self.director)
        matches = [i for i in data['items'] if i['type'] == 'filing' and i['res_id'] == instance.id]
        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0]['group'], 'overdue')

    def test_meeting_attendee_appears_under_meetings(self):
        resolution, meeting = self._make_resolution(self.company, self.director.partner_id)
        meeting.date = Date.context_today(self.env.user).strftime('%Y-%m-%d') + ' 10:00:00'
        data = self._get_items(self.director)
        matches = [i for i in data['items'] if i['type'] == 'meeting' and i['res_id'] == meeting.id]
        self.assertEqual(len(matches), 1)
        self.assertEqual(data['counts']['meetings'], 1)

    def test_other_company_item_never_appears(self):
        """Multi-company isolation: an item that would otherwise match
        lives in a company the user has no access to."""
        other_contract = self.env['govoo.contract'].create({
            'name': 'CTR-266-other-co',
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': self.other_company.id,
            'value': 1000.0,
            'state': 'in_approval',
        })
        data = self._get_items(self.approver)
        self.assertNotIn(
            other_contract.id,
            [i['res_id'] for i in data['items'] if i['type'] == 'contract'],
        )

    def test_tabs_and_counts_agree_with_items(self):
        self._make_resolution(self.company, self.approver.partner_id)
        data = self._get_items(self.approver)
        all_tab = next(t for t in data['tabs'] if t['key'] == 'all')
        self.assertEqual(all_tab['count'], len(data['items']))
        for tab in data['tabs']:
            if tab['key'] == 'all':
                continue
            self.assertEqual(
                tab['count'],
                len([i for i in data['items'] if i['type'] == tab['key']]),
            )

    # -- Issue #266 follow-up: governance-health KPI tiles --------------
    # These are company-wide, not per-user, so assertions are delta-based
    # against the shared seeded demo data rather than exact totals (same
    # discipline as test_vote_item_appears_for_eligible_voter above).

    def _make_active_contract(self, **overrides):
        vals = {
            'name': 'CTR-266-KPI',
            'contract_type_id': self.contract_type.id,
            'counterparty_id': self.counterparty.id,
            'company_id': self.company.id,
            'value': 5000000.0,
            'state': 'active',
        }
        vals.update(overrides)
        return self.env['govoo.contract'].create(vals)

    def _kpi(self, user, key):
        kpis = self._get_items(user)['kpis']
        return next((k for k in kpis if k['key'] == key), None)

    def test_contract_kpis_present_for_approver_absent_for_plain_user(self):
        self.assertIsNotNone(self._kpi(self.approver, 'expiring_contracts'))
        self.assertIsNotNone(self._kpi(self.approver, 'active_contracts_value'))
        self.assertIsNotNone(self._kpi(self.approver, 'undeclared_conflicts'))
        self.assertIsNone(self._kpi(self.director, 'expiring_contracts'))

    def test_expiring_contracts_kpi_counts_a_new_expiring_contract(self):
        before = int(self._kpi(self.approver, 'expiring_contracts')['value'])
        self._make_active_contract(date_end=Date.today() + timedelta(days=30))
        after = int(self._kpi(self.approver, 'expiring_contracts')['value'])
        self.assertEqual(after, before + 1)

    def test_expiring_contracts_kpi_excludes_a_far_future_contract(self):
        before = int(self._kpi(self.approver, 'expiring_contracts')['value'])
        self._make_active_contract(date_end=Date.today() + timedelta(days=400))
        after = int(self._kpi(self.approver, 'expiring_contracts')['value'])
        self.assertEqual(after, before)

    def test_active_contracts_value_kpi_includes_new_contract_value(self):
        def parsed(kpi):
            return int(''.join(ch for ch in kpi['value'] if ch.isdigit()))

        before = parsed(self._kpi(self.approver, 'active_contracts_value'))
        self._make_active_contract(value=5000000.0)
        after = parsed(self._kpi(self.approver, 'active_contracts_value'))
        self.assertEqual(after, before + 5000000)

    def _make_related_party_counterparty(self):
        """is_related_party is computed from the counterparty partner's
        own govoo_is_director/shareholder/officer/beneficial_owner flags
        (govoo_contract.py's _compute_is_related_party) -- it can't be set
        directly on the contract, only earned via a genuinely flagged
        partner."""
        partner = self.env['res.partner'].create({
            'name': 'Related Party 266',
            'company_id': self.company.id,
            'govoo_is_director': True,
        })
        return partner

    def test_undeclared_conflicts_kpi_counts_undeclared_related_party_contract(self):
        before = int(self._kpi(self.approver, 'undeclared_conflicts')['value'])
        self._make_active_contract(
            counterparty_id=self._make_related_party_counterparty().id, conflict_declared=False,
        )
        after = int(self._kpi(self.approver, 'undeclared_conflicts')['value'])
        self.assertEqual(after, before + 1)

    def test_undeclared_conflicts_kpi_excludes_declared_related_party_contract(self):
        before = int(self._kpi(self.approver, 'undeclared_conflicts')['value'])
        self._make_active_contract(
            counterparty_id=self._make_related_party_counterparty().id, conflict_declared=True,
        )
        after = int(self._kpi(self.approver, 'undeclared_conflicts')['value'])
        self.assertEqual(after, before)

    def test_pending_board_packs_kpi_present_for_any_user(self):
        self.assertIsNotNone(self._kpi(self.director, 'pending_board_packs'))

    def test_pending_board_packs_kpi_counts_a_new_draft_pack(self):
        meeting = self._make_resolution(self.company, self.director.partner_id)[1]
        before = int(self._kpi(self.director, 'pending_board_packs')['value'])
        self.env['govoo.board.pack'].create({'meeting_id': meeting.id})
        after = int(self._kpi(self.director, 'pending_board_packs')['value'])
        self.assertEqual(after, before + 1)
