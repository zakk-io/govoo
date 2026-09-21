# Traceability Matrix

Maps: **Source requirement (§ in `Govoo_Technical_Specification.md`) → Engineering requirement
(FR-*) → Module → Model(s) → Workflow spec → UI spec → Test(s) (TC-*)**.

Use this file to answer "have I implemented every requirement from the original specification?"
before marking a module Done (`implementation/module-checklists.md`).

| Source § | FR ID | Module | Model(s) | Workflow spec | UI spec | Test(s) |
| --- | --- | --- | --- | --- | --- | --- |
| §7.1.1 | FR-BASE-001 | govoo_base | `res.partner` (ext.) | — | `ui/views.md` | TC-BASE-001 |
| §7.1.2 | FR-BASE-002 | govoo_base | `res.company` (ext.) | — | `ui/views.md` | TC-BASE-002 |
| §7.1.3 | FR-BASE-003 | govoo_base | `govoo.appointment` | `workflows/appointments.md` | `ui/views.md` | TC-BASE-003 |
| §7.1.4 | FR-BASE-004 | govoo_base | `govoo.committee` | `workflows/committees.md` | `ui/views.md` | TC-BASE-004 |
| §6.1 | FR-BASE-005 | govoo_base | `res.groups` (data) | — | — | TC-SEC-001 |
| §7.2.1 | FR-SEC-001 | govoo_secretarial | `govoo.register.director` | `workflows/statutory-registers.md` | `ui/views.md` | TC-SEC-STAT-001 |
| §7.2.2 | FR-SEC-002 | govoo_secretarial | `govoo.register.member` | `workflows/statutory-registers.md` | `ui/views.md` | TC-SEC-STAT-002 |
| §7.2.3 | FR-SEC-003 | govoo_secretarial | `govoo.register.beneficial.owner` | `workflows/statutory-registers.md` | `ui/views.md` | TC-SEC-STAT-003 |
| §7.2.4 | FR-SEC-004 | govoo_secretarial | `govoo.register.charge` | `workflows/statutory-registers.md` | `ui/views.md` | TC-SEC-STAT-004 |
| §7.2.5 | FR-SEC-005 | govoo_secretarial | `govoo.register.entry` | `workflows/statutory-registers.md` | `ui/views.md` | TC-SEC-STAT-005 |
| §7.3.1 | FR-SHARE-001 | govoo_shares | `govoo.share.class` | `workflows/share-management.md` | `ui/views.md` | TC-SHARE-001 |
| §7.3.2 | FR-SHARE-002 | govoo_shares | `govoo.share.allotment` | `workflows/share-management.md` | `ui/views.md` | TC-SHARE-002 |
| §7.3.3 | FR-SHARE-003 | govoo_shares | `govoo.share.transfer` | `workflows/share-management.md` | `ui/views.md` | TC-SHARE-003 |
| §7.3.4 | FR-SHARE-004 | govoo_shares | `govoo.share.holding` | `workflows/share-management.md` | `ui/dashboards.md` | TC-SHARE-004 |
| §7.3.5 | FR-SHARE-005 | govoo_shares | `account.move` hook | `workflows/share-management.md` | — | TC-SHARE-005 |
| §7.4.1 | FR-BOARD-001 | govoo_board | `govoo.meeting` | `workflows/meetings.md` | `ui/views.md` | TC-BOARD-001 |
| §7.4.2 | FR-BOARD-002 | govoo_board | `govoo.agenda.item` | `workflows/meetings.md` | `ui/views.md` | TC-BOARD-002 |
| §7.4.3 | FR-BOARD-003 | govoo_board | `govoo.board.pack` | `workflows/board-packs.md` | `ui/views.md` | TC-BOARD-003 |
| §7.4.4 | FR-BOARD-004 | govoo_board | `govoo.minutes` | `workflows/minutes.md` | `ui/views.md` | TC-BOARD-004 |
| §7.4.5 | FR-BOARD-005 | govoo_board | `govoo.resolution` | `workflows/resolutions.md` | `ui/views.md` | TC-BOARD-005 |
| §7.4.6 | FR-BOARD-006 | govoo_board | `govoo.vote` | `workflows/voting.md` | `ui/views.md` | TC-BOARD-006 |
| §7.5.1 | FR-COMP-001 | govoo_compliance | `govoo.compliance.obligation` | `workflows/compliance.md` | `ui/views.md` | TC-COMP-001 |
| §7.5.2 | FR-COMP-002 | govoo_compliance | `govoo.compliance.instance` | `workflows/compliance.md` | `ui/dashboards.md` | TC-COMP-002 |
| §7.5.3 | FR-COMP-003 | govoo_compliance | cron + `mail.activity` | `workflows/compliance.md` | `ui/dashboards.md` | TC-COMP-003 |
| §7.5.4 | FR-COMP-004 | govoo_compliance | `govoo.compliance.instance` (export) | `workflows/compliance.md` | `ui/views.md` | TC-COMP-004 |
| §8.1 | FR-RW-001 | govoo_rw | config data | — | — | TC-RW-001 |
| §8.2 | FR-RW-002 | govoo_rw | retention config, disposal job | `workflows/compliance.md` | — | TC-RW-002 |
| §8.3 | FR-RW-003 | govoo_rw | `govoo.compliance.obligation` (seed data) | `workflows/compliance.md` | — | TC-RW-003 |
| §8.5 | FR-RW-004 | govoo_rw | checklist model | `workflows/compliance.md` | `ui/views.md` | TC-RW-004 |
| §7.6.1 | FR-EVAL-001 | govoo_evaluation | `govoo.evaluation.campaign` | — | `ui/views.md` | TC-EVAL-001 |
| §7.6.2 | FR-EVAL-002 | govoo_evaluation | `govoo.evaluation.result` | — | `ui/dashboards.md` | TC-EVAL-002 |
| §6.2, §6.3 | FR-PORTAL-001 | Portal | (record rules over govoo_board models) | `workflows/meetings.md`, `workflows/voting.md` | `ui/portal-ui.md` | TC-SEC-005 |
| §6.2 | FR-PORTAL-002 | Portal | (record rules over govoo_shares/govoo_board) | `workflows/share-management.md`, `workflows/voting.md` | `ui/portal-ui.md` | TC-SEC-005 |
| §6.3 | FR-PORTAL-003 | Portal | `portal.mixin` (all portal-exposed models) | — | `ui/portal-ui.md` | TC-SEC-005, TC-SEC-006 |

