# Role × Top-Task Matrix

Click counts are estimates derived from the `step`/`task` text in the raw findings, counting each navigation/open/field-entry/submit action as one click. Where a task was only exercised on one viewport, the other viewport's feasibility is marked "not tested" rather than guessed.

## Company Secretary

| Top task | Steps to complete | Est. clicks | Viewport feasibility | Notes |
|---|---|---|---|---|
| Find the board pack for a specific meeting | Board & Meetings → Board Packs → (list shows only raw IDs, no identifying columns) → open record 1 → not it → open record 2 → … | 2 to reach list, then **up to 10 blind opens** (worst case, no way to target the right one) | Desktop-only tested | SEC-001 (critical) — task is effectively broken, not just slow |
| Review Governance Settings before relying on statutory deadlines | Configuration → Governance Settings → read form → hover each "?" tooltip to learn fields are unconfirmed placeholders | 2 clicks + up to 4 hover-discoveries | Desktop-only tested | SEC-003 — the "steps to complete" undercount the actual cognitive work since nothing is visible without hovering |
| Verify who was reminded to vote / voted on a resolution | Board & Meetings → Resolutions → open resolution → read chatter/activity panel | 2-3 clicks | Desktop-only tested | SEC-004 — task completes but gives a false answer (OdooBot, not the real director) |
| "What needs my attention today" (home screen triage) | Land on Dashboard (0 extra clicks) → read 3 widgets → scroll each widget's internal horizontal scrollbar to see Status/Date | 0 clicks to arrive, 3 extra scroll gestures to read the actually-useful columns | **Desktop: degraded** (needs inner scroll even at 1440px) · **Mobile: broken** (SEC-005, only the title column is visible, status/date fully hidden) | Fails the 5-second test on both viewports, catastrophically on mobile |
| Find meetings/compliance items needing action | Board & Meetings → Meetings (or Compliance → Instances) → manually apply "Upcoming" filter (not default) | 2 clicks to reach + 1 click to filter every session | Desktop-only tested | SEC-006 — works, but adds a repeated manual step every single session |
| Create a new meeting without hitting an unclear validation error | Board & Meetings → Meetings → New → fill fields (no asterisk cues) → Save → re-fill after red-highlight-only error | 3 clicks + 1 retry round-trip | Desktop-only tested | SEC-007 |

## Board Administrator

| Top task | Steps to complete | Est. clicks | Viewport feasibility | Notes |
|---|---|---|---|---|
| (Attempted, should be blocked) Edit a board meeting | Board & Meetings → Meetings → open meeting → edit Meeting Name field → Save | 4 clicks | Desktop-only tested (role restricted to desktop this pass) | BOA-001 (critical) — completes successfully when it should fail; no viewport-dependent mitigation exists since this is an access-control gap, not a layout one |
| Review statutory deadline configuration | Configuration → Governance Settings → read Statutory Deadlines section | 2 clicks | Desktop-only tested | BOA-003 — all 4 values read as 0, indistinguishable from "not yet configured" |
| Review the Register of Charges for data integrity | Statutory Registers → Register of Charges → scan rows | 2 clicks | Desktop-only tested | BOA-004 (critical) — task surfaces a live test-fixture record mixed into real statutory data |
| Trace a statutory register change to a responsible person | Statutory Registers → Audit Ledger → scan "Register" and "Changed By" columns | 2 clicks | Desktop-only tested | BOA-005/BOA-006 — task technically completes but the answer is uninformative (raw model names, 100% "OdooBot") |
| Check AI usage transparency | AI → Request Log → scan Feature/Model Used columns | 2 clicks | Desktop-only tested | BOA-009 — low-severity microcopy issue only |

## Director (Portal)

