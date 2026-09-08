# Module: govoo_board

Source: §3.2, §7.4 of the source spec. Build order: **Step 4** (depends on `govoo_base`,
`govoo_shares`).

## Module overview
- **Purpose:** Run board/committee/shareholder meetings end-to-end: agenda → pack → minutes →
  resolutions → e-voting.
- **Responsibility:** Meetings, agenda items, board packs, minutes, resolutions, votes.
- **Depends on (Odoo):** `base`, `mail`, `calendar`, `documents` (feature-flagged), `sign`
  (feature-flagged).
- **Depends on (custom):** `govoo_base`; `govoo_shares` (for weighted shareholder votes via
  `govoo.share.holding`).
- **Owns:** `govoo.meeting`, `govoo.agenda.item`, `govoo.board.pack`, `govoo.minutes`,
  `govoo.resolution`, `govoo.vote`.
- **Must NOT own:** compliance-deadline data (a resolution may prompt a filing, but the obligation
  itself belongs to `govoo_compliance`); share transaction data (owned by `govoo_shares` — this
  module only *reads* `govoo.share.holding` for vote weight).

## Odoo technical structure
```
govoo_board/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_base, govoo_shares, calendar, documents (soft), sign (soft)
|-- models/
|   |-- __init__.py
|   |-- govoo_meeting.py
|   |-- govoo_agenda_item.py
|   |-- govoo_board_pack.py
|   |-- govoo_minutes.py
|   |-- govoo_resolution.py
|   `-- govoo_vote.py
|-- views/
|-- security/
|   |-- ir.model.access.csv
|   `-- govoo_board_security.xml   # director-portal: own-committee only
|-- data/
|-- report/
|   `-- (QWeb: board pack merge, minutes document, resolution/voting summary)
|-- tests/
|   |-- test_meeting.py          # quorum computation, state machine
|   |-- test_resolution.py       # state machine, result computation
|   `-- test_vote.py             # weight sourcing, conflicted-vote exclusion, tally
`-- i18n/
```

## Models

### `govoo.meeting` (relates to `calendar.event`)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | |
| `committee_id` | Many2one `govoo.committee` | Yes | |
| `meeting_type` | Selection (`board`/`committee`/`agm`/`egm`) | Yes | |
| `calendar_event_id` | Many2one `calendar.event` | No | scheduling/reminders |
| `date` | Datetime | Yes | |
| `location` | Char | No | + a separate virtual-link field `[ENGINEERING DETAIL — name it `virtual_link` (Char/URL)]` |
| `attendee_ids` | Many2many `res.partner` | No | |
| `quorum_required` | Integer | Yes | > 0 |
| `quorum_met` | Boolean | — (computed) | from confirmed attendance vs `quorum_required` |
| `agenda_ids` | One2many `govoo.agenda.item` | No | |
| `pack_id` | Many2one `govoo.board.pack` | No | |
| `minutes_id` | Many2one `govoo.minutes` | No | |
| `state` | Selection (`draft`/`scheduled`/`held`/`minuted`/`closed`) | Yes | default `draft` |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **Constraints:** `quorum_required > 0`.
- **Computed fields:** `quorum_met`.
- **State transitions:** see `data-model/state-machines.md`, `workflows/meetings.md`. Whether
  `held` is hard-blocked without quorum is `[CONFIRM]` (not explicit in source).
- **Access requirements:** Director Portal restricted to meetings of committees they belong to.
- Source: §7.4.1. Requirement: FR-BOARD-001.

### `govoo.agenda.item`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `meeting_id` | Many2one `govoo.meeting` | Yes | |
| `sequence` | Integer | No | display order |
| `title` | Char | Yes | |
| `description` | Html | No | |
| `presenter_id` | Many2one `res.partner` | No | |
| `item_type` | Selection (`discussion`/`decision`/`noting`) | Yes | |
| `document_ids` | Many2many `documents.document` | No | Feature-flagged |
| `resolution_ids` | One2many `govoo.resolution` | No | |
- **Inheritance:** `mail.thread`.
- Source: §7.4.2. Requirement: FR-BOARD-002.

### `govoo.board.pack`
- **Description:** Compiles agenda + linked documents into one distributable PDF (QWeb merge)
  stored in Documents; supports per-recipient confidential-item redaction.
- **Fields:** `meeting_id` (m2o), `document_id` (m2o `documents.document`, feature-flagged /
  `ir.attachment` fallback), `distribution_ids` (o2m tracking per-recipient
  distribution + redaction state) `[ENGINEERING DETAIL — model this as a child model
  `govoo.board.pack.recipient` with `partner_id`, `sent_date`, `redacted_item_ids` if per-recipient
  tracking is required; source describes the behavior but not the exact sub-model]`.
- **Inheritance:** `mail.thread`.
- **Methods/business behavior:** compile (merge agenda + docs into one PDF); redact confidential
  agenda items per recipient authorization *before* generating that recipient's copy
  (BR-BOARD-003).
- **Access requirements:** company/committee-scoped; redaction logic tested explicitly
  (TC-BOARD-003).
- Source: §7.4.3. Requirement: FR-BOARD-003.

### `govoo.minutes`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `meeting_id` | Many2one `govoo.meeting` | Yes | |
| `body` | Html | No | |
| `attendance_ids` | Many2many `res.partner` | No | |
| `apologies_ids` | Many2many `res.partner` | No | |
| `state` | Selection (`draft`/`for_approval`/`approved`/`signed`) | Yes | default `draft` |
| `sign_request_id` | Many2one `sign.request` | No | Feature-flagged; gated on legal-validity `[CONFIRM]` |
| `signed_document_id` | Many2one `documents.document` | No | Feature-flagged |
| `retention_until` | Date | — (computed) | 10 years, from `govoo_rw` config, never a literal here |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **Computed fields:** `retention_until` — depends on `create_date` + `govoo_rw` retention setting.
- **State transitions:** see `workflows/minutes.md`; only forward progression.
- Source: §7.4.4. Requirement: FR-BOARD-004.

### `govoo.resolution`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `meeting_id` | Many2one `govoo.meeting` | No | nullable for written resolutions |
| `title` | Char | Yes | |
| `text` | Html | No | |
| `resolution_type` | Selection (`ordinary`/`special`/`written`) | Yes | |
| `state` | Selection (`draft`/`open`/`passed`/`failed`/`withdrawn`) | Yes | default `draft` |
| `vote_ids` | One2many `govoo.vote` | No | |
| `result` | — (computed) | | computed from tallied votes vs quorum/majority |
| `effective_date` | Date | No | |
| `sign_request_id` | Many2one `sign.request` | No | Feature-flagged; gated on legal-validity `[CONFIRM]` |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **State transitions:** see `data-model/state-machines.md`, `workflows/resolutions.md`.
- **Access requirements:** Board Administrator cannot vote (checked at `govoo.vote` create time, not
  here, but the resolution's `open` action must notify only eligible voters).
- Source: §7.4.5. Requirement: FR-BOARD-005.

### `govoo.vote`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `resolution_id` | Many2one `govoo.resolution` | Yes | |
| `voter_id` | Many2one `res.partner` | Yes | |
| `choice` | Selection (`for`/`against`/`abstain`) | Yes | |
| `weight` | Float | Yes | 1.0 per director; sourced from `govoo.share.holding.voting_power` for shareholder resolutions |
| `is_conflicted` | Boolean | No | default `False`; declared interest |
| `timestamp` | Datetime | Yes | immutable once cast |
- **Inheritance:** `mail.thread` (via parent resolution's thread; vote rows themselves may not need
  their own thread — `[ENGINEERING DETAIL]`).
- **Constraints:** one vote per `(resolution_id, voter_id)` — `[CONFIRM]` whether a second vote is
  rejected or overwrites the first (not explicit in source).
- **Access requirements:** only the named `voter_id`'s own user (or documented proxy) can create
  their vote; Board Administrator group has no create access on this model (BR-SEC-004).
- Source: §7.4.6. Requirement: FR-BOARD-006.

## E-voting flow (source §7.4.6, summarized — full detail in `workflows/voting.md`)
resolution `open` → eligible voters notified (activity + portal) → cast vote (in-app/portal) →
auto-tally `passed`/`failed` vs quorum + majority per `resolution_type` → optional Sign → signed PDF
to Documents → register updated if it affects capital/directors.

`[CONFIRM]` legal validity: verify e-signature and electronic/written resolutions are valid under
Rwandan law and the client's articles **before enabling** Sign/e-voting as legally binding features.
Gate `sign_request_id` usage and any "this is a legally binding e-vote" UI messaging on that
confirmation.

## Reports (QWeb)
Board pack merge PDF, minutes document, resolution/voting summary.

## Tests
- TC-BOARD-001: quorum computes correctly.
- TC-BOARD-005/006: tally respects weights and majority thresholds; conflicted votes excluded where
  required.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_board` section.
