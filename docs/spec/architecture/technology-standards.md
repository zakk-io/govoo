# Technology & Standards

Source: §4, §9 of the source spec.

## 1. Stack (source §4)
| Layer | Choice | Status |
| --- | --- | --- |
| Framework | Odoo 19 | Confirmed — see `decisions/confirmed-decisions.md` entry [1] (diverges from the originally-considered 17/18 options) |
| Language | Python 3.11+ (server), OWL/JS + XML (views), QWeb (reports) | Confirmed by source |
| Database | PostgreSQL 14+ | Confirmed by source |
| Version control | Git — feature branches, PR review | Confirmed by source |
| Dependency management | `requirements.txt` for external Python libs; OCA modules pinned by version | Confirmed by source |
| Testing | Odoo `TransactionCase` unit tests per module | Confirmed by source |
| Environments | dev → staging → production | See `devops/environments.md` |
| CI | Lint (`flake8` / `pylint-odoo`) + run tests on every PR | See `devops/ci-cd.md` |

`[ENGINEERING DETAIL]` Pin the exact point release (`19.0`) in `requirements.txt`/
`__manifest__.py` `version` keys, and pin OCA module commits/tags rather than tracking `main`.

## 2. Module & naming conventions (source §9, MUST follow)
- **Module naming:** `govoo_*` (e.g. `govoo_base`, `govoo_shares`).
- **Model naming:** `govoo.*` (e.g. `govoo.share.allotment`).
- **Field naming:** `snake_case`; extensions added to *standard* Odoo models (`res.partner`,
  `res.company`) are prefixed `govoo_` (e.g. `govoo_is_director`, `govoo_company_number`) to avoid
  clashing with core/OCA fields. Fields on *custom* `govoo.*` models do not need the prefix (the
  model name already namespaces them).
- **File/directory layout per module** (Odoo standard, MUST follow):
  ```
  govoo_<name>/
  |-- __init__.py
  |-- __manifest__.py
  |-- models/
  |-- views/
  |-- security/
  |-- data/
  |-- report/
  |-- tests/
  `-- i18n/
  ```

## 3. Security-first rule (source §9, MUST follow)
Every model ships `security/ir.model.access.csv` **and** record rules where the model holds
per-company or need-to-know data, in the same PR that introduces the model. **No model is merged
without access rules.** See `security/`.

## 4. No hard-coded legal values (source §9, §10, MUST follow — hard constraint)
- Rates, statutory dates, thresholds, and legal article numbers **must** live in data records
  (`ir.config_parameter`, dedicated config models, or template records) — never as Python literals,
  never as XML `<field>` defaults hard-coding a legal number.
- Anything uncertain is marked `[CONFIRM]` **in code comments at the point of definition** and
  defaults to `active = False` / disabled, so it cannot silently reach a client as authoritative.
- This applies most strongly to: compliance-obligation frequency/deadline data (`govoo_rw`), CIT/VAT/
  PAYE/WHT/RSSB rates, beneficial-ownership thresholds, and retention periods. See
  `data-model/constraints.md` and `modules/govoo_rw.md`.

## 5. Translations (source §9)
- Every user-facing string is wrapped for translation with `_()`.
- Ship `.po` translation stubs for French (`fr`) and Kinyarwanda (`rw`) with every module that has
  user-facing strings; `govoo_rw` ships the reviewed Kinyarwanda legal-terminology translations
  (source §8.1 — legal terms reviewed by a local advisor).

## 6. Money (source §9)
- All monetary fields are Odoo `Monetary` fields paired with a `currency_id` field — never plain
  `Float`.
- Respect RWF's 0-decimal-place convention (configured in `govoo_rw`, source §8.1) — do not assume
  2-decimal currency formatting anywhere in custom code, reports, or JS.

## 7. Audit (source §9)
- Every transactional custom model inherits `mail.thread` (`mail.activity.mixin` where reminders/
  activities apply).
- `tracking=True` on every statutory field (i.e. any field whose change history has legal
  significance — register fields, appointment dates, share quantities, resolution state, etc.).

## 8. Feature flags (source §9, §3.3 — MUST follow)
- Every call into an Enterprise-only app (Documents, Sign, Spreadsheet Dashboards, Approvals) is
  guarded so the custom module **installs and functions, with reduced UX, on Community**.
- Pattern: `[ENGINEERING DETAIL]` guard with a config/feature flag (e.g. an `ir.config_parameter` or
  a computed `env['ir.module.module'].search([('name','=','documents'),('state','=','installed')])`
  check) at the point of use, and provide a Community-safe fallback path (e.g. `ir.attachment`
  instead of `documents.document`; manual PDF download instead of `sign.request`). Never let a
  missing Enterprise app raise an unhandled error for an end user.

## 9. Tests (source §9)
- Every module ships `tests/` with at least happy-path `TransactionCase` coverage of its core
  business logic (state transitions, computed fields, constraints). See `testing/`.

## 10. Migrations (source §9)
- Provide data-migration scripts/mappings for pilot/legacy data.
- **Never** manually edit production data outside of a reviewed migration script. See
  `devops/migrations.md`.
