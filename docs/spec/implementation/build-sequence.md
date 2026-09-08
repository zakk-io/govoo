# Build Sequence

Source: §12 of the source spec (baseline build order), expanded per the master prompt's request
for objectives/prerequisites/deliverables/dependencies/tests/exit-criteria per phase.

## Baseline sequence (source, verbatim order)
```
1. govoo_base
2. govoo_secretarial
3. govoo_shares
4. govoo_board
5. govoo_compliance
6. govoo_rw
7. govoo_evaluation
8. Portal + dashboard
9. Optional accounting / EBM
```
Steps 1-4 are the **board/register MVP**. Steps 5-6 are **compliance/localization**. Step 8 is
**external-user capability**. (Source's own phase grouping, restated.)

## Phase 1 — MVP: govoo_base → govoo_secretarial → govoo_shares → govoo_board
| | |
| --- | --- |
| **Objective** | A working internal governance core: people/roles, statutory registers, cap table, and full meeting/resolution/voting lifecycle, usable by internal Secretary/Admin/Auditor roles. |
| **Prerequisites** | Odoo version/edition confirmed (`decisions/open-decisions.md` item 1); dev environment available. |
| **Deliverables** | `govoo_base`, `govoo_secretarial`, `govoo_shares`, `govoo_board` installed and passing tests, in that dependency order. |
| **Dependencies** | Each module depends on the prior per `architecture/dependency-graph.md` — do not start `govoo_shares` before `govoo_secretarial`'s registers exist, since the member register consumes share holdings. |
| **Tests** | `TC-BASE-*`, `TC-SEC-STAT-*`, `TC-SHARE-*`, `TC-BOARD-*`, `TC-WF-BOARD-*`, `TC-WF-SHARE-*`, `TC-ACC-001`, `TC-ACC-002`, `TC-ACC-005` through `TC-ACC-008` (security/isolation must hold from the start, not bolted on later). |
| **Exit criteria** | Definition of Done (`implementation/module-checklists.md`) met for all four modules; AC-01, AC-02, AC-05..08 pass. |

## Phase 2 — Compliance & localization: govoo_compliance → govoo_rw
| | |
| --- | --- |
| **Objective** | Statutory obligation tracking with reminders, and Rwanda-specific configuration/localization layered on top of the MVP core. |
| **Prerequisites** | Phase 1 complete (govoo_rw depends on govoo_secretarial/govoo_shares/govoo_board/govoo_compliance per `architecture/dependency-graph.md`). |
| **Deliverables** | `govoo_compliance` installed and passing tests; `govoo_rw` installed with all Rwanda-specific obligation templates seeded but `active = False` pending advisor confirmation. |
| **Dependencies** | `govoo_compliance` needs only `govoo_base`, so it can technically start in parallel with late Phase 1 work, but `govoo_rw` cannot start until `govoo_compliance` (and the rest of Phase 1) is done. |
| **Tests** | `TC-COMP-*`, `TC-RW-*`, `TC-WF-COMP-001`, `TC-ACC-003`, `TC-ACC-004`. |
| **Exit criteria** | Definition of Done met for both modules; **no** Rwanda-seeded legal/tax value is `active = True` without a corresponding `decisions/confirmed-decisions.md` entry. |

## Phase 3 — Evaluation (parallelizable with Phase 2)
| | |
| --- | --- |
| **Objective** | Board/committee performance evaluation capability. |
| **Prerequisites** | `govoo_base` only. |
| **Deliverables** | `govoo_evaluation` installed and passing tests. |
| **Dependencies** | None beyond `govoo_base` — may be built any time after Phase 1's `govoo_base` step, in parallel with Phase 2. |
| **Tests** | `TC-EVAL-*`, `TC-ACC-010`. |
| **Exit criteria** | Definition of Done met; TC-ACC-010 (confidentiality) passes. |

## Phase 4 — External-user capability: Portal + Dashboard
| | |
| --- | --- |
| **Objective** | Director and shareholder self-service, plus the aggregated internal dashboard. |
| **Prerequisites** | Phases 1-3 complete (Portal depends on all custom modules per `architecture/dependency-graph.md`). |
| **Deliverables** | Portal controllers/views (per `modules/portal.md`) and dashboard aggregation layer, installed and passing tests. |
| **Dependencies** | All prior modules. |
| **Tests** | `TC-SEC-005`, `TC-SEC-005b`, `TC-WF-PORTAL-*`, `TC-ACC-007`. |
| **Exit criteria** | Definition of Done met; AC-07 passes; pre-go-live checklist (`devops/environments.md` §4) started. |

## Phase 5 — Optional: govoo_rw_accounting / govoo_rw_ebm
| | |
| --- | --- |
| **Objective** | Tax/accounting and e-invoicing capability, **only if the client needs it**. |
| **Prerequisites** | Phase 2 complete (`govoo_rw`); explicit client requirement for accounting/EBM functionality. |
| **Deliverables** | `govoo_rw_accounting` and/or `govoo_rw_ebm`, installed and passing tests, without being required by any prior phase. |
| **Dependencies** | `govoo_rw` (and, for EBM, `govoo_rw_accounting`). |
| **Tests** | Module-specific tests plus the CI boundary check in `devops/ci-cd.md` §1 step 5 (governance core must still install/pass without these). |
| **Exit criteria** | Definition of Done met; boundary check passes. |

## Recommended first implementation
**`govoo_base`.** It is the root of the dependency graph and every other module's access rules
reference the groups it defines.
