# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_portal')
class TestCommitteeContractAccess(HttpCase):
    """Issue #342: a Procurement Committee portal member can open the
    contract linked to a tender their committee evaluated -- reuses
    govoo_contracts's own Contract Viewer Portal route
    (/my/contracts/<id>), mirrors test_procurement_committee_portal.py's
    own HTTP-level test shape."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'IT Procurement Committee', 'company_id': cls.company.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Facilities Procurement Committee', 'company_id': cls.company.id,
        })
        # Issue #337: a Financial Evaluation meeting can have a
        # different committee than the Technical one -- proves the
        # portal scoping is an OR across both, not just the first.
        cls.committee_financial_only = cls.env['govoo.committee'].create({
            'name': 'IT Procurement Committee (Financial Stage)', 'company_id': cls.company.id,
        })

        cls.user_member_a = new_test_user(
            cls.env, login='test_contract_committee_a',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )
        cls.user_member_b = new_test_user(
            cls.env, login='test_contract_committee_b',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )
        cls.user_member_financial_only = new_test_user(
            cls.env, login='test_contract_committee_financial_only',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )

        for user, committee in (
            (cls.user_member_a, cls.committee_a),
            (cls.user_member_b, cls.committee_b),
            (cls.user_member_financial_only, cls.committee_financial_only),
        ):
            cls.env['govoo.appointment'].create({
                'partner_id': user.partner_id.id,
                'committee_id': committee.id,
                'role': 'committee_member',
                'company_id': cls.company.id,
                'date_appointed': '2026-01-01',
            })

        cls.meeting_a = cls.env['govoo.meeting'].create({
            'name': 'IT Tender Technical Evaluation', 'committee_id': cls.committee_a.id,
            'meeting_type': 'committee', 'date': '2026-03-15 10:00:00', 'company_id': cls.company.id,
        })
        cls.meeting_b = cls.env['govoo.meeting'].create({
            'name': 'Facilities Tender Evaluation', 'committee_id': cls.committee_b.id,
            'meeting_type': 'committee', 'date': '2026-03-15 14:00:00', 'company_id': cls.company.id,
        })
        cls.meeting_financial_only = cls.env['govoo.meeting'].create({
            'name': 'IT Tender Financial Evaluation', 'committee_id': cls.committee_financial_only.id,
            'meeting_type': 'committee', 'date': '2026-04-01 10:00:00', 'company_id': cls.company.id,
        })

        cls.tender_a = cls.env['govoo.tender'].create({
            'name': 'TND-A - IT Equipment', 'company_id': cls.company.id,
            'technical_evaluation_meeting_id': cls.meeting_a.id,
            'financial_evaluation_meeting_id': cls.meeting_financial_only.id,
        })
        cls.tender_b = cls.env['govoo.tender'].create({
            'name': 'TND-B - Facilities Works', 'company_id': cls.company.id,
            'technical_evaluation_meeting_id': cls.meeting_b.id,
        })

        # Issue #330: a contract can't link to a tender until its
        # Technical/Financial Evaluation minutes are both approved --
        # same "different approver" config gotcha already documented in
        # govoo_contracts/tests/common.py's own helper.
        minutes_approver = new_test_user(
            cls.env, login='test_contract_access_minutes_approver',
            groups='govoo_base.group_govoo_secretary', company_id=cls.company.id,
        )
        for meeting in (cls.meeting_a, cls.meeting_financial_only):
            meeting.state = 'minuted'
            minutes = cls.env['govoo.minutes'].create({'meeting_id': meeting.id})
            minutes.action_submit_for_approval()
            minutes.with_user(minutes_approver).action_approve()
            meeting.minutes_id = minutes.id

        cls.contract_type = cls.env['govoo.contract.type'].create({
            'name': 'Supply Agreement', 'company_id': cls.company.id,
        })
        cls.counterparty = cls.env['res.partner'].create({
            'name': 'IT Equipment Supplier Ltd', 'company_id': cls.company.id,
        })
        cls.contract_a = cls.env['govoo.contract'].create({
            'name': 'CTR-A', 'contract_type_id': cls.contract_type.id,
            'counterparty_id': cls.counterparty.id, 'company_id': cls.company.id,
            'value': 50000.0, 'tender_id': cls.tender_a.id,
        })

    def _password(self, login):
        return login + 'x' * (8 - len(login))

    def test_committee_member_can_open_own_tenders_contract(self):
        self.authenticate('test_contract_committee_a', self._password('test_contract_committee_a'))
        response = self.url_open('/my/contracts/%s' % self.contract_a.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.contract_a.name, response.text)

    def test_other_committee_member_cannot_open_contract(self):
        self.authenticate('test_contract_committee_b', self._password('test_contract_committee_b'))
        response = self.url_open('/my/contracts/%s' % self.contract_a.id)
        self.assertNotIn(self.contract_a.name, response.text)
        self.assertNotIn('/my/contracts/%s' % self.contract_a.id, response.url)

    def test_financial_only_committee_member_can_open_contract(self):
        """Proves the OR across both evaluation meetings, not just the
        technical one."""
        self.authenticate(
            'test_contract_committee_financial_only',
            self._password('test_contract_committee_financial_only'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract_a.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.contract_a.name, response.text)

    def test_tender_detail_page_links_to_its_contract(self):
        self.authenticate('test_contract_committee_a', self._password('test_contract_committee_a'))
        response = self.url_open('/my/procurement/tenders/%s' % self.tender_a.id)
        self.assertIn('/my/contracts/%s' % self.contract_a.id, response.text)
