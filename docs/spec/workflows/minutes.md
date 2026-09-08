# Workflow: Minutes

Source: §7.4.4. Requirement: FR-BOARD-004. Model: `govoo.minutes`.

## Actor
Company Secretary (draft); Directors of the relevant committee (approve/sign).

## Trigger
Meeting reaches `state = 'held'`.

## Steps
1. Secretary creates/opens `govoo.minutes` linked to the meeting (`state = 'draft'`), records
   `attendance_ids`/`apologies_ids`, and drafts `body` (Html) — including references to any
   resolutions decided at the meeting.
2. Secretary transitions `draft → for_approval` and circulates to the relevant Directors.
3. Directors review; Secretary (on their instruction) or the Directors themselves (if portal-
   enabled for this action) transition `for_approval → approved`.
4. If e-signature is enabled and legally confirmed (`[CONFIRM]`, BR-BOARD-008), a `sign_request_id`
   is created and, once all required signatories sign, `approved → signed`; `signed_document_id` is
   set. If e-signature is not yet confirmed/enabled, `signed` is only reached via a manual
   "signed copy uploaded" path.
5. On `approved`/`signed`, `retention_until` is computed/confirmed from `govoo_rw`'s retention
   configuration (10 years) — see `data-model/computed-fields.md`.
6. Meeting `state` advances `held → minuted` once minutes reach at least `for_approval`
   (`workflows/meetings.md`).

## Validation
- State only advances forward (`data-model/state-machines.md`).
- `for_approval → approved` requires the linked meeting to be at least `held`.

## Database changes
- `govoo.minutes` create/update; `meeting.minutes_id` set; `retention_until` computed and stored.

## Notifications
- `mail.thread` messages; `mail.activity` to Directors when minutes reach `for_approval`
  (approval request).

## Documents generated
- Minutes document (QWeb-rendered, and/or the signed PDF once `signed`).

## Audit events
- `mail.thread`; `tracking=True` on `state`.

## Portal behavior
- Director Portal users of the relevant committee can read minutes at `approved`/`signed` (and
  possibly `for_approval`, if review-via-portal is intended — `[ENGINEERING DETAIL]`).

## Failure scenarios
- Attempt to sign before legal validity of e-signature is confirmed → the Sign integration path is
  disabled/hidden entirely (feature flag), forcing the manual-upload path instead — this is not a
  runtime error but a build-time/config gate (BR-BOARD-008).
- Attempt to skip `for_approval` → rejected.

## Completion criteria
- Minutes reach `approved` (minimum) or `signed` (if enabled); `retention_until` set; meeting
  reflects `minuted`.

## Acceptance criteria
- See AC-01 in `requirements/acceptance-criteria.md`.
