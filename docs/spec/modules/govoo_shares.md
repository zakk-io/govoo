# Module: govoo_shares

Source: §3.2, §7.3 of the source spec. Build order: **Step 3** (depends on `govoo_secretarial`).

## Module overview
- **Purpose:** Ownership as structured data — the cap table / share register.
- **Responsibility:** Share classes, allotments, transfers, and computed holdings; feeds the
  Register of Members (`govoo_secretarial`) and shareholder-vote weighting (`govoo_board`).
- **Depends on (Odoo):** `base`, `mail`.
- **Depends on (custom):** `govoo_secretarial` (and transitively `govoo_base`).
- **Owns:** `govoo.share.class`, `govoo.share.allotment`, `govoo.share.transfer`,
  `govoo.share.holding`.
- **Must NOT own:** statutory register presentation (owned by `govoo_secretarial`, which consumes
  `govoo.share.holding` — do not duplicate register-of-members fields here).

## Odoo technical structure
```
govoo_shares/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_secretarial
|-- models/
|   |-- __init__.py
|   |-- govoo_share_class.py
|   |-- govoo_share_allotment.py
|   |-- govoo_share_transfer.py
|   `-- govoo_share_holding.py   # computed/materialized
|-- views/
|-- security/
|   |-- ir.model.access.csv
|   `-- govoo_shares_security.xml   # shareholder-portal record rule: own holdings only
|-- data/
|-- report/
|   `-- (QWeb: cap-table snapshot, ownership %, voting-power table)
|-- tests/
|   |-- test_allotment.py       # over-allotment rejected
|   |-- test_transfer.py        # over-transfer rejected
|   `-- test_holding.py         # recompute + percentages sum to 100
`-- i18n/
```

## Models

### `govoo.share.class`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `name` | Char | Yes | e.g. "Ordinary A" |
| `company_id` | Many2one `res.company` | Yes | |
| `nominal_value` | Monetary | No | |
| `currency_id` | Many2one `res.currency` | No | RWF default in `govoo_rw` |
| `votes_per_share` | Float | No | |
| `total_authorised` | Integer | Yes | > 0 |
| `is_redeemable` | Boolean | No | default `False` |
- **Inheritance:** `mail.thread`.
- **Constraints:** `total_authorised > 0`; `nominal_value >= 0`.
- **Access requirements:** company-scoped.
- Source: §7.3.1. Requirement: FR-SHARE-001. Business rule: BR-SHARE-001.

### `govoo.share.allotment` (issuance)
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `company_id` | Many2one `res.company` | Yes | |
| `share_class_id` | Many2one `govoo.share.class` | Yes | |
| `partner_id` | Many2one `res.partner` | Yes | allottee |
| `quantity` | Integer | Yes | > 0 |
| `price_per_share` | Monetary | No | |
| `date_allotted` | Date | No | |
| `certificate_no` | Char | No | |
| `certificate_document_id` | Many2one `documents.document` | No | Feature-flagged |
- **Inheritance:** `mail.thread`.
- **Constraints:** `quantity > 0`; SQL/Python constraint enforcing BR-SHARE-001 (cumulative
  allotments for the class <= `total_authorised`).
- **Methods/business behavior:** `create()` triggers `govoo.share.holding` recompute for
  `(partner_id, share_class_id)`.
- **Access requirements:** company-scoped; Secretary/Admin write.
- Source: §7.3.2. Requirement: FR-SHARE-002.

### `govoo.share.transfer`
| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `share_class_id` | Many2one `govoo.share.class` | Yes | |
| `transferor_id` | Many2one `res.partner` | Yes | |
| `transferee_id` | Many2one `res.partner` | Yes | `!= transferor_id` |
| `quantity` | Integer | Yes | > 0 |
| `price` | Monetary | No | |
| `date_transferred` | Date | No | |
| `stamp_duty` | Monetary | No | |
| `transfer_instrument_id` | Many2one `documents.document` | No | Feature-flagged |
| `sign_request_id` | Many2one `sign.request` | No | Feature-flagged; gated on `[CONFIRM]` legal validity |
| `state` | Selection (`draft`/`approved`/`registered`) | Yes | default `draft` |
- **Inheritance:** `mail.thread`.
- **Constraints:** `quantity > 0`; on transition to `registered`, `quantity <=` transferor's
  current holding in that class (BR-SHARE-002); `transferor_id != transferee_id`.
- **Methods/business behavior:** reaching `state = 'registered'` triggers `govoo.share.holding`
  recompute for both `transferor_id` and `transferee_id`.
- **State transitions:** see `data-model/state-machines.md` (`govoo.share.transfer`) and
  `workflows/share-management.md`.
- **Access requirements:** company-scoped; state-transition permissions per
  `workflows/share-management.md`.
- Source: §7.3.3. Requirement: FR-SHARE-003.

### `govoo.share.holding` (computed/materialized)
- **Description:** Current position per `(partner, share_class)`: `quantity`, `percentage`,
  `voting_power`. Recomputed from allotments minus registered transfers. Backs the cap-table view
  and Register of Members.
- **Fields:** `partner_id` (m2o), `share_class_id` (m2o), `company_id` (m2o, related),
  `quantity` (Integer, computed/stored), `percentage` (Float, computed/stored),
  `voting_power` (Float, computed/stored, normalized against total voting shares of the class).
- **Inheritance:** `mail.thread` (for recompute history) — `[ENGINEERING DETAIL]` since this is
  derived data, tracking may instead be limited to a recompute log entry rather than full
  `mail.thread`; **decide during implementation and document the choice**.
- **Constraints:** percentages across all holders of a class sum to 100% (or 0 if none); `quantity`
  never negative — a would-be-negative recompute must raise, not clamp.
- **Methods/business behavior:** a `_recompute_holdings(share_class_id)` method triggered by
  allotment `create()` and transfer `state -> 'registered'`.
- **Access requirements:** Shareholder Portal record rule limits to the logged-in partner's own
  rows.
- Source: §7.3.4. Requirement: FR-SHARE-004. Business rule: BR-SHARE-003.

### GL posting hook `[CONFIRM]` `[OPTIONAL]`
- **Description:** Optional hook to `account.move` for capital events. **Off by default**; enabled
  only per the client's confirmed accounting policy.
- Source: §7.3.5; §13 item 7. Requirement: FR-SHARE-005. Business rule: BR-SHARE-004.

## Reports (QWeb)
Cap-table snapshot (as-of date), ownership % table, voting-power table — optionally also rendered
in a Spreadsheet Dashboard (feature-flagged, Enterprise) per `ui/dashboards.md`.

## Tests
- TC-SHARE-001..003: allotment/transfer/holding constraints and recompute correctness.
- TC-SHARE-004: percentages sum to 100% after allotment + transfer sequence.
- TC-SHARE-005: no `account.move` created unless GL hook explicitly enabled.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_shares` section.
