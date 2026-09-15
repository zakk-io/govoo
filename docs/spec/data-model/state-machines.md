# Data Model — State Machines

Source: §7 field tables (`state` columns) plus workflow narrative in §7.4.6, §7.5.3. Every model
below with a `state` field gets an explicit machine definition here; implementation MUST NOT allow
transitions not listed.

## `govoo.appointment.state` (computed, not user-triggered)
```
active  <--->  resigned
```
- **States:** `active`, `resigned`.
- **Allowed transitions:** N/A — this is a *computed* field, not a user-triggered state machine.
  It is recalculated from `date_appointed`/`date_resigned` on every relevant write.
- **Who can trigger:** nobody directly; changing `date_resigned` indirectly changes `state`.
- **Required conditions:** `state = 'resigned'` iff `date_resigned` is set and `<=` today.
- **Side effects:** a `resigned` appointment should stop counting toward `quorum_met` calculations
  and committee `member_ids` "current membership" views (though historical reporting still shows
  it).
- **Audit:** `tracking=True`, so the computed transition still appears in `mail.thread`.

## `govoo.meeting.state`
```
draft --> scheduled --> held --> minuted --> closed
```
- **States:** `draft`, `scheduled`, `held`, `minuted`, `closed`.
- **Allowed transitions:** strictly forward, one step at a time (no skipping — BR-BOARD-002).
- **Who can trigger:** Company Secretary (all transitions); attendees do not change meeting state.
- **Required conditions:**
  - `draft → scheduled`: `calendar_event_id` and `date` set.
  - `scheduled → held`: meeting `date` has passed (or is being recorded as having occurred);
    attendance recorded. Whether `quorum_met = False` **blocks** this transition is `[CONFIRM]`
    (source does not state explicitly — recommend blocking with an explicit override permission for
    Secretary, but treat as open until confirmed).
  - `held → minuted`: `minutes_id` is set and `govoo.minutes.state` has reached at least
    `for_approval`.
  - `minuted → closed`: all agenda-linked resolutions are in a terminal state
    (`passed`/`failed`/`withdrawn`).
- **Forbidden transitions:** any backward transition; skipping a state.
- **Side effects:** `held → minuted` typically triggers minutes drafting workflow start
  (`workflows/minutes.md`).
- **Notifications:** state changes notify `attendee_ids` via `mail.activity`/message (standard
  `mail.thread` behavior).
- **Audit:** `tracking=True` on `state`.

## `govoo.minutes.state`
```
draft --> for_approval --> approved --> signed
```
- **States:** `draft`, `for_approval`, `approved`, `signed`.
- **Allowed transitions:** strictly forward.
- **Who can trigger:** Company Secretary (`draft → for_approval`); Directors of the relevant
  committee (`for_approval → approved`); signing flow (`approved → signed`) gated on `[CONFIRM]`
  legal validity of e-signature (source §7.4.6, §13 item 3) — until confirmed, `signed` may only be
  reached via a manual "signed copy uploaded" path, not an automated Sign integration.
- **Required conditions:** `for_approval → approved` requires the linked meeting to be `state =
  'held'` at minimum.
- **Side effects:** `approved`/`signed` sets/confirms `retention_until` (computed from `govoo_rw`
  config).
- **Audit:** `tracking=True` on `state`.

## `govoo.resolution.state`
```
draft --> open --> passed
              |--> failed
              `--> withdrawn
