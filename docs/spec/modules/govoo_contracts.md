# Module: govoo_contracts

Source: `contract_management_clagov_contracts.md` v1.0 (hereafter "the addendum"), §3-§9. Naming
reconciled per the addendum's own Step 0 instruction: the addendum's `clagov_contracts`/
`clagov.contract.*` naming is translated to this repository's canonical `govoo_` / `govoo.`
convention throughout — `clagov_contracts` → `govoo_contracts`, `clagov.contract` → `govoo.contract`,
etc. No `clagov_*` identifier appears anywhere in this module's implementation.

Build order: **Step 6** (new — inserted after `govoo_compliance`; depends on `govoo_base`,
`govoo_compliance`, `govoo_board`). See `implementation/build-sequence.md` Phase 2b.

## Module overview
- **Purpose:** Governance-grade Contract Lifecycle Management (CLM). Its differentiator over a
  generic CLM tool is deep wiring into Govoo's own governance machinery: board approval,
  delegation-of-authority, related-party checks, and the compliance-calendar reminder engine
  (addendum §3.1).
- **Responsibility:** Contract register, template/clause library, approval routing with
  board-resolution and delegation-of-authority gating, related-party conflict checks, e-signature
  execution, key-date/obligation/milestone tracking, renewal/termination workflow, optional
  financial linkage.
- **Depends on (Odoo):** `base`, `mail`, `documents` (feature-flagged, contract versions/executed
  PDFs), `sign` (feature-flagged, execution).
- **Depends on (custom):** `govoo_base` (partners, appointments, security groups);
  `govoo_compliance` (key-date reminders feed the existing reminder engine, not a parallel one);
  `govoo_board` (`govoo.resolution` linkage for board-approval gating).
- **Owns:** `govoo.contract`, `govoo.contract.type`, `govoo.contract.template`,
  `govoo.contract.clause`, `govoo.contract.obligation`, `govoo.contract.milestone`.