| Top task | Steps to complete | Est. clicks | Viewport feasibility | Notes |
|---|---|---|---|---|
| View a meeting's details | Login → Home → My Meetings → open a meeting | 3 clicks | **Mobile tested — broken for access scope** (DIR-001, critical: committee-restricted director can open other committees' meetings) | The layout itself renders fine on mobile; the defect is a data-access leak, not a responsive-design issue |
| Cast a vote on a board resolution | Home → My Votes → open vote → select For/Against/Abstain (+ COI checkbox) → Submit Vote | 4-5 clicks | **Desktop: completes but no confirmation (DIR-002)** · **Mobile: completes, same missing confirmation, plus undersized tap targets (DIR-006)** | Both viewports "complete" the task technically but leave the director unsure it worked |
| Understand what a resolution says before voting | My Votes → open vote → (no resolution text, no link to meeting) | 2 clicks, but **dead end** — no further navigation reaches the full text | Desktop-only tested | DIR-003 — task cannot actually be completed as intended; informed voting is not possible from this screen |
| Find the next upcoming meeting among many | Home → My Meetings → manually scan flat list of 11 | 2 clicks + manual scan (no filter/sort) | Desktop-only tested | DIR-005 |
| Recover from a bad/stale meeting link | Click a stale link / mistyped URL → silently redirected to Home with no message | 1 click (but gives no feedback) | Desktop-only tested | DIR-004 — fail-safe but confusing |

## Shareholder (Portal)

| Top task | Steps to complete | Est. clicks | Viewport feasibility | Notes |
|---|---|---|---|---|
| Check my shareholding (quantity, %, voting power) | Login → Home → My Holdings | 2 clicks | Desktop tested; **mobile not evaluated in findings** (listed as coverage gap) | SHA-005 — page loads, but unformatted "Voting Power: 30000.0" and no heading/context |
| Cast a vote on a shareholder resolution | Home → My Votes → open vote → select For/Against/Abstain (+ COI checkbox) → Submit Vote | 4-5 clicks | **Desktop: completes but no voting-weight shown before submit (SHA-001, critical) and no confirmation after (SHA-002)** · **Mobile: cast flow NOT re-verified** — only one open resolution existed and it was consumed by the desktop pass, so mobile shows the correct empty state but the live cast-vote form itself is "not tested" on mobile this pass | Desktop is the only viewport where the actual voting flow was observed end-to-end |
| Notice a vote is pending on login | Login → Home (0 extra clicks) | 0 clicks | Desktop-only tested | SHA-003 — task fails silently: no badge/callout, shareholder must guess to check My Votes |
| Move between Holdings / Votes / Register | My Holdings → Home (icon only, no label) → My Votes | 2 round-trip clicks per hop (no direct sibling nav) | Desktop + Mobile both show the same gap | SHA-007 — works on both viewports, just inefficient on both |

## Auditor (Read-only)

| Top task | Steps to complete | Est. clicks | Viewport feasibility | Notes |
|---|---|---|---|---|
| Confirm the session is genuinely read-only before relying on it | Open a Meeting, a Compliance Instance, and a Resolution → inspect statusbar/header buttons | 2-3 clicks per record × 3 records ≈ 6-9 clicks | Desktop-only tested (role restricted to desktop this pass) | AUD-001 (high) — buttons appear live (not disabled); live click-through was intentionally not performed (harness risk control), so the actual failure behavior on click is itself a coverage gap |
| Reconstruct who-did-what-when on a statutory record | Open a Meeting (multi-transition) or Minuted AGM → scroll chatter | 2 clicks + scroll | Desktop-only tested | AUD-002 (high) — task fails: chatter shows only the original "created by OdooBot" entry, no transition history |
| Survey what modules this role can access | Click each top-level menu in turn | 1 click per menu × 8 menus | Desktop-only tested | AUD-004 — 2 of 8 top menus (Contract Management, Evaluations) are dead ends with no explanation |
| 5-second "am I in a restricted view" check | Land on Dashboard | 0 clicks | Desktop-only tested | AUD-005 — fails; dashboard is identical to every other role's, including a false "my vote" prompt |

## Cross-role observation

No top task for any role was fully exercised on **both** Desktop 1440x900 and Mobile 390x844 with a clean pass on both. Where mobile was tested at all (Director, Secretary's dashboard, Shareholder's post-vote empty state), it either reproduced the same defect as desktop (DIR-001, DIR-002) or made it worse (SEC-005 critical mobile table collapse, DIR-006 tap targets). Board Administrator and Auditor were restricted to desktop only per this pass's explicit scope, so their mobile feasibility is "not tested," not "passed."
