# Module: govoo_base

Source: §3.2, §6.1, §7.1 of the source spec. Build order: **Step 1 (build first)**.

## Module overview
- **Purpose:** Foundation module. Shared security groups; `res.partner`/`res.company` extensions;
  appointment (role-over-time) and committee models.
- **Responsibility:** Defines the six security groups every other module's access rules reference;
  defines the person/entity fields every other module reads.
- **Depends on (Odoo):** `base`, `mail`, `contacts`.
- **Depends on (custom):** none — this is the root of the dependency graph.
- **Owns:** security groups (`res.groups` data), `res.partner` governance-role/PII fields,
  `res.company` statutory-entity fields, `govoo.appointment`, `govoo.committee`.
- **Must NOT own:** register content (`govoo_secretarial`), share data (`govoo_shares`), meeting/
  resolution data (`govoo_board`), compliance data (`govoo_compliance`), Rwanda-specific config
  values (`govoo_rw`).

## Odoo technical structure
```
govoo_base/
|-- __init__.py
|-- __manifest__.py            # depends: base, mail, contacts
|-- models/
|   |-- __init__.py
|   |-- res_partner.py         # extends res.partner
|   |-- res_company.py         # extends res.company
|   |-- govoo_appointment.py
|   `-- govoo_committee.py
|-- views/
|   |-- res_partner_views.xml
|   |-- res_company_views.xml
|   |-- govoo_appointment_views.xml
|   |-- govoo_committee_views.xml
|   `-- govoo_base_menus.xml
|-- security/
|   |-- govoo_base_groups.xml       # the 6 groups (source §6.1)
|   |-- ir.model.access.csv
|   `-- govoo_base_security.xml     # record rules (company_id scoping)
|-- data/
|   `-- (none required at this layer — Rwanda seed data lives in govoo_rw)
|-- report/
|   `-- (none — first reports appear in govoo_secretarial/govoo_board)
|-- tests/
|   |-- __init__.py
|   |-- test_appointment.py
|   `-- test_committee.py
`-- i18n/
    |-- govoo_base.pot
    |-- fr.po
    `-- rw.po
```

## Models

### `res.partner` (inherit, extend)
| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `govoo_is_director` | Boolean | No | `False` | |
| `govoo_is_shareholder` | Boolean | No | `False` | |
| `govoo_is_officer` | Boolean | No | `False` | |
| `govoo_is_beneficial_owner` | Boolean | No | `False` | Replaces "PSC" terminology |
| `govoo_national_id` | Char | No | — | **PII, group-restricted** (Secretary/Admin only) |
| `govoo_date_of_birth` | Date | No | — | **PII, group-restricted**; must be a past date |
| `govoo_nationality_id` | Many2one `res.country` | No | — | |
| `govoo_appointment_ids` | One2many `govoo.appointment` (`partner_id`) | No | — | |
- **Tracking:** `tracking=True` on all boolean role flags and PII fields.
- **Access requirements:** PII fields restricted via `groups=` attribute or a dedicated
  view/field-group referencing `govoo_base.group_govoo_secretary,govoo_base.group_govoo_admin`.
- **Methods/business behavior:** none beyond field storage at this layer (registers in
  `govoo_secretarial` read these flags).
- Source: §7.1.1. Requirement: FR-BASE-001.

### `res.company` (inherit, extend)
| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `govoo_company_number` | Char | No | — | Registration number |
| `govoo_tin` | Char | No | — | Tax ID |
| `govoo_incorporation_date` | Date | No | — | |
| `govoo_entity_type` | Selection (`private`/`public`/`llc`/`branch`) | No | — | |
| `govoo_registered_office_id` | Many2one `res.partner` | No | — | Must be in-country (§8); `[CONFIRM]` exact validation |
| `govoo_financial_year_end` | Char or Selection | No | — | Drives FYE-relative compliance dates |
- **Tracking:** `tracking=True` on all fields above.
- **Access requirements:** Board Administrator / Company Secretary write; standard multi-company
  record rules for read/write isolation.
- Source: §7.1.2. Requirement: FR-BASE-002.

### `govoo.appointment`
| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `partner_id` | Many2one `res.partner` | Yes | — | |
| `company_id` | Many2one `res.company` | Yes | current company | `check_company=True` |
| `role` | Selection (`director`/`secretary`/`chair`/`md`/`committee_member`) | Yes | — | |
| `committee_id` | Many2one `govoo.committee` | No | — | Optional |
| `date_appointed` | Date | Yes | — | |
| `date_resigned` | Date | No | — | Must be `>= date_appointed` |
| `state` | Selection (`active`/`resigned`) | — (computed) | — | Computed, stored, not user-editable |
| `appointment_document_id` | Many2one `documents.document` | No | — | Feature-flagged (Documents/Enterprise) |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **Constraints:** `@api.constrains` — `date_resigned >= date_appointed` when set.
- **Computed fields:** `state` — `@api.depends('date_appointed', 'date_resigned')`, stored for
  filtering/searching.
- **Methods/business behavior:** none beyond the computed `state`.
- **State transitions:** see `data-model/state-machines.md` (`govoo.appointment`).
- **Access requirements:** company-scoped record rule; Secretary/Admin write, Governance User/
  Auditor read.
- Source: §7.1.3. Requirement: FR-BASE-003.

### `govoo.committee`
| Field | Type | Required | Default | Notes |
| --- | --- | --- | --- | --- |
| `name` | Char | Yes | — | |
| `company_id` | Many2one `res.company` | Yes | current company | |
| `parent_committee_id` | Many2one `govoo.committee` | No | — | Self-referential; no cycles; same company |
| `chair_partner_id` | Many2one `res.partner` | No | — | |
| `member_ids` | One2many `govoo.appointment` (`committee_id`) | No | — | |
| `terms_of_reference_id` | Many2one `documents.document` | No | — | Feature-flagged |
- **Inheritance:** `mail.thread`, `mail.activity.mixin`.
- **Constraints:** `@api.constrains` on `parent_committee_id` — same company, no cycle (recursive
  check similar to `res.partner.parent_id` cycle checks).
- **Methods/business behavior:** `member_ids` resolves live from `govoo.appointment` records
  filtered by `committee_id`; no data duplication.
- **Access requirements:** company-scoped; Director Portal record rule restricts to committees the
  portal user's partner belongs to.
- Source: §7.1.4. Requirement: FR-BASE-004.

## Security groups defined here (data, not a model)
See `security/access-control.md` for the full matrix. XML IDs, all in `govoo_base`:
`group_govoo_user`, `group_govoo_secretary`, `group_govoo_admin`, `group_govoo_director_portal`,
`group_govoo_shareholder_portal`, `group_govoo_auditor`.

## Views (see `ui/views.md` for full spec)
- `res.partner` form: add a "Governance" notebook page with role flags + appointment_ids; PII
  fields shown only to authorized groups via `groups=` on the page/fields.
- `res.company` form: add a "Governance" section with entity/statutory fields.
- `govoo.appointment`: list + form.
- `govoo.committee`: list + form (form shows resolved `member_ids`).

## Tests (see `testing/unit-tests.md`)
- TC-BASE-001: PII field visibility restricted by group.
- TC-BASE-003: appointment `state` computes correctly from dates.
- TC-BASE-004: committee membership resolves; cycle rejected.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_base` section.
