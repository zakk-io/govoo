# Data Model — Relationships

Source: §5, §7 of the source spec, cross-referenced with `architecture/dependency-graph.md`
(module-level view). This file gives the field-level relationship (cardinality) detail.

## 1. Governance/board relationship chain
```
res.partner (1) ----< (M) govoo.appointment (M) >---- (1) res.company
govoo.appointment (M) >---- (0..1) govoo.committee
govoo.committee (0..1 parent) self-referential (board vs sub-committee)
govoo.committee (1) ----< (M) govoo.meeting
govoo.meeting (1) ----< (M) govoo.agenda.item
govoo.meeting (1) ---- (0..1) govoo.board.pack
govoo.meeting (1) ---- (0..1) govoo.minutes
govoo.agenda.item (1) ----< (M) govoo.resolution   [also: govoo.resolution.meeting_id nullable for written resolutions]
govoo.resolution (1) ----< (M) govoo.vote
govoo.vote (M) >---- (1) res.partner [voter_id]
govoo.meeting (1) ---- (0..1) calendar.event [calendar_event_id]
```

## 2. Ownership/cap-table relationship chain
```
res.company (1) ----< (M) govoo.share.class
govoo.share.class (1) ----< (M) govoo.share.allotment
govoo.share.class (1) ----< (M) govoo.share.transfer
govoo.share.allotment (M) >---- (1) res.partner [partner_id, allottee]
govoo.share.transfer (M) >---- (1) res.partner [transferor_id]
govoo.share.transfer (M) >---- (1) res.partner [transferee_id]

(allotments - registered transfers) ----> govoo.share.holding  [derived, keyed on (partner_id, share_class_id)]
govoo.share.holding (M) >---- (1) res.partner
govoo.share.holding (M) >---- (1) govoo.share.class
govoo.share.holding (1) ----< used by ----> govoo.register.member.holding_ids
govoo.share.holding.voting_power ----> used as ----> govoo.vote.weight (shareholder resolutions only)
```

## 3. Statutory register relationship chain
```
govoo.appointment -------------------> govoo.register.director   (curated view, 1:1-ish per appointment)
govoo.share.holding -------------------> govoo.register.member    (curated, keyed on partner_id)
res.partner (govoo_is_beneficial_owner) -> govoo.register.beneficial.owner (M) >---- (1) res.company
(standalone entry) --------------------> govoo.register.charge (M) >---- (1) res.company

ALL FOUR (create/update/cease) ---------> govoo.register.entry (append-only, 1 entry per change event,
                                            keyed on register_model + res_id, not a foreign key —
                                            deliberately polymorphic reference, see note below)
```
**Note on `govoo.register.entry`'s polymorphic reference:** the source defines `register_model`
(Char) + `res_id` (Integer) rather than a `reference` field or four separate optional FKs. This is a
deliberate, generic pattern so the ledger works uniformly across all four (and any future) register
models without schema change. Implementation should NOT replace this with per-register foreign
keys — that would violate the append-only, model-agnostic design intent (source §7.2.5).

## 4. Compliance relationship chain
```
govoo.compliance.obligation (1) ----< (M) govoo.compliance.instance
govoo.compliance.instance (M) >---- (1) res.company
govoo.compliance.instance (M) >---- (0..1) res.users [responsible_id]
govoo.compliance.instance ----> generates ----> mail.activity (staged reminders, not a stored FK
                                                  relationship — created via `mail.activity` API)
```

## 5. Evaluation relationship chain
```
govoo.committee (0..1) ----< (M) govoo.evaluation.campaign
govoo.evaluation.campaign (1) ---- (1) survey.survey
govoo.evaluation.campaign (M) >---< (M) res.partner [participant_ids]
survey.survey (1) ----< (M) survey.user_input  (standard Odoo)
survey.user_input (M) ----> aggregated into ----> govoo.evaluation.result (per campaign/dimension)
```

## 6. Cross-module relationships requiring careful FK/dependency direction
| Relationship | Direction | Why this direction (not the reverse) |
| --- | --- | --- |
| `govoo.vote.weight` reads `govoo.share.holding.voting_power` | `govoo_board` → `govoo_shares` (read-only dependency) | `govoo_board` depends on `govoo_shares` per the build order; `govoo_shares` never references `govoo.vote` |
| `govoo.register.member.holding_ids` reads `govoo.share.holding` | `govoo_secretarial` ← `govoo_shares` (secretarial consumes shares' output) | Statutory register presentation is `govoo_secretarial`'s job; the underlying computation is `govoo_shares`'s |
| `govoo.minutes.retention_until` reads `govoo_rw` retention config | `govoo_board` → `govoo_rw` (config dependency, not a hard code dependency) | `[ENGINEERING DETAIL]` implement via `ir.config_parameter` lookup rather than a Python import of `govoo_rw`, so `govoo_board` does not need a hard module dependency on `govoo_rw` for deployments that never localize to Rwanda |
| `govoo.compliance.instance.due_date` reads `govoo_rw` deadline templates | `govoo_compliance` → `govoo_rw` (data dependency) | Same rationale — obligation catalogue rows are data seeded BY `govoo_rw`, not a code dependency FROM `govoo_compliance` TO `govoo_rw` |

## 7. Foreign key / index guidance (`[RECOMMENDED]`, not explicit in source)
- Index `company_id` on every model that has it (multi-company query performance).
- Index `(partner_id, share_class_id)` on `govoo.share.holding` (frequent lookup key).
- Index `(register_model, res_id)` on `govoo.register.entry` (frequent lookup key for
  "show me this record's history").
- Index `due_date` and `state` on `govoo.compliance.instance` (dashboard/cron query patterns).
