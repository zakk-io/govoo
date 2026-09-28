# Confirmed Decisions

Source: facts directly stated by the source spec (not inferred, not engineering assumptions). This
file also serves as the **required destination** for any `decisions/open-decisions.md` item once it
is genuinely resolved — each new entry must record who confirmed it, when, and which spec files
were updated as a result.

## Confirmed by the source spec itself (no further sign-off needed — these are baseline facts, not
open items)
| # | Decision | Source |
| --- | --- | --- |
| 1 | Govoo is built on Odoo (version confirmed as 19 — see the "Resolved from open-decisions.md" entry below) as a modular monolith, not microservices | §1, §3.1 |
| 2 | Person = `res.partner`, Company = `res.company` — no parallel models | §3.1 |
| 3 | Six security groups: Governance User, Company Secretary, Board Administrator, Director (Portal), Shareholder (Portal), Auditor | §6.1 |
| 4 | Board Administrator cannot cast board votes, despite configuration privileges | §6.1, §6.2 |
| 5 | Portal users have no internal licence; access is via `portal.mixin` + tokens + record rules, never URL guessing | §6.3 |
| 6 | Currency RWF, 0 decimal places, for Rwanda deployments | §8.1 |
| 7 | Minutes/resolutions retained 10 years; accounts/auditor/board reports retained 10 accounting periods | §8.2 |
| 8 | Tax/e-invoicing (RRA EBM) is optional and outside the governance core | §1.2, §8.4 |
| 9 | No official Odoo `l10n_rw` localization exists — `govoo_rw_accounting`'s chart of accounts is genuinely custom | §8.4 |
| 10 | Govoo is not a native mobile app, not an AI minute-drafting tool, not a multi-entity consolidation reporting system in v1 | §1.2 |
| 11 | RRA EBM/VSDC is described as "the one confirmed real-time government API" available, but scoped to the optional `govoo_rw_ebm` module | §8.4 |
| 12 | Build order: `govoo_base` → `govoo_secretarial` → `govoo_shares` → `govoo_board` → `govoo_compliance` → `govoo_rw` → `govoo_evaluation` → Portal + dashboard → optional accounting/EBM | §12 |

## Resolved from `decisions/open-decisions.md` (template — populate as decisions are made)
```
### [N] <decision title>
- **Resolved value:** <the confirmed value/decision>
- **Confirmed by:** <name/role, e.g. "Rwandan legal advisor — [name/firm]">
- **Date:** <date>
- **Spec files updated:** <list — must include data-model/constraints.md if the decision touches a
  previously-inactive configuration value, and the specific modules/*.md / security/*.md files
  affected>
- **Activation note:** <if this unlocks previously `active=False` data, name the specific data rows
  and confirm they were switched to `active=True` deliberately, not by a blanket migration>
```

### [1] Odoo version (17 vs 18)
- **Resolved value:** Odoo 19. Not one of the two options the open question originally considered
  (17 or 18) — the implementation shipped on 19 without a recorded sponsor sign-off at the time.
  This entry documents the as-built state rather than asserting that sign-off happened; if a
  genuine technical-sponsor confirmation exists elsewhere, replace the line below with its
  provenance.
- **Confirmed by:** not verified against a named technical-sponsor sign-off — recorded here as the
  factual, already-implemented state (every module manifest and the vendored core are Odoo 19).
- **Date:** 2026-09-14
- **Spec files updated:** `decisions/open-decisions.md` item 1 (version half removed, edition
  half remains open), `architecture/technology-standards.md` §1.
- **Activation note:** N/A — no previously-inactive (`active=False`) configuration data is
  unlocked by this entry.

The edition question (Enterprise vs Community + OCA) from the same original open-decisions.md
item 1 remains genuinely open — confirming the version in code doesn't resolve it.

### [24] AI provider selection — partial (provider/deployment path only, not hosting region or DPA)
- **Resolved value:** `govoo_ai`'s AI provider is **OpenAI**, via the **direct OpenAI platform API**
  (not Azure OpenAI Service, not a self-hosted model). This resolves only the "which provider /
  which deployment path" sub-part of open-decisions.md item 24.
- **Confirmed by:** zakk-io (repo/product owner), in-session product decision, 2026-09-28. Not a
  legal/counsel or NCSA sign-off — see below for what that still leaves open.
- **Date:** 2026-09-28
- **Spec files updated:** `decisions/open-decisions.md` items 24 and 25 (both narrowed, not closed —
  see those entries for exactly what remains).
- **Activation note:** N/A — no previously-inactive (`active=False`) configuration data is unlocked
  by this entry. `govoo.ai.config.provider`/`data_region` (per
  `docs/ai_services_layer_clagov_ai.md` §2.3) must still ship inactive/unset by default; this entry
  only fixes which value they'll eventually hold once the remaining items below clear.
- **What this does NOT resolve (still open, see `decisions/open-decisions.md` items 24/25):**
  - **Hosting region / data residency.** The direct OpenAI API does not offer region pinning the way
    Azure OpenAI Service would have — choosing this path makes the Rwanda NCSA / Law 058/2021
    residency question (open-decisions.md item 2, and the AI-hosting half of item 25) *more*
    pressing, not resolved. Counsel + NCSA sign-off is still required before any real client PII is
    sent to this provider from a Rwanda deployment.
  - **DPA / zero-retention contract terms (`AI-N01`).** No OpenAI Business/Enterprise DPA has been
    reviewed or signed as part of this decision. Until it is, `govoo.ai.config` must ship with the
    feature inactive for any tenant handling real (non-test) data.
  - **Token-usage caps / pricing / metering model (item 29).** Untouched by this decision.
  - This also supersedes the model-family suggestion in `docs/ai_services_layer_clagov_ai.md`
    §2.4 `AI-N08` ("target current Claude models") for provider selection purposes — that addendum
    text is left as-is (it's a verbatim record of the original client document), but the actual
    provider is now OpenAI per this entry, not Claude, behind the same swappable service-interface
    requirement `AI-N08` already mandates.

No further entries exist below this line beyond the ones above — this repository otherwise ships
with **zero** resolved `[CONFIRM]` items beyond the source-confirmed facts listed above. Every
implementer inherits the obligation to populate this section only via genuine stakeholder
confirmation, never by assumption.
