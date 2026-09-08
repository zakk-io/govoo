# Govoo Engineering Specification Repository

## What Govoo is
Govoo is a multi-company, Odoo-based (19, Community + selected Enterprise apps) platform for corporate
governance, board management, statutory registers, share/cap-table management, and compliance
tracking, localized for Rwanda. It lets a company secretary, board, and shareholders run meetings,
resolutions, e-voting, statutory registers, and compliance deadlines from one system built on
`res.partner` / `res.company`, with secure external self-service via the Odoo portal.

## What this repository contains
This `spec/` tree decomposes the baseline document **`Govoo_Technical_Specification.md`** (v1.0,
August 2026 — hereafter **"the source spec"**) into implementation-ready, testable, traceable
engineering specifications, organized by concern (architecture, requirements, per-module design,
data model, security, workflows, UI, integrations, testing, devops, and open decisions), so that an
AI coding agent (Claude Code, Codex, or similar) can implement Govoo module-by-module without
repeatedly re-reading or re-interpreting the source document.

## Source of truth
- **The original `Govoo_Technical_Specification.md` is the authoritative product baseline.** It is not
  modified by this repository.
- Where this repository adds engineering detail not present in the source (naming conventions, test
  IDs, file layouts, matrices), that detail is **derived, non-authoritative elaboration**, clearly
  labelled `[RECOMMENDED]` or `[ENGINEERING DETAIL]`.
- Where the source marks something `[CONFIRM]`, this repository preserves that marker. **No
  `[CONFIRM]` item is converted into a definitive fact anywhere in this repository.** See
  `decisions/open-decisions.md`.
- Where the source is silent or ambiguous on an implementation detail, this repository marks it
  explicitly as `[CONFIRM]` and states what must be confirmed and by whom.

## Architecture overview (see `architecture/`)
Govoo is a **modular monolith on Odoo** — not microservices, not a bespoke backend. Every person is a
`res.partner`; every managed entity is a `res.company`. Custom modules extend Odoo rather than
replace it, per the source's "reuse before build" principle (§3.1, §25 of this repo's ground rules).

Custom module dependency stack:
```
govoo_base  →  govoo_secretarial  →  govoo_shares  →  govoo_board
     │                                                     ▲
     └────────────────────────────────────────────────────┘
govoo_base  →  govoo_compliance  →  govoo_rw
govoo_base  →  govoo_evaluation (wraps survey)
all of the above → Portal + Dashboard
(optional, separate) → govoo_rw_accounting, govoo_rw_ebm
```

## Where an AI coding agent should start
1. Read this file (`spec/README.md`) in full.
2. Read `architecture/system-architecture.md`, `architecture/module-architecture.md`,
   `architecture/dependency-graph.md`, `architecture/technology-standards.md`.
3. Read `implementation/ai-agent-instructions.md` — the operating loop for every module.
4. Read `implementation/build-sequence.md` to confirm which module to build next.
5. For the module being built, read: `modules/<module>.md`, the relevant files in `data-model/`,
   `security/`, `workflows/`, `ui/`, `testing/`, and any `integrations/` file it touches.
6. Cross-check `requirements/traceability.md` before marking any module complete.

**Recommended first implementation: `govoo_base`.**

## How specifications relate to implementation
Every functional requirement in `requirements/` has a stable ID (`FR-*`), every business rule in
`requirements/business-rules.md` has a stable ID (`BR-*`), and every test in `testing/` has a stable ID
(`TC-*`). `requirements/traceability.md` maps source requirement → engineering requirement → module →
model → workflow → UI → test, so completeness against the source spec is always checkable.

## Unresolved `[CONFIRM]` items (summary — full detail in `decisions/open-decisions.md`)
1. Odoo version (17 vs 18) and edition (Enterprise vs Community + OCA).
2. In-Rwanda / NCSA-authorized hosting for real personal data (data residency).
3. Legal validity of e-signature and electronic/written resolutions under Rwandan law and the
   client's articles of association.
4. Beneficial-ownership control thresholds and exact statutory register contents.
5. Exact annual-return filing window; CIT/VAT/PAYE/WHT/RSSB rates and statutory article numbers.
6. Whether RDB/Irembo exposes any public filing API.
7. GL posting policy for capital events (default: off).
8. RPO/RTO targets and backup location.

None of these may be hard-coded, pre-seeded as authoritative, or treated as resolved anywhere in
this repository or in the implementation. See `data-model/constraints.md` and `modules/govoo_rw.md`
for how each is represented as inactive/configurable data pending confirmation.

## Definition of Done
A module is **Done** only when it satisfies all ten criteria in the source spec §11, restated in
`implementation/module-checklists.md` and cross-referenced per module in each `modules/*.md` file.
In summary: models/fields/relations exist and migrate; required views exist; `ir.model.access.csv` +
record rules exist and are access-tested; `mail.thread` audit works; QWeb reports render; unit tests
pass; strings are translatable (fr/rw stubs present); no hard-coded legal/tax value; multi-company
isolation is verified; Enterprise integrations degrade gracefully on Community.

## How to use these specs during development
- Treat each `modules/*.md` file as the single work order for that module — it links out to the
  data-model, security, workflow, UI, and test detail needed to implement it.
- Do not implement a `[CONFIRM]` item as a hard-coded value. Implement it as configurable/inactive
  data per `data-model/constraints.md` and flag it in code comments as instructed in
  `architecture/technology-standards.md`.
- Follow the build order in `implementation/build-sequence.md`; do not start a module whose
  dependencies are incomplete.
- After implementing a module, run its checklist in `implementation/module-checklists.md` and update
  `requirements/traceability.md` status before moving to the next module.

> The specifications in this directory are derived from the baseline Govoo specification. The
> original specification remains authoritative where an engineering detail has not been further
> defined.
