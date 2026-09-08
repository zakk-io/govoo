# Acceptance Criteria (consolidated, Given/When/Then)

Per-requirement acceptance criteria are embedded in `requirements/product-requirements.md`. This
file consolidates the criteria that span multiple requirements/modules (end-to-end scenarios) so
they are not duplicated across individual FR entries. Each maps to one or more `TC-*` tests in
`testing/acceptance-tests.md`.

## AC-01 — Board-meeting-to-minutes end-to-end (govoo_board)
- **Given** a committee with 5 active members and `quorum_required = 3`,
- **When** a meeting is scheduled, agenda items with a decision-type resolution are added, the
  meeting is held with 4 confirmed attendees, the resolution is opened, voted on (3 for, 1 against,
  1 abstain), and minutes are drafted, approved, and (if enabled) signed,
- **Then** `quorum_met = True`, the resolution `state = 'passed'` (assuming a simple-majority
  threshold), minutes `state` progresses to `approved`/`signed`, and `retention_until` is set from
  `govoo_rw` configuration.
- Maps to: FR-BOARD-001..006, TC-BOARD-001..004.

## AC-02 — Cap table integrity across allotment and transfer (govoo_shares)
- **Given** a share class with `total_authorised = 1000`,
- **When** 600 shares are allotted to Partner A and 400 to Partner B, then Partner A transfers 200
  to Partner C and the transfer is registered,
- **Then** holdings recompute to A=400 (40%), B=400 (40%), C=200 (20%), summing to 100%, and the
  Register of Members reflects Partner C as newly entered.
- Maps to: FR-SHARE-001..004, FR-SEC-002, TC-SHARE-001..003.

## AC-03 — Beneficial ownership register remains provisional until confirmed (govoo_secretarial,
govoo_rw)
- **Given** `nature_of_control` thresholds are unconfirmed (`[CONFIRM]`),
- **When** a beneficial-owner record is created and viewed by any role,
- **Then** the UI/report clearly marks the control-category data as provisional and does not state a
  specific percentage as legally authoritative.
- Maps to: FR-SEC-003, BR-SEC-STAT-003, TC-SEC-003.

## AC-04 — Compliance instance generation respects unconfirmed deadlines (govoo_compliance,
govoo_rw)
- **Given** the Rwanda provisional deadline templates are seeded but not confirmed,
- **When** the compliance cron runs,
- **Then** no instance is generated from an unconfirmed template (because it is `active = False`),
  and once an administrator explicitly activates a confirmed template, subsequent cron runs
  generate instances correctly per its `basis`.
- Maps to: FR-COMP-001..002, FR-RW-003, BR-COMP-001, TC-COMP-001..003.

## AC-05 — Multi-company isolation holds across every governance model (security, cross-cutting)
- **Given** two companies (Company X, Company Y) in one database, each with their own directors,
  shareholders, meetings, and registers,
- **When** a user with access only to Company X attempts to read, list, or directly navigate
  (by ID/URL) to any Company Y governance record,
- **Then** access is denied for every model in `data-model/entities.md`, including via portal
  access-token misuse attempts.
- Maps to: BR-SEC-001, BR-SEC-006, TC-SEC-001..002.

## AC-06 — Separation of duties holds for voting (govoo_board, security)
- **Given** a Board Administrator user with no director/shareholder appointment,
- **When** they attempt to cast a `govoo.vote` on any resolution,
- **Then** the action is denied regardless of their configuration privileges.
- Maps to: BR-SEC-004, BR-BOARD-006, TC-SEC-004.

## AC-07 — Portal record-rule enforcement, not menu-hiding (portal, security)
- **Given** a Director Portal user belonging only to Committee A,
- **When** they attempt to open a Committee B meeting by direct portal URL (with a guessed or
  reused ID),
- **Then** access is denied at the record-rule/token level, not merely absent from their menu.
- Maps to: FR-PORTAL-001, FR-PORTAL-003, BR-SEC-002, BR-SEC-006, TC-SEC-005.

## AC-08 — Register append-only ledger cannot be altered (govoo_secretarial)
- **Given** an existing `govoo.register.entry`,
- **When** any user, including Board Administrator, attempts to edit or delete it via ORM, API, or
  UI,
- **Then** the operation is rejected in all cases.
- Maps to: FR-SEC-005, BR-SEC-STAT-005, TC-SEC-006.

## AC-09 — Enterprise feature graceful degradation (architecture, integrations)
- **Given** a deployment on Odoo Community (Documents/Sign/Dashboards not installed),
- **When** a user triggers a workflow that would normally use Documents (board pack storage) or
  Sign (minutes/resolution signing),
- **Then** the workflow completes using the Community fallback (`ir.attachment`, manual
  signed-copy upload) without raising an unhandled error.
- Maps to: `architecture/technology-standards.md` §8, `integrations/`, TC-BASE-005.

## AC-10 — Evaluation confidentiality holds under aggregation (govoo_evaluation)
- **Given** a closed evaluation campaign with 6 participant responses,
- **When** a participant (not Secretary/Admin) views the campaign results,
- **Then** they see only aggregated scores, never another individual's raw response.
- Maps to: FR-EVAL-002, BR-EVAL-001, TC-EVAL-002.
