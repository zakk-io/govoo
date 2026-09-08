# Migrations

Source: §9 ("Migrations: provide data-migration scripts for pilot data") of the source spec.

## 1. Requirement
Every module that ingests pre-existing client data (e.g. a client migrating from spreadsheets or
another system) must ship or be accompanied by a **reviewed migration script/mapping** — never a
manual, ad-hoc production data edit (`architecture/technology-standards.md` §10).

## 2. Migration scope (typical, per module — `[ENGINEERING DETAIL]`, source states the requirement
generally, not module-by-module)
| Module | Typical migration source data |
| --- | --- |
| `govoo_base` | Existing director/officer/shareholder contact lists, committee structures |
| `govoo_secretarial` | Existing statutory registers (often spreadsheet-based) |
| `govoo_shares` | Existing cap table / share register |
| `govoo_board` | Historical meeting minutes/resolutions, if the client wants them in-system (optional — may be attached as documents rather than fully structured data) |
| `govoo_compliance` | Existing compliance calendar / filing history |

## 3. Migration process
1. Extract client data (spreadsheet, prior system export).
2. Map to Govoo's model/field structure per the relevant `modules/*.md` and `data-model/` specs.
3. Validate against the constraints in `data-model/constraints.md` **before** import — e.g. a
   migrated cap table must satisfy BR-SHARE-001/BR-SHARE-003 (percentages summing to 100%,
   allotments within authorized capacity) or the migration script must flag and resolve the
   discrepancy, not silently import inconsistent data.
4. Import via a reviewed script (not manual UI data entry for bulk data) into staging first;
   validate; then production.
5. Record the migration event itself — `[RECOMMENDED]` a `govoo.register.entry`-style ledger note
   or equivalent, so migrated historical data is distinguishable from data entered through normal
   system use if that distinction matters for audit purposes.

## 4. What NOT to do
- Never bypass `data-model/constraints.md` validations "just for the migration" — if legacy data is
  genuinely inconsistent (e.g. a cap table that doesn't sum to 100% due to historical
  record-keeping errors), that inconsistency must be resolved (with the client) before import, not
  imported as-is and left to break downstream computations.
