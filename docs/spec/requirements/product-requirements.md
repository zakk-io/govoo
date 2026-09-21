# Product / Functional Requirements

Source: §1, §2, §5, §7 of the source spec. Every requirement below has a stable ID referenced from
`requirements/traceability.md` and from `testing/`. IDs are never renumbered once assigned.

Priority key: **MUST** (source states as required) / **SHOULD** / **MAY** / `[CONFIRM]` (source marks
uncertain — implement as inactive/configurable) / `[OPTIONAL]` (separate install) / `[RECOMMENDED]`
(engineering addition, not a source requirement).

---

## govoo_base

### FR-BASE-001 — Extend `res.partner` with governance roles and PII
- **Priority:** MUST
- **Description:** Add boolean role flags (`govoo_is_director`, `govoo_is_shareholder`,
  `govoo_is_officer`, `govoo_is_beneficial_owner`) and PII fields (`govoo_national_id`,
  `govoo_date_of_birth`, `govoo_nationality_id`) plus `govoo_appointment_ids` to `res.partner`.
- **Actors:** Company Secretary, Board Administrator (data entry); all governance users (read, PII
  restricted).
- **Preconditions:** `res.partner` record exists (person or, where relevant, organization acting as
  a corporate shareholder).
- **Trigger:** Onboarding a director, shareholder, officer, or beneficial owner.
- **Expected behavior:** Role flags are independently settable (a partner may be director AND
  shareholder). PII fields are only visible/editable to Secretary/Admin groups (field-level
  security, see `security/`).
- **Business rules:** BR-BASE-001.
- **Validation rules:** `govoo_date_of_birth` must be a past date if set.
- **Failure behavior:** Non-privileged users attempting to read/write PII fields receive an access
  error, not silently blanked data.
- **Security considerations:** Field-level restriction to Secretary/Admin (source §6.2).
- **Audit requirements:** `res.partner` already inherits `mail.thread` in standard Odoo; ensure
  `tracking=True` on all `govoo_*` fields added here.
- **Dependencies:** None (first model touched).
- **Acceptance criteria:**
  - *Given* a user in the Governance User group, *when* they open a partner record with beneficial
    owner data, *then* `govoo_national_id` and `govoo_date_of_birth` are not shown.
  - *Given* a Company Secretary, *when* they set `govoo_is_beneficial_owner = True` on a partner,
    *then* the partner becomes eligible for `govoo.register.beneficial.owner` entry.
- **Source reference:** §7.1.1.

### FR-BASE-002 — Extend `res.company` with statutory entity fields
- **Priority:** MUST
- **Description:** Add `govoo_company_number`, `govoo_tin`, `govoo_incorporation_date`,
  `govoo_entity_type` (private/public/llc/branch), `govoo_registered_office_id` (m2o `res.partner`,
  must be in-country per §8), `govoo_financial_year_end` to `res.company`.
- **Actors:** Board Administrator (config-level access).
- **Preconditions:** `res.company` record exists.
- **Trigger:** Entity onboarding / initial configuration.
- **Expected behavior:** `govoo_financial_year_end` drives FYE-relative compliance-date computation
  in `govoo_compliance`/`govoo_rw` (FR-COMP-002, FR-RW-004).
- **Business rules:** BR-BASE-002.
- **Validation rules:** `govoo_registered_office_id` should resolve to a partner whose address is in
  Rwanda `[CONFIRM exact validation rule with legal advisor]`.
- **Failure behavior:** Missing `govoo_financial_year_end` blocks generation of FYE-relative
  compliance instances for that company (fail closed, not silently defaulted).
- **Security considerations:** Only Board Administrator/Secretary can edit; standard multi-company
  record rules apply so one company's users cannot edit another's entity data.
- **Audit requirements:** `tracking=True` on all fields.
- **Dependencies:** None.
- **Acceptance criteria:**
  - *Given* a company with no `govoo_financial_year_end` set, *when* the compliance cron runs,
    *then* no FYE-relative instance is generated for that company and a warning is logged.
- **Source reference:** §7.1.2.

### FR-BASE-003 — Appointment lifecycle (`govoo.appointment`)
- **Priority:** MUST
- **Description:** Model a person's role over time at a company: `partner_id`, `company_id`, `role`
  (director/secretary/chair/md/committee_member), optional `committee_id`, `date_appointed`,
  `date_resigned`, computed `state` (active/resigned), and a feature-flagged
  `appointment_document_id`.
- **Actors:** Company Secretary (create/manage), Board Administrator (config), all governance users
  (read, own-company).
- **Preconditions:** `partner_id` and `company_id` exist.
- **Trigger:** New appointment, resignation, or role change is recorded.
- **Expected behavior:** `state` is computed from `date_appointed`/`date_resigned` (active if
  resigned date is unset or in the future; resigned otherwise) — never manually set.
- **Business rules:** BR-BASE-003.
- **Validation rules:** `date_resigned`, if set, must be >= `date_appointed`. `date_appointed` is
  required.
- **Failure behavior:** Attempting to set `date_resigned` before `date_appointed` raises a
  `ValidationError`.
- **Security considerations:** `company_id` scoped record rule (multi-company isolation).
  Board Administrator can configure appointments but per source §6.2 does not gain board voting
  rights from doing so (separation of duties is about `govoo.vote`, not appointment CRUD).
- **Audit requirements:** `mail.thread`; `tracking=True` on `role`, `date_appointed`,
  `date_resigned`, `state`.
- **Dependencies:** FR-BASE-001, FR-BASE-002.
- **Acceptance criteria:**
  - *Given* an appointment with `date_appointed` in the past and no `date_resigned`, *when* the
    record is read, *then* `state = 'active'`.
  - *Given* an appointment with `date_resigned` in the past, *when* the record is read, *then*
    `state = 'resigned'`.
- **Source reference:** §7.1.3.

### FR-BASE-004 — Committee structure (`govoo.committee`)
- **Priority:** MUST
- **Description:** Model boards and sub-committees: `name`, `company_id`, `parent_committee_id`
  (self-referential, board vs sub-committee), `chair_partner_id`, `member_ids` (o2m
  `govoo.appointment`), `terms_of_reference_id` (feature-flagged document link).
- **Actors:** Company Secretary, Board Administrator.
- **Preconditions:** `company_id` exists; for sub-committees, `parent_committee_id` exists.
- **Trigger:** Board/committee is established or restructured.
- **Expected behavior:** Committee membership resolves via `govoo.appointment` records where
  `committee_id` matches; the committee form view shows resolved members.
- **Business rules:** BR-BASE-004.
- **Validation rules:** `parent_committee_id` must belong to the same `company_id`; no cycles
  (a committee cannot be its own ancestor).
- **Failure behavior:** Cyclical `parent_committee_id` assignment raises a `ValidationError`.
- **Security considerations:** Company-scoped record rule; Director Portal users are restricted to
  meetings/packs of committees they belong to (FR-PORTAL-001, source §6.2).
- **Audit requirements:** `mail.thread`; `tracking=True` on `chair_partner_id`,
  `parent_committee_id`.
- **Dependencies:** FR-BASE-003.
- **Acceptance criteria:**
  - *Given* a committee with three active appointments referencing it, *when* the committee form is
    opened, *then* all three members are listed.
- **Source reference:** §7.1.4.

### FR-BASE-005 — Security groups defined
- **Priority:** MUST
- **Description:** Define the six security groups from source §6.1 in `govoo_base`:
  Governance User, Company Secretary, Board Administrator, Director (Portal), Shareholder (Portal),
  Auditor (read-only).
- **Actors:** Board Administrator (assigns groups).
- **Preconditions:** None (foundational).
- **Trigger:** Module installation.
- **Expected behavior:** Groups exist with the XML IDs specified in `security/access-control.md`
  and are referenced by every other module's `ir.model.access.csv`.
- **Business rules:** BR-SEC-001 through BR-SEC-005.
- **Validation rules:** N/A (data definition).
- **Failure behavior:** N/A.
- **Security considerations:** This IS the security foundation — see `security/` in full.
- **Audit requirements:** Group membership changes are tracked via standard Odoo `res.groups`/
  `res.users` audit, not a custom requirement.
- **Dependencies:** None.
- **Acceptance criteria:**
  - *Given* the module is installed, *when* `security/access-control.md`'s group list is checked
    against the database, *then* all six groups exist with the specified XML IDs.
- **Source reference:** §6.1.

---

## govoo_secretarial

### FR-SEC-001 — Register of Directors & Secretaries
- **Priority:** MUST
- **Description:** `govoo.register.director` is a curated view over `govoo.appointment` plus
  statutory particulars, with change history via `mail.thread`.
- **Actors:** Company Secretary (curate), Auditor (read), Director Portal (read own record only).
- **Preconditions:** Relevant `govoo.appointment` records exist.
- **Trigger:** Director/secretary appointment, resignation, or particulars change.
- **Expected behavior:** Register reflects current and historical appointments without duplicate
  data entry (derived from `govoo.appointment`, not re-keyed).
