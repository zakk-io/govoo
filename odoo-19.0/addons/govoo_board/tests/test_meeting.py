# Part of Govoo. See LICENSE file for full copyright and licensing details.

from odoo.exceptions import ValidationError
from odoo.tests import tagged

from .common import GovooBoardTestBase


@tagged('post_install', '-at_install', 'govoo_board')
class GovooMeetingTC(GovooBoardTestBase):
    """TC-BOARD-001, 001b — Meeting quorum and state machine."""

    def test_quorum_met_with_sufficient_attendees(self):
        """TC-BOARD-001: Meeting with quorum_required=3, 4 attendees → quorum_met=True."""
        meeting = self._make_meeting(quorum=3)
        self.assertTrue(meeting.quorum_met)

    def test_quorum_not_met(self):
        """Meeting with quorum_required=5, 4 attendees → quorum_met=False."""
        meeting = self._make_meeting(quorum=5)
        self.assertFalse(meeting.quorum_met)

    def test_quorum_required_must_be_positive(self):
        """quorum_required must be > 0."""
        with self.assertRaises(ValidationError):
            self.env['govoo.meeting'].create({
                'name': 'Invalid Meeting',
                'meeting_type': 'board',
                'committee_id': self.committee.id,
                'date': '2026-04-01 10:00:00',
                'quorum_required': 0,
                'company_id': self.company.id,
            })

    def test_state_transition_out_of_order_rejected(self):
        """TC-BOARD-001b: draft → held is rejected (must go through scheduled)."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.state, 'draft')
        with self.assertRaises(ValidationError):
            meeting.action_hold()

    def test_state_transition_sequential(self):
        """State advances draft → scheduled → held correctly."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        self.assertEqual(meeting.state, 'scheduled')
        meeting.action_hold()
        self.assertEqual(meeting.state, 'held')

    def test_close_blocked_by_open_resolution(self):
        """Cannot close meeting with non-terminal resolutions."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()

        # Create minutes
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        meeting.minutes_id = minutes
        meeting.action_minute()
        self.assertEqual(meeting.state, 'minuted')

        # Create a resolution that is still open
        resolution = self._make_resolution(meeting)
        resolution.action_open()

        with self.assertRaises(ValidationError):
            meeting.action_close()

    def test_agenda_items_resolve_in_sequence_order(self):
        """TC-BOARD-002: agenda items resolve in sequence order,
        regardless of creation order."""
        meeting = self._make_meeting()
        third = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Third',
            'item_type': 'noting',
            'sequence': 30,
        })
        first = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'First',
            'item_type': 'noting',
            'sequence': 10,
        })
        second = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Second',
            'item_type': 'noting',
            'sequence': 20,
        })
        self.assertEqual(list(meeting.agenda_ids.sorted('sequence')), [first, second, third])

    def test_full_lifecycle_with_terminal_resolution_reaches_closed(self):
        """TC-WF-BOARD-001: draft -> scheduled -> held -> minuted -> closed,
        with agenda items and a linked resolution throughout; meeting only
        reaches closed once the resolution is terminal."""
        meeting = self._make_meeting()
        self.assertEqual(meeting.state, 'draft')

        self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Approve Q1 Budget',
            'item_type': 'decision',
            'sequence': 1,
        })

        resolution = self._make_resolution(meeting)
        resolution.action_open()
        for partner in [self.partner_a, self.partner_b]:
            self.env['govoo.vote'].create({
                'resolution_id': resolution.id,
                'voter_id': partner.id,
                'choice': 'for',
            })

        meeting.action_schedule()
        self.assertEqual(meeting.state, 'scheduled')
        meeting.action_hold()
        self.assertEqual(meeting.state, 'held')

        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        meeting.minutes_id = minutes
        meeting.action_minute()
        self.assertEqual(meeting.state, 'minuted')

        # Resolution must reach a terminal state before close succeeds
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')

        meeting.action_close()
        self.assertEqual(meeting.state, 'closed')
