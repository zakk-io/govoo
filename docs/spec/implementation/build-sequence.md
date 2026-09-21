# Build Sequence

Source: §12 of the source spec (baseline build order), expanded per the master prompt's request
for objectives/prerequisites/deliverables/dependencies/tests/exit-criteria per phase.

## Baseline sequence (source, verbatim order, extended)
```
1. govoo_base
2. govoo_secretarial
3. govoo_shares
4. govoo_board
5. govoo_compliance
6. govoo_contracts        (new — addendum, depends on govoo_base, govoo_compliance, govoo_board)
7. govoo_rw
8. govoo_evaluation
9. Portal + dashboard
10. Optional accounting / EBM
```
Steps 1-4 are the **board/register MVP**. Steps 5-6 are **compliance/localization**, now including
`govoo_contracts` as step 6 per the addendum's own build sequence (§8: it depends on `govoo_base`,
`govoo_compliance`, and `govoo_board`, and must therefore land after all three — step 5 is the
earliest point that dependency set is satisfied). `govoo_rw`, `govoo_evaluation`, and Portal are
renumbered 7-9 accordingly; nothing about their own content or dependencies changes, only their
position in this list. Step 9 is **external-user capability**. (Source's own phase grouping,
restated, with the addendum module inserted per its own stated dependencies rather than appended at
the end.)

The addendum's build sequence (§8) also lists two out-of-scope steps — `govoo_ai` (its own step 1)
and "Contract intelligence" (its own step 3, after both `govoo_ai` and `govoo_contracts` are
stable) — neither of which is specced in this repository; see
`integrations/future-integrations.md` for why they are tracked but not built here.

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

## Phase 2b — Contract Management: govoo_contracts (addendum, inserted after govoo_compliance)
| | |
| --- | --- |
| **Objective** | Contract register, template/clause library, approval routing linked to board approval and delegation-of-authority, related-party conflict checks, e-signature execution, and obligation/milestone/renewal tracking. |
| **Prerequisites** | `govoo_base` (groups, company scoping), `govoo_compliance` (reused reminder engine), and `govoo_board` (resolution linkage for the board-approval gate) all installed and passing tests. |
| **Deliverables** | `govoo_contracts` installed and passing tests, per `modules/govoo_contracts.md` and `workflows/contracts.md`. |
| **Dependencies** | Cannot start before `govoo_board` (step 4) and `govoo_compliance` (step 5) are both done — this is later than the addendum's own minimal dependency set would technically allow if only `govoo_base` were required, because the board-approval gate (BR-CM-001) and reminder reuse (BR-CM-006) are core, not optional, features of this module. |
| **Tests** | `TC-CM-*`, `TC-WF-CM-001`, `TC-SEC-010..011`, `TC-ACC-011`, `TC-ACC-012`. |
| **Exit criteria** | Definition of Done (`implementation/module-checklists.md`) met; AC-11, AC-12 pass; CM-F15 (financial linkage) and CM-F19/F20 (AI) remain off/unbuilt per their `[OPTIONAL]`/out-of-scope status — their absence must not block this module's own DoD. |

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
| **Prerequisites** | Phases 1-3 and 2b complete (Portal depends on all custom modules, including `govoo_contracts`, per `architecture/dependency-graph.md`). |
| **Deliverables** | Portal controllers/views (per `modules/portal.md`) and dashboard aggregation layer, installed and passing tests — including the Contract Viewer Portal (`ui/portal-ui.md` §2b) and contract dashboard (`ui/dashboards.md` §4b). |
| **Dependencies** | All prior modules, including `govoo_contracts`. |
| **Tests** | `TC-SEC-005`, `TC-SEC-005b`, `TC-SEC-010`, `TC-WF-PORTAL-*`, `TC-ACC-007`, `TC-ACC-012`. |
| **Exit criteria** | Definition of Done met; AC-07 and AC-12 pass; pre-go-live checklist (`devops/environments.md` §4) started. |

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
