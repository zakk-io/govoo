# Workflow: Contracts

Source: `contract_management_clagov_contracts.md` (the addendum) §3.2, §3.4. Requirements:
FR-CM-06 through FR-CM-14. Models: `govoo.contract`, `govoo.contract.obligation`,
`govoo.contract.milestone`.

## Actor
Contract Manager (draft/submit); Contract Approver (approve within delegation-of-authority limits);
Company Secretary (drafts the linked board resolution in `govoo_board`, where required); the
counterparty (portal, receives/signs).

## Trigger
A new contract is needed — drafted manually, generated from a `govoo.contract.template` (FR-CM-05),
or raised to formalize an already-agreed arrangement.

## Steps (contract lifecycle)
```
draft -> in_approval -> [board-resolution gate] -> [delegation-of-authority check]
                      -> [related-party check] -> approved -> executed (e-signature)
                      -> active -> key-date reminders -> renewal | termination -> expired | terminated
```
1. **Draft:** Contract Manager creates `govoo.contract` (manually, or via
   `action_generate_contract()` from a `govoo.contract.template`, FR-CM-05). Mandatory clauses for
   the `contract_type_id` must be present (FR-CM-04).
2. **Submit for approval:** Contract Manager transitions `draft → in_approval` (FR-CM-06). Routing
   steps (legal → finance → board) are configuration, not hard-coded.
3. **Board-resolution gate (if applicable):** if `contract_type_id.requires_board_approval` or
   `value >= contract_type_id.approval_threshold`, the contract must carry a `resolution_id` whose
   `govoo.resolution.state = 'passed'` before approval can complete (BR-CM-001, FR-CM-07). This
   resolution follows `workflows/resolutions.md` in full — `govoo_contracts` never re-implements
   voting/tallying.
4. **Delegation-of-authority check:** at the point of execution (not merely approval), the acting
   user's signing authority must cover the contract's type/value per the board-approved matrix
   (BR-CM-002, FR-CM-08). This is a hard block, not a warning.
5. **Related-party check:** `is_related_party` is computed from `counterparty_id` against
   `govoo_base`/`govoo_secretarial` interests data (FR-CM-09). If `True`, a conflict-of-interest
   declaration must be recorded before `in_approval → approved` can complete (BR-CM-003).
6. **Approved:** `state → approved` once steps 3-5 (as applicable) are satisfied.
7. **E-signature execution:** Contract Approver (within their delegated authority) initiates
   execution. If Sign is installed **and** e-signature is legally confirmed for the client
   (BR-CM-005), a `sign_request_id` is created; otherwise, a manual signed-copy-upload path is used.
   On completion, `state → executed` and the executed document becomes write-once (BR-CM-004,
   FR-CM-10).
8. **Active:** `state → active` once `date_start` is reached. Key-date reminders begin
   (FR-CM-11) via the *existing* `govoo_compliance` reminder engine (BR-CM-006) — no parallel
   mechanism.
9. **Obligations/milestones:** `govoo.contract.obligation`/`govoo.contract.milestone` rows are
   tracked independently through the contract's active life (FR-CM-13); an obligation's `due_date`
   feeds the same reminder engine as step 8.
10. **Renewal or termination:** as `date_end` approaches, an evergreen contract
    (`renewal_type = 'auto'`) alerts within its `notice_period_days` window (FR-CM-12); the
    Contract Manager renews, renegotiates, or terminates (FR-CM-14). Absent action, the contract
    reaches `state = 'expired'` at `date_end`; an explicit termination reaches
    `state = 'terminated'`. Both are terminal.

## Validation
- Cannot move to `in_approval` without mandatory clauses present (FR-CM-04).
- Cannot move to `approved` without the board-resolution gate (where applicable) and, if
  `is_related_party`, a recorded conflict declaration (BR-CM-001, BR-CM-003).
- Cannot move to `executed` without the delegation-of-authority check passing (BR-CM-002).

## Database changes
- `govoo.contract` create/update; possible `govoo.contract.obligation`/`.milestone` rows created
  alongside; `resolution_id` set (referencing an existing `govoo_board` record, never a new one
  created by this module); `sign_request_id` set on execution (feature-flagged).

## Notifications
- Approval-routing notifications to each configured approver step; execution notification to the
  counterparty (portal, where applicable); renewal/notice-window alerts via the `govoo_compliance`
  reminder engine.

## Documents generated
- Generated contract document (from template); executed/signed version (write-once, BR-CM-004).

## Audit events
- `mail.thread` on `govoo.contract`; `tracking=True` on `state`, `resolution_id`, `sign_request_id`,
  `is_related_party`.

## Portal behavior
- Counterparties/named approvers (Contract Viewer Portal) see their own contract via the standard
  portal record-rule/token mechanism (`security/portal-security.md`) — never another counterparty's
  contract (BR-CM-007).

## Failure scenarios
- Attempting `in_approval → approved` without a passed board resolution (where required) is
  rejected; state remains `in_approval` (BR-CM-001).
- Attempting execution outside the acting user's delegated authority is rejected; state remains
  `approved` (BR-CM-002).
- Attempting approval of a related-party contract with no recorded conflict declaration is rejected
  (BR-CM-003).
- If Documents/Sign (Enterprise) is unavailable, falls back to `ir.attachment`/manual signed-copy
  upload per the feature-flag pattern — the workflow must still complete (AC-09-equivalent for this
  module).

## Completion criteria
- Contract reaches a terminal state (`expired`/`terminated`) or remains `active` with all
  obligations/milestones tracked; the executed document, once set, was never altered in place.

## Acceptance criteria
- See `requirements/acceptance-criteria.md` AC-11, AC-12; also FR-CM-06 through FR-CM-14 acceptance
  criteria in `requirements/product-requirements.md`.
