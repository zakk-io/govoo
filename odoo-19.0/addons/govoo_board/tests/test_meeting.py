# Part of Govoo. See LICENSE file for full copyright and licensing details.

from datetime import timedelta

from odoo import fields
from odoo.exceptions import UserError, ValidationError
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

    def test_quorum_not_met_blocks_hold_with_accurate_message(self):
        """Issue #83: action_hold's quorum block is unconditional (no
        override path exists), and its error message must not imply
        one does."""
        meeting = self._make_meeting(quorum=5)
        meeting.action_schedule()
        self.assertFalse(meeting.quorum_met)
        with self.assertRaises(UserError) as cm:
            meeting.action_hold()
        self.assertNotIn('Proceed anyway', str(cm.exception))
        self.assertEqual(meeting.state, 'scheduled')

    def test_state_transition_sequential(self):
        """State advances draft → scheduled → held correctly."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        self.assertEqual(meeting.state, 'scheduled')
        meeting.action_hold()
        self.assertEqual(meeting.state, 'held')

    def test_scheduling_attaches_a_reminder_alarm(self):
        """Issue #236: action_schedule() previously created a
        calendar.event with no alarm at all, so Odoo's own calendar
        reminder engine never fired for board/committee meetings."""
        meeting = self._make_meeting()
        meeting.action_schedule()
        self.assertTrue(meeting.calendar_event_id)
        self.assertIn(
            self.env.ref('govoo_board.alarm_meeting_email_1_day'),
            meeting.calendar_event_id.alarm_ids,
        )

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

    def test_calendar_view_included_and_renders(self):
        """Issue #50: govoo.meeting's action includes a Calendar view
        (driven by date_end), and it renders without error."""
        action = self.env.ref('govoo_board.govoo_meeting_action')
        self.assertIn('calendar', action.view_mode.split(','))

        calendar_view = self.env.ref('govoo_board.govoo_meeting_view_calendar')
        arch = self.env['govoo.meeting'].get_view(
            view_id=calendar_view.id, view_type='calendar',
        )['arch']
        self.assertIn('date_stop="date_end"', arch)

    def test_full_lifecycle_end_to_end(self):
        """TC-ACC-001: board-meeting-to-minutes end-to-end.

        Quorum computed correctly; resolution passes per tally; minutes
        reach signed; retention set.
        """
        meeting = self._make_meeting(quorum=3)
        self.assertTrue(meeting.quorum_met)
        meeting.action_schedule()
        meeting.action_hold()

        resolution = self._make_resolution(meeting)
        resolution.action_open()
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_a.id,
            'choice': 'for',
        })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_b.id,
            'choice': 'for',
        })
        self.env['govoo.vote'].create({
            'resolution_id': resolution.id,
            'voter_id': self.partner_c.id,
            'choice': 'against',
        })
        resolution.action_tally()
        self.assertEqual(resolution.state, 'passed')
        self.assertEqual(resolution.result, 'passed')

        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes content.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        # BR-BOARD-008: signing is blocked unless e-signature legal validity
        # is confirmed (or a signed document is manually uploaded) -- not
        # this end-to-end test's concern, so confirm it to reach 'signed'.
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.e_signature_legally_confirmed', 'True',
        )
        minutes.action_sign()
        self.assertEqual(minutes.state, 'signed')
        self.assertTrue(minutes.retention_until, 'Retention date should be set on minutes.')

        meeting.minutes_id = minutes
        meeting.action_minute()
        meeting.action_close()
        self.assertEqual(meeting.state, 'closed')

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

    # -- Issue #271 item 2: cancel & reschedule --------------------------

    def test_cancel_from_draft(self):
        meeting = self._make_meeting()
        meeting.action_cancel(reason='Venue unavailable')
        self.assertEqual(meeting.state, 'cancelled')
        self.assertEqual(meeting.cancel_reason, 'Venue unavailable')

    def test_cancel_from_scheduled(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_cancel()
        self.assertEqual(meeting.state, 'cancelled')

    def test_cancel_blocked_once_held(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()
        with self.assertRaises(ValidationError):
            meeting.action_cancel()

    def test_cancel_blocked_by_open_resolution(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        with self.assertRaises(ValidationError):
            meeting.action_cancel()
        self.assertEqual(meeting.state, 'draft')

    def test_cancel_allowed_after_resolution_withdrawn(self):
        meeting = self._make_meeting()
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        resolution.action_withdraw()
        meeting.action_cancel()
        self.assertEqual(meeting.state, 'cancelled')

    def test_reschedule_cancels_original_and_links_new_meeting(self):
        meeting = self._make_meeting()
        new_date = fields.Datetime.now() + timedelta(days=30)
        new_meeting = meeting.action_reschedule(new_date)
        self.assertEqual(meeting.state, 'cancelled')
        self.assertEqual(meeting.cancel_reason, 'Rescheduled')
        self.assertEqual(meeting.rescheduled_to_id, new_meeting)
        self.assertEqual(new_meeting.rescheduled_from_id, meeting)
        self.assertEqual(new_meeting.state, 'draft')
        self.assertEqual(new_meeting.date, new_date)
        self.assertEqual(new_meeting.committee_id, meeting.committee_id)
        self.assertEqual(new_meeting.attendee_ids, meeting.attendee_ids)

    def test_reschedule_does_not_copy_agenda_or_resolutions(self):
        meeting = self._make_meeting()
        self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Item',
            'item_type': 'noting',
        })
        resolution = self._make_resolution(meeting)
        resolution.action_open()
        resolution.action_withdraw()
        new_meeting = meeting.action_reschedule(fields.Datetime.now() + timedelta(days=30))
        self.assertFalse(new_meeting.agenda_ids)
        self.assertFalse(new_meeting.resolution_ids)

    # -- Issue #271 item 3: meeting notice period -------------------------

    def test_meeting_notice_period_unset_preserves_default_behavior(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        self.assertEqual(meeting.state, 'scheduled')

    def test_meeting_notice_period_blocks_schedule_when_too_soon(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.meeting_notice_period_days', '14',
        )
        meeting = self._make_meeting()
        meeting.date = fields.Datetime.now() + timedelta(days=5)
        with self.assertRaises(ValidationError):
            meeting.action_schedule()

    def test_meeting_notice_period_allows_schedule_when_far_enough_out(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.meeting_notice_period_days', '14',
        )
        meeting = self._make_meeting()
        meeting.date = fields.Datetime.now() + timedelta(days=30)
        meeting.action_schedule()
        self.assertEqual(meeting.state, 'scheduled')

    # -- Issue #271 item 4: confirmed vs invited attendees ----------------

    def test_quorum_falls_back_to_invited_when_confirmed_empty(self):
        meeting = self._make_meeting(quorum=3)
        self.assertTrue(meeting.quorum_met)

    def test_quorum_uses_confirmed_attendees_when_populated(self):
        meeting = self._make_meeting(quorum=3)
        meeting.confirmed_attendee_ids = [(6, 0, [self.partner_a.id, self.partner_b.id])]
        self.assertFalse(meeting.quorum_met)

    def test_quorum_confirmed_attendees_can_still_meet_quorum(self):
        meeting = self._make_meeting(quorum=2)
        meeting.confirmed_attendee_ids = [(6, 0, [self.partner_a.id, self.partner_b.id])]
        self.assertTrue(meeting.quorum_met)

    # -- Issue #271 item 8: close requires approved minutes ---------------

    def test_close_allowed_with_for_approval_minutes_by_default(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        meeting.minutes_id = minutes
        meeting.action_minute()
        meeting.action_close()
        self.assertEqual(meeting.state, 'closed')

    def test_close_blocked_without_approved_minutes_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.meeting_close_requires_minutes_approved', 'True',
        )
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        meeting.minutes_id = minutes
        meeting.action_minute()
        with self.assertRaises(ValidationError):
            meeting.action_close()

    def test_close_allowed_with_approved_minutes_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.meeting_close_requires_minutes_approved', 'True',
        )
        meeting = self._make_meeting()
        meeting.action_schedule()
        meeting.action_hold()
        minutes = self.env['govoo.minutes'].create({
            'meeting_id': meeting.id,
            'body': '<p>Minutes.</p>',
        })
        minutes.action_submit_for_approval()
        minutes.action_approve()
        meeting.minutes_id = minutes
        meeting.action_minute()
        meeting.action_close()
        self.assertEqual(meeting.state, 'closed')

    # -- Issue #271 item 7: agenda freeze ---------------------------------

    def test_agenda_item_addable_after_scheduled_by_default(self):
        meeting = self._make_meeting()
        meeting.action_schedule()
        item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Late item',
            'item_type': 'noting',
        })
        self.assertTrue(item.exists())

    def test_agenda_freeze_blocks_new_item_once_scheduled_when_enabled(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.agenda_freeze_on_schedule', 'True',
        )
        meeting = self._make_meeting()
        meeting.action_schedule()
        with self.assertRaises(ValidationError):
            self.env['govoo.agenda.item'].create({
                'meeting_id': meeting.id,
                'title': 'Late item',
                'item_type': 'noting',
            })

    def test_agenda_freeze_still_allows_items_while_draft(self):
        self.env['ir.config_parameter'].sudo().set_param(
            'govoo_board.agenda_freeze_on_schedule', 'True',
        )
        meeting = self._make_meeting()
        item = self.env['govoo.agenda.item'].create({
            'meeting_id': meeting.id,
            'title': 'Item',
            'item_type': 'noting',
        })
        self.assertTrue(item.exists())

    # -- #269/#271 compatibility: cancelled meetings also gate voting ----

    def test_resolution_open_blocked_on_cancelled_meeting(self):
        meeting = self._make_meeting()
        meeting.action_cancel()
        resolution = self._make_resolution(meeting)
        with self.assertRaises(ValidationError):
            resolution.action_open()
