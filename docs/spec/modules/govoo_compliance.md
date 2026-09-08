# Module: govoo_compliance

Source: §3.2, §7.5 of the source spec. Build order: **Step 5** (depends on `govoo_base`).

## Module overview
- **Purpose:** Track statutory/regulatory obligations and fire reminders.
- **Responsibility:** Obligation catalogue, concrete due-item instances, cron-driven reminder/
  escalation engine, filing-pack export.
- **Depends on (Odoo):** `base`, `mail`.
- **Depends on (custom):** `govoo_base`.
- **Owns:** `govoo.compliance.obligation`, `govoo.compliance.instance`, the cron/reminder engine
  logic (`govoo.compliance.rule` — a mechanism, see note below), filing-pack export.
- **Must NOT own:** statutory register content (`govoo_secretarial`); Rwanda-specific deadline
  **values** (owned as data by `govoo_rw`, which seeds this module's obligation catalogue).

**Note on `govoo.compliance.rule`:** the source describes this as "Engine: `ir.cron` generates..." —
i.e. it is a scheduled-action/engine, not necessarily a persisted record model with its own table.
`[ENGINEERING DETAIL]` implement as an `ir.cron` record plus a model method
(e.g. `govoo.compliance.instance._cron_generate_and_remind()`), and only introduce a
`govoo.compliance.rule` model if per-obligation rule configuration needs its own editable records
beyond what `govoo.compliance.obligation` already holds.

## Odoo technical structure
```
govoo_compliance/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_base
|-- models/
|   |-- __init__.py
|   |-- govoo_compliance_obligation.py
|   |-- govoo_compliance_instance.py
|   `-- govoo_compliance_cron.py     # cron/engine logic
|-- views/
|-- security/
|   |-- ir.model.access.csv
|   `-- govoo_compliance_security.xml
|-- data/
|   `-- ir_cron_data.xml       # scheduled action definition (no obligation VALUES here — those are govoo_rw's)
|-- report/
|   `-- (filing-pack export template)
|-- tests/
|   |-- test_instance_generation.py   # monthly/quarterly/annual/FYE-relative
|   `-- test_late_transition.py
`-- i18n/
```

## Models

### `govoo.compliance.obligation` (catalogue)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | e.g. "Annual Return" |
| `authority` | Char or Selection | No | regulator |
| `frequency` | Selection (`annual`/`quarterly`/`monthly`/`event`) | Yes | |
| `basis` | Selection (`fixed_date`/`fye_relative`/`event_relative`) | Yes | |
| `lead_time_days` | Integer | No | >= 0 |
| `applies_to_entity_type` | Selection | No | |
| `active` | Boolean | Yes | default `False` for any seeded-but-unconfirmed template |
- **Inheritance:** `mail.thread`.
- **Constraints:** `lead_time_days >= 0`.
- **Access requirements:** config-level (Secretary/Admin).
- Source: §7.5.1. Requirement: FR-COMP-001. Business rule: BR-COMP-001.

### `govoo.compliance.instance` (a concrete due item)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `obligation_id` | Many2one `govoo.compliance.obligation` | Yes | |
| `company_id` | Many2one `res.company` | Yes | |
| `period` | Char | No | e.g. "2027-Q1" |
| `due_date` | Date | Yes | computed per `basis`, never hard-coded |
| `responsible_id` | Many2one `res.users` | No | |
| `state` | Selection (`upcoming`/`in_progress`/`filed`/`late`/`waived`) | Yes | default `upcoming` |
| `filed_date` | Date | No | |
| `reference_no` | Char | No | acknowledgement reference |
| `filing_document_id` | Many2one `documents.document` | No | Feature-flagged |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **Constraints:** no duplicate `(obligation_id, company_id, period)`; `due_date` computation
  requires `govoo_financial_year_end` set on the company when `basis = 'fye_relative'` — otherwise
  no instance is generated for that company (fail closed).
- **State transitions:** see `data-model/state-machines.md`, `workflows/compliance.md`.
- **Access requirements:** company-scoped.
- Source: §7.5.2. Requirement: FR-COMP-002. Business rule: BR-COMP-002.

### Compliance reminder / escalation engine
- **Description:** `ir.cron` (recommended daily) generates upcoming instances from active
  obligations and creates staged `mail.activity` reminders (e.g. -30/-7/-1 days) for the responsible
  user. Overdue → `late` → escalate.
- **Methods:** `_cron_generate_instances()`, `_cron_send_reminders()` (or combined),
  `_check_and_escalate_late()`.
- **Views:** calendar, Kanban by state, RAG (red/amber/green) dashboard.
- **`[IMPORTANT]`** (source, verbatim intent): do not pre-seed unverified deadlines as authoritative
  — see `modules/govoo_rw.md` and BR-COMP-001.
- Source: §7.5.3. Requirement: FR-COMP-003. Business rule: BR-COMP-002, BR-COMP-003.

### Filing-pack export (feature)
- **Description:** Since RDB/Irembo has no confirmed public filing API, generate filing-ready
  documents for manual portal upload; record submission + acknowledgement (`reference_no`,
  `filed_date`) on the instance.
- **Methods:** `action_generate_filing_pack()` on `govoo.compliance.instance`.
- Source: §7.5.4; §13 item 6. Requirement: FR-COMP-004. Business rule: BR-COMP-004.

## Tests
- TC-COMP-001..003: cron generates correct instances for monthly/quarterly/annual/FYE-relative
  rules.
- TC-COMP-004: late transition fires correctly.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_compliance` section.
