# Workflow: Resolutions

Source: §7.4.5, §7.4.6 (resolution lifecycle summary in the master prompt). Requirement:
FR-BOARD-005. Model: `govoo.resolution`.

## Actor
Company Secretary (draft/open); eligible directors/shareholders (vote — see `workflows/voting.md`
for the voting sub-workflow); Board Administrator (configure only, cannot vote).

## Trigger
A decision requiring board/committee or shareholder approval arises — either linked to a meeting's
decision-type agenda item, or as a standalone written resolution (`meeting_id` null).

## Steps (resolution lifecycle)
```
draft -> open -> eligible voters notified -> voting -> tally -> passed/failed
                                                              -> optional signing
                                                              -> document storage
                                                              -> register update where applicable
```
1. **Draft:** Secretary creates `govoo.resolution`: `title`, `text`, `resolution_type`
   (ordinary/special/written), optionally `meeting_id` and `agenda_item` linkage.
2. **Open:** Secretary transitions `draft → open`. System identifies eligible voters (committee
   members for board/committee resolutions; shareholders with a nonzero voting-class holding for
   shareholder resolutions — see `security/record-rules.md` §4).
3. **Eligible voters notified:** `mail.activity`/portal notification to each eligible voter.
4. **Voting:** eligible voters cast `govoo.vote` rows (see `workflows/voting.md` for full detail on
   weight sourcing and conflicted-vote handling).
5. **Tally:** system computes `result` from `vote_ids`, applying quorum and the majority threshold
   appropriate to `resolution_type` (BR-BOARD-005) — thresholds are configuration, following the
   client's articles of association, `[CONFIRM per company articles / Rwandan law]`.
6. **Passed / failed:** `state` set accordingly. `open → withdrawn` is also possible if the
   Secretary withdraws before a tally is finalized.
7. **Optional signing:** if the resolution requires a signed record (e.g. a written resolution) and
   Sign is enabled/confirmed (BR-BOARD-008), a `sign_request_id` is created.
8. **Document storage:** the executed resolution document is stored (Documents/`ir.attachment`
   fallback).
9. **Register update where applicable:** if the resolution affects capital (triggers a
   `govoo_shares` transaction) or directors (triggers a `govoo_base`/`govoo_secretarial`
   appointment/register change), that downstream update is performed — this is a cross-module
   consequence, not automatic unless explicitly wired by the implementer
   `[ENGINEERING DETAIL — source describes this at the workflow-narrative level; the exact trigger
   mechanism (manual follow-up action vs. automatic cascade) is not specified — CONFIRM]`.

## Validation
- Cannot move to `open` without eligible voters identified.
- Cannot move to `passed`/`failed` without a completed tally (BR-BOARD-005).

## Database changes
- `govoo.resolution` create/update; `govoo.vote` rows created during voting; possible downstream
  `govoo.share.allotment`/`transfer` or `govoo.appointment` records if the resolution triggers a
  capital/director change.

## Notifications
- Eligible-voter notification on `open`; result notification on `passed`/`failed`.

## Documents generated
- Executed resolution document; signed copy if applicable.

## Audit events
- `mail.thread`; `tracking=True` on `state`, `result`.

## Portal behavior
- Director/Shareholder Portal users see resolutions they are eligible to vote on
  (`security/record-rules.md` §4) and cast their vote there.

## Failure scenarios
- Tally that cannot resolve cleanly (e.g. missing weight data due to an un-synced
  `govoo.share.holding`) must not silently default to `passed` or `failed` — surface an error and
  block the transition until data integrity is restored `[RECOMMENDED]`.

## Completion criteria
- Resolution reaches a terminal state (`passed`/`failed`/`withdrawn`); if `passed`, downstream
  effects (document storage, register update where applicable) are complete.

## Acceptance criteria
- See AC-01 in `requirements/acceptance-criteria.md`; also FR-BOARD-005/006 acceptance criteria.