- **Business rules:** BR-SEC-001.
- **Validation rules:** N/A beyond `govoo.appointment` validation (FR-BASE-003).
- **Failure behavior:** N/A.
- **Security considerations:** Company-scoped; PII fields inherit FR-BASE-001 restrictions.
- **Audit requirements:** `mail.thread`; every change also produces a `govoo.register.entry`
  (FR-SEC-005).
- **Dependencies:** FR-BASE-003.
- **Acceptance criteria:**
  - *Given* an appointment's `date_resigned` is set, *when* the register of directors is viewed,
    *then* the director shows as ceased as of that date.
- **Source reference:** §7.2.1.

### FR-SEC-002 — Register of Members
- **Priority:** MUST
- **Description:** `govoo.register.member`: `partner_id`, `company_id`, `holding_ids` (o2m
  `govoo.share.holding` from `govoo_shares`), `date_entered`, `date_ceased`.
- **Actors:** Company Secretary (curate), Auditor (read), Shareholder Portal (read own record only).
- **Preconditions:** `govoo_shares` installed and at least one `govoo.share.holding` exists.
- **Trigger:** A partner becomes/ceases to be a shareholder (derived from holdings reaching
  zero/nonzero).
- **Expected behavior:** Member register is populated/updated from `govoo.share.holding`
  recomputation, not independently entered.
- **Business rules:** BR-SEC-002, BR-SHARE-003.
- **Validation rules:** `date_ceased` >= `date_entered` if both set.
- **Failure behavior:** N/A.
- **Security considerations:** Company-scoped; shareholder portal record rule restricts to own
  holdings only (source §6.2).
- **Audit requirements:** `mail.thread`; `govoo.register.entry` on create/update/cease.
- **Dependencies:** FR-SHARE-004 (share holding computation).
- **Acceptance criteria:**
  - *Given* a partner's total holding across all classes drops to zero after a transfer, *when*
    holdings recompute, *then* `date_ceased` is set on their member register entry.
- **Source reference:** §7.2.2.

### FR-SEC-003 — Beneficial Ownership Register
- **Priority:** MUST (Rwanda legal requirement, per source explicitly)
- **Description:** `govoo.register.beneficial.owner`: `partner_id`, `company_id`,
  `nature_of_control` (thresholds `[CONFIRM per Rwanda law]`), `date_became_registrable`,
  `evidence_document_id`.
- **Actors:** Company Secretary (curate, MUST), Auditor (read).
- **Preconditions:** Partner has `govoo_is_beneficial_owner = True` or otherwise meets control
  criteria.
- **Trigger:** A person is identified as meeting beneficial-ownership control criteria.
- **Expected behavior:** Selectable `nature_of_control` values represent the legally defined control
  categories (>25% shares / >25% voting / appoint majority of board / significant influence) —
  **the exact thresholds are `[CONFIRM per Rwanda law]` and must not be hard-coded as legal fact**;
  implement as configurable selection/data seeded by `govoo_rw` and flagged pending confirmation.
- **Business rules:** BR-SEC-003.
- **Validation rules:** `nature_of_control` must be set before the record can be marked complete.
- **Failure behavior:** A record with unconfirmed threshold data must not be presented to end users
  as a certified/final legal determination — surface as provisional in the UI.
- **Security considerations:** High-sensitivity PII; Secretary/Admin only for write; company-scoped.
- **Audit requirements:** `mail.thread`; `govoo.register.entry` on every change (this register is
  the highest-scrutiny statutory register).
- **Dependencies:** FR-BASE-001.
- **Acceptance criteria:**
  - *Given* the beneficial-ownership threshold values are unconfirmed, *when* a
    `govoo.register.beneficial.owner` record is created, *then* it is flagged/labelled as
    provisional and does not present a specific legal percentage as authoritative.
- **Source reference:** §7.2.3; also §13 item 4 (`[CONFIRM]`).

### FR-SEC-004 — Register of Charges
- **Priority:** MUST
- **Description:** `govoo.register.charge`: `chargee_partner_id`, `amount` (Monetary),
  `date_created`/`date_registered`, `property_description`, `satisfied` (Boolean),
  `charge_document_id`.
- **Actors:** Company Secretary (curate), Auditor (read).
- **Preconditions:** `company_id` exists (derivable, though not explicitly listed as a field in the
  source table — `[ENGINEERING DETAIL]` add `company_id` for multi-company scoping consistent with
  every other register).
- **Trigger:** A charge/security interest is created, registered, or satisfied.
- **Expected behavior:** `satisfied` toggles independently of deletion — charges are never deleted,
  only marked satisfied (consistent with append-only philosophy of the register subsystem).
- **Business rules:** BR-SEC-004.
- **Validation rules:** `amount` > 0; `date_registered` >= `date_created` if both set.
- **Failure behavior:** N/A.
- **Security considerations:** Company-scoped; Secretary/Admin write, Auditor read.
- **Audit requirements:** `mail.thread`; `govoo.register.entry` on create/update.
- **Dependencies:** FR-BASE-002 (company_id scoping).
- **Acceptance criteria:**
  - *Given* a charge marked `satisfied = True`, *when* the register of charges is printed, *then*
    it still appears (historically), marked as satisfied.
- **Source reference:** §7.2.4.

### FR-SEC-005 — Append-only register entry ledger
- **Priority:** MUST
- **Description:** `govoo.register.entry`: `register_model`, `res_id`, `change_type`
  (create/update/cease), `effective_date`, `user_id`. Write-once — no edit or delete permitted at
  the model/access-rule level.
