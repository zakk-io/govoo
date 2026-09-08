# Testing Strategy

Source: §9 ("Tests" standard), §11 (Definition of Done) of the source spec.

## 1. Test levels
| Level | Scope | Framework | Detail file |
| --- | --- | --- | --- |
| Unit | Models, methods, computed fields, constraints, single module | Odoo `TransactionCase` | `testing/unit-tests.md` |
| Integration | Module interactions (e.g. `govoo_shares` → `govoo_board` vote weighting) | Odoo `TransactionCase`, multi-module install | (covered within `unit-tests.md` per affected module; no separate file needed at this scale — see note) |
| Workflow (end-to-end) | Full lifecycle across states, e.g. meeting → minutes → resolution → vote | Odoo `TransactionCase` / `HttpCase` where portal is involved | `testing/workflow-tests.md` |
| Security | Cross-company isolation, portal permissions, sensitive fields, auditor access, separation of duties | Odoo `TransactionCase` with multiple test users/groups | `testing/security-tests.md` |
| Regression | Critical governance workflows re-run on every change | Same suite as unit/workflow, run in CI on every PR | `devops/ci-cd.md` |
| Acceptance | Business-level Given/When/Then scenarios | Maps to `requirements/acceptance-criteria.md` | `testing/acceptance-tests.md` |

**Note on integration tests:** the source does not call for a separate "integration test" file
distinct from unit tests; cross-module behavior (e.g. vote weight sourced from `govoo_shares`) is
tested within the owning module's `tests/` directory as part of its unit-test suite, using the
dependency module's models directly (since Odoo `TransactionCase` naturally exercises the full
installed dependency graph). This avoids an artificial split the source doesn't ask for.

## 2. Test ID scheme
`TC-<AREA>-<NNN>`, stable once assigned, referenced from `requirements/traceability.md` and from
`implementation/module-checklists.md`. Areas: `BASE`, `SEC` (base security), `SEC-STAT` (statutory
registers), `SHARE`, `BOARD`, `COMP`, `RW`, `EVAL`.

## 3. Coverage bar (source §11, Definition of Done criterion 6)
> "Unit tests pass for models/business logic."

Every module's `tests/` directory must, at minimum, cover:
- every constraint in `data-model/constraints.md` for that module's models,
- every state transition in `data-model/state-machines.md` for that module's models,
- every computed field in `data-model/computed-fields.md` for that module's models,
- every security/record-rule restriction in `security/` that touches that module's models.

## 4. What "Done" testing looks like per module
See `implementation/module-checklists.md` for the per-module checklist, which references the exact
`TC-*` IDs a module must pass before being marked complete.

## 5. Non-functional testing (source §10.2, §10.4)
- Penetration test before go-live (external, not part of the automated suite — tracked in
  `devops/environments.md`).
- Backup restore test (see `devops/backup-recovery.md`) — "a backup is only valid if tested"
  (BR-NFR-002).

## 6. What NOT to test (avoid over-engineering, source §25)
- Do not write tests asserting specific unconfirmed legal values (e.g. a specific tax rate or
  filing deadline) as if they were correct — such tests would themselves encode an unverified
  `[CONFIRM]` item as fact. Instead, test that unconfirmed obligations remain `active = False`
  (TC-RW-003) and that the *mechanism* (cron, computation) is correct given arbitrary/example
  configuration data.
