# AI Coding Agent Instructions

Source: master-prompt §19 requirements, grounded throughout in the source spec's own standards
(§9, §11). This file is the operating manual for any AI coding agent (Claude Code, Codex, or
similar) implementing Govoo from this spec repository.

## Before writing any code
1. Read `spec/README.md` in full.
2. Read `architecture/system-architecture.md`, `architecture/module-architecture.md`,
   `architecture/dependency-graph.md`, `architecture/technology-standards.md`.
3. Read this file in full.
4. Read `implementation/build-sequence.md` and confirm which module/phase is next.

## The ten operating rules
1. **Read the spec for the module you're about to build** — `modules/<name>.md` first, then the
   linked `data-model/`, `security/`, `workflows/`, `ui/`, `testing/`, `integrations/` sections it
   references. Do not start from memory of the source document; start from the module spec, which
   is already the decomposed, implementation-ready version.
2. **Read architecture specs before coding** — confirm the module's dependency chain
   (`architecture/dependency-graph.md`) is already built and passing before starting.
3. **Implement modules in dependency order** — per `implementation/build-sequence.md`. Do not build
   `govoo_shares` before `govoo_secretarial`, `govoo_board` before `govoo_shares`, or `govoo_rw`
   before steps 2-5. Parallelizable exceptions (`govoo_compliance`/`govoo_evaluation` after
   `govoo_base`) are noted explicitly in the build sequence — do not parallelize anything not
   marked as such.
4. **Never skip security requirements** — every model gets `ir.model.access.csv` entries and, where
   applicable, record rules, in the **same** unit of work that introduces the model. Reference
   `security/access-control.md` and `security/record-rules.md` for the exact matrix/domains — do
   not improvise a permission scheme.
5. **Never invent legal values** — any rate, date, threshold, or article number not explicitly
   given as confirmed in `data-model/constraints.md` §3 or `decisions/confirmed-decisions.md` is
   implemented as configurable data, `active=False`/disabled by default, never a Python literal.
   If you find yourself about to type a specific tax percentage or filing deadline into code,
   stop — check `decisions/open-decisions.md` first.
6. **Never implement unresolved `[CONFIRM]` items as authoritative** — a `[CONFIRM]` marker in any
   spec file means: build the mechanism, do not assert the value/decision. Where a UI would
   otherwise state something as fact, label it provisional (see FR-SEC-003, FR-RW-003 for the
   pattern).
7. **Write tests alongside implementation** — not after. Use the `TC-*` IDs in `testing/` as your
   test names/docstrings so they remain traceable. A model/method is not "done" until its
   corresponding `TC-*` tests exist and pass.
8. **Follow Odoo conventions** — module/model/field naming per
   `architecture/technology-standards.md` §2; file layout per the `modules/*.md` "Odoo technical
   structure" section for each module.
9. **Keep modules isolated and maintainable** — respect the "owns / must NOT own" boundaries stated
   at the top of every `modules/*.md` file. If an implementation need seems to require one module
   to own data listed as another module's, stop and re-read `architecture/module-architecture.md`
   §3 before proceeding — the boundary is deliberate.
10. **Respect Community/Enterprise feature flags** — every Documents/Sign/Dashboards/Approvals call
    is guarded per `architecture/technology-standards.md` §8 and the specific pattern in
    `integrations/documents.md`/`integrations/sign.md`. Test the Community fallback path
    explicitly (AC-09), don't just assume it works.
11. **Preserve multi-company isolation** — every transactional model gets `company_id` with
    `check_company=True` and the record rule from `security/record-rules.md` §1, no exceptions.
12. **Run relevant tests before considering a module complete** — the full `TC-*` set listed for
    that module in `implementation/module-checklists.md`, not a subset chosen for convenience.
13. **Compare implementation against the corresponding specification** — after implementing a
    model/workflow, re-read its `modules/*.md` entry and `requirements/traceability.md` row to
    confirm nothing was dropped or silently altered.
14. **Update implementation documentation when behavior changes** — if an implementation detail
    diverges from a spec file (e.g. a `[CONFIRM]` item gets resolved, or an `[ENGINEERING DETAIL]`
    decision is made a specific way), update the relevant spec file (and, if it resolves an open
    decision, `decisions/open-decisions.md` → `decisions/confirmed-decisions.md`) in the same
    change — the spec repository must not drift from the implementation it describes.

## The repeatable implementation loop (per model/workflow unit of work)
```
READ SPEC                    (modules/*.md + linked data-model/security/workflow/ui/test files)
    |
UNDERSTAND DEPENDENCIES      (architecture/dependency-graph.md — is everything this needs already built?)
    |
IMPLEMENT MODEL              (fields, relations, per data-model/entities.md + relationships.md)
    |
IMPLEMENT CONSTRAINTS        (data-model/constraints.md — validation, uniqueness, referential rules)
    |
IMPLEMENT SECURITY           (security/access-control.md, record-rules.md — same unit of work, not a follow-up PR)
    |
IMPLEMENT VIEWS              (ui/views.md, ui/navigation.md)
    |
IMPLEMENT WORKFLOW           (workflows/*.md — state machine per data-model/state-machines.md)
    |
IMPLEMENT REPORTS            (ui/views.md reports table, per-module report sections)
    |
WRITE TESTS                  (testing/*.md — use the exact TC-* IDs)
    |
RUN TESTS
    |
SECURITY CHECK                (testing/security-tests.md subset relevant to this model)
    |
SPEC COMPLIANCE CHECK         (requirements/traceability.md row — does this satisfy the source FR?)
    |
MARK TASK COMPLETE            (implementation/module-checklists.md checkbox)
```

## What "done" means for the whole project
All modules through `implementation/build-sequence.md` Phase 4 (Portal + Dashboard) complete their
`implementation/module-checklists.md` entries, all `requirements/traceability.md` rows are
satisfied, and `decisions/open-decisions.md` items have either been resolved (moved to
`decisions/confirmed-decisions.md`) or are explicitly and visibly still pending in a way the client
can see (never silently defaulted). Phase 5 (optional accounting/EBM) is built only if the client
requires it.

## If you are unsure
Prefer asking a clarifying question (or leaving an explicit `[CONFIRM]`/`[ENGINEERING DETAIL]` note
in code comments, matching the pattern already used throughout this spec repository) over guessing
and moving on. Guessing on a governance/compliance system produces legal risk, not just a bug.