- **Must NOT own:** board-resolution voting mechanics (owned by `govoo_board` — this module only
  *links to and reads* a resolution's `state`/`result`, never re-implements approval/voting);
  compliance-instance/reminder mechanics (owned by `govoo_compliance` — this module *creates
  instances against the existing obligation/reminder engine*, it does not build a second one);
  statutory register content or beneficial-ownership/related-party source data (owned by
  `govoo_secretarial`/`govoo_base` — this module *reads* that data to compute `is_related_party`,
  it is not the source of truth for who is related-party); GL posting logic (owned by `account`/
  the client's accounting configuration, behind a flag, off by default, same pattern as
  `govoo_shares` FR-SHARE-005).

## Odoo technical structure
```
govoo_contracts/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_base, govoo_compliance, govoo_board,
|                               #          documents (soft), sign (soft)
|-- models/
|   |-- __init__.py
|   |-- govoo_contract.py
|   |-- govoo_contract_type.py
|   |-- govoo_contract_template.py
|   |-- govoo_contract_clause.py
|   |-- govoo_contract_obligation.py
|   `-- govoo_contract_milestone.py
|-- views/
|-- security/
|   |-- ir.model.access.csv
|   `-- govoo_contracts_security.xml   # Contract Viewer (Portal): own-contract only
|-- data/
|   `-- (seed: default contract types, e.g. NDA/service/lease/related-party — approval_threshold
|        and requires_board_approval left [CONFIRM], same inactive-until-confirmed discipline as
|        govoo_rw obligation templates)
|-- report/
|   `-- (QWeb: generated contract document from template, register extract)
|-- tests/
|   |-- test_contract.py            # state machine, is_related_party computation
|   |-- test_contract_approval.py   # board-approval gating, delegation-of-authority enforcement
|   |-- test_contract_obligation.py # obligation → compliance-reminder integration
|   `-- test_contract_portal.py     # Contract Viewer Portal isolation
`-- i18n/
```

## Models

### `govoo.contract` (inherits `mail.thread`, `mail.activity.mixin`)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | contract title |
| `reference` | Char | No | contract number; `[ENGINEERING DETAIL — recommend an `ir.sequence` per company, not itemized in the addendum's field table]` |
| `company_id` | Many2one `res.company` | Yes | managing entity |
| `counterparty_id` | Many2one `res.partner` | Yes | other party |
| `contract_type_id` | Many2one `govoo.contract.type` | Yes | |
| `value` | Monetary | No | contract value |
| `currency_id` | Many2one `res.currency` | Yes | RWF default via `govoo_rw`, 0-decimal convention (BR-RW-001) |
| `date_start` | Date | No | term start |
| `date_end` | Date | No | term end |
| `renewal_type` | Selection (`none`/`manual`/`auto`) | Yes | default `none`; `auto` = evergreen (CM-F12) |
| `notice_period_days` | Integer | No | drives renewal/notice alerts (CM-F12) |
| `resolution_id` | Many2one `govoo.resolution` | No | board approval linkage — **read-only reference into `govoo_board`, never a duplicate approval mechanism** (CM-F07) |
| `is_related_party` | Boolean | — (computed) | CM-F09; computed against `govoo_base`/`govoo_secretarial` interests data, never independently entered |
| `sign_request_id` | Many2one `sign.request` | No | Feature-flagged; execution (CM-F10); gated on the same e-signature legal-validity `[CONFIRM]` as `govoo_board` (BR-BOARD-008, BR-CM-005) |
| `document_ids` | Many2many `documents.document` | No | draft/executed versions (CM-F03); feature-flagged, `ir.attachment` fallback |
| `obligation_ids` | One2many `govoo.contract.obligation` | No | |
| `milestone_ids` | One2many `govoo.contract.milestone` | No | |
| `state` | Selection (`draft`/`in_approval`/`approved`/`executed`/`active`/`expired`/`terminated`) | Yes | default `draft` |
- **Constraints:** `date_end >= date_start` when both set; `value >= 0` when set.
- **Computed fields:** `is_related_party` — see `data-model/computed-fields.md`.
- **State transitions:** see `data-model/state-machines.md` (`govoo.contract.state`),
  `workflows/contracts.md`. Board-approval gating (BR-CM-001), delegation-of-authority enforcement
  (BR-CM-002), and related-party conflict declaration (BR-CM-003) are all enforced at the
  `in_approval → approved` transition — see business rules below.
- **Access requirements:** Contract Manager RWCD; Contract Approver read + the approval action only
  (cannot author); Contract Viewer (Portal) reads only contracts where they are the counterparty or
  a named approver (BR-CM-007); Auditor global read, no write.
- Source: addendum §3.2 CM-F01/F06/F07/F08/F09/F10, §3.3.

### `govoo.contract.type`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | e.g. officer/service agreement, NDA, shareholder agreement, related-party, lease, supplier, engagement letter, SLA (CM-F02) |
| `company_id` | Many2one `res.company` | No | `[ENGINEERING DETAIL — the addendum does not state whether contract types are global or per-company; recommend company-scoped for consistency with every other config model, nullable if a shared/global catalogue is later preferred — CONFIRM]` |
| `approval_threshold` | Monetary | No | CM-F07 threshold above which board approval is required — **value itself is `[CONFIRM]`, addendum §9 item 4; never hard-coded** |
| `requires_board_approval` | Boolean | No | default `False`; which types require it is `[CONFIRM]`, addendum §9 item 4 |
| `mandatory_clause_ids` | Many2many `govoo.contract.clause` | No | clauses that must be present for this type (CM-F04) |
| `retention_years` | Integer | No | aligns to `govoo_rw` retention configuration (CM-F18) — computed/consumed the same way `govoo.minutes.retention_until` reads `govoo_rw` config, never a literal here |
- **Inheritance:** `mail.thread`.
- Source: addendum §3.2 CM-F02, §3.4.

### `govoo.contract.template`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | |
| `contract_type_id` | Many2one `govoo.contract.type` | No | |
| `body` | Html | No | template body with merge fields from partner/company data (CM-F04) |
| `language` | Selection (`en`/`fr`/`rw`) | Yes | CM-F05 — English/French/Kinyarwanda, matching `govoo_rw`'s language set |
- **Inheritance:** `mail.thread`.
- **Methods/business behavior:** `action_generate_contract()` produces a `govoo.contract` (QWeb) from
  the template, merging partner/company field values — reuses the same QWeb-report pattern already
  established in `govoo_board`/`govoo_compliance`, not a new templating engine.
- Source: addendum §3.2 CM-F04/CM-F05.

### `govoo.contract.clause`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | |
| `body` | Html | No | |
| `is_mandatory` | Boolean | No | default `False` |
| `clause_category` | Selection or Char | No | standard vs optional grouping (addendum §3.3); `[ENGINEERING DETAIL — addendum states "standard vs optional, mandatory flag" without a fixed vocabulary; a free Selection with `standard`/`optional` values satisfies this]` |
- **Inheritance:** `mail.thread`.
- Source: addendum §3.2 CM-F04, §3.3.

### `govoo.contract.obligation`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `contract_id` | Many2one `govoo.contract` | Yes | |
| `name` | Char | Yes | obligation/milestone description |
| `due_date` | Date | Yes | → creates a `govoo_compliance`-style reminder (CM-F11, BR-CM-006) |
| `responsible_id` | Many2one `res.users` | No | |
| `amount` | Monetary | No | payment schedule (optional) |
| `state` | Selection (`open`/`done`/`overdue`/`waived`) | Yes | default `open` |
- **Inheritance:** `mail.thread`.
- **State transitions:** mirrors `govoo.compliance.instance.state`'s `late`/`waived` pattern
  (`data-model/state-machines.md`) rather than inventing a new vocabulary.
- **Side effects:** `due_date` feeds staged reminders via the *existing* `govoo_compliance` engine —
  see `workflows/contracts.md` and BR-CM-006. This model does **not** own its own cron/reminder
  logic.
- Source: addendum §3.2 CM-F13, §3.3.

### `govoo.contract.milestone`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `contract_id` | Many2one `govoo.contract` | Yes | |
| `name` | Char | Yes | deliverable/payment milestone |
| `date` | Date | No | |
| `value` | Monetary | No | |
| `state` | Selection (`pending`/`delivered`/`paid`) | Yes | default `pending`; `[ENGINEERING DETAIL — addendum states "deliverable/payment milestone (date, value, status)" without itemizing the status vocabulary]` |
- **Inheritance:** `mail.thread`.
- Source: addendum §3.3.

## Governance integration (the differentiator — addendum §3.4)
- **Board-approval linkage (CM-F07):** contracts above a configured threshold, or of a type flagged
  `requires_board_approval`, link to a `govoo.resolution`; execution is blocked until that
  resolution reaches `state = 'passed'` (BR-CM-001). Thresholds/types are `[CONFIRM]`
  (addendum §9 item 4) — never hard-coded, represented as `govoo.contract.type` config data,
  inactive/zero until confirmed.
- **Delegation-of-authority matrix (CM-F08):** execution is blocked outside a board-approved
  signing-authority matrix (who may sign what type/value) — BR-CM-002. The matrix itself is
  `[CONFIRM]` (addendum §9 item 5); represented as configurable data.
- **Related-party check (CM-F09):** the counterparty is cross-referenced against the
  directors'-interests / related-party data already modeled in `govoo_base`/`govoo_secretarial`;
  a match sets `is_related_party = True` and forces a conflict-of-interest declaration before
  approval can proceed (BR-CM-003) — the same declared-interest philosophy as `govoo.vote.is_conflicted`
  (BR-BOARD-007), applied to contracts instead of votes.
- **Key-date tracking (CM-F11):** `govoo.contract.obligation.due_date` and contract
  renewal/notice dates feed the *existing* `govoo_compliance` reminder engine (BR-CM-006) — this
  module must not build a second, parallel reminder mechanism.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_contracts` section (not yet built; see the
addendum's own §7, restated per this repository's 10-point criteria).

## Reports (QWeb)
Generated contract document (from template + merge fields), contract register extract.

## Tests
- TC-CM-001..003: model/state-machine/computed-field coverage.
- TC-CM-004/005: board-approval gating and delegation-of-authority enforcement.
- TC-CM-006: related-party conflict declaration forced before approval.
- TC-CM-007: write-once executed document.
- TC-CM-008: obligation `due_date` produces a reminder via the existing `govoo_compliance` engine.
- TC-CM-009/010: Contract Viewer (Portal) isolation.
See `testing/unit-tests.md` for the full table.

## Out of scope for this module (addressed elsewhere or not yet specced)
- **CM-F19/CM-F20 (AI extraction / summarization / Q&A):** the addendum marks these `Could` priority
  and states they depend on a separate `govoo_ai` module (build order §8, step 3: "Contract
  intelligence ... once both are stable"). `govoo_ai` is **not specced by this document** — this
  module's models (`document_ids`, `obligation_ids`) are shaped so a future `govoo_ai` integration
  can consume them, but no AI-specific field, security group, or workflow is introduced here.
  See `integrations/future-integrations.md`.
- **Financial linkage (CM-F15):** optional, behind a flag, off by default — see BR-CM-008,
  same pattern as `govoo_shares` FR-SHARE-005/BR-SHARE-004.
