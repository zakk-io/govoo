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

## How to keep this file current
Whenever a module is implemented, update the implicit "status" of each row (not tracked as a column
here to avoid this file going stale faster than the code — instead, track completion in
`implementation/module-checklists.md`, which references these same FR/model/test IDs). This file's
job is to guarantee **coverage**, not to duplicate a live project-tracking board.
