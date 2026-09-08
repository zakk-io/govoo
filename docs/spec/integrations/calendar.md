# Integration: Calendar

Source: §3.3, §7.4.1 of the source spec.

- **Purpose:** Meeting scheduling, invites, and reminders, reusing Odoo's Calendar app.
- **Integration owner:** `govoo_board` (`govoo.meeting.calendar_event_id`).
- **Direction:** Govoo → Calendar (create/update `calendar.event` when a meeting is scheduled),
  Calendar → Govoo (attendee RSVP status may inform, but does not directly set, `quorum_met` —
  actual attendance is recorded separately per `workflows/meetings.md`).
- **Data exchanged:** meeting date/time, location/virtual link, attendee list, reminders.
- **Trigger:** meeting `draft → scheduled` transition creates/links the `calendar.event`; date/
  attendee changes on the meeting sync to the event (or vice versa — `[ENGINEERING DETAIL]` decide
  a single source of truth for date/time to avoid sync conflicts; recommend `govoo.meeting` as the
  authoritative source with the `calendar.event` as a derived scheduling artifact).
- **Failure behavior:** Calendar is Community-available; no fallback needed.
- **Feature flag:** none needed (`calendar` is a hard dependency of `govoo_board`).
- **Community fallback:** N/A.
- **Enterprise dependency:** none.
- **Security:** calendar event visibility should not leak meeting details to attendees outside the
  committee's authorized set — invite only the resolved `attendee_ids`, never all users.
- **Testing:** covered implicitly by TC-BOARD-001 (meeting lifecycle); no dedicated calendar test
  beyond confirming the event is created/linked correctly.
