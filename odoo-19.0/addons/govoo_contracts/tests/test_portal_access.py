# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError
from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user

from .common import GovooContractsTestBase


@tagged('post_install', '-at_install')
class TestPortalAccess(GovooContractsTestBase):
    """Portal Access / Contract Viewer Portal (issue #177): BR-CM-007.

    Resolves the previously-open "named approver" data-model gap
    (docs/spec/decisions/assumptions.md) via the new
    portal_approver_ids field, rather than assuming it always equals
    counterparty_id.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.counterparty_partner = cls.counterparty
        cls.named_approver_partner = cls.env['res.partner'].create({
            'name': 'Named Approver Partner',
            'company_id': cls.company.id,
        })
        cls.outsider_partner = cls.env['res.partner'].create({
            'name': 'Unrelated Partner',
            'company_id': cls.company.id,
        })
        cls.counterparty_portal_user = new_test_user(
            cls.env, login='test_counterparty_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.counterparty_partner.id,
        )
        cls.approver_portal_user = new_test_user(
            cls.env, login='test_named_approver_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.named_approver_partner.id,
        )
        cls.outsider_portal_user = new_test_user(
            cls.env, login='test_outsider_portal',
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id,
            partner_id=cls.outsider_partner.id,
        )

    def test_counterparty_can_read_own_contract(self):
        contract = self._make_contract()
        contracts = self.env['govoo.contract'].with_user(
            self.counterparty_portal_user,
        ).search([])
        self.assertIn(contract, contracts)

    def test_named_approver_can_read_contract(self):
        contract = self._make_contract(portal_approver_ids=[(4, self.named_approver_partner.id)])
        contracts = self.env['govoo.contract'].with_user(
            self.approver_portal_user,
        ).search([])
        self.assertIn(contract, contracts)

    def test_outsider_cannot_read_contract(self):
        contract = self._make_contract(portal_approver_ids=[(4, self.named_approver_partner.id)])
        contracts = self.env['govoo.contract'].with_user(
            self.outsider_portal_user,
        ).search([])
        self.assertNotIn(contract, contracts)

    def test_outsider_cannot_browse_contract_by_id(self):
        """TC-SEC-010: direct/guessed-ID access denied at the record-rule
        level, not merely absent from the list."""
        contract = self._make_contract()
        contract_as_outsider = contract.with_user(self.outsider_portal_user)
        with self.assertRaises(AccessError):
            contract_as_outsider.check_access('read')

    def test_counterparty_cannot_write(self):
        contract = self._make_contract()
        with self.assertRaises(AccessError):
            contract.with_user(self.counterparty_portal_user).write({'value': 1.0})


@tagged('post_install', '-at_install', 'govoo_contracts')
class TestContractPortalContent(HttpCase):
    """Issue #350: the Contract Viewer Portal detail page shows useful
    content -- counterparty, value, a human-readable status, an
    explanatory message when no document exists yet, and a link back
    to the originating tender only when the current viewer can
    actually reach it."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.contract_type = cls.env['govoo.contract.type'].create({
            'name': 'Supply Agreement', 'company_id': cls.company.id,
        })
        cls.counterparty = cls.env['res.partner'].create({
            'name': 'Acme Supplies Ltd', 'company_id': cls.company.id,
        })
        cls.counterparty_user = new_test_user(
            cls.env, login='test_contract_content_counterparty',
            # new_test_user's default `name` would otherwise overwrite
            # counterparty.name too: res.users/res.partner share `name`
            # via _inherits, so writing it on the user writes straight
            # through to the same partner record.
            name=cls.counterparty.name,
            groups='govoo_base.group_govoo_contract_portal',
            company_id=cls.company.id, partner_id=cls.counterparty.id,
        )

        # A committee member who can reach the originating tender, so
        # the "View Tender" link should appear for them.
        cls.committee = cls.env['govoo.committee'].create({
            'name': 'IT Procurement Committee', 'company_id': cls.company.id,
        })
        cls.committee_user = new_test_user(
            cls.env, login='test_contract_content_committee',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )
        cls.env['govoo.appointment'].create({
            'partner_id': cls.committee_user.partner_id.id,
            'committee_id': cls.committee.id,
            'role': 'committee_member', 'company_id': cls.company.id,
            'date_appointed': '2026-01-01',
        })

        minutes_approver = new_test_user(
            cls.env, login='test_contract_content_minutes_approver',
            groups='govoo_base.group_govoo_secretary', company_id=cls.company.id,
        )
        meetings = {}
        for key in ('technical', 'financial'):
            meeting = cls.env['govoo.meeting'].create({
                'name': 'IT Tender %s Evaluation' % key.capitalize(),
                'committee_id': cls.committee.id, 'meeting_type': 'committee',
                'date': '2026-03-15 10:00:00', 'company_id': cls.company.id,
                'state': 'minuted',
            })
            minutes = cls.env['govoo.minutes'].create({'meeting_id': meeting.id})
            minutes.action_submit_for_approval()
            minutes.with_user(minutes_approver).action_approve()
            meeting.minutes_id = minutes.id
            meetings[key] = meeting

        cls.tender = cls.env['govoo.tender'].create({
            'name': 'TND - Test Equipment', 'company_id': cls.company.id,
            'technical_evaluation_meeting_id': meetings['technical'].id,
            'financial_evaluation_meeting_id': meetings['financial'].id,
        })

        # Also readable by the counterparty (via counterparty_id), but
        # the counterparty holds no procurement-committee access, so
        # the "View Tender" link must not appear for them.
        cls.contract = cls.env['govoo.contract'].create({
            'name': 'CTR-CONTENT-TEST',
            'contract_type_id': cls.contract_type.id,
            'counterparty_id': cls.counterparty.id,
            'company_id': cls.company.id,
            'value': 25000.0,
            'tender_id': cls.tender.id,
        })

    def _password(self, login):
        return login + 'x' * (8 - len(login))

    def test_counterparty_and_value_shown(self):
        self.authenticate(
            'test_contract_content_committee',
            self._password('test_contract_content_committee'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract.id)
        self.assertIn('Acme Supplies Ltd', response.text)
        # RWF (this company's currency) has 0 decimal places.
        self.assertIn('25,000', response.text)

    def test_status_shows_human_label_not_raw_key(self):
        self.authenticate(
            'test_contract_content_committee',
            self._password('test_contract_content_committee'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract.id)
        self.assertIn('Draft', response.text)

    def test_no_document_message_shown_while_drafting(self):
        self.authenticate(
            'test_contract_content_committee',
            self._password('test_contract_content_committee'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract.id)
        self.assertIn('still being drafted', response.text)

    def test_tender_link_shown_for_committee_member(self):
        self.authenticate(
            'test_contract_content_committee',
            self._password('test_contract_content_committee'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract.id)
        self.assertIn('/my/procurement/tenders/%s' % self.tender.id, response.text)

    def test_tender_link_hidden_for_counterparty_without_access(self):
        self.authenticate(
            'test_contract_content_counterparty',
            self._password('test_contract_content_counterparty'),
        )
        response = self.url_open('/my/contracts/%s' % self.contract.id)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('/my/procurement/tenders/%s' % self.tender.id, response.text)
