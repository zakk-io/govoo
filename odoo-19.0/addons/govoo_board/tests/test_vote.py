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

    def test_admin_cannot_cast_vote(self):
        """TC-ACC-006: separation of duties — Board Administrator cannot
        cast a vote under any configuration (BR-SEC-004)."""
        admin = new_test_user(
            self.env, login='test_vote_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        with self.assertRaises(AccessError):
            self.env['govoo.vote'].with_user(admin).create({
                'resolution_id': resolution.id,
                'voter_id': self.partner_a.id,
                'choice': 'for',
            })

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

    def test_admin_cannot_create_vote(self):
        """TC-BOARD-006b: Board Administrator create-vote is rejected
        (separation of duties, BR-SEC-004)."""
        admin = new_test_user(
            self.env, login='test_board_admin',
            groups='govoo_base.group_govoo_admin',
            company_id=self.company.id,
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        with self.assertRaises(AccessError):
            self.env['govoo.vote'].with_user(admin).create({
                'resolution_id': resolution.id,
                'voter_id': self.partner_a.id,
                'choice': 'for',
            })

    def test_shareholder_resolution_conflicted_vote_excluded_from_weighted_tally(self):
        """TC-WF-BOARD-005: shareholder resolution, votes weighted by
        voting_power, one conflicted vote excluded, result reflects the
        remaining weighted votes."""
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 1000,
            'company_id': self.company.id,
        })
        # A: 100 shares (for, conflicted -- excluded)
        # B: 50 shares (for)
        # C: 200 shares (against)
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 100,
            'date_allotted': '2026-01-01',
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_b.id,
            'quantity': 50,
            'date_allotted': '2026-01-01',
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_c.id,
            'quantity': 200,
            'date_allotted': '2026-01-01',
        })

        meeting = self._make_meeting()
        meeting.meeting_type = 'agm'
        resolution = self._make_resolution(meeting, resolution_type='ordinary')
        resolution.action_open()

        vote_a = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
            'is_conflicted': True,
        })
        self.assertEqual(vote_a.weight, 100.0)
        vote_b = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_b.id,
            'choice': 'for',
        })
        self.assertEqual(vote_b.weight, 50.0)
        vote_c = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_c.id,
            'choice': 'against',
        })
        self.assertEqual(vote_c.weight, 200.0)

        resolution.action_tally()
        # A's 100-weight for-vote is excluded (conflicted); remaining tally
        # is 50 for vs 200 against -> fails.
        self.assertEqual(resolution.state, 'failed')
        self.assertEqual(resolution.result, 'failed')

    def test_written_shareholder_resolution_vote_weight_from_holding(self):
        """Issue #85: a written resolution (no meeting_id at all) with
        a shareholder-eligible resolution_type still sources vote
        weight from the voter's holding, not the 1.0 default."""
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 100,
            'company_id': self.company.id,
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 40,
            'date_allotted': '2026-01-01',
        })

        resolution = self.env['govoo.resolution'].create({
            'title': 'Written Shareholder Resolution',
            'resolution_type': 'ordinary',
        })
        self.assertFalse(resolution.meeting_id)
        resolution.action_open()

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.assertEqual(vote.weight, 40.0)

    def test_board_resolution_shareholder_director_gets_plain_weight(self):
        """Issue #85: a director who also happens to be a shareholder
        must still get a plain 1.0 vote on a regular board-meeting
        resolution -- resolution_type alone is not a sufficient signal
        since 'ordinary' is also used for non-shareholder resolutions."""
        share_class = self.env['govoo.share.class'].create({
            'name': 'Ordinary Shares',
            'nominal_value': 1000,
            'votes_per_share': 1.0,
            'total_authorised': 100,
            'company_id': self.company.id,
        })
        self.env['govoo.share.allotment'].create({
            'share_class_id': share_class.id,
            'partner_id': self.partner_a.id,
            'quantity': 40,
            'date_allotted': '2026-01-01',
        })

        meeting = self._make_meeting()  # meeting_type='board'
        resolution = self._make_resolution(meeting)  # resolution_type='ordinary'
        resolution.action_open()

        vote = self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.assertEqual(vote.weight, 1.0)
