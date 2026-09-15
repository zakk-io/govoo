# Part of Govoo. See LICENSE file for full copyright and licensing details.

import re

from odoo.tests import HttpCase, tagged
from odoo.tests.common import new_test_user


@tagged('post_install', '-at_install', 'govoo_portal')
class TestPortal(HttpCase):
    """TC-SEC-005, TC-SEC-005b, TC-WF-PORTAL-001..002: Portal tests.

    Exercises the real HTTP/controller layer (not just ORM domain
    filtering) since that's the layer where record-rule/token-bypass
    bugs (BR-SEC-006) actually show up.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'Audit Committee',
            'company_id': cls.company.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Finance Committee',
            'company_id': cls.company.id,
        })

        cls.user_director_a = new_test_user(
            cls.env, login='test_director_a',
            groups='govoo_base.group_govoo_director_portal',
            company_id=cls.company.id,
        )
        cls.user_director_b = new_test_user(
            cls.env, login='test_director_b',
            groups='govoo_base.group_govoo_director_portal',
            company_id=cls.company.id,
        )
        cls.user_shareholder = new_test_user(
            cls.env, login='test_shareholder',
            groups='govoo_base.group_govoo_shareholder_portal',
            company_id=cls.company.id,
        )

        # Appointments using the users' own partners (portal rule filters by user.partner_id)
        cls.env['govoo.appointment'].create({
            'partner_id': cls.user_director_a.partner_id.id,
            'committee_id': cls.committee_a.id,
            'role': 'committee_member',
            'company_id': cls.company.id,
            'date_appointed': '2026-01-01',
        })
        cls.env['govoo.appointment'].create({
            'partner_id': cls.user_director_b.partner_id.id,
            'committee_id': cls.committee_b.id,
            'role': 'committee_member',
            'company_id': cls.company.id,
            'date_appointed': '2026-01-01',
        })

        cls.meeting_a = cls.env['govoo.meeting'].create({
            'name': 'Audit Meeting',
            'committee_id': cls.committee_a.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': cls.company.id,
        })
        cls.meeting_b = cls.env['govoo.meeting'].create({
            'name': 'Finance Meeting',
            'committee_id': cls.committee_b.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 14:00:00',
            'company_id': cls.company.id,
        })

        cls.share_class = cls.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'total_authorised': 1000,
            'company_id': cls.company.id,
        })
        # govoo.share.holding.quantity/company_id are computed/related --
        # not directly settable. Allot shares so a real holding exists
        # (a direct holding .create() with quantity= is silently ignored,
        # computing back to 0 from the absence of any allotment).
        cls.env['govoo.share.allotment'].create({
            'share_class_id': cls.share_class.id,
            'partner_id': cls.user_shareholder.partner_id.id,
            'quantity': 100,
            'date_allotted': '2026-01-01',
        })
        cls.holding = cls.env['govoo.share.holding'].search([
            ('partner_id', '=', cls.user_shareholder.partner_id.id),
            ('share_class_id', '=', cls.share_class.id),
        ], limit=1)

    def _password(self, login):
        # matches odoo.tests.common.new_test_user's auto-generated password
        return login + 'x' * (8 - len(login))

    def test_001_director_sees_own_committee_meeting(self):
        """TC-SEC-005: Director Portal user can open own committee's meeting."""
        self.authenticate('test_director_a', self._password('test_director_a'))
        response = self.url_open('/my/meetings/%s' % self.meeting_a.id)
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.meeting_a.name, response.text)

    def test_002_director_cannot_open_other_committee_meeting(self):
        """TC-SEC-005: Director cannot open another committee's meeting by ID."""
        self.authenticate('test_director_a', self._password('test_director_a'))
        response = self.url_open('/my/meetings/%s' % self.meeting_b.id)
        # controller catches AccessError/MissingError and redirects to /my;
        # url_open follows redirects, so we assert on the final content/URL.
        self.assertNotIn(self.meeting_b.name, response.text)
        self.assertNotIn('/my/meetings/%s' % self.meeting_b.id, response.url)

    def test_003_access_token_does_not_bypass_committee_scoping(self):
        """BR-SEC-006: a valid access_token must not grant access outside record rules."""
        token = self.meeting_b._portal_ensure_token()
        self.authenticate('test_director_a', self._password('test_director_a'))
        response = self.url_open(
            '/my/meetings/%s?access_token=%s' % (self.meeting_b.id, token),
        )
        self.assertNotIn(self.meeting_b.name, response.text)
        self.assertNotIn('/my/meetings/%s' % self.meeting_b.id, response.url)

    def test_004_shareholder_sees_own_holdings(self):
        """TC-SEC-005b: Shareholder Portal user sees own holdings via /my/holdings."""
        self.authenticate('test_shareholder', self._password('test_shareholder'))
        response = self.url_open('/my/holdings')
        self.assertEqual(response.status_code, 200)
        self.assertIn(self.share_class.name, response.text)

    def test_005_vote_recorded_correctly(self):
        """TC-WF-PORTAL-001: casting a vote via POST records correct voter/weight."""
        resolution = self.env['govoo.resolution'].create({
            'title': 'Test Resolution',
            'resolution_type': 'ordinary',
            'meeting_id': self.meeting_a.id,
        })
        resolution.action_open()

        self.authenticate('test_director_a', self._password('test_director_a'))
        cast_page = self.url_open('/my/votes/%s/cast' % resolution.id)
        csrf_token = re.search(
            r'name="csrf_token" value="([^"]+)"', cast_page.text,
        ).group(1)
        self.url_open(
            '/my/votes/%s/cast' % resolution.id,
            data={'vote_choice': 'for', 'csrf_token': csrf_token},
        )

        vote = self.env['govoo.vote'].sudo().search([
            ('resolution_id', '=', resolution.id),
            ('voter_id', '=', self.user_director_a.partner_id.id),
        ])
        self.assertEqual(len(vote), 1)
        self.assertEqual(vote.choice, 'for')
        self.assertEqual(vote.weight, 1.0)

    def test_006_shareholder_vote_weight_from_voting_power(self):
        """TC-WF-PORTAL-002: Shareholder Portal user views holdings, casts
        a vote on an eligible shareholder resolution; weight is sourced
        from their voting_power."""
        # A resolution's company_id is related to meeting_id.company_id
        # (null/false for a truly standalone written resolution) -- the
        # shareholder eligibility rule needs a real company_id to match,
        # so this uses an AGM-type meeting the shareholder isn't a portal
        # member of (shareholder eligibility is holdings-based, not
        # committee-membership-based).
        agm_meeting = self.env['govoo.meeting'].create({
            'name': 'Annual General Meeting',
            'committee_id': self.committee_a.id,
            'meeting_type': 'agm',
            'date': '2026-04-01 10:00:00',
            'company_id': self.company.id,
        })
        resolution = self.env['govoo.resolution'].create({
            'title': 'Shareholder Resolution',
            'resolution_type': 'ordinary',
            'meeting_id': agm_meeting.id,
        })
        resolution.action_open()

        self.authenticate('test_shareholder', self._password('test_shareholder'))
        cast_page = self.url_open('/my/holdings/votes/%s/cast' % resolution.id)
        match = re.search(r'name="csrf_token" value="([^"]+)"', cast_page.text)
        self.assertIsNotNone(
            match,
            'Cast-vote page did not render as expected. status=%s url=%s body[:500]=%r'
            % (cast_page.status_code, cast_page.url, cast_page.text[:500]),
        )
        csrf_token = match.group(1)
        self.url_open(
            '/my/holdings/votes/%s/cast' % resolution.id,
            data={'vote_choice': 'for', 'csrf_token': csrf_token},
        )

        vote = self.env['govoo.vote'].sudo().search([
            ('resolution_id', '=', resolution.id),
            ('voter_id', '=', self.user_shareholder.partner_id.id),
        ])
        self.assertEqual(len(vote), 1)
        self.assertEqual(vote.choice, 'for')
        self.assertEqual(vote.weight, self.holding.voting_power)

    def test_007_confidential_agenda_item_hidden_in_portal_view(self):
        """TC-WF-BOARD-002 (partial -- see issue #58 comment): the portal
        agenda view hides confidential item titles from a recipient.

        The literal "authorized vs unauthorized recipient" distinction
        from workflow-tests.md isn't implementable yet -- action_compile()
        has no per-recipient authorization concept at all (tracked
        separately as #51). What's tested here is what's actually
        implemented today: confidential items are never shown by title to
        any portal viewer, non-confidential ones are.
        """
        confidential_item = self.env['govoo.agenda.item'].create({
            'meeting_id': self.meeting_a.id,
            'title': 'Confidential Merger Discussion',
            'item_type': 'discussion',
            'sequence': 1,
            'is_confidential': True,
        })
        open_item = self.env['govoo.agenda.item'].create({
            'meeting_id': self.meeting_a.id,
            'title': 'Approve Meeting Minutes',
            'item_type': 'decision',
            'sequence': 2,
            'is_confidential': False,
        })

        self.authenticate('test_director_a', self._password('test_director_a'))
        response = self.url_open('/my/meetings/%s' % self.meeting_a.id)

        self.assertNotIn(confidential_item.title, response.text)
        self.assertIn(open_item.title, response.text)
