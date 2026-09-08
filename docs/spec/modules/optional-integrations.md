# Optional Modules: govoo_rw_accounting, govoo_rw_ebm

Source: §3.2, §8.4 of the source spec. Build order: **Step 9**, optional, only if the client needs
tax/EBM functionality. Kept explicitly **outside** the governance core so a governance-only client
never installs tax machinery it doesn't need.

## `govoo_rw_accounting`
- **Purpose:** Custom Rwanda chart of accounts + tax codes. No official Odoo `l10n_rw` localization
  exists, so this is genuinely custom (an exception to reuse-before-build, justified by the absence
  of an Odoo-native equivalent).
- **Depends on (Odoo):** `account`.
- **Depends on (custom):** `govoo_rw`.
- **Owns:** chart-of-accounts data, tax-code data (as configurable records, per BR-RW-002 — no
  hard-coded rates).
- **Interacts with core via:** the optional GL-posting hook in `govoo_shares` (FR-SHARE-005), which
  remains off by default regardless of whether this module is installed.
- **`[CONFIRM]`:** exact chart-of-accounts structure and tax-code values pending accountant/tax
  advisor confirmation; ship as inactive/template data until confirmed (same discipline as
  `govoo_rw`'s compliance templates).

## `govoo_rw_ebm`
- **Purpose:** RRA EBM/VSDC e-invoicing connector — described in the source as "the one confirmed
  real-time government API" available to this system.
- **Depends on (Odoo):** `account`.
- **Depends on (custom):** `govoo_rw_accounting`.
- **Implementation approach:** license a proven third-party connector, or build against the
  published VSDC specification — the source does not mandate one approach, only that this stays
  **out of the governance core**.
- **Security:** e-invoicing credentials/certificates are handled with the same "never hard-code,
  never log secrets" discipline as any other integration credential; see
  `security/privacy.md`.

## Why these are separate from the governance core (architectural rationale, source §1.2, §8.4)
Tax/e-invoicing is explicitly named a **non-goal of the governance core (v1)** — "Tax/e-invoicing
(RRA EBM) is an optional, separately installable module not part of the governance core." Bundling
it into `govoo_rw` or any governance module would violate the module-boundary rule in
`architecture/module-architecture.md` §3 and force every governance-only client to carry accounting
dependencies they didn't ask for.

## Definition of Done
Both modules follow the same Definition of Done as any other module
(`implementation/module-checklists.md`) **plus**: they must not be required for `govoo_base`
through `govoo_evaluation` to install, run, or pass their tests. A CI check
(`[RECOMMENDED]`) that installs the governance core without these two modules and runs the full
test suite is the concrete way to verify this boundary holds.
