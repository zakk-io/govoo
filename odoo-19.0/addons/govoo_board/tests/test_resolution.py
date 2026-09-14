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

    def test_sign_request_blocked_without_legal_confirmation(self):
        """BR-BOARD-008: sign_request_id cannot be set while e-signature
        legal validity under Rwandan law is unconfirmed (the default)."""
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        attachment = self.env['ir.attachment'].create({
            'name': 'sign_request.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        with self.assertRaises(ValidationError):
            resolution.sign_request_id = attachment

    def test_sign_request_allowed_when_legally_confirmed(self):
        """Once confirmed, sign_request_id can be set."""
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        attachment = self.env['ir.attachment'].create({
            'name': 'sign_request.pdf',
            'datas': b'ZmFrZSBwZGY=',
        })
        resolution.sign_request_id = attachment
        self.assertEqual(resolution.sign_request_id, attachment)
