# Module: govoo_rw

Source: §3.2, §8 of the source spec. Build order: **Step 6** (depends on `govoo_secretarial`,
`govoo_shares`, `govoo_board`, `govoo_compliance` — i.e. steps 2-5).

## Module overview
- **Purpose:** Rwanda localization layer that adapts the core for Rwanda.
- **Responsibility:** Three parts per source §8 — (1) configuration data (currency/language/locale/
  company fields), (2) feature adjustments driven by `govoo_rw` data (register-to-law mapping,
  retention, provisional compliance calendar), (3) optional modules (`govoo_rw_accounting`,
  `govoo_rw_ebm`) and the CMA governance-code feature.
- **Depends on (Odoo):** `base`.
- **Depends on (custom):** `govoo_secretarial`, `govoo_shares`, `govoo_board`, `govoo_compliance`.
- **Owns:** locale/currency config, Kinyarwanda/French translations, retention configuration +
  disposal job, provisional compliance-deadline **template data**, CMA checklist configuration.
- **Must NOT own:** any core transactional model, any hard-coded legal value.

## Odoo technical structure
```
govoo_rw/
|-- __init__.py
|-- __manifest__.py            # depends: govoo_secretarial, govoo_shares, govoo_board, govoo_compliance
|-- models/
|   |-- __init__.py
|   |-- res_config_settings.py     # currency/locale settings extension
|   `-- govoo_rw_retention.py      # retention config + disposal job
|-- views/
|-- security/
|-- data/
|   |-- res_currency_data.xml         # RWF, 0 decimals (or confirms it's already standard)
|   |-- govoo_compliance_obligation_data.xml   # Rwanda templates, ALL active=False
|   `-- ir_cron_disposal_data.xml
|-- report/
|-- tests/
|   |-- test_retention.py
|   `-- test_provisional_obligations_inactive.py
`-- i18n/
    |-- rw.po       # reviewed Kinyarwanda legal terminology
    `-- fr.po
```

## 1. Configuration (data records / settings) — source §8.1
| Setting | Value |
| --- | --- |
| Currency | RWF, 0 decimal places |
| Languages | English (primary), Kinyarwanda, French; Swahili optional |
| Date format | DD/MM/YYYY |
| Locale/timezone | Africa/Kigali |
| Company fields | TIN, RDB company number, registered office (in Rwanda) — fields already exist on
  `res.company` from `govoo_base` (FR-BASE-002); this module supplies Rwanda-specific defaults/
  validation. |

Ship `Kinyarwanda.po` translation files as **custom translation; legal terms reviewed by a local
advisor** (source §10 risk note — do not machine-translate legal terminology without review).
Requirement: FR-RW-001.

## 2. Feature adjustments (in core, driven by govoo_rw data) — source §8.2
- Registers mapped to Rwanda company law (share register, register of directors' interests,
  beneficial ownership register) — implemented as data/config consumed by `govoo_secretarial`
  models, not new models.
- **Retention:** minutes & resolutions retained 10 years; accounts/auditor/board reports 10
  accounting periods — implemented as `retention_until` computed fields (on `govoo.minutes` etc.)
  reading this module's configuration, plus a disposal job.
- Compliance calendar seeded with Rwanda obligations as **provisional, editable templates** with
  `effective_date` and source note, gated behind local-advisor sign-off, shown with a disclaimer.
  **Never present unverified dates as authoritative** (verbatim source instruction).
Requirement: FR-RW-002. Business rules: BR-RW-002, BR-RW-003.

## 3. Provisional compliance deadlines (seed as templates) — source §8.3, `[CONFIRM with Rwandan
advisor]`
| Obligation | Frequency | Deadline (provisional) |
| --- | --- | --- |
| VAT/PAYE/WHT/RSSB | Monthly | 15th of following month |
| VAT — small taxpayers (turnover <= RWF 200m) | Quarterly | within 15 days of quarter-end |
| CIT quarterly instalments | 3x/yr | 30 Jun / 30 Sep / 31 Dec |
| CIT annual declaration | Annual | within 3 months of year-end (31 Mar for Dec YE) |
| Annual return + accounts | Annual | reported Jan-Jul following year `[CONFIRM exact window]` |

**All rates (CIT, VAT, RSSB) and dates in this table are configurable data, never constants —
Rwanda is mid tax-reform** (verbatim source instruction). Every row above is seeded into
`govoo.compliance.obligation` with `active = False` and a disclaimer/source note; activation is a
deliberate, logged administrator action taken only after advisor confirmation (BR-RW-002).
Requirement: FR-RW-003.

## 4. Optional modules (separate installs) — source §8.4
- `govoo_rw_accounting` — custom Rwanda chart of accounts + tax codes (no official Odoo `l10n_rw`
  exists). Kept **outside** the governance core.
- `govoo_rw_ebm` — RRA EBM/VSDC e-invoicing connector (the one confirmed real-time government API in
  the source). License a proven third-party connector or build against the VSDC spec. Kept outside
  the governance core.
See `modules/optional-integrations.md` for detail.

## 5. Governance code (feature) — source §8.5
CMA Corporate Governance Code 2024 self-assessment checklist ("apply-and-explain") for listed/
public-company clients — implemented as a configurable obligation set + checklist model, reusing
the `govoo_compliance` obligation pattern rather than a bespoke model. Requirement: FR-RW-004.

## Tests
- TC-RW-001..002: config applied correctly (currency decimals, locale).
- TC-RW-003: all Rwanda-seeded obligation templates are `active = False` on fresh install.

## Definition of Done checklist
See `implementation/module-checklists.md` — `govoo_rw` section. **Special DoD note:** this module
cannot be marked Done merely by having code that compiles — it must be verified that **no** legal/
tax value shipped in its `data/` files is `active = True` without a corresponding, documented
advisor confirmation recorded in `decisions/confirmed-decisions.md`.