- **Actors:** System (auto-created by every register model's write/create/unlink-equivalent logic);
  Auditor (read).
- **Preconditions:** A change occurs on any `govoo.register.*` model.
- **Trigger:** Create/update/cease on a register record.
- **Expected behavior:** A ledger entry is created for every register-affecting change, independent
  of and in addition to `mail.message` history, to provide a legally defensible, tamper-evident
  change log.
- **Business rules:** BR-SEC-005.
- **Validation rules:** No `write()` or `unlink()` permitted on existing `govoo.register.entry`
  records at the ORM/access-rule level.
- **Failure behavior:** Any attempt to edit/delete an existing entry is rejected with an access
  error, not silently ignored.
- **Security considerations:** No group — including Board Administrator — has write/unlink access
  to existing entries; only `create` is permitted, and only via the register models' own logic
  (not directly by end users).
- **Audit requirements:** This model IS the audit requirement for the register subsystem.
- **Dependencies:** FR-SEC-001 through FR-SEC-004.
- **Acceptance criteria:**
  - *Given* an existing `govoo.register.entry`, *when* any user (including Board Administrator)
    attempts to write or unlink it, *then* the operation is rejected.
- **Source reference:** §7.2.5.

---

## govoo_shares

### FR-SHARE-001 — Share class definition
- **Priority:** MUST
- **Description:** `govoo.share.class`: `name`, `company_id`, `nominal_value` (Monetary),
  `currency_id` (RWF default via `govoo_rw`), `votes_per_share` (Float), `total_authorised`
  (Integer), `is_redeemable` (Boolean).
- **Actors:** Company Secretary.
- **Preconditions:** `company_id` exists.
- **Trigger:** A new class of shares is authorized.
- **Expected behavior:** Total allotted quantity for a class must never exceed `total_authorised`
  (enforced at allotment time, FR-SHARE-002).
- **Business rules:** BR-SHARE-001.
- **Validation rules:** `total_authorised` > 0; `nominal_value` >= 0.
- **Failure behavior:** N/A at this model level (enforcement happens on allotment).
- **Security considerations:** Company-scoped.
- **Audit requirements:** `mail.thread`; `tracking=True` on `total_authorised`, `votes_per_share`.
- **Dependencies:** FR-BASE-002.
- **Acceptance criteria:**
  - *Given* a share class with `total_authorised = 1000`, *when* allotments summing to 1000 exist
    and a further allotment of 1 is attempted, *then* it is rejected.
- **Source reference:** §7.3.1.

### FR-SHARE-002 — Share allotment (issuance)
- **Priority:** MUST
- **Description:** `govoo.share.allotment`: `company_id`, `share_class_id`, `partner_id` (allottee),
  `quantity` (required Integer), `price_per_share` (Monetary), `date_allotted`, `certificate_no`,
  `certificate_document_id`.
- **Actors:** Company Secretary.
- **Preconditions:** `share_class_id` exists with sufficient unissued authorized capacity.
- **Trigger:** Shares are issued to a person/entity.
- **Expected behavior:** Creating an allotment triggers recomputation of the allottee's
  `govoo.share.holding` (FR-SHARE-004).
- **Business rules:** BR-SHARE-001, BR-SHARE-002.
- **Validation rules:** `quantity` > 0; cumulative allotments for the class must not exceed
  `total_authorised` (BR-SHARE-001).
- **Failure behavior:** Over-allotment raises a `ValidationError` and the record is not saved.
- **Security considerations:** Company-scoped; Secretary/Admin write.
- **Audit requirements:** `mail.thread`; `tracking=True` on `quantity`, `partner_id`.
- **Dependencies:** FR-SHARE-001.
- **Acceptance criteria:**
  - *Given* an allotment of 100 shares to partner A, *when* saved, *then* partner A's
    `govoo.share.holding` for that class increases by 100.
- **Source reference:** §7.3.2.

### FR-SHARE-003 — Share transfer
- **Priority:** MUST
- **Description:** `govoo.share.transfer`: `share_class_id`, `transferor_id`/`transferee_id`,
  `quantity`, `price`, `date_transferred`, `stamp_duty`, `transfer_instrument_id`,
  `sign_request_id` (feature-flagged), `state` (draft/approved/registered).
- **Actors:** Company Secretary (create/approve), transferor/transferee (portal, sign if enabled).
- **Preconditions:** Transferor holds >= `quantity` of the specified class.
- **Trigger:** A shareholder sells/gifts/transfers shares.
- **Expected behavior:** On `state = 'registered'`, holdings recompute: transferor decreases,
  transferee increases, for that class.
- **Business rules:** BR-SHARE-002, BR-SHARE-003.
- **Validation rules:** `quantity` > 0; `quantity` <= transferor's current holding in that class at
  time of registration; `transferor_id != transferee_id`.
- **Failure behavior:** Attempting to register a transfer exceeding the transferor's holding raises
  a `ValidationError`; state remains at its prior value.
- **Security considerations:** Company-scoped; state transitions restricted per
  `workflows/share-management.md`.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `quantity`.
- **Dependencies:** FR-SHARE-002.
- **Acceptance criteria:**
  - *Given* transferor holds 50 shares and a transfer of 60 is attempted, *when* moving to
    `registered`, *then* it is rejected.
  - *Given* transferor holds 50 shares and a transfer of 30 is registered, *when* holdings
    recompute, *then* transferor holds 20 and transferee's holding increases by 30.
- **Source reference:** §7.3.3.

### FR-SHARE-004 — Share holding computation (cap table)
- **Priority:** MUST
- **Description:** `govoo.share.holding` (computed/materialized): current position per
  `(partner, share_class)` — quantity, percentage, voting_power — recomputed from allotments minus
  registered transfers. Backs the cap table view and Register of Members (FR-SEC-002).
- **Actors:** System (recompute), all roles (read, scoped).
- **Preconditions:** At least one allotment exists for the class.
- **Trigger:** Allotment created, or transfer reaches `registered` state.
- **Expected behavior:** `percentage = quantity / total_allotted_in_class`; `voting_power` derives
  from `quantity * share_class.votes_per_share`, normalized against total voting shares for use as
  `govoo.vote.weight` on shareholder resolutions.
- **Business rules:** BR-SHARE-003.
- **Validation rules:** Percentages across all holders of a class must sum to 100% (or 0 if no
  allotments); `quantity` never negative.
- **Failure behavior:** A recompute that would produce a negative holding indicates a data integrity
  fault and must raise, not silently clamp to zero.
- **Security considerations:** Shareholder portal users see only their own holding rows (source
  §6.2).
- **Audit requirements:** Recomputation is logged (who/when triggered it) even though the model
  itself is derived data.
- **Dependencies:** FR-SHARE-002, FR-SHARE-003.
- **Acceptance criteria:** see BR-SHARE-003 acceptance criteria; also:
  - *Given* allotments totaling 1000 shares across 3 holders, *when* percentages are computed,
    *then* they sum to exactly 100% (tolerant of only rounding-safe representation, e.g. compute
    the last holder's percentage as a remainder rather than an independent division).
- **Source reference:** §7.3.4.

### FR-SHARE-005 — GL posting hook (optional)
- **Priority:** `[CONFIRM]` / `[OPTIONAL]`
- **Description:** Optional hook posting capital events (allotments, transfers with consideration)
  to `account.move`.
- **Actors:** Client accounting team (enables/configures).
- **Preconditions:** `account` module installed; client accounting policy confirmed.
- **Trigger:** Capital event occurs, IF this feature is enabled.
- **Expected behavior:** **Off by default.** Only enabled per the client's confirmed accounting
  policy (source §13 item 7, `[CONFIRM]`).
- **Business rules:** N/A until confirmed.
- **Validation rules:** N/A until confirmed.
- **Failure behavior:** If disabled (default), no GL entries are ever created by `govoo_shares`.
- **Security considerations:** Only Accounting-privileged users can enable this feature.
- **Audit requirements:** If enabled, standard `account.move` audit applies.
- **Dependencies:** FR-SHARE-002, FR-SHARE-003.
- **Acceptance criteria:**
  - *Given* the GL posting hook is not explicitly enabled, *when* an allotment or transfer is
    registered, *then* no `account.move` is created.
- **Source reference:** §7.3.5; §13 item 7.

---

## govoo_board

### FR-BOARD-001 — Meeting lifecycle
- **Priority:** MUST
- **Description:** `govoo.meeting`: `name`, `committee_id`, `meeting_type`
  (board/committee/agm/egm), `calendar_event_id` (m2o `calendar.event`), `date`, `location` (+
  virtual link field), `attendee_ids` (m2m `res.partner`), `quorum_required` (Integer),
  `quorum_met` (computed Boolean), `agenda_ids`, `pack_id`, `minutes_id`, `state`
  (draft/scheduled/held/minuted/closed).
- **Actors:** Company Secretary (create/manage), Board Administrator, attendees (portal, view own
  meetings).
- **Preconditions:** `committee_id` exists.
- **Trigger:** A meeting is scheduled.
- **Expected behavior:** `quorum_met` computed from count of confirmed attendees vs
  `quorum_required` at the point attendance is recorded. State only advances via
  `workflows/meetings.md` transitions.
- **Business rules:** BR-BOARD-001, BR-BOARD-002.
- **Validation rules:** `quorum_required` > 0.
- **Failure behavior:** Meeting cannot move to `held` if `quorum_met = False`
  `[ENGINEERING DETAIL — confirm whether this is a hard block or an overridable warning; source does
  not state explicitly, mark [CONFIRM]]`.
- **Security considerations:** Director Portal restricted to meetings of committees they belong to
  (source §6.2, record rule).
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `date`.
- **Dependencies:** FR-BASE-004 (committee).
- **Acceptance criteria:** see `workflows/meetings.md`.
- **Source reference:** §7.4.1.

### FR-BOARD-002 — Agenda item management
- **Priority:** MUST
- **Description:** `govoo.agenda.item`: `meeting_id`, `sequence`, `title`, `description` (Html),
  `presenter_id`, `item_type` (discussion/decision/noting), `document_ids` (m2m
  `documents.document`), `resolution_ids` (o2m `govoo.resolution`).
- **Actors:** Company Secretary.
- **Preconditions:** `meeting_id` exists, state `draft` or `scheduled`.
- **Trigger:** Agenda is prepared for a meeting.
- **Expected behavior:** Items ordered by `sequence`; `item_type = 'decision'` items typically link
  one or more resolutions.
- **Business rules:** N/A beyond ordering.
- **Validation rules:** `sequence` unique-ish (not required unique, but drives display order).
- **Failure behavior:** N/A.
- **Security considerations:** Inherits meeting's company/committee scoping.
- **Audit requirements:** `mail.thread`.
- **Dependencies:** FR-BOARD-001.
- **Acceptance criteria:**
  - *Given* three agenda items with sequences 1, 2, 3, *when* the agenda is displayed, *then* they
    appear in that order.
- **Source reference:** §7.4.2.

### FR-BOARD-003 — Board pack compilation
- **Priority:** MUST
- **Description:** `govoo.board.pack` compiles agenda + linked documents into one distributable PDF
  (QWeb merge) stored in Documents, supporting per-recipient confidential-item redaction.
- **Actors:** Company Secretary (compile/distribute), attendees (portal, receive).
- **Preconditions:** Meeting has agenda items with attached documents.
- **Trigger:** Secretary compiles/distributes the pack ahead of a meeting.
- **Expected behavior:** Confidential agenda items are excluded from packs sent to recipients not
  authorized for them (redaction per recipient).
- **Business rules:** BR-BOARD-003.
- **Validation rules:** N/A.
- **Failure behavior:** If Documents (Enterprise) is unavailable, fall back to `ir.attachment`
  storage per the feature-flag pattern (`architecture/technology-standards.md` §8).
- **Security considerations:** Redaction logic MUST be applied before distribution, not
  after — a leaked confidential item cannot be un-sent.
- **Audit requirements:** `mail.thread` on the pack record; distribution events logged.
- **Dependencies:** FR-BOARD-001, FR-BOARD-002.
- **Acceptance criteria:**
  - *Given* an agenda item marked confidential and a recipient not authorized for it, *when* their
    pack is generated, *then* that item's content is excluded.
- **Source reference:** §7.4.3.

### FR-BOARD-004 — Minutes lifecycle
- **Priority:** MUST
- **Description:** `govoo.minutes`: `meeting_id`, `body` (Html), `attendance_ids`/`apologies_ids`
  (m2m `res.partner`), `state` (draft/for_approval/approved/signed), `sign_request_id`
  (feature-flagged), `signed_document_id`, `retention_until` (computed, 10 years in `govoo_rw`).
- **Actors:** Company Secretary (draft), Directors (approve/sign).
- **Preconditions:** Meeting `state = 'held'`.
- **Trigger:** Minutes are drafted after a meeting.
- **Expected behavior:** `retention_until` computed from `govoo_rw` retention configuration (10
  years), never a literal in `govoo_board`.
- **Business rules:** BR-BOARD-004, BR-RW-001 (retention).
- **Validation rules:** State only advances forward (no skipping `for_approval`).
- **Failure behavior:** Signing (`state = 'signed'`) is gated behind `[CONFIRM]` legal validity of
  e-signature under Rwandan law (source §7.4.6, §13 item 3) — the Sign integration must remain
  feature-flagged off until that is confirmed.
- **Security considerations:** Only Secretary/Admin draft; only Directors of the relevant committee
  approve/sign (separation of duties).
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`.
- **Dependencies:** FR-BOARD-001.
- **Acceptance criteria:** see `workflows/minutes.md`.
- **Source reference:** §7.4.4.

### FR-BOARD-005 — Resolution lifecycle
- **Priority:** MUST
- **Description:** `govoo.resolution`: `meeting_id` (nullable, for written resolutions), `title`,
  `text` (Html), `resolution_type` (ordinary/special/written), `state`
  (draft/open/passed/failed/withdrawn), `vote_ids`, computed `result`, `effective_date`,
  `sign_request_id` (feature-flagged).
- **Actors:** Company Secretary (draft/open), eligible voters (vote), Board Administrator
  (configure, cannot vote).
- **Preconditions:** For meeting-linked resolutions, `meeting_id.state` in an appropriate stage;
  for written resolutions, `meeting_id` is null.
- **Trigger:** A decision requiring board/shareholder approval is raised.
- **Expected behavior:** `result` computed from tallied `vote_ids` against quorum and the majority
  threshold appropriate to `resolution_type` (see `workflows/resolutions.md`,
  `workflows/voting.md`).
- **Business rules:** BR-BOARD-005, BR-BOARD-006.
- **Validation rules:** Cannot move to `open` without eligible voters identified; cannot move to
  `passed`/`failed` without a completed tally.
- **Failure behavior:** N/A beyond state-machine enforcement (`data-model/state-machines.md`).
- **Security considerations:** Admins cannot cast votes (source §6.2 separation of duties).
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `result`.
- **Dependencies:** FR-BOARD-001, FR-BOARD-006 (vote), FR-SHARE-004 (for shareholder resolutions'
  weighting).
- **Acceptance criteria:** see `workflows/resolutions.md`.
- **Source reference:** §7.4.5.

### FR-BOARD-006 — Vote casting and tally (e-voting)
- **Priority:** MUST
- **Description:** `govoo.vote`: `resolution_id`, `voter_id`, `choice` (for/against/abstain),
  `weight` (Float — 1 per director, or voting power from `govoo.share.holding` for shareholder
  resolutions), `is_conflicted` (Boolean), `timestamp`.
- **Actors:** Eligible voters (director or shareholder, per resolution context).
- **Preconditions:** `resolution_id.state = 'open'`; voter is eligible (committee member or
  shareholder as applicable).
- **Trigger:** Resolution opened → eligible voters notified → voter casts a vote.
- **Expected behavior:** `weight` is 1.0 for director/board resolutions; for shareholder
  resolutions, sourced from the voter's `govoo.share.holding.voting_power` at the time of voting.
  Conflicted votes (`is_conflicted = True`) are excluded from the tally where the applicable rule
  requires it (declared-interest exclusion).
- **Business rules:** BR-BOARD-006, BR-BOARD-007.
- **Validation rules:** One vote per `(resolution_id, voter_id)` — no duplicate voting; `choice`
  required.
- **Failure behavior:** A second vote attempt by the same voter on the same resolution is rejected
  (or, `[ENGINEERING DETAIL]`, overwrites the prior vote if the business wants vote-changing before
  close — **`[CONFIRM]`** which behavior is intended; source does not state explicitly).
- **Security considerations:** Only the named `voter_id` (or a user acting on their behalf with
  documented authority) can create their own vote row; Board Administrator cannot vote (source
  §6.2).
- **Audit requirements:** `mail.thread` on the resolution; `timestamp` on every vote is immutable
  once cast.
- **Dependencies:** FR-BOARD-005, FR-SHARE-004.
- **Acceptance criteria:** see `workflows/voting.md`.
- **Source reference:** §7.4.6.

---

## govoo_compliance

### FR-COMP-001 — Compliance obligation catalogue
- **Priority:** MUST
- **Description:** `govoo.compliance.obligation`: `name`, `authority`, `frequency`
  (annual/quarterly/monthly/event), `basis` (fixed_date/fye_relative/event_relative),
  `lead_time_days`, `applies_to_entity_type`, `active`.
- **Actors:** Board Administrator / Company Secretary (maintain catalogue).
- **Preconditions:** None (foundational data model for the module).
- **Trigger:** A new statutory/regulatory obligation type is defined.
- **Expected behavior:** Obligations seeded by `govoo_rw` as provisional templates are `active =
  False` until confirmed by a local advisor (source §8.2, `[IMPORTANT]`).
- **Business rules:** BR-COMP-001, BR-RW-002.
- **Validation rules:** `lead_time_days` >= 0.
- **Failure behavior:** N/A.
- **Security considerations:** Config-level access (Secretary/Admin).
- **Audit requirements:** `mail.thread`; `tracking=True` on `active`.
- **Dependencies:** None.
- **Acceptance criteria:**
  - *Given* an obligation seeded from an unconfirmed `govoo_rw` template, *when* the module is
    installed, *then* `active = False` by default.
- **Source reference:** §7.5.1.

### FR-COMP-002 — Compliance instance generation
- **Priority:** MUST
- **Description:** `govoo.compliance.instance`: `obligation_id`, `company_id`, `period`,
  `due_date`, `responsible_id`, `state` (upcoming/in_progress/filed/late/waived), `filed_date`,
  `reference_no`, `filing_document_id`. Generated per company from active obligations.
- **Actors:** System (`ir.cron`), Company Secretary (own/track), responsible user.
- **Preconditions:** Obligation `active = True`; for `fye_relative` obligations, company's
  `govoo_financial_year_end` is set.
- **Trigger:** Scheduled `ir.cron` run (see FR-COMP-003 engine) generates the next instance(s) per
  active obligation per company.
- **Expected behavior:** `due_date` computed per `basis` (fixed_date, fye_relative, event_relative)
  using confirmed configuration data only — never a hard-coded date.
- **Business rules:** BR-COMP-001, BR-COMP-002.
- **Validation rules:** No duplicate instance for the same `(obligation_id, company_id, period)`.
- **Failure behavior:** If required config (e.g. FYE) is missing, no instance is generated for that
  company (fail closed, logged) — see FR-BASE-002 acceptance criteria.
- **Security considerations:** Company-scoped.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`.
- **Dependencies:** FR-COMP-001, FR-BASE-002.
- **Acceptance criteria:** see `testing/unit-tests.md` TC-COMP-001..003.
- **Source reference:** §7.5.2.

### FR-COMP-003 — Reminder / escalation engine
- **Priority:** MUST
- **Description:** `govoo.compliance.rule` engine: `ir.cron` generates upcoming instances from
  active obligations and creates staged `mail.activity` reminders (e.g. -30/-7/-1 days) for the
  responsible user. Overdue instances transition to `late`, then escalate.
- **Actors:** System (cron), responsible user (receives activities).
- **Preconditions:** FR-COMP-002 instance exists with a future or past `due_date`.
- **Trigger:** Scheduled cron execution (daily, `[RECOMMENDED]`).
- **Expected behavior:** Staged reminders fire at the configured lead-time offsets; an instance past
  `due_date` with `state` not in (`filed`, `waived`) transitions to `late` and triggers escalation
  (e.g. activity to a supervisor — exact escalation recipient `[CONFIRM — not specified in source]`).
- **Business rules:** BR-COMP-002, BR-COMP-003.
- **Validation rules:** N/A.
- **Failure behavior:** Cron failures must be logged and retried per standard `ir.cron` behavior;
  a missed run must not silently skip reminder generation for that window (catch-up logic
  `[RECOMMENDED]`).
- **Security considerations:** Cron runs as system user; created activities respect the responsible
  user's normal access.
- **Audit requirements:** Activity creation/completion is tracked by standard `mail.activity`
  mechanisms.
- **Dependencies:** FR-COMP-002.
- **Acceptance criteria:** see `testing/unit-tests.md` TC-COMP-004.
- **Source reference:** §7.5.3.

### FR-COMP-004 — Filing-pack export
- **Priority:** MUST
- **Description:** Since RDB/Irembo has no confirmed public filing API (`[CONFIRM]`, source §13 item
  6), generate filing-ready documents for manual portal upload, and record submission +
  acknowledgement (`reference_no`, `filed_date`) on the `govoo.compliance.instance`.
- **Actors:** Company Secretary / responsible user.
- **Preconditions:** Instance `state` reaches a stage where filing is due.
- **Trigger:** User requests a filing pack for an instance.
- **Expected behavior:** Exported document bundle assembled from already-modeled register/
  compliance data; no assumption of an external submission API. After manual submission, the user
  records `reference_no` and `filed_date`, moving `state` to `filed`.
- **Business rules:** BR-COMP-004.
- **Validation rules:** `reference_no` required to mark `filed` `[RECOMMENDED — not explicit in
  source but implied by "acknowledgement"]`.
- **Failure behavior:** If an RDB/Irembo API is later confirmed available, this workflow should be
  extensible without a breaking model change — design the export as a distinct step from
  state-transition recording. `[CONFIRM]`.
- **Security considerations:** Company-scoped; exported documents may contain PII — access
  restricted per `security/`.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `reference_no`, `filed_date`.
- **Dependencies:** FR-COMP-002.
- **Acceptance criteria:** see `workflows/compliance.md`.
- **Source reference:** §7.5.4; §13 item 6.

---

## govoo_contracts

Source: `contract_management_clagov_contracts.md` (the addendum) §3.2, one FR per addendum feature
ID (CM-F01–F20). Priority carries the addendum's MoSCoW rating (§3.5): Must→MUST, Should→SHOULD,
Could→MAY.

### FR-CM-01 — Contract register
- **Priority:** MUST
- **Description:** `govoo.contract`: central register with `counterparty_id`, `company_id`,
  `contract_type_id`, `value`, `state`, linked documents.
- **Actors:** Contract Manager (create/manage), Contract Approver (read + approve action),
  Contract Viewer Portal (read own), Auditor (read).
- **Preconditions:** `company_id` and `counterparty_id` (a `res.partner`) exist.
- **Trigger:** A new contract is drafted or generated from a template.
- **Expected behavior:** Every contract is a single `govoo.contract` row tracked through its full
  lifecycle (`data-model/state-machines.md`); no parallel/shadow contract list is created elsewhere.
- **Business rules:** BR-CM-001 through BR-CM-005 (lifecycle gating).
- **Validation rules:** `date_end >= date_start` when both set; `value >= 0` when set.
- **Failure behavior:** N/A at this model level.
- **Security considerations:** Company-scoped (BR-SEC-001); Contract Viewer Portal restricted to own
  contracts (BR-CM-007).
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `value`, `counterparty_id`.
- **Dependencies:** `govoo_base` (partners/companies).
- **Acceptance criteria:**
  - *Given* a new contract is created, *when* saved, *then* it defaults to `state = 'draft'` and is
    visible only within its `company_id`.
- **Source reference:** addendum §3.2 CM-F01, §3.3.

### FR-CM-02 — Types & tagging
- **Priority:** MUST
- **Description:** `govoo.contract.type` categorizes contracts: officer/service agreements, NDAs,
  shareholder agreements, related-party, leases, supplier agreements, engagement letters, SLAs.
- **Actors:** Contract Manager (maintain catalogue).
- **Preconditions:** None (foundational config model).
- **Trigger:** A new contract category is needed, or an existing contract is tagged.
- **Expected behavior:** `contract_type_id` drives `approval_threshold`,
  `requires_board_approval`, and `mandatory_clause_ids` for every contract of that type.
- **Business rules:** BR-CM-001 (threshold gating references this model's config).
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Config-level access (Contract Manager).
- **Audit requirements:** `mail.thread`; `tracking=True` on `approval_threshold`,
  `requires_board_approval`.
- **Dependencies:** None.
- **Acceptance criteria:**
  - *Given* a contract type with `requires_board_approval = True`, *when* a contract of that type
    is saved, *then* it is subject to BR-CM-001 at approval time.
- **Source reference:** addendum §3.2 CM-F02.

### FR-CM-03 — Version control
- **Priority:** MUST
- **Description:** Every draft/executed version of a contract is retained via `document_ids`
  (Documents, feature-flagged; `ir.attachment` fallback).
- **Actors:** Contract Manager (upload/generate versions), Auditor (read history).
- **Preconditions:** A contract exists.
- **Trigger:** A new draft is produced, or the contract is executed.
- **Expected behavior:** No version is ever overwritten in place — each is a distinct
  `documents.document`/`ir.attachment` row linked via `document_ids`, same pattern as
  `govoo.board.pack.document_id` and `govoo.minutes.signed_document_id`.
- **Business rules:** BR-CM-004 (the executed version specifically is write-once).
- **Validation rules:** N/A.
- **Failure behavior:** If Documents (Enterprise) is unavailable, falls back to `ir.attachment`
  per the feature-flag pattern (`architecture/technology-standards.md` §8).
- **Security considerations:** Documents inherit the parent contract's access restrictions
  (`integrations/documents.md`).
- **Audit requirements:** `mail.thread` records every version added.
- **Dependencies:** FR-CM-01.
- **Acceptance criteria:**
  - *Given* a contract with two draft versions and one executed version, *when* the document
    history is viewed, *then* all three remain individually accessible.
- **Source reference:** addendum §3.2 CM-F03.

### FR-CM-04 — Template & clause library
- **Priority:** SHOULD
- **Description:** `govoo.contract.template` (body + merge fields + language) and
  `govoo.contract.clause` (reusable, standard vs optional, mandatory flag).
- **Actors:** Contract Manager (author templates/clauses).
- **Preconditions:** None.
- **Trigger:** A recurring contract type needs a standard starting point.
- **Expected behavior:** Templates reference clauses; a `contract_type_id`'s
  `mandatory_clause_ids` are checked for presence before a contract of that type can leave `draft`
  `[ENGINEERING DETAIL — exact enforcement point not itemized in the addendum; recommend checking
  at draft → in_approval, mirroring how govoo_board checks agenda readiness before a pack compiles]`.
- **Business rules:** N/A beyond mandatory-clause presence.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Config-level access (Contract Manager).
- **Audit requirements:** `mail.thread` on template/clause changes.
- **Dependencies:** FR-CM-02.
- **Acceptance criteria:**
  - *Given* a contract type with two mandatory clauses, *when* a contract of that type generated
    from a template omits one, *then* it is flagged before approval can begin.
- **Source reference:** addendum §3.2 CM-F04, §3.3.

### FR-CM-05 — Generate from template
- **Priority:** SHOULD
- **Description:** Produce a contract document (QWeb) in English, French, or Kinyarwanda from a
  `govoo.contract.template`.
- **Actors:** Contract Manager.
- **Preconditions:** A template exists for the desired `contract_type_id`/language.
- **Trigger:** Contract Manager generates a new contract from a template.
- **Expected behavior:** Merge fields are populated from `res.partner`/`res.company` data (same
  QWeb-merge approach already used for board packs/reports — no new templating engine).
- **Business rules:** N/A.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** N/A beyond standard model access.
- **Audit requirements:** `mail.thread` records the generation event.
- **Dependencies:** FR-CM-04.
- **Acceptance criteria:**
  - *Given* a template with a `{{counterparty_name}}` merge field, *when* a contract is generated
    for a specific counterparty, *then* the field is populated correctly in the output document.
- **Source reference:** addendum §3.2 CM-F05.

### FR-CM-06 — Approval routing
- **Priority:** MUST
- **Description:** Configurable legal → finance → board routing before a contract can execute.
- **Actors:** Contract Manager (submits), Contract Approver (approves within delegation-of-authority
  limits).
- **Preconditions:** Contract in `draft`, mandatory clauses present (FR-CM-04).
- **Trigger:** Contract Manager submits for approval.
- **Expected behavior:** `draft → in_approval` transition; routing steps themselves are
  configuration, not a hard-coded sequence, so different contract types can have different routing
  `[ENGINEERING DETAIL — exact routing-step data model not itemized in the addendum; recommend a
  simple ordered approver list per contract_type_id, consistent with "configurable" language in
  §3.2]`.
- **Business rules:** BR-CM-001 (board-approval gating layers on top of this routing, not instead of
  it).
- **Validation rules:** Cannot move to `in_approval` without mandatory clauses present.
- **Failure behavior:** N/A.
- **Security considerations:** Only Contract Approver group can action the approval step; Contract
  Manager cannot approve their own submission `[ENGINEERING DETAIL — separation-of-duties rule
  inferred from the existing Secretary/Director pattern (BR-SEC-004), not explicit in the addendum
  — CONFIRM]`.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`.
- **Dependencies:** FR-CM-01, FR-CM-04.
- **Acceptance criteria:** see `workflows/contracts.md`.
- **Source reference:** addendum §3.2 CM-F06.

### FR-CM-07 — Board-approval linkage
- **Priority:** MUST (critical — governance differentiator)
- **Description:** Contracts above a threshold, or of a defined type, require a linked
  `govoo.resolution` in state `passed` before execution.
- **Actors:** Contract Approver, Company Secretary (drafts the linked resolution in `govoo_board`).
- **Preconditions:** `contract_type_id.requires_board_approval = True` or `value >=
  contract_type_id.approval_threshold`.
- **Trigger:** Approval routing reaches the board-approval step.
- **Expected behavior:** `in_approval → approved` is blocked while `resolution_id` is unset or its
  `state != 'passed'` (BR-CM-001).
- **Business rules:** BR-CM-001.
- **Validation rules:** Thresholds/qualifying types are `[CONFIRM]` — addendum §9 item 4; never
  hard-coded, represented as `govoo.contract.type` config data, inactive/zero until confirmed.
- **Failure behavior:** Attempting to approve without a passed resolution raises a `ValidationError`;
  state remains at `in_approval`.
- **Security considerations:** This is a hard gate, not a warning — no group, including Contract
  Approver, can bypass it.
- **Audit requirements:** `mail.thread`; `tracking=True` on `resolution_id`.
- **Dependencies:** FR-CM-06, `govoo_board` FR-BOARD-005 (resolution lifecycle).
- **Acceptance criteria:**
  - *Given* a contract of a type requiring board approval with no linked passed resolution, *when*
    approval is attempted, *then* it is rejected.
- **Source reference:** addendum §3.2 CM-F07, §3.4; §9 item 4.

### FR-CM-08 — Delegation-of-authority matrix
- **Priority:** MUST (critical — governance differentiator)
- **Description:** Who may sign what contract type/value; execution is blocked outside that
  authority.
- **Actors:** Contract Approver (signs within limits), Board Administrator (configures the matrix,
  cannot sign on that basis alone — same separation-of-duties principle as BR-SEC-004).
- **Preconditions:** A board-approved delegation-of-authority matrix exists as configuration data.
- **Trigger:** Execution (`approved → executed`) is attempted.
- **Expected behavior:** The executing user's authority (role/value limit per the matrix) must cover
  the contract's `contract_type_id`/`value`; otherwise execution is blocked (BR-CM-002).
- **Business rules:** BR-CM-002.
- **Validation rules:** The matrix itself is `[CONFIRM]` — addendum §9 item 5; represented as
  configurable data, never a hard-coded limit in Python.
- **Failure behavior:** Execution attempted outside authority raises a `ValidationError`; `state`
  remains `approved`.
- **Security considerations:** Enforced at the model/workflow layer, not merely a UI hint — mirrors
  BR-SEC-004's "the constraint is enforced at the access/business-rule layer, not by trust" pattern.
- **Audit requirements:** `mail.thread`; every execution attempt (successful or blocked) is logged.
- **Dependencies:** FR-CM-07.
- **Acceptance criteria:**
  - *Given* a delegation-of-authority matrix limiting a role to contracts under a stated value,
    *when* a user in that role attempts to execute a contract above it, *then* execution is
    rejected.
- **Source reference:** addendum §3.2 CM-F08, §3.4; §9 item 5.

### FR-CM-09 — Related-party check
- **Priority:** SHOULD
- **Description:** Cross-reference the counterparty against the directors'-interests / related-party
  data; flag conflicts.
- **Actors:** System (computes `is_related_party`), Contract Manager/Approver (declare/review
  conflict).
- **Preconditions:** `counterparty_id` set.
- **Trigger:** Contract created/counterparty changed.
- **Expected behavior:** `is_related_party` is computed, never independently entered; a `True` value
  forces a conflict-of-interest declaration before approval (BR-CM-003).
- **Business rules:** BR-CM-003.
- **Validation rules:** N/A beyond the declaration gate.
- **Failure behavior:** Approval blocked without a recorded declaration when `is_related_party =
  True`.
- **Security considerations:** Same declared-interest philosophy as `govoo.vote.is_conflicted`
  (BR-BOARD-007).
- **Audit requirements:** `mail.thread`; `tracking=True` on `is_related_party`.
- **Dependencies:** `govoo_base`/`govoo_secretarial` interests data.
- **Acceptance criteria:**
  - *Given* a counterparty matching a director's declared interest, *when* the contract is created,
    *then* `is_related_party = True` and approval is blocked pending a conflict declaration.
- **Source reference:** addendum §3.2 CM-F09, §3.4.

### FR-CM-10 — E-signature
- **Priority:** MUST
- **Description:** Execute via Odoo Sign (ordered signing, audit trail); the resulting executed PDF
  is locked (write-once, BR-CM-004).
- **Actors:** Signatories (per delegation-of-authority), Contract Manager (initiates).
- **Preconditions:** `state = 'approved'`; delegation-of-authority check passes (FR-CM-08).
- **Trigger:** Execution is initiated.
- **Expected behavior:** `sign_request_id` created; on completion, the signed document becomes the
  write-once executed version and `state → executed`.
- **Business rules:** BR-CM-004, BR-CM-005.
- **Validation rules:** N/A beyond the state-machine precondition.
- **Failure behavior:** Gated behind the same Rwanda e-signature legal-validity `[CONFIRM]` as
  `govoo_board` (BR-BOARD-008) — until confirmed, execution uses a manual signed-copy-upload path,
  and the system must not present an e-signed contract as legally conclusive.
- **Security considerations:** Signed documents inherit the parent contract's access restrictions.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`, `sign_request_id`.
- **Dependencies:** FR-CM-08, `integrations/sign.md`.
- **Acceptance criteria:** see `workflows/contracts.md`.
- **Source reference:** addendum §3.2 CM-F10; §9 item 3.

### FR-CM-11 — Key-date tracking
- **Priority:** MUST
- **Description:** Start/end/renewal/notice dates auto-create compliance reminders via the
  *existing* `govoo_compliance` engine.
- **Actors:** System (reminder generation), responsible user (receives reminders).
- **Preconditions:** Contract `state = 'active'` with relevant dates set.
- **Trigger:** Contract becomes active, or an obligation's `due_date` approaches.
- **Expected behavior:** Reminders are staged the same way `govoo.compliance.instance` reminders are
  (BR-CM-006) — no parallel reminder mechanism is built in this module.
- **Business rules:** BR-CM-006.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** N/A beyond standard model access.
- **Audit requirements:** Reminder creation/completion tracked via standard `mail.activity`
  mechanisms, same as `govoo_compliance`.
- **Dependencies:** `govoo_compliance` FR-COMP-003 (reminder engine).
- **Acceptance criteria:**
  - *Given* a contract obligation with a `due_date` 30 days out, *when* the existing compliance
    reminder cron runs, *then* a staged reminder is created for the responsible user, using the
    same mechanism as a statutory obligation.
- **Source reference:** addendum §3.2 CM-F11, §3.4.

### FR-CM-12 — Auto-renewal & notice alerts
- **Priority:** SHOULD
- **Description:** Evergreen (`renewal_type = 'auto'`) tracking; alert before the notice window
  (`notice_period_days`) lapses.
- **Actors:** System (alerting), Contract Manager (acts on renewal/termination decision).
- **Preconditions:** `renewal_type = 'auto'`, `date_end` and `notice_period_days` set.
- **Trigger:** Current date enters the notice window before `date_end`.
- **Expected behavior:** A reminder fires via the same engine as FR-CM-11; if no termination notice
  is recorded before `date_end`, the contract's evergreen nature is reflected in reporting
  `[ENGINEERING DETAIL — exact "renewed" state representation not itemized; recommend the contract
  remaining `active` with a new implicit term rather than a fresh `govoo.contract` row, to avoid
  document/version fragmentation — CONFIRM]`.
- **Business rules:** BR-CM-006 (shares the reminder mechanism).
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** N/A.
- **Audit requirements:** `mail.thread`.
- **Dependencies:** FR-CM-11.
- **Acceptance criteria:**
  - *Given* an evergreen contract with a 60-day notice period, *when* the current date enters that
    window before `date_end`, *then* a reminder is generated.
- **Source reference:** addendum §3.2 CM-F12.

### FR-CM-13 — Obligation & milestone tracking
- **Priority:** SHOULD
- **Description:** `govoo.contract.obligation` (deliverables) and `govoo.contract.milestone`
  (payment/delivery milestones) with owners and status.
- **Actors:** Contract Manager (define), responsible user (action/update status).
- **Preconditions:** Contract exists.
- **Trigger:** Contract has deliverables or a payment schedule.
- **Expected behavior:** Each obligation/milestone tracked independently with its own `state`; an
  obligation's `due_date` feeds FR-CM-11.
- **Business rules:** N/A beyond FR-CM-11's reminder integration.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Inherits parent contract's company/portal scoping.
- **Audit requirements:** `mail.thread` on both models.
- **Dependencies:** FR-CM-01.
- **Acceptance criteria:**
  - *Given* an obligation marked `done`, *when* the contract's obligation list is reviewed, *then*
    it no longer counts toward outstanding/overdue reporting.
- **Source reference:** addendum §3.2 CM-F13, §3.3.

### FR-CM-14 — Renewal/termination workflow
- **Priority:** SHOULD
- **Description:** Guided renew, renegotiate, or terminate flow as a contract approaches `date_end`.
- **Actors:** Contract Manager.
- **Preconditions:** Contract `state = 'active'`, approaching or past `date_end`.
- **Trigger:** Contract Manager acts on a renewal/notice reminder (FR-CM-12), or `date_end` passes.
- **Expected behavior:** `active → expired` (no action taken) or `active → terminated` (early/at-term
  termination recorded); a renewal produces a new term (mechanism `[ENGINEERING DETAIL]`, see
  FR-CM-12).
- **Business rules:** N/A beyond the state machine (`data-model/state-machines.md`).
- **Validation rules:** Terminal states (`expired`, `terminated`) do not transition further.
- **Failure behavior:** N/A.
- **Security considerations:** Contract Manager action; Contract Approver notified per routing
  config.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`.
- **Dependencies:** FR-CM-01, FR-CM-12.
- **Acceptance criteria:** see `workflows/contracts.md`.
- **Source reference:** addendum §3.2 CM-F14.

### FR-CM-15 — Financial linkage (optional)
- **Priority:** `[CONFIRM]` / `[OPTIONAL]` (MAY)
- **Description:** Value + payment schedule in RWF; optional link to Odoo Accounting behind a flag.
- **Actors:** Client accounting team (enables/configures).
- **Preconditions:** `account` module installed; client accounting policy confirmed.
- **Trigger:** A contract's milestone/obligation reaches a billable event, IF this feature is
  enabled.
- **Expected behavior:** **Off by default.** Same pattern as `govoo_shares` FR-SHARE-005/
  BR-SHARE-004 — only enabled per a client-confirmed accounting policy.
- **Business rules:** BR-CM-008.
- **Validation rules:** N/A until confirmed.
- **Failure behavior:** If disabled (default), no `account.move`/invoice/PO is ever created by
  `govoo_contracts`.
- **Security considerations:** Only Accounting-privileged users can enable this feature.
- **Audit requirements:** If enabled, standard `account.move` audit applies.
- **Dependencies:** FR-CM-13.
- **Acceptance criteria:**
  - *Given* the financial linkage is not explicitly enabled, *when* a milestone is marked `paid`,
    *then* no `account.move` is created.
- **Source reference:** addendum §3.2 CM-F15, §5.

### FR-CM-16 — Portal access
- **Priority:** MUST
- **Description:** Counterparties/approvers see only their own contracts via record rules.
- **Actors:** Contract Viewer (Portal).
- **Preconditions:** Portal user linked to a `res.partner` that is a contract counterparty or named
  approver.
- **Trigger:** Portal login.
- **Expected behavior:** Record rules restrict `govoo.contract` (and its obligations/milestones)
  visibility to contracts where the portal user's partner is the counterparty or a named approver
  (BR-CM-007) — same "deny, don't merely hide" discipline as FR-PORTAL-001/002.
- **Business rules:** BR-CM-007, BR-SEC-002, BR-SEC-006.
- **Validation rules:** N/A.
- **Failure behavior:** Direct-URL access to another counterparty's contract is denied, not merely
  hidden from menus.
- **Security considerations:** `portal.mixin` + access tokens, per `security/portal-security.md`.
- **Audit requirements:** Standard portal access-log behavior.
- **Dependencies:** FR-CM-01.
- **Acceptance criteria:**
  - *Given* a Contract Viewer Portal user who is a counterparty on Contract A but not Contract B,
    *when* they attempt to open Contract B by direct URL, *then* access is denied.
- **Source reference:** addendum §3.2 CM-F16, §4.

### FR-CM-17 — Dashboards
- **Priority:** SHOULD
- **Description:** Register, expiry/renewal calendar, obligations status, spend by counterparty.
- **Actors:** Contract Manager, Contract Approver, Board Administrator.
- **Preconditions:** Contracts/obligations exist.
- **Trigger:** Dashboard viewed.
- **Expected behavior:** Same Enterprise-Spreadsheet-Dashboards-with-Community-fallback pattern as
  every other dashboard in the system (`ui/dashboards.md` §5) — content available either way,
  presentation richness differs.
- **Business rules:** N/A.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Company-scoped; portal users do not see this internal dashboard.
- **Audit requirements:** N/A.
- **Dependencies:** FR-CM-01, FR-CM-13.
- **Source reference:** addendum §3.2 CM-F17.

### FR-CM-18 — Retention
- **Priority:** SHOULD
- **Description:** Align contract retention to the statutory retention rules already configured in
  `govoo_rw`.
- **Actors:** System (disposal job), Contract Manager (oversight).
- **Preconditions:** `govoo_rw` retention configuration exists.
- **Trigger:** Contract creation (retention period computed) / scheduled disposal job run.
- **Expected behavior:** `contract_type_id.retention_years` is read from/aligned with `govoo_rw`
  configuration at compute time, never a literal in `govoo_contracts` — same discipline as
  `govoo.minutes.retention_until` (BR-BOARD-004, BR-RW-002).
- **Business rules:** BR-RW-002, BR-RW-003 (erasure-rights reconciliation applies here too).
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Disposal job restricted to system/Admin execution, same as `govoo_rw`
  FR-RW-002.
- **Audit requirements:** Every disposal action is itself logged before the underlying record is
  removed.
- **Dependencies:** `govoo_rw` FR-RW-002.
- **Source reference:** addendum §3.2 CM-F18, §3.4.

### FR-CM-19 — AI extraction
- **Priority:** `[OPTIONAL]` (MAY) — depends on a separate, not-yet-specced module
- **Description:** Pull key terms/dates/obligations from legacy contracts, human-confirmed, using
  `govoo_ai`.
- **Actors:** Contract Manager (reviews/confirms extracted data).
- **Preconditions:** `govoo_ai` installed and configured (out of scope for this document — see
  `modules/govoo_contracts.md` "Out of scope").
- **Trigger:** A legacy contract document is uploaded for extraction.
- **Expected behavior:** Extraction output is never auto-committed to `govoo.contract`/
  `govoo.contract.obligation` fields — a human reviews and confirms before it becomes the record of
  fact (human-in-the-loop, addendum §7 criterion 4).
- **Business rules:** N/A (governed by `govoo_ai`'s own rules once that module is specced).
- **Validation rules:** N/A.
- **Failure behavior:** If `govoo_ai` is not installed, this feature is simply absent — no error, no
  degraded core-contract-management functionality (addendum §6, "contract workflows never depend on
  AI being available").
- **Security considerations:** N/A here (governed by `govoo_ai`'s own security model).
- **Audit requirements:** N/A here.
- **Dependencies:** `govoo_ai` (not specced by this repository as of this addendum).
- **Source reference:** addendum §3.2 CM-F19, §8 step 3.

### FR-CM-20 — AI summarize / risk / Q&A
- **Priority:** `[OPTIONAL]` (MAY) — depends on a separate, not-yet-specced module
- **Description:** Summarize contracts, flag risky/missing clauses, detect template deviation,
  answer questions over contract content, using `govoo_ai`.
- **Actors:** Contract Manager, Contract Approver (consult AI output as an aid, not a decision-maker).
- **Preconditions:** `govoo_ai` installed and configured.
- **Trigger:** User requests a summary/risk-flag/Q&A over one or more contracts.
- **Expected behavior:** AI output is clearly labelled as such and never presented as an official
  approval/compliance determination — a named human remains accountable for every official record
  (addendum's closing note).
- **Business rules:** N/A (governed by `govoo_ai`).
- **Validation rules:** N/A.
- **Failure behavior:** Same graceful-absence behavior as FR-CM-19.
- **Security considerations:** AI retrieval must honour existing record rules/company scope — an AI
  query must never surface a contract the requesting user could not otherwise read (addendum §4).
- **Audit requirements:** Every AI request/response is logged (governed by `govoo_ai`'s own audit
  model once specced).
- **Dependencies:** `govoo_ai` (not specced by this repository as of this addendum).
- **Source reference:** addendum §3.2 CM-F20, §8 step 3.

---

## govoo_rw

### FR-RW-001 — Locale, currency, and company field configuration
- **Priority:** MUST
- **Description:** Configure currency (RWF, 0 decimals), languages (English primary, Kinyarwanda,
  French; Swahili optional), date format (DD/MM/YYYY), timezone (Africa/Kigali), and company fields
  (TIN, RDB company number, registered office in Rwanda).
- **Actors:** Board Administrator (deployment-time config).
- **Preconditions:** `govoo_base` installed (registered office / company number fields already
  exist there; `govoo_rw` supplies the Rwanda-specific defaults/validation).
- **Trigger:** Deployment for a Rwanda-based client.
- **Expected behavior:** RWF configured with 0 decimal places system-wide; Kinyarwanda `.po`
  translation shipped (legal terms reviewed by a local advisor — source §8.1 risk note).
- **Business rules:** BR-RW-001.
- **Validation rules:** N/A (config data).
- **Failure behavior:** N/A.
- **Security considerations:** N/A.
- **Audit requirements:** N/A (config, not transactional data).
- **Dependencies:** FR-BASE-002.
- **Source reference:** §8.1.

### FR-RW-002 — Register-to-law mapping and retention rules
- **Priority:** MUST
- **Description:** Map registers to Rwanda company law (share register, register of directors'
  interests, beneficial ownership register); implement retention as `retention_until` computed
  fields (minutes/resolutions: 10 years; accounts/auditor/board reports: 10 accounting periods) plus
  a disposal job.
- **Actors:** System (disposal job), Company Secretary (oversight).
- **Preconditions:** Relevant register/board models exist (`govoo_secretarial`, `govoo_board`).
- **Trigger:** Record creation (retention_until computed) / scheduled disposal job run.
- **Expected behavior:** `retention_until` computed at creation from `govoo_rw`'s retention
  configuration data, not a literal in the owning module.
- **Business rules:** BR-RW-002.
- **Validation rules:** Disposal job must reconcile the 10-year statutory retention against
  data-subject erasure rights (source §10.3) — i.e. must not blindly delete before checking for a
  legal hold `[CONFIRM exact reconciliation process with legal/DPO]`.
- **Failure behavior:** Disposal job dry-runs before any deletion `[RECOMMENDED]`.
- **Security considerations:** Disposal job restricted to system/Admin execution.
- **Audit requirements:** Every disposal action is itself logged (what was disposed, when, by what
  rule) before the underlying record is removed.
- **Dependencies:** FR-BOARD-004, FR-SEC-001..004.
- **Source reference:** §8.2.

### FR-RW-003 — Provisional compliance deadline templates
- **Priority:** `[CONFIRM]` (content) / MUST (mechanism)
- **Description:** Seed the compliance-obligation catalogue (FR-COMP-001) with Rwanda obligation
  templates (VAT/PAYE/WHT/RSSB monthly; VAT small-taxpayer quarterly; CIT quarterly instalments;
  CIT annual declaration; annual return + accounts) as data, gated behind local-advisor sign-off,
  shown with a disclaimer.
- **Actors:** Local advisor (confirms), Board Administrator (activates post-confirmation).
- **Preconditions:** FR-COMP-001 model exists.
- **Trigger:** `govoo_rw` module installation seeds templates as `active = False`.
- **Expected behavior:** No template is ever presented as authoritative before advisor sign-off;
  the exact annual-return filing window is explicitly `[CONFIRM exact window]` in the source and
  must remain marked as such in the UI/data until resolved.
- **Business rules:** BR-RW-002, BR-COMP-001.
- **Validation rules:** Template `active` field cannot be set to `True` by data migration/seed
  scripts — only by explicit, logged administrator action after confirmation
  `[ENGINEERING DETAIL]`.
- **Failure behavior:** N/A.
- **Security considerations:** N/A.
- **Audit requirements:** Activation of a previously-provisional template is tracked (who, when).
- **Dependencies:** FR-COMP-001.
- **Acceptance criteria:**
  - *Given* a freshly installed `govoo_rw`, *when* the obligation catalogue is inspected, *then*
    every Rwanda-seeded template has `active = False` and a disclaimer/source note.
- **Source reference:** §8.3; §13 item 5.

### FR-RW-004 — CMA Corporate Governance Code self-assessment
- **Priority:** SHOULD (for listed/public-company clients)
- **Description:** CMA Corporate Governance Code 2024 "apply-and-explain" self-assessment
  checklist, implemented as a configurable obligation set + checklist model.
- **Actors:** Company Secretary, Board (for public/listed entities).
- **Preconditions:** Company `govoo_entity_type = 'public'` (or otherwise in scope)
  `[ENGINEERING DETAIL — exact applicability rule not specified in source, mark [CONFIRM]]`.
- **Trigger:** Periodic self-assessment cycle.
- **Expected behavior:** Checklist items configurable (not hard-coded to the 2024 code text, which
  may be amended).
- **Business rules:** N/A beyond configurability.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** Company-scoped.
- **Audit requirements:** `mail.thread` on checklist responses.
- **Dependencies:** FR-COMP-001 (reuses obligation-set pattern).
- **Source reference:** §8.5.

---

## govoo_evaluation

### FR-EVAL-001 — Evaluation campaign
- **Priority:** MUST
- **Description:** `govoo.evaluation.campaign`: `name`, `committee_id`, `survey_id` (m2o
  `survey.survey`), `evaluation_type` (board/committee/peer/chair/self), `participant_ids`,
  `state` (draft/open/closed).
- **Actors:** Company Secretary / Board Administrator (create/manage), participants (respond via
  Surveys).
- **Preconditions:** `survey.survey` module installed; a survey exists or is created.
- **Trigger:** A board/committee performance evaluation cycle begins.
- **Expected behavior:** Campaign wraps a standard `survey.survey`; no duplicate question-authoring
  UI is built (reuse-before-build).
- **Business rules:** N/A beyond standard state progression.
- **Validation rules:** `participant_ids` must be committee members if `evaluation_type` in
  (board, committee, peer).
- **Failure behavior:** N/A.
- **Security considerations:** Company/committee-scoped.
- **Audit requirements:** `mail.thread`; `tracking=True` on `state`.
- **Dependencies:** FR-BASE-004.
- **Source reference:** §7.6.1.

### FR-EVAL-002 — Evaluation result aggregation & confidentiality
- **Priority:** MUST
- **Description:** `govoo.evaluation.result`: aggregated scores per participant/dimension from
  `survey.user_input`, feeding trend dashboards; individual responses not exposed to
  non-authorized roles.
- **Actors:** Company Secretary / Board Administrator (view aggregates), participants (never see
  others' individual responses unless explicitly authorized).
- **Preconditions:** Campaign `state = 'closed'` (or partially, per aggregation rule
  `[ENGINEERING DETAIL]`).
- **Trigger:** Survey responses submitted / campaign closes.
- **Expected behavior:** Aggregation computes summary scores; record rules prevent any user other
  than Secretary/Admin (or the respondent themselves, for their own input) from reading raw
  individual `survey.user_input` rows tied to the campaign.
- **Business rules:** BR-EVAL-001.
- **Validation rules:** N/A.
- **Failure behavior:** N/A.
- **Security considerations:** This is a confidentiality-critical requirement — test explicitly
  (TC-EVAL-002).
- **Audit requirements:** `mail.thread` on the result record (aggregate level only).
- **Dependencies:** FR-EVAL-001.
- **Acceptance criteria:**
  - *Given* a non-Secretary/Admin participant, *when* they attempt to view another participant's
    individual survey response, *then* access is denied.
- **Source reference:** §7.6.2.

---

## Portal (cross-cutting)

### FR-PORTAL-001 — Director portal self-service
- **Priority:** MUST
- **Description:** Director Portal users view meetings/packs/minutes/resolutions for committees
  they belong to, and cast votes on resolutions they are eligible for.
- **Actors:** Director (Portal) group.
- **Preconditions:** Portal user linked to a `res.partner` with an active `govoo.appointment`.
- **Trigger:** Portal login.
- **Expected behavior:** Record rules restrict visibility to own-committee data only (source §6.2).
- **Business rules:** BR-SEC-002 (portal record rules), BR-BOARD-006.
- **Validation rules:** N/A.
- **Failure behavior:** Attempting to access another committee's meeting by direct URL is denied,
  not merely hidden from menus (source §6.3 — never rely on URL obscurity).
- **Security considerations:** `portal.mixin`, `_compute_access_url`, access tokens — see
  `security/portal-security.md`.
- **Audit requirements:** Portal access attempts follow standard Odoo access-log behavior.
- **Dependencies:** FR-BASE-003, FR-BOARD-001, FR-BOARD-006.
- **Source reference:** §6.2, §6.3.

### FR-PORTAL-002 — Shareholder portal self-service
- **Priority:** MUST
- **Description:** Shareholder Portal users view only their own `govoo.share.holding` and
  shareholder resolutions.
- **Actors:** Shareholder (Portal) group.
- **Preconditions:** Portal user linked to a `res.partner` with a nonzero `govoo.share.holding`.
- **Trigger:** Portal login.
- **Expected behavior:** Record rules restrict `govoo.share.holding` and shareholder-type
  `govoo.resolution` visibility to the user's own partner.
- **Business rules:** BR-SEC-002.
- **Validation rules:** N/A.
- **Failure behavior:** Same as FR-PORTAL-001 — deny, don't merely hide.
- **Security considerations:** See `security/portal-security.md`.
- **Audit requirements:** N/A beyond standard.
- **Dependencies:** FR-SHARE-004, FR-BOARD-005.
- **Source reference:** §6.2.

### FR-PORTAL-003 — Portal access-token security
- **Priority:** MUST
- **Description:** No record is ever exposed by URL guessing; every portal-exposed record uses
  `portal.mixin` access tokens combined with the record rules above.
- **Actors:** System.
- **Preconditions:** N/A.
- **Trigger:** Any portal request for a governance record.
- **Expected behavior:** Requests without a valid token/record-rule match are denied.
- **Business rules:** BR-SEC-002.
- **Validation rules:** N/A.
- **Failure behavior:** Denied, logged.
- **Security considerations:** This is a security-critical control; see
  `security/portal-security.md` and TC-SEC tests.
- **Audit requirements:** N/A beyond standard access logs.
- **Dependencies:** FR-PORTAL-001, FR-PORTAL-002.
- **Source reference:** §6.3.