```
- **States:** `draft`, `open`, `passed`, `failed`, `withdrawn`.
- **Allowed transitions:**
  - `draft → open`: Company Secretary opens the resolution for voting; eligible voters are
    identified and notified.
  - `open → passed`: tally reaches quorum + majority threshold for `resolution_type` before/at
    close.
  - `open → failed`: tally does not reach the threshold.
  - `open → withdrawn`: Company Secretary withdraws before a tally is finalized (e.g. procedural
    withdrawal).
  - `draft → withdrawn`: also permitted (withdrawn before ever opening).
- **Forbidden transitions:** `passed`/`failed`/`withdrawn` are terminal — no transition out of them.
- **Who can trigger:** Company Secretary (`draft→open`, `*→withdrawn`); the system
  (`open→passed`/`open→failed`, computed from tally, not manually set).
- **Required conditions:** `open→passed`/`open→failed` require the tally computation described in
  `workflows/voting.md` and BR-BOARD-005.
- **Side effects:** `passed` may trigger register updates if the resolution affects capital or
  directors (source §7.4.6 e-voting flow), and may trigger a `govoo_compliance` filing obligation
  (cross-module, not automatic unless explicitly wired).
- **Audit:** `tracking=True` on `state` and `result`.

## `govoo.share.transfer.state`
```
draft --> approved --> registered
```
- **States:** `draft`, `approved`, `registered`.
- **Allowed transitions:** strictly forward.
- **Who can trigger:** Company Secretary (`draft→approved`, `approved→registered`); optionally
  gated on `sign_request_id` completion if Sign is enabled and legally confirmed.
- **Required conditions:** `approved→registered` enforces BR-SHARE-002 (`quantity <=` transferor's
  current holding at the moment of registration — re-checked at this transition, not only at
  `draft` creation, since holdings may have changed in the interim).
- **Forbidden transitions:** backward moves; skipping `approved`.
- **Side effects:** `registered` triggers `govoo.share.holding` recompute for both parties
  (FR-SHARE-004) and may update `govoo.register.member` (`date_entered`/`date_ceased`).
- **Audit:** `tracking=True` on `state`.

## `govoo.compliance.instance.state`
```
upcoming --> in_progress --> filed
     |            |
     `----------> late --> (filed | waived)
                   |
                   `-------------------> waived
```
- **States:** `upcoming`, `in_progress`, `filed`, `late`, `waived`.
- **Allowed transitions:**
  - `upcoming → in_progress`: responsible user begins work (manual or on first activity
    interaction).
  - `in_progress → filed`: filing recorded (`reference_no`, `filed_date` set) — see BR-COMP-004.
  - `upcoming|in_progress → late`: system transition, `due_date` passed and not yet `filed`/
    `waived` (BR-COMP-003).
  - `late → filed`: late filing recorded.
  - any non-terminal state `→ waived`: administrator marks the obligation waived for this instance
    (e.g. not applicable this period) — `[ENGINEERING DETAIL — who may waive is not specified in
    source; recommend restricting to Secretary/Admin]`.
- **Forbidden transitions:** `filed`/`waived` are terminal.
- **Who can trigger:** responsible user (`in_progress`, `filed`); system cron (`late`);
  Secretary/Admin (`waived`).
- **Side effects:** `late` triggers escalation (FR-COMP-003).
- **Audit:** `tracking=True` on `state`.

## `govoo.board.pack.state`
`[undocumented-extra]` not mentioned anywhere else in this file — added here for completeness
since the model does define a real state machine, per issue #87.
```
draft --> compiled --> distributed
```
- **States:** `draft`, `compiled`, `distributed`.
- **Allowed transitions:** strictly forward, one step at a time.
- **Who can trigger:** Company Secretary (`action_compile`, `action_distribute`).
- **Required conditions:**
  - `draft → compiled`: merges the meeting's agenda + linked documents into one distributable PDF
    (`document_id`); computes each recipient's per-recipient redaction
    (`govoo.board.pack.recipient.redacted_item_ids`) based on their own authorization for
    confidential agenda items (BR-BOARD-003).
  - `compiled → distributed`: notifies each recipient (`mail.thread` message) and records
    `sent_date` on their `govoo.board.pack.recipient` row.
- **Forbidden transitions:** any backward transition; skipping a state.
- **Side effects:** `distributed` posts a portal notification message to each recipient.
- **Audit:** `tracking=True` on `state`.

## `govoo.evaluation.campaign.state`
```
draft --> open --> closed
```
- **States:** `draft`, `open`, `closed`.
- **Allowed transitions:** strictly forward.
- **Who can trigger:** Company Secretary / Board Administrator.
- **Required conditions:** `open→closed` typically after all/most `participant_ids` have responded
  (exact completion threshold `[ENGINEERING DETAIL]`, not specified in source).
- **Side effects:** `closed` triggers `govoo.evaluation.result` aggregation (FR-EVAL-002).
- **Audit:** `tracking=True` on `state`.