## Contract Management addendum (`docs/contract_management_clagov_contracts.md`, hereafter "the
addendum" — not a source-spec §, tracked separately since it post-dates the original baseline)
| Addendum § | FR ID | Module | Model(s) | Workflow spec | UI spec | Test(s) |
| --- | --- | --- | --- | --- | --- | --- |
| §3.2 CM-F01 | FR-CM-01 | govoo_contracts | `govoo.contract` | `workflows/contracts.md` | `ui/views.md` | TC-CM-001 |
| §3.2 CM-F02 | FR-CM-02 | govoo_contracts | `govoo.contract.type` | `workflows/contracts.md` | `ui/views.md` | TC-CM-009 |
| §3.2 CM-F03 | FR-CM-03 | govoo_contracts | `govoo.contract.template` | `workflows/contracts.md` | `ui/views.md` | TC-CM-009 |
| §3.2 CM-F04 | FR-CM-04 | govoo_contracts | `govoo.contract.clause` | `workflows/contracts.md` | `ui/views.md` | TC-CM-009 |
| §3.2 CM-F07 | FR-CM-07 | govoo_contracts | `govoo.contract` (state gate) | `workflows/contracts.md` | `ui/views.md` | TC-CM-001 |
| §3.2 CM-F08 | FR-CM-08 | govoo_contracts | `govoo.contract` (approval routing) | `workflows/contracts.md` | `ui/views.md` | TC-CM-002 |
| §3.2 CM-F09 | FR-CM-09 | govoo_contracts | `govoo.contract` (`is_related_party`) | `workflows/contracts.md` | `ui/views.md` | TC-CM-003 |
| §3.2 CM-F10 | FR-CM-10 | govoo_contracts | `govoo.contract` (`sign_request_id`) | `workflows/contracts.md` | `integrations/sign.md` | TC-CM-005 |
| §3.2 CM-F11 | FR-CM-11 | govoo_contracts | `govoo.contract.obligation`, `govoo.contract.milestone` | `workflows/contracts.md` | `ui/views.md` | TC-CM-006 |
| §3.2 CM-F12 | FR-CM-12 | govoo_contracts | `govoo.contract` (renewal/termination) | `workflows/contracts.md` | `ui/views.md` | TC-CM-010 |
| §3.2 CM-F15 | FR-CM-15 | govoo_contracts | `account.move` hook (optional) | `workflows/contracts.md` | — | TC-CM-008 |
| §3.2 CM-F16 | FR-CM-16 | govoo_contracts | (record rules over `govoo.contract`) | `workflows/contracts.md` | `ui/portal-ui.md` §2b | TC-CM-007, TC-SEC-010 |
| §3.2 CM-F17 | FR-CM-17 | govoo_contracts | `govoo.contract` (dashboard aggregation) | — | `ui/dashboards.md` §4b | — |
| §3.2 CM-F18 | FR-CM-18 | govoo_contracts | `govoo.contract.type.retention_years` | — | — | — |
| §3.2 CM-F19, CM-F20 | FR-CM-19, FR-CM-20 | *(out of scope — `govoo_ai`)* | — | — | — | — |

