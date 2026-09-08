# Module: govoo_secretarial

Source: §3.2, §7.2 of the source spec. Build order: **Step 2** (depends on `govoo_base`).

## Module overview
- **Purpose:** Statutory registers as structured legal data. Underlying files live in Documents;
  this module owns the structured register data itself.
- **Responsibility:** Register of directors, register of members, beneficial ownership register,
  register of charges, and the append-only audit ledger (`govoo.register.entry`) that underlies all
  four.
- **Depends on (Odoo):** `base`, `mail`, `documents` (feature-flagged).
- **Depends on (custom):** `govoo_base`.
- **Owns:** the four register models + the append-only ledger.
- **Must NOT own:** share allotment/transfer transactional logic (owned by `govoo_shares`, which
  the member register consumes via `govoo.share.holding`); appointment CRUD (owned by `govoo_base`,
  the director register only curates a view over it).

## Odoo technical structure
```
govoo_secretarial/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_base, documents (soft)
|-- models/
|   |-- __init__.py
|   |-- govoo_register_director.py
|   |-- govoo_register_member.py
|   |-- govoo_register_beneficial_owner.py
|   |-- govoo_register_charge.py
|   `-- govoo_register_entry.py
|-- views/
|   `-- (list/form per register, see ui/views.md)
|-- security/
|   |-- ir.model.access.csv     # NOTE: no write/unlink on govoo.register.entry for ANY group
|   `-- govoo_secretarial_security.xml
|-- data/
|-- report/
|   `-- (QWeb: printable register extracts per register type)
|-- tests/
|   |-- test_register_entry.py  # append-only enforcement
|   `-- test_beneficial_owner.py
`-- i18n/
```

## Models

### `govoo.register.director`
- **Description:** Curated view over `govoo.appointment` + statutory particulars.
- **Inheritance:** `mail.thread`.
- **Fields:** derived/related fields from `govoo.appointment` (partner, role, dates, state) plus
  any additional statutory particulars required for the register extract report
  `[ENGINEERING DETAIL — exact particulars list not itemized in source beyond "statutory
  particulars"; confirm with legal advisor what must appear on the printed register]`.
- **Constraints:** none beyond the underlying appointment's.
- **Access requirements:** company-scoped; Auditor read; Secretary/Admin curate.
- Source: §7.2.1. Requirement: FR-SEC-001.

### `govoo.register.member`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `partner_id` | Many2one `res.partner` | Yes | shareholder |
| `company_id` | Many2one `res.company` | Yes | |
| `holding_ids` | One2many `govoo.share.holding` | No | from `govoo_shares` |
| `date_entered` | Date | No | |
| `date_ceased` | Date | No | set when aggregate holding reaches zero |
- **Inheritance:** `mail.thread`.
- **Constraints:** `date_ceased >= date_entered` when both set.
- **Access requirements:** company-scoped; Shareholder Portal record rule limits to own record.
- Source: §7.2.2. Requirement: FR-SEC-002.

### `govoo.register.beneficial.owner` — Rwanda legal requirement, MUST
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `partner_id` | Many2one `res.partner` | Yes | |
| `company_id` | Many2one `res.company` | Yes | |
| `nature_of_control` | Selection or Many2many | Yes | `[CONFIRM per Rwanda law]` — thresholds not hard-coded (>25% shares / >25% voting / appoint majority of board / significant influence) |
| `date_became_registrable` | Date | No | |
| `evidence_document_id` | Many2one `documents.document` | No | Feature-flagged |
- **Inheritance:** `mail.thread`.
- **Constraints:** `nature_of_control` required before the record can be marked complete.
- **UI requirement:** any record built on unconfirmed threshold data is visually flagged as
  provisional (BR-SEC-STAT-003).
- **Access requirements:** highest-sensitivity register; Secretary/Admin write only; company-scoped.
- Source: §7.2.3; §13 item 4. Requirement: FR-SEC-003.

### `govoo.register.charge`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `company_id` | Many2one `res.company` | Yes | `[ENGINEERING DETAIL]` — add for consistency; not explicitly listed in the source's field table but implied by every other register being company-scoped |
| `chargee_partner_id` | Many2one `res.partner` | No | |
| `amount` | Monetary | No | with `currency_id` |
| `date_created` / `date_registered` | Date | No | |
| `property_description` | Text | No | |
| `satisfied` | Boolean | No | default `False` |
| `charge_document_id` | Many2one `documents.document` | No | Feature-flagged |
- **Inheritance:** `mail.thread`.
- **Constraints:** `amount > 0`; `date_registered >= date_created` when both set.
- **Methods/business behavior:** charges are never deleted, only marked `satisfied`
  (BR-SEC-STAT-004).
- **Access requirements:** company-scoped; Secretary/Admin write, Auditor read.
- Source: §7.2.4. Requirement: FR-SEC-004.

### `govoo.register.entry` — append-only audit ledger
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `register_model` | Char | Yes | which register |
| `res_id` | Integer | Yes | record affected |
| `change_type` | Selection (`create`/`update`/`cease`) | Yes | |
| `effective_date` | Date | Yes | |
| `user_id` | Many2one `res.users` | Yes | |
- **Inheritance:** none beyond base (not `mail.thread` — this model IS the audit mechanism, not a
  subject of one).
- **Constraints:** enforced via `ir.model.access.csv` (no `write`/`unlink` for any group) AND a
  Python override of `write()`/`unlink()` raising `UserError` as defense in depth.
- **Methods/business behavior:** created automatically by the four register models' create/write
  logic (via `create()`/`write()` overrides or a shared mixin), never directly by end users.
- **Access requirements:** `create` only, by system logic; `read` for Auditor and Secretary/Admin;
  no `write`/`unlink` for anyone.
- Source: §7.2.5. Requirement: FR-SEC-005.

## Reports (QWeb)
Printable register extracts per register type (director, member, beneficial owner, charges) — see
`ui/dashboards.md` / report section of `ui/views.md` for layout requirements.

## Tests
- TC-SEC-STAT-005: `govoo.register.entry` is append-only (no group can edit/delete).
- TC-SEC-STAT-003: beneficial-owner `nature_of_control` validation and provisional-flag display.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_secretarial` section.
