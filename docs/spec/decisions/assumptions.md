# Engineering Assumptions

Source: assumptions made only where necessary to make the source spec implementation-ready, per
master-prompt §22 instruction to keep this category separate from confirmed facts and open
decisions. These are **not** authoritative — they are reasonable defaults an implementer may build
against, clearly flagged so they can be revisited without archaeology through the whole repository.

## Packaging / structure assumptions
- **Portal + Dashboard packaging:** portal templates ship inside each owning module; a thin
  `govoo_portal`/`govoo_dashboard` module handles only the cross-module aggregated dashboard.
  (`modules/portal.md` "Note on packaging".) Not stated explicitly in source, which describes
  behavior, not module boundaries, for this layer.
- **`govoo.compliance.rule` is a mechanism (`ir.cron` + model methods), not a separate persisted
  model**, unless per-obligation rule configuration later needs its own editable records.
  (`modules/govoo_compliance.md` "Note on `govoo.compliance.rule`".)

## Contract Management addendum assumptions
- **`FR-CM-NN` uses 2-digit numbering (`FR-CM-01`..`FR-CM-20`)**, deviating from every other area's
  3-digit `FR-<AREA>-NNN` convention. This is deliberate: the addendum source document numbers its
  own features `CM-F01`..`CM-F20`, and matching that numbering exactly gives 1:1 traceability
  between `requirements/product-requirements.md` and the addendum without a lookup table. If this
  repository's ID convention is later tightened to enforce a single fixed width, renumber
  `FR-CM-*` to 3 digits and update every cross-reference (`requirements/traceability.md`,
  `modules/govoo_contracts.md`, `workflows/contracts.md`) in the same change.
- **"Named approver" is not yet modeled as a distinct field on `govoo.contract`** — the Contract
  Viewer Portal's read scope (BR-CM-007, `security/record-rules.md` §6b) is specified in terms of
  "counterparty or named approver" per the addendum, but no field currently carries "named approver"
  as data (only `approver_id`/`approval_ids` in the internal approval-routing flow, which the portal
  should not need to read). Flagged `[ENGINEERING DETAIL — CONFIRM]` at the record-rule definition
  itself; an implementer must either add an explicit `portal_approver_ids` field or confirm that
  "named approver" always coincides with `counterparty_id` for the addendum's intended use cases.

## Data-model assumptions
- **`govoo.register.charge` has a `company_id` field** for consistency with every other register,
  even though the source's field table for this specific model doesn't list it explicitly.
  (`modules/govoo_secretarial.md`.)
- **`govoo.share.holding` tracking:** full `mail.thread` vs. a lighter recompute log is left as an
  implementation choice, defaulting toward `mail.thread` for consistency, to be revisited if
  performance at scale becomes a concern. (`modules/govoo_shares.md`.)
- **Referential-integrity `ondelete` policy** (`restrict` rather than `cascade` on register/audit
  models' partner/company FKs) is a recommended default, not a source-stated rule.
  (`data-model/constraints.md` §5.)
- **Indexing recommendations** (`company_id`, `(partner_id, share_class_id)`,
  `(register_model, res_id)`, `due_date`/`state`) are performance-engineering defaults, not source
  requirements. (`data-model/relationships.md` §7.)

## Process assumptions
- **Cron cadence:** daily, for both compliance instance generation/reminders
  (`modules/govoo_compliance.md`) and any future scheduled job — a reasonable default pending
  no source-stated cadence.
- **CI pipeline shape** (`devops/ci-cd.md`) — lint, install, test, acceptance-test, boundary-check,
  hard-coded-value-lint stages — is derived to satisfy the source's stated testing/version-control
  expectations (§4, §9), not a literal pipeline definition from the source.
- **Backup cadence placeholder** (daily full + continuous WAL archiving) pending RPO/RTO
  confirmation (`devops/backup-recovery.md` §2) — explicitly NOT to be treated as the confirmed
  target.
- **Restore-drill cadence** (quarterly, pending client agreement) — same caveat.

## UI assumptions
- **Menu tree** in `ui/navigation.md` is derived from the model/workflow set, not prescribed by the
  source, which does not specify an exact menu structure.
- **RAG (red/amber/green) compliance coloring thresholds** (`ui/dashboards.md` §2) — green/amber
  boundary at the obligation's own `lead_time_days`, red at `late` — is a reasonable reading of the
  source's "reminders at -30/-7/-1 days" example, not a stated coloring rule.

## How to treat this file
Every item here is a **default an implementer may proceed with** absent stakeholder input, but each
is revisit-able — if a stakeholder later states a preference that conflicts with an assumption
here, update both this file (remove or correct the entry) and the spec file(s) it affects, the same
way a resolved `[CONFIRM]` item moves to `decisions/confirmed-decisions.md`.