## Non-functional / open-decision traceability
| Source § | Item | Owning spec | Status |
| --- | --- | --- | --- |
| §13 item 1 | Odoo version / edition | `architecture/technology-standards.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 2 | In-Rwanda hosting / data residency | `devops/environments.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 3 | E-signature/e-voting legal validity | `modules/govoo_board.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 4 | Beneficial-ownership thresholds | `modules/govoo_secretarial.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 5 | Annual-return window, tax/RSSB rates | `modules/govoo_rw.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 6 | RDB/Irembo filing API | `modules/govoo_compliance.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 7 | GL posting policy | `modules/govoo_shares.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| §13 item 8 | RPO/RTO, backup location | `devops/backup-recovery.md`, `decisions/open-decisions.md` | `[CONFIRM]` |
| addendum §9 item 1 | AI provider/hosting/DPA | `integrations/future-integrations.md`, `decisions/open-decisions.md` (item 24) | `[CONFIRM]` |
| addendum §9 item 2 | Self-hosted-model necessity | `integrations/future-integrations.md`, `decisions/open-decisions.md` (item 25) | `[CONFIRM]` |
| addendum §9 item 3 | Contract e-signature legal validity (CM-F10) | `modules/govoo_contracts.md`, `integrations/sign.md`, `decisions/open-decisions.md` (item 26) | `[CONFIRM]` |
| addendum §9 item 4 | Board-approval thresholds/contract types (CM-F07) | `modules/govoo_contracts.md`, `decisions/open-decisions.md` (item 27) | `[CONFIRM]` |
| addendum §9 item 5 | Delegation-of-authority matrix (CM-F08) | `modules/govoo_contracts.md`, `decisions/open-decisions.md` (item 28) | `[CONFIRM]` |
| addendum §9 item 6 | AI token caps/pricing | `integrations/future-integrations.md`, `decisions/open-decisions.md` (item 29) | `[CONFIRM]` |

## How to keep this file current
Whenever a module is implemented, update the implicit "status" of each row (not tracked as a column
here to avoid this file going stale faster than the code — instead, track completion in
`implementation/module-checklists.md`, which references these same FR/model/test IDs). This file's
job is to guarantee **coverage**, not to duplicate a live project-tracking board.
