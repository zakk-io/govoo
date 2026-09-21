# Data Model — Constraints

Source: §7 (field tables), §8, §9, §13 of the source spec. This file consolidates every validation
constraint and, critically, every place a value MUST remain configurable rather than hard-coded.

## 1. Field-level validation constraints (by model)
| Model | Field(s) | Constraint | Source |
| --- | --- | --- | --- |
| `res.partner` | `govoo_date_of_birth` | Must be a past date if set | §7.1.1 (engineering addition) |
| `govoo.appointment` | `date_resigned` | `>= date_appointed` when set | §7.1.3 |
| `govoo.committee` | `parent_committee_id` | Same `company_id`; no cycles | §7.1.4 |
| `govoo.register.member` | `date_ceased` | `>= date_entered` when both set | §7.2.2 |
| `govoo.register.beneficial.owner` | `nature_of_control` | Required before record marked complete | §7.2.3 |
| `govoo.register.charge` | `amount` | `> 0` | §7.2.4 |
| `govoo.register.charge` | `date_registered` | `>= date_created` when both set | §7.2.4 |
| `govoo.register.entry` | (all) | `write()`/`unlink()` forbidden for every group | §7.2.5 |
| `govoo.share.class` | `total_authorised` | `> 0` | §7.3.1 |
| `govoo.share.class` | `nominal_value` | `>= 0` | §7.3.1 |
| `govoo.share.allotment` | `quantity` | `> 0`; cumulative <= `share_class.total_authorised` | §7.3.1, §7.3.2 |
| `govoo.share.transfer` | `quantity` | `> 0`; `<=` transferor's current holding at registration | §7.3.3 |
| `govoo.share.transfer` | `transferor_id`/`transferee_id` | Must differ | §7.3.3 (engineering addition) |
| `govoo.share.holding` | `percentage` (per class) | All holders' percentages sum to 100% (or 0%) | §7.3.4 |
| `govoo.share.holding` | `quantity` | Never negative; a would-be-negative recompute raises | §7.3.4 (engineering addition) |
| `govoo.meeting` | `quorum_required` | `> 0` | §7.4.1 |
| `govoo.vote` | `(resolution_id, voter_id)` | Unique — one vote per voter per resolution; exact re-vote behavior `[CONFIRM]` | §7.4.6 |
| `govoo.compliance.obligation` | `lead_time_days` | `>= 0` | §7.5.1 |
| `govoo.compliance.instance` | `(obligation_id, company_id, period)` | Unique — no duplicate instance | §7.5.2 (engineering addition) |
| `govoo.contract` | `date_end` | `>= date_start` when both set | addendum §3.3 (engineering addition) |
| `govoo.contract` | `value` | `>= 0` when set | addendum §3.3 (engineering addition) |
| `govoo.contract.obligation` | `due_date` | Required | addendum §3.3 |
| `govoo.contract.type` | `approval_threshold` | `>= 0` when set | addendum §3.4 (engineering addition) |

## 2. Multi-company constraints (every transactional model)
Every model listed in `data-model/entities.md` §1 has `company_id` with `check_company=True`, and is
subject to the standard record-rule pattern in `security/record-rules.md`. This is not optional per
model — it is a blanket rule from source §6.2.

## 3. Configurability constraints — values that MUST NEVER be hard-coded (source §8, §9, closing
disclaimer — the single most important constraint category in the whole system)
| Value category | Where it would be tempting to hard-code | Where it MUST live instead | Confirmation gate |
| --- | --- | --- | --- |
| Tax rates (CIT, VAT, PAYE, WHT, RSSB) | `govoo_rw_accounting` tax code Python | `account.tax` / config records | Tax/legal advisor (§13 item 5) |
| Statutory filing deadlines | `govoo_compliance` cron logic | `govoo.compliance.obligation` data rows, `active=False` until confirmed | Rwandan advisor (§13 item 5) |
| Beneficial-ownership thresholds | `govoo.register.beneficial.owner` selection values | Configurable selection/data, provisional | Legal advisor (§13 item 4) |
| Retention periods | `govoo.minutes`/register computed-field Python | `govoo_rw` retention config | Legal/DPO (§10.3) |
| Legal article numbers (any obligation description referencing a specific law article) | Free text or code comments treated as fact | Data field, clearly labelled as reference, not enforcement logic | Legal advisor |
| RPO/RTO targets | DevOps runbook as fixed numbers | Config per environment tier, `[CONFIRM]` | DevOps + sponsor (§13 item 8) |
| Annual-return filing window | `govoo_rw` obligation seed | Data row, `active=False`, `[CONFIRM exact window]` | Tax/legal advisor (§13 item 5) |
| Contract board-approval thresholds/qualifying types | `govoo_contracts` approval-gating Python | `govoo.contract.type.approval_threshold`/`requires_board_approval` data, inactive/zero until confirmed | Client board/counsel (addendum §9 item 4) |
| Delegation-of-authority (signing) matrix | `govoo_contracts` execution-gating Python | Configurable data, never a hard-coded limit | Client board (addendum §9 item 5) |

**Enforcement mechanism (`[RECOMMENDED]`):** a CI lint rule/grep check that fails the build if a
percentage, currency amount, or date literal appears inside `govoo_rw`, `govoo_compliance`,
`govoo_contracts`, or `govoo_rw_accounting` Python files outside of `tests/` — forcing such values
into `data/` XML/CSV or `ir.config_parameter` instead. `govoo_contracts` is added to this list here
because it introduces the same class of confirmable threshold/matrix values (board-approval
thresholds, delegation-of-authority limits) as `govoo_rw`/`govoo_compliance`'s tax/deadline values —
see `devops/ci-cd.md` §1 step 6.

## 4. `[CONFIRM]` items represented as inactive/configurable data (cross-reference)
Every row in the table above traces to `decisions/open-decisions.md`. No `[CONFIRM]` item may be
converted to `active = True` seed data, a hard default, or authoritative UI copy without a
corresponding entry being added to `decisions/confirmed-decisions.md` recording who confirmed it
and when.

## 5. Referential-integrity constraints (`[RECOMMENDED]`, not all explicit in source but implied by
the model design)
- `ondelete` policy: register/audit models (`govoo.register.entry`, `govoo.share.holding`) should
  use `ondelete='restrict'` on their partner/company FKs rather than `cascade`, so deleting a
  partner does not silently destroy statutory history — deactivation, not deletion, is the expected
  lifecycle for a `res.partner` with governance history.
- `govoo.vote` rows are immutable once `timestamp` is set — no `ondelete='cascade'` from
  `govoo.resolution` that would let deleting a draft resolution silently discard cast votes; discard
  is only valid while `state = 'draft'` and no votes exist yet.
