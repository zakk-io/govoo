# Workflow: Voting (e-voting)

Source: §7.4.6. Requirement: FR-BOARD-006. Model: `govoo.vote`.

## Actor
Eligible voters (directors for board/committee resolutions; shareholders for shareholder
resolutions). Board Administrator explicitly excluded (BR-SEC-004).

## Trigger
A `govoo.resolution` reaches `state = 'open'`.

## Steps
1. System determines the eligible-voter set for the resolution:
   - Board/committee resolution: active `govoo.appointment` holders of the relevant `committee_id`.
   - Shareholder resolution: partners with a nonzero `govoo.share.holding` in a voting share class
     of the resolution's company at the time voting opens.
2. Each eligible voter casts a `govoo.vote`: `choice` (for/against/abstain), optionally flags
   `is_conflicted = True` if they have a declared interest.
3. System sets `weight`:
   - Board/committee resolution: `weight = 1.0` per director (one member, one vote).
   - Shareholder resolution: `weight` = the voter's `govoo.share.holding.voting_power` at the time
     of voting (sourced from `govoo_shares`, FR-SHARE-004).
4. System sets `timestamp` at the moment the vote is cast; the vote row becomes immutable after
   this point.
5. On resolution close (Secretary action or automatic per a configured voting window
   `[ENGINEERING DETAIL — automatic close-on-deadline not specified in source; assume manual close
   by Secretary unless/until a deadline field is added]`), system tallies:
   - Votes with `is_conflicted = True` are excluded from the tally where the applicable governance
     rule requires exclusion of conflicted votes (BR-BOARD-007).
   - Remaining `for`/`against`/`abstain` weights are summed.
   - `result` = `passed` if quorum is met AND the sum of `for` weight clears the majority threshold
     appropriate to `resolution_type` (simple majority for `ordinary`, higher threshold for
     `special` — exact percentage `[CONFIRM per company articles / Rwandan law]`); otherwise
     `failed`.
6. Resolution `state` is set to `passed`/`failed` accordingly (see `workflows/resolutions.md`).

## Validation
- One vote per `(resolution_id, voter_id)` — duplicate-vote behavior (reject vs. overwrite)
  `[CONFIRM]`, not explicit in source.
- `choice` required.

## Database changes
- `govoo.vote` create; `govoo.resolution.result`/`state` update on tally.

## Notifications
- Confirmation to the voter that their vote was recorded; result notification to all eligible
  voters once tallied.

## Documents generated
- None directly (the resolution document itself is handled in `workflows/resolutions.md`).

## Audit events
- `mail.thread` on the resolution; each `govoo.vote` row is itself an audit-relevant record
  (immutable `timestamp`).

## Portal behavior
- Eligible Director/Shareholder Portal users cast their vote via the portal, subject to the record
  rules in `security/record-rules.md` §4 — a portal user may only create a vote row where
  `voter_id = user.partner_id`.

## Failure scenarios
- Board Administrator attempting to vote → denied at the access-rights layer (no `create`
  permission on `govoo.vote` for that group), not merely a record-rule filter (see
  `security/access-control.md` §5).
- A voter attempting to vote on a resolution they are not eligible for (wrong committee, no
  shareholding) → denied by record rule.
- A second vote attempt by the same voter → behavior `[CONFIRM]` (reject vs. overwrite).

## Completion criteria
- All eligible voters have either voted or the voting window has closed; tally is computed and
  resolution state set accordingly.

## Acceptance criteria
- See AC-01, AC-06 in `requirements/acceptance-criteria.md`; also FR-BOARD-006 acceptance criteria.
