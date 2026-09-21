# Record Rules

Source: §6.2, §6.3 of the source spec. This file specifies the exact record-rule domains an
implementer should write — phrased so precisely that "handle permissions properly" is never the
instruction (per source §26 quality bar).

## 1. Multi-company record rule (applies to EVERY transactional model in `data-model/entities.md`)
- **Rule:** `[('company_id', 'in', company_ids)]` where `company_ids` is the requesting user's
  allowed companies (`self.env.companies` / standard Odoo multi-company mechanism).
- **Applies to groups:** all internal groups (Governance User, Company Secretary, Board
  Administrator, Auditor). Portal groups get a further-restricted rule (see §2-4 below) layered on
  top of, not instead of, this one.
- **Source:** §6.2 — "a corporate-services firm administers many client entities in one DB with
  strict isolation."

## 2. `govoo.meeting`, `govoo.agenda.item`, `govoo.board.pack`, `govoo.minutes` — Director Portal
- **Rule (Director Portal):**
  ```
  The record rule for govoo.meeting must restrict Director Portal users to meetings whose
  committee_id.member_ids.partner_id includes the partner associated with the portal user
  (i.e. the logged-in partner has an active govoo.appointment with committee_id equal to the
  meeting's committee_id, or an ancestor committee thereof if sub-committee visibility is intended
  — [CONFIRM whether parent-committee visibility cascades; source does not specify]).
  ```
  Domain sketch: `[('committee_id.member_ids.partner_id', '=', user.partner_id.id)]`, further
  restricted to `active` appointments only (`state = 'active'`) — a resigned director should not
  retain live visibility into future meetings, though historical read access `[CONFIRM]` may be
  desired for compliance purposes.
- `govoo.agenda.item`, `govoo.board.pack`, `govoo.minutes` inherit the same committee-membership
  domain via their `meeting_id` relation.
- **Source:** §6.2 — "Director portal user sees only meetings/packs of committees they belong to."

## 3. `govoo.share.holding`, `govoo.register.member` — Shareholder Portal
- **Rule (Shareholder Portal):**
  ```
  The record rule for govoo.share.holding must restrict Shareholder Portal users to rows where
  partner_id equals the partner associated with the portal user.
  ```
  Domain: `[('partner_id', '=', user.partner_id.id)]`.
- `govoo.register.member` inherits the same `partner_id` domain.
- **Source:** §6.2 — "Shareholder sees only their own govoo.share.holding and shareholder
  resolutions."

## 4. `govoo.resolution`, `govoo.vote` — Shareholder Portal / Director Portal (eligibility)
- **Rule (Shareholder Portal, resolutions):**
  ```
  The record rule for govoo.resolution must restrict Shareholder Portal users to resolutions where
  resolution_type indicates a shareholder-eligible resolution AND the portal user's partner has a
  nonzero govoo.share.holding in a voting share class of the resolution's company at the time of
  read [ENGINEERING DETAIL — exact "shareholder-eligible" flag not itemized as a distinct field in
  source; recommend deriving eligibility from resolution_type in ('ordinary','special') combined
  with a company match, since 'written' resolutions may be board- or shareholder-facing depending
  on context — CONFIRM the intended mapping].
  ```
- **Rule (Director Portal, resolutions/votes):** committee-membership domain as in §2, applied via
  `meeting_id.committee_id`.
- **Rule (`govoo.vote`, both portal groups):** a portal user may only `create` a vote row where
  `voter_id = user.partner_id` — enforced both by record rule and, per
  `security/access-control.md` §5, by omitting `create` rights entirely for any group/user not
  eligible.
- **Source:** §6.2, §7.4.6.

## 5. Auditor — global read, no write (all models)
- **Rule (Auditor):** no row-level restriction beyond the multi-company rule in §1 — Auditor sees
  all governance rows within their assigned companies. **No** `write`/`create`/`unlink` access at
  the `ir.model.access.csv` level (see `access-control.md` §2) — this is enforced at the access-
  rights layer, not via a record rule, since the constraint is "never write," not "write only to
  some rows."
- **Source:** §6.2 — "Auditor group: global read, no write."

## 6. `govoo.evaluation.result` / `survey.user_input` confidentiality
- **Rule:** a non-Secretary/Admin participant may read their own `survey.user_input` row (if any)
  and any `govoo.evaluation.result` aggregate row, but never another participant's individual
  `survey.user_input` row.
  Domain (for `survey.user_input`, scoped to campaigns this module creates):
  `[('partner_id', '=', user.partner_id.id)]` OR user is in `group_govoo_secretary`/
  `group_govoo_admin`.
- **Source:** §7.6.2 — "individual responses not exposed to non-authorized roles."

## 6b. `govoo.contract`, `govoo.contract.obligation`, `govoo.contract.milestone` — Contract Viewer Portal
- **Rule (Contract Viewer Portal):**
  ```
  The record rule for govoo.contract restricts Contract Viewer Portal users to contracts where
  counterparty_id equals the partner associated with the portal user, OR that partner appears in
  portal_approver_ids on that contract.
  ```
  Domain: `['|', ('counterparty_id', '=', user.partner_id.id), ('portal_approver_ids', 'in', user.partner_id.id)]`.
- **`[ENGINEERING DETAIL — resolved, issue #177]** "Named approver" is modeled as an explicit
  `govoo.contract.portal_approver_ids` (Many2many `res.partner`) field, set by the Contract
  Manager/Admin on the contract form — a deliberate choice over widening this to reference the
  internal approval-routing (`Contract Approver` group / `govoo.contract.delegation`) data, since
  that data controls *who may approve internally*, not *who may view externally as a portal user*;
  the two are related but not the same concept, and conflating them would let every internal
  approver see every contract via the portal regardless of whether they're actually a party to it.
- `govoo.contract.obligation` and `govoo.contract.milestone` inherit the same domain via their
  `contract_id` relation, once those models exist (issue #174).
- **Source:** addendum §3.2 CM-F16, §4 — "Counterparties/approvers see only their contracts (record
  rules)."

## 7. `govoo.register.entry` — no write/unlink rule needed (handled at access-rights layer)
- As stated in `access-control.md`, this model's protection is `ir.model.access.csv`-level (no
  group gets `write`/`unlink` permission at all), not a record-rule restriction on *which* rows —
  because *no* row may ever be altered by *anyone* through normal means. A record rule is
  insufficient here since it would still need a `write`/`unlink` permission to evaluate against;
  the correct control is withholding the permission entirely, backed by a `write()`/`unlink()`
  Python override raising `UserError` as defense in depth (see `modules/govoo_secretarial.md`).

## 8. Implementation pattern reminder
Every rule above must be expressed as `ir.rule` XML records scoped to the relevant group via
`groups="govoo_base.group_govoo_..."`, domain as sketched above, with `perm_read`/`perm_write`/
`perm_create`/`perm_unlink` set per the access matrix in `access-control.md` §2 — never rely on
domain alone to also imply which CRUD operations are allowed; that is the access-rights layer's job.
