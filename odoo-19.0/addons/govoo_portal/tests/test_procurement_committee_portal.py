# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_portal')
class TestProcurementCommitteePortal(HttpCase):
    """Issue #333: real HTTP/controller-layer tests for the Procurement
    Committee Portal, exercising the actual record-rule/token-bypass
    boundary (BR-SEC-006) rather than just ORM domain filtering --
    mirrors TestPortal's own director-portal tests (test_portal.py)."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'IT Procurement Committee',
            'company_id': cls.company.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Facilities Procurement Committee',
            'company_id': cls.company.id,
        })

        cls.user_member_a = new_test_user(
            cls.env, login='test_committee_portal_a',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )
        cls.user_member_b = new_test_user(
            cls.env, login='test_committee_portal_b',
            groups='govoo_procurement.group_govoo_procurement_committee_portal',
            company_id=cls.company.id,
        )

        cls.env['govoo.appointment'].create({
            'partner_id': cls.user_member_a.partner_id.id,
            'committee_id': cls.committee_a.id,
            'role': 'committee_member',
            'company_id': cls.company.id,
            'date_appointed': '2026-01-01',
        })
        cls.env['govoo.appointment'].create({
            'partner_id': cls.user_member_b.partner_id.id,
            'committee_id': cls.committee_b.id,
            'role': 'committee_member',
            'company_id': cls.company.id,
            'date_appointed': '2026-01-01',
        })

        cls.meeting_a = cls.env['govoo.meeting'].create({
            'name': 'IT Tender Evaluation',
            'committee_id': cls.committee_a.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': cls.company.id,
        })
        cls.meeting_b = cls.env['govoo.meeting'].create({
            'name': 'Facilities Tender Evaluation',
            'committee_id': cls.committee_b.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 14:00:00',
            'company_id': cls.company.id,
        })

        cls.tender_a = cls.env['govoo.tender'].create({
            'name': 'TND-A - IT Equipment',
            'company_id': cls.company.id,
            'evaluation_meeting_id': cls.meeting_a.id,
        })
        cls.tender_b = cls.env['govoo.tender'].create({
            'name': 'TND-B - Facilities Works',
            'company_id': cls.company.id,
            'evaluation_meeting_id': cls.meeting_b.id,
        })

    def _password(self, login):
        return login + 'x' * (8 - len(login))

    def test_001_committee_member_sees_own_tender(self):
        self.authenticate('test_committee_portal_a', self._password('test_committee_portal_a'))
        response = self.url_open('/my/procurement/tenders/%s' % self.tender_a.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.tender_a.name, response.text)

    def test_002_committee_member_cannot_open_other_committees_tender(self):
        self.authenticate('test_committee_portal_a', self._password('test_committee_portal_a'))
        response = self.url_open('/my/procurement/tenders/%s' % self.tender_b.id)
        self.assertNotIn(self.tender_b.name, response.text)
        self.assertNotIn('/my/procurement/tenders/%s' % self.tender_b.id, response.url)

    def test_003_tenders_list_only_shows_own_committees_tenders(self):
        self.authenticate('test_committee_portal_a', self._password('test_committee_portal_a'))
        response = self.url_open('/my/procurement/tenders')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.tender_a.name, response.text)
        self.assertNotIn(self.tender_b.name, response.text)
