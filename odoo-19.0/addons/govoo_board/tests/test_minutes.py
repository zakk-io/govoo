# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install')
class TestMinutesWorkflow(GovooBoardTestBase):
    """TC-WF-BOARD-003: draft -> for_approval -> approved, retention_until
    computed. govoo_board's own suite has no govoo_rw installed, so this
    exercises the documented fallback default (10 years); the real
    govoo_rw-config path is covered in govoo_rw's own test suite (#32)."""

    def test_minutes_lifecycle_and_retention(self):
        meeting = self._make_meeting()
        meeting.write({'state': 'held'})
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        self.assertEqual(minutes.state, 'draft')

        minutes.action_submit_for_approval()
        self.assertEqual(minutes.state, 'for_approval')

        minutes.action_approve()
        self.assertEqual(minutes.state, 'approved')

        expected_retention = minutes.create_date.date().replace(
            year=minutes.create_date.year + 10,
        )
        self.assertEqual(minutes.retention_until, expected_retention)
