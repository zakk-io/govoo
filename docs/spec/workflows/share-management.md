# Workflow: Share Management (cap table)

Source: §7.3 (share lifecycle summary in the master prompt). Requirements: FR-SHARE-001..005.
Models: `govoo.share.class`, `govoo.share.allotment`, `govoo.share.transfer`,
`govoo.share.holding`.

## Actor
Company Secretary (drives all steps); transferor/transferee (portal, sign if enabled).

## Lifecycle
```
share class -> allotment -> holding calculation -> transfer -> registration -> updated ownership
```

## Steps

### A. Share class setup
1. Secretary creates `govoo.share.class`: `name`, `nominal_value`, `currency_id` (RWF default),
   `votes_per_share`, `total_authorised`.

### B. Allotment (issuance)
1. Secretary creates `govoo.share.allotment`: `share_class_id`, `partner_id` (allottee), `quantity`,
   `price_per_share`, `date_allotted`.
2. System validates cumulative allotments for the class do not exceed `total_authorised`
   (BR-SHARE-001) — rejects if they would.
3. On save, system triggers `govoo.share.holding` recompute for `(partner_id, share_class_id)`
   (FR-SHARE-004).
4. `govoo.register.member` (in `govoo_secretarial`) reflects the new/updated holder.

### C. Transfer
1. Secretary (or a party via portal, if that entry point is enabled) creates
   `govoo.share.transfer` (`state = 'draft'`): `share_class_id`, `transferor_id`, `transferee_id`,
   `quantity`, `price`.
2. Secretary transitions `draft → approved` (internal review/sign-off).
3. If Sign is enabled and legally confirmed, a `sign_request_id` is created and both parties sign;
   otherwise a manual instrument upload is used.
4. Secretary transitions `approved → registered`. System **re-checks** at this point that
   `quantity <=` transferor's *current* holding (BR-SHARE-002) — not just at draft creation, since
   holdings may have changed since.
5. On `registered`, system triggers `govoo.share.holding` recompute for both `transferor_id` and
   `transferee_id`.
6. `govoo.register.member` updates: `date_ceased` set for the transferor if their aggregate holding
   across all classes reaches zero; `date_entered` set for the transferee if this is their first
   holding.

### D. Holding recomputation (system-triggered, both from B and C)
1. Recompute `quantity` per `(partner, share_class)` from `sum(allotments) - sum(registered
   transfers out) + sum(registered transfers in)`.
2. Recompute `percentage = quantity / total_allotted_in_class` (validated to sum to 100% across all
   holders of the class — BR-SHARE-003).
3. Recompute `voting_power` from `quantity * share_class.votes_per_share`, normalized for use as
   `govoo.vote.weight` on shareholder resolutions (FR-BOARD-006).

## Validation
- BR-SHARE-001 (allotment vs authorized capacity).
- BR-SHARE-002 (transfer vs current holding).
- BR-SHARE-003 (percentages sum to 100%).

## Database changes
- `govoo.share.allotment` / `govoo.share.transfer` create/update; `govoo.share.holding` recompute
  (stored); `govoo.register.member` update.

## Notifications
- `mail.thread` messages on allotment/transfer records; portal notification to transferor/
  transferee at each state transition (if Sign/portal flow is used).

## Documents generated
- Share certificate (`certificate_document_id`); transfer instrument (`transfer_instrument_id`).

## Audit events
- `mail.thread`; `tracking=True` on `quantity`, `state`; `govoo.register.entry` ledger entry via
  `govoo_secretarial`'s register-of-members logic.

## Portal behavior
- Shareholder Portal users see their own `govoo.share.holding` rows only (record rule,
  `security/record-rules.md` §3); they may be a party to a transfer (transferor/transferee) with
  read access to that specific transfer record `[ENGINEERING DETAIL — exact portal exposure of
  transfer records as a party, not itemized field-by-field in source]`.

## Failure scenarios
- Over-allotment or over-transfer → `ValidationError`, no state change.
- GL posting hook fires unexpectedly → this must never happen; hook is off by default (FR-SHARE-005)
  and any code path that posts to `account.move` without the feature being explicitly enabled is a
  defect.

## Completion criteria
- Transfer reaches `registered`; holdings recomputed and percentages sum to 100%; register of
  members reflects current holders.

## Acceptance criteria
- See AC-02 in `requirements/acceptance-criteria.md`.
