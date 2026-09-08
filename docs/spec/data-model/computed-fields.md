# Data Model — Computed Fields

Source: §7 field tables (columns marked "computed") of the source spec. Every computed field is
listed here with its dependency graph, storage decision, and recompute trigger, so an implementer
does not need to infer these from the model tables alone.

| Field | Model | Depends on | Stored? | Recompute trigger | Notes |
| --- | --- | --- | --- | --- | --- |
| `state` | `govoo.appointment` | `date_appointed`, `date_resigned` | Yes (needed for search/filter) | Write to either dependency | Never directly user-editable; see `data-model/state-machines.md` |
| `quorum_met` | `govoo.meeting` | `attendee_ids` (confirmed subset), `quorum_required` | Yes | Attendance recorded / `quorum_required` changed | Exact "confirmed attendance" definition `[ENGINEERING DETAIL — recommend a dedicated `confirmed_attendee_ids` or an `attendance_state` on the attendee relation, since `attendee_ids` alone doesn't distinguish invited-vs-attended]` |
| `result` | `govoo.resolution` | `vote_ids` (choice, weight, is_conflicted), `resolution_type`, quorum config | Yes | Vote cast/changed; resolution closed | Computation detailed in `workflows/voting.md` |
| `retention_until` | `govoo.minutes` | `create_date` (or `date` of the meeting), `govoo_rw` retention config (10 years) | Yes | Record creation; retention config change (rare) | Must read config, not a literal — BR-BOARD-004 |
| `quantity`, `percentage`, `voting_power` | `govoo.share.holding` | `govoo.share.allotment` (sum per partner/class), `govoo.share.transfer` (registered only) | Yes (materialized) | Allotment `create()`; transfer `state → 'registered'` | This model IS the computed layer for the cap table — see FR-SHARE-004 |
| `state` (transition eligibility check, not the field itself) | `govoo.compliance.instance` | `due_date`, current date, prior `state` | N/A — `state` itself is source data set by user/cron, but the *late* transition is computed | Daily cron evaluation | See BR-COMP-003 |
| `due_date` | `govoo.compliance.instance` | `obligation_id.basis`, `obligation_id.frequency`, `res.company.govoo_financial_year_end` (if `fye_relative`), `govoo_rw` deadline template data (if seeded from Rwanda templates) | Yes (set at instance-generation time, not re-derived live) | Instance generation (cron) | Must never be a literal — BR-COMP-002 |
| `aggregate_score`, `participant_count` | `govoo.evaluation.result` | `survey.user_input` rows for the campaign | Yes | Campaign `state → 'closed'` (or on demand, `[ENGINEERING DETAIL]`) | Must never expose per-respondent data through this computation — BR-EVAL-001 |

## General rules for computed fields in this system
1. **Store when the field is used in search/filter/report or read frequently** (e.g. dashboards,
   list-view columns) — all fields in the table above meet this bar and are `store=True`.
2. **Never allow direct user edits to a computed field** — no `inverse=` method should let a user
   silently overwrite `state`, `quorum_met`, `result`, `retention_until`, or any `govoo.share.holding`
   field. If manual correction is ever needed, it happens through the *source data* (e.g. correcting
   a mis-entered allotment), which then triggers a legitimate recompute — not through editing the
   derived field.
3. **Recompute must be idempotent and safe to re-run** — re-running the holdings recompute (or any
   other computed field's dependency chain) twice in a row must produce the same result.
4. **Legal/statutory values feeding a computation are configuration, read at compute time, never a
   Python literal inside the `@api.depends` method body** — applies especially to `retention_until`
   and `due_date`. See `data-model/constraints.md` §3.
