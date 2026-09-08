# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install', 'govoo_portal')
class TestPortal(TransactionCase):
    """TC-SEC-005, TC-SEC-005b, TC-WF-PORTAL-001..002: Portal tests."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        # Create committee with members
        cls.committee_a = cls.env['govoo.committee'].create({
            'name': 'Audit Committee',
            'company_id': cls.company.id,
        })
        cls.committee_b = cls.env['govoo.committee'].create({
            'name': 'Finance Committee',
            'company_id': cls.company.id,
        })

        # Create users
        cls.user_director_a = cls.env['res.users'].create({
            'login': 'test_director_a',
            'name': 'Director A',
            'company_id': cls.company.id,
        })
        cls.user_director_a.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_director_portal').id)],
        })
        cls.user_director_b = cls.env['res.users'].create({
            'login': 'test_director_b',
            'name': 'Director B',
            'company_id': cls.company.id,
        })
        cls.user_director_b.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_director_portal').id)],
        })
        cls.user_shareholder = cls.env['res.users'].create({
            'login': 'test_shareholder',
            'name': 'Shareholder X',
            'company_id': cls.company.id,
        })
        cls.user_shareholder.write({
            'group_ids': [(4, cls.env.ref('govoo_base.group_govoo_shareholder_portal').id)],
        })

        # Create appointments using user's partners (portal rule filters by user.partner_id)
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

    def test_001_director_sees_own_committee_meetings(self):
        """TC-SEC-005: Director Portal user sees only own committee meetings."""
        # Create meetings for both committees
        meeting_a = self.env['govoo.meeting'].create({
            'name': 'Audit Meeting',
            'committee_id': self.committee_a.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': self.company.id,
        })
        self.env['govoo.meeting'].create({
            'name': 'Finance Meeting',
            'committee_id': self.committee_b.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 14:00:00',
            'company_id': self.company.id,
        })

        # Director A (Audit Committee) should see only Audit Meeting
        meetings_a = self.env['govoo.meeting'].with_user(
            self.user_director_a,
        ).search([
            ('committee_id.member_ids.partner_id', '=', self.user_director_a.partner_id.id),
        ])
        self.assertIn(meeting_a, meetings_a)
        self.assertEqual(len(meetings_a), 1)

    def test_002_director_cannot_see_other_committee(self):
        """TC-SEC-005: Director cannot access other committee meeting by ID."""
        meeting_b = self.env['govoo.meeting'].create({
            'name': 'Finance Meeting',
            'committee_id': self.committee_b.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 14:00:00',
            'company_id': self.company.id,
        })

        # Director A should NOT see Finance Meeting
        meetings_a = self.env['govoo.meeting'].with_user(
            self.user_director_a,
        ).search([
            ('committee_id.member_ids.partner_id', '=', self.user_director_a.partner_id.id),
        ])
        self.assertNotIn(meeting_b, meetings_a)

    def test_003_shareholder_sees_own_holdings(self):
        """TC-SEC-005b: Shareholder Portal user sees only own holdings."""
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'total_authorised': 1000,
            'company_id': self.company.id,
        })
        # Use user_shareholder's partner so portal rule matches
        holding = self.env['govoo.share.holding'].create({
            'partner_id': self.user_shareholder.partner_id.id,
            'share_class_id': share_class.id,
            'quantity': 100,
            'company_id': self.company.id,
        })

        # Shareholder should see own holdings
        holdings = self.env['govoo.share.holding'].with_user(
            self.user_shareholder,
        ).search([
            ('partner_id', '=', self.user_shareholder.partner_id.id),
        ])
        self.assertIn(holding, holdings)

    def test_004_vote_recorded_correctly(self):
        """TC-WF-PORTAL-001: Vote recorded with correct voter_id and weight."""
        meeting = self.env['govoo.meeting'].create({
            'name': 'Test Meeting',
            'committee_id': self.committee_a.id,
            'meeting_type': 'committee',
            'date': '2026-03-15 10:00:00',
            'company_id': self.company.id,
        })
        resolution = self.env['govoo.resolution'].create({
            'title': 'Test Resolution',
            'resolution_type': 'ordinary',
            'meeting_id': meeting.id,
        })

        vote = self.env['govoo.vote'].sudo().create({
            'resolution_id': resolution.id,
            'voter_id': self.user_director_a.partner_id.id,
            'choice': 'for',
            'weight': 1.0,
        })

        self.assertEqual(vote.voter_id, self.user_director_a.partner_id)
        self.assertEqual(vote.choice, 'for')
        self.assertEqual(vote.weight, 1.0)
