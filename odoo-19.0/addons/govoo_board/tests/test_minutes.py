# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestGovooMinutesDelete(GovooBoardTestBase):
    """access-control.md: Secretary D restricted post-approval (draft/
    for_approval deletable, approved/signed blocked)."""

    def test_delete_allowed_in_draft(self):
        meeting = self._make_meeting()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.unlink()
        self.assertFalse(minutes.exists())

    def test_delete_allowed_in_for_approval(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        self.assertEqual(minutes.state, 'for_approval')
        minutes.unlink()
        self.assertFalse(minutes.exists())

    def test_delete_blocked_once_approved(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        self.assertEqual(minutes.state, 'approved')
        with self.assertRaises(ValidationError):
            minutes.unlink()
