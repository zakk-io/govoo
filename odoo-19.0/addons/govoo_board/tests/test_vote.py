# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import AccessError, ValidationError
from odoo.tests import tagged
from odoo.tests.common import new_test_user

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooVoteTC(GovooBoardTestBase):
    """TC-BOARD-006, 006b, 006c — Vote weight, admin exclusion, conflicted votes."""

    def test_vote_weight_defaults_to_one_for_directors(self):
        """TC-BOARD-006: Director vote weight defaults to 1.0."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.assertEqual(vote.weight, 1.0)
        self.assertTrue(vote.timestamp)

    def test_vote_immutable_after_cast(self):
        """Vote cannot be modified once timestamped."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        with self.assertRaises(ValidationError):
            vote.choice = 'against'

    def test_duplicate_vote_rejected(self):
        """SQL constraint: one vote per (resolution, voter)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        with self.assertRaises(Exception):
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': self.partner_a.id,
                'choice': 'against',
            })

    def test_conflicted_vote_excluded_from_tally(self):
        """TC-BOARD-006c: Conflicted vote excluded from tally."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        # 2 for (1 conflicted), 1 against
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_b.id,
            'choice': 'for',
            'is_conflicted': True,
        })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_c.id,
            'choice': 'against',
        })

        resolution.action_tally()
        # Only partner_a's for vote counts (weight=1), partner_c against (weight=1)
        # partner_b excluded → 1 for vs 1 against → fails (not majority)
        self.assertEqual(resolution.state, 'failed')

    def test_vote_with_no_eligible_votes_rejected(self):
        """Tally with all votes conflicted → rejected."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
            'is_conflicted': True,
        })

        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_shareholder_vote_weight_from_holding(self):
        """TC-BOARD-006: Shareholder resolution vote weight sourced from holding."""
        # Create a share class and holdings
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 2.0,
            'total_authorised': 100,
            'company_id': self.company.id,
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 30,
            'date_allotted': '2026-01-01',
        })

        meeting = self._make_meeting()
        meeting.meeting_type = 'agm'
        resolution = self._make_resolution(meeting, resolution_type='ordinary')
        resolution.action_open()

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        # weight should be sourced from holding: 30 shares * 2.0 votes = 60.0
        self.assertEqual(vote.weight, 60.0)

    def test_board_admin_cannot_create_vote(self):
        """TC-SEC-004: Board Administrator is denied at the access-rights
        layer, regardless of configuration privileges (BR-SEC-004) --
        even with no director/shareholder appointment at all."""
        admin = new_test_user(
            self.env, login='test_board_admin_vote',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        with self.assertRaises(AccessError):
            self.env['govoo.vote'].with_user(admin).create({
                'resolution_id': resolution.id,
                'voter_id': admin.partner_id.id,
                'choice': 'for',
            })
