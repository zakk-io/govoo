# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooResolutionCronTC(GovooBoardTestBase):
    """Issue #269 item 3: voting deadline + auto-close cron."""

    def test_vote_deadline_set_when_window_configured(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.resolution_voting_window_days', '3',
        )
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertTrue(resolution.vote_deadline)

    def test_vote_deadline_blank_when_window_unset(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.assertFalse(resolution.vote_deadline)

    def test_cron_closes_expired_resolution(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        resolution.vote_deadline = fields.Datetime.now() - timedelta(hours=1)
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.env['govoo.board.cron']._cron_close_expired_resolutions()
        self.assertEqual(resolution.state, 'passed')

    def test_cron_leaves_resolution_without_deadline_untouched(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.env['govoo.board.cron']._cron_close_expired_resolutions()
        self.assertEqual(resolution.state, 'open')

    def test_cron_leaves_future_deadline_untouched(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        resolution.vote_deadline = fields.Datetime.now() + timedelta(days=1)
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.env['govoo.board.cron']._cron_close_expired_resolutions()
        self.assertEqual(resolution.state, 'open')
