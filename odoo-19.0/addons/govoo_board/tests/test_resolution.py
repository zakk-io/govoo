# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooResolutionTC(GovooBoardTestBase):
    """TC-BOARD-004, 005 — Resolution state machine and tally."""

    def test_resolution_state_machine(self):
        """draft → open → passed/failed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        self.assertEqual(resolution.state, 'draft')
        resolution.action_open()
        self.assertEqual(resolution.state, 'open')

    def test_resolution_invalid_transition_rejected(self):
        """Cannot skip from draft to passed via tally."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_resolution_withdraw_from_draft(self):
        """Resolution can be withdrawn from draft."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_withdraw()
        self.assertEqual(resolution.state, 'withdrawn')

    def test_tally_passes_with_majority(self):
        """TC-BOARD-005: Resolution open, quorum met, majority achieved → passed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        # Cast votes: 3 for, 1 against
        for partner in [self.partner_a, self.partner_b, self.partner_c]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_d.id,
            'choice': 'against',
        })

        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')
        self.assertEqual(resolution.result, 'passed')

    def test_tally_fails_without_majority(self):
        """Resolution with more against votes → failed."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        # Cast votes: 1 for, 3 against
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        for partner in [self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'against',
            })

        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        self.assertEqual(resolution.result, 'failed')

    def test_tally_on_non_open_rejected(self):
        """Can only tally an open resolution."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        # Still in draft
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_tally_fails_when_quorum_not_met_despite_unanimous_votes(self):
        """BR-BOARD-005: quorum is a precondition for 'passed', independent
        of the vote tally -- unanimous votes on a meeting that never met
        quorum must still fail."""
        meeting = self._make_meeting(quorum=10)  # only 4 attendees -> never met
        self.assertFalse(meeting.quorum_met)
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'failed')
        self.assertEqual(resolution.result, 'failed')

    def test_special_resolution_tally_raises_without_configured_threshold(self):
        """A 'special' resolution cannot be tallied at all until the
        majority threshold is explicitly configured (no silent plain
        majority fallback)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting, resolution_type='special')
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b, self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        with self.assertRaises(ValidationError):
            resolution.action_tally()

    def test_special_resolution_tally_uses_configured_threshold(self):
        """Once configured, a 'special' resolution passes/fails at the
        configured supermajority fraction rather than plain majority."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.special_resolution_majority_threshold', '0.75',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting, resolution_type='special')
        resolution.action_open()
        # 3 for, 1 against = 75% -- exactly clears a 0.75 threshold
        for partner in [self.partner_a, self.partner_b, self.partner_c]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_d.id,
            'choice': 'against',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')

        # 2 for, 2 against = 50% -- does not clear 0.75
        meeting2 = self._make_meeting()
        resolution2 = self._make_resolution(meeting2, resolution_type='special')
        resolution2.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution2.id,
                'voter_id': partner.id,
                'choice': 'for',
            })
        for partner in [self.partner_c, self.partner_d]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution2.id,
                'voter_id': partner.id,
                'choice': 'against',
            })
        resolution2.action_tally()
        self.assertEqual(resolution2.state, 'failed')
