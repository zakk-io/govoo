# CI/CD

Source: §4 ("Testing: TransactionCase per module"), §9 ("Tests: every module ships tests/") of the
source spec — the source states the testing/version-control expectations; the specific CI pipeline
shape below is `[ENGINEERING DETAIL]` derived to satisfy those expectations, kept minimal per §25.

## 1. Pipeline stages (on every PR)
1. **Lint:** `flake8` / `pylint-odoo` against changed modules.
2. **Install:** spin up a clean Odoo instance and install the affected module(s) plus their
   declared dependency chain (`architecture/dependency-graph.md`).
3. **Unit + workflow + security tests:** run the module's `tests/` suite
   (`testing/unit-tests.md`, `testing/workflow-tests.md`, `testing/security-tests.md`).
4. **Acceptance tests:** run the relevant `TC-ACC-*` scenarios that touch the changed module(s)
   (`testing/acceptance-tests.md`).
5. **Boundary check `[RECOMMENDED]`:** install the governance core (`govoo_base` through
   `govoo_evaluation` + Portal) **without** `govoo_rw_accounting`/`govoo_rw_ebm` and confirm it
   still installs and passes tests (enforces the module-boundary rule in
   `modules/optional-integrations.md`).
6. **Hard-coded-value lint `[RECOMMENDED]`:** grep/lint check that fails the build if a percentage,
   currency literal, or date literal appears in `govoo_rw`, `govoo_compliance`, `govoo_contracts`
   (addendum — board-approval thresholds, delegation-of-authority limits, retention years, per
   FR-CM-07/08/18), or `govoo_rw_accounting` Python outside `tests/` (enforces
   `data-model/constraints.md` §3).

## 2. Branching / review
- Feature branches, PR review required before merge (source §4).
- No model may merge without its `ir.model.access.csv` entries and (where applicable) record rules
  in the same PR (source §9, `security/security-model.md` §5).

## 3. Version control
- Git; OCA module dependencies pinned by version/tag/commit, not tracking `main`
  (`architecture/technology-standards.md` §1).

## 4. Release cadence
`[ENGINEERING DETAIL — not specified in source]`. Recommend releasing per completed module
(`implementation/build-sequence.md` phase) rather than a fixed calendar cadence, so each release
maps cleanly to a Definition-of-Done milestone.
