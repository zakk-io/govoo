# Dependency Graph

Source: §3.2, §5, §7, §12 of the source spec.

## 1. Module dependency graph
```
govoo_base
  |-- govoo_secretarial
  |     `-- govoo_shares
  |           `-- govoo_board  (also depends directly on govoo_base)
  |-- govoo_compliance
  |-- govoo_evaluation  (also depends on standard `survey`)
  `-- (Portal + Dashboard depends on ALL of the above)

govoo_rw depends on: govoo_secretarial, govoo_shares, govoo_board, govoo_compliance
                      (source §12 lists govoo_rw depends on "2-5", i.e. secretarial/shares/board/compliance)

govoo_contracts (addendum) depends on: govoo_base, govoo_compliance, govoo_board
                      (addendum §8: board-approval gate needs govoo_board's govoo.resolution;
                       key-date reminders reuse govoo_compliance's engine, not a new one)

govoo_rw_accounting (optional) depends on: govoo_rw, standard `account`
govoo_rw_ebm (optional) depends on: govoo_rw_accounting

(unspecced, future) govoo_ai depends on: govoo_base at minimum (not further specified here)
(unspecced, future) Contract intelligence depends on: govoo_ai, govoo_contracts (addendum §8 step 3)
```

## 2. Model-level dependency chain — governance/board
```
res.partner (standard, extended in govoo_base)
    |
    v
govoo.appointment  (govoo_base)
    |
    v
govoo.committee  (govoo_base)
    |
    v
govoo.meeting  (govoo_board)
    |
    v
govoo.agenda.item  (govoo_board)
    |
    v
govoo.resolution  (govoo_board)
    |
    v
govoo.vote  (govoo_board)  -- weight sourced from govoo.share.holding for shareholder resolutions
```

## 3. Model-level dependency chain — ownership/cap table
```
govoo.share.class  (govoo_shares)
    |
    v
govoo.share.allotment  (govoo_shares)          govoo.share.transfer  (govoo_shares)
    |                                                    |
    +---------------------+-----------------------------+
                           v
                  govoo.share.holding  (govoo_shares, computed/materialized)
                           |
              +------------+-------------+
              v                          v
   govoo.register.member          cap table / voting-power report
   (govoo_secretarial)            (used by govoo.vote weight for shareholder resolutions)
```

## 4. Model-level dependency chain — statutory registers
```
govoo.appointment  ---------> govoo.register.director  (curated view, govoo_secretarial)
govoo.share.holding ---------> govoo.register.member  (govoo_secretarial)
res.partner (govoo_is_beneficial_owner=True) -> govoo.register.beneficial.owner  (govoo_secretarial)
(standalone) -----------------> govoo.register.charge  (govoo_secretarial)

ALL of the above write to:
govoo.register.entry  (govoo_secretarial, append-only audit ledger, independent of mail.message)
```

## 5. Model-level dependency chain — compliance
```
govoo.compliance.obligation (catalogue, seeded as templates by govoo_rw data, inactive until confirmed)
    |
    v  (ir.cron, per govoo.compliance.rule engine logic)
govoo.compliance.instance (per company, per period)
    |
    +--> mail.activity reminders (staged, e.g. -30/-7/-1 days)
    +--> state machine: upcoming -> in_progress -> filed | late -> waived
    +--> filing-pack export (manual submission workflow, since no confirmed RDB/Irembo API)
```

## 6. Cross-module data dependencies (non-obvious, must be respected in implementation order)
| Consumer | Depends on data produced by | Why |
| --- | --- | --- |
| `govoo.vote.weight` (shareholder resolutions) | `govoo.share.holding` (`govoo_shares`) | Weighted voting power must exist before shareholder e-voting can tally correctly. |
| `govoo.register.member` | `govoo.share.holding` | The member register is a curated view over computed holdings, not independent data entry. |
| `govoo.register.director` | `govoo.appointment` | The director register is a curated view over appointments, not independent data entry. |
| `govoo.minutes.retention_until` | `govoo_rw` retention config | Computed field depends on Rwanda retention rule (10 years) shipped as `govoo_rw` data, not a literal in `govoo_board`. |
| `govoo.compliance.instance.due_date` | `govoo_rw` provisional deadline templates + `res.company.govoo_financial_year_end` | FYE-relative obligations need the company's financial year end field (from `govoo_base`) and the (provisional, `[CONFIRM]`) deadline template from `govoo_rw`. |
| Filing-pack export | `govoo.compliance.instance` + relevant register/document data | Must assemble from already-modeled data; do not assume an external API exists (`[CONFIRM]`, source §13 item 6). |
| `govoo.contract.resolution_id` (addendum) | `govoo.resolution` (`govoo_board`) | Board-approval gate (BR-CM-001) reads an actual passed resolution; it cannot exist before `govoo_board` does. |
| `govoo.contract.obligation.due_date` reminders (addendum) | `govoo_compliance`'s reminder/cron engine | Reused directly, not reimplemented, per BR-CM-006 — `govoo_contracts` cannot ship reminders before `govoo_compliance` exists. |
| `govoo.contract.is_related_party` (addendum) | `govoo_base`/`govoo_secretarial` party/relationship data | The conflict check (BR-CM-003) reads existing related-party classification; it does not introduce a second one. |

## 7. Implication for build order
Because `govoo_board`'s shareholder e-voting depends on `govoo_shares`, and `govoo_secretarial`'s
member/director registers depend on both `govoo_base` (appointments) and `govoo_shares` (holdings),
the source build order (§12) is a hard sequencing constraint, not a suggestion:
`govoo_base` → `govoo_secretarial` → `govoo_shares` → `govoo_board`. `govoo_compliance` and
`govoo_evaluation` only need `govoo_base` and can be parallelized. `govoo_rw` must come after
`govoo_secretarial`/`govoo_shares`/`govoo_board`/`govoo_compliance` because it supplies
configuration data those modules consume. `govoo_contracts` (addendum) must come after `govoo_board`
and `govoo_compliance` for the same reason as §6 above — it consumes their data rather than
duplicating it. See `implementation/build-sequence.md`.
