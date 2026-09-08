# Workflow: Meetings

Source: §7.4.1, §7.4.2, board-lifecycle summary in the master prompt. Requirements: FR-BOARD-001,
FR-BOARD-002. Models: `govoo.meeting`, `govoo.agenda.item`.

## Actor
Company Secretary (drives the workflow); attendees (confirm attendance); Director Portal users
(view, for their committee).

## Trigger
A board, committee, AGM, or EGM meeting needs to be held.

## Steps (meeting creation → closure)
1. **Creation:** Secretary creates a `govoo.meeting` (`draft`): `committee_id`, `meeting_type`,
   `date`, `location`/virtual link, `quorum_required` (typically defaulted from the committee's
   standing quorum rule if one exists — `[ENGINEERING DETAIL]`, not specified as a stored default in
   source).
2. **Scheduling:** Secretary links/creates a `calendar_event_id`, sets `attendee_ids`, and
   transitions `draft → scheduled`. Calendar invites go out via standard Odoo Calendar behavior.
3. **Agenda preparation:** Secretary adds `govoo.agenda.item` rows (FR-BOARD-002) in `sequence`
   order, attaching documents and linking `govoo.resolution` rows for decision items.
4. **Board pack generation:** Secretary compiles/distributes the `govoo.board.pack` (see
   `workflows/board-packs.md`) ahead of the meeting.
5. **Attendance / quorum validation:** at or after the meeting date, Secretary records actual
   attendance. System computes `quorum_met` from confirmed attendee count vs `quorum_required`.
6. **Meeting held:** Secretary transitions `scheduled → held`. Whether this transition is blocked
   when `quorum_met = False` is `[CONFIRM]` (see `data-model/state-machines.md`).
7. **Minutes:** Secretary starts drafting minutes (`workflows/minutes.md`); once minutes reach at
   least `for_approval`, meeting transitions `held → minuted`.
8. **Closure:** once all agenda-linked resolutions reach a terminal state
   (`passed`/`failed`/`withdrawn`), Secretary transitions `minuted → closed`.

## Validation
- `quorum_required > 0`.
- State transitions strictly forward, one step at a time (BR-BOARD-002).

## Database changes
- `govoo.meeting`, `govoo.agenda.item` create/update; downstream `govoo.board.pack`,
  `govoo.minutes`, `govoo.resolution` records link back via `meeting_id`.

## Notifications
- `calendar.event` standard invite/reminder behavior; `mail.activity` reminders ahead of the
  meeting date `[RECOMMENDED]`.

## Documents generated
- Board pack (see `workflows/board-packs.md`); eventually minutes (see `workflows/minutes.md`).

## Audit events
- `mail.thread` on the meeting record; `tracking=True` on `state`.

## Portal behavior
- Director Portal users see meetings of committees they belong to (record rule,
  `security/record-rules.md` §2); they can confirm attendance if that action is portal-exposed
  `[ENGINEERING DETAIL — attendance confirmation via portal not explicitly described in source;
  reasonable to expose as a portal action]`.

## Failure scenarios
- Attempt to skip a state (e.g. `draft → held` directly) → rejected.
- Attempt to add an agenda item to a `closed` meeting → rejected.

## Completion criteria
- Meeting reaches `closed`; all linked resolutions terminal; minutes exist and are at least
  `approved`.

## Acceptance criteria
- See AC-01 in `requirements/acceptance-criteria.md` for the full board-meeting-to-minutes
  end-to-end scenario.
