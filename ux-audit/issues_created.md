# Issues Created — Govoo UX Audit + Clagov Brand/UX Spec Reconciliation

Filed 2026-10-06 via GitHub MCP, from `ux-audit-evidence` branch evidence. 15 issues total
(Track A's "Issue 8" was deliberately **not** filed standalone — its findings and screenshots
were absorbed into Epic P3 / #252 instead, per the merge decision in `MANAGER_SPEC_ANALYSIS.md`).

## Track A — Governance-Critical Fixes (9 filed)

| # | Title | Priority | Effort |
|---|---|---|---|
| [#241](https://github.com/zakk-io/govoo/issues/241) | Statutory Register of Charges contains visible test/QA fixture data | P0 | S |
| [#242](https://github.com/zakk-io/govoo/issues/242) | Governance Settings shows statutory deadlines as "0" with no visible explanation | P1 | S |
| [#243](https://github.com/zakk-io/govoo/issues/243) | Resolution vote-reminder activities are assigned to the system account, not the voting director | P1 | M |
| [#244](https://github.com/zakk-io/govoo/issues/244) | Minutes, Board Pack, and Governance Settings forms show raw technical identifiers as their title | P1 | M |
| [#245](https://github.com/zakk-io/govoo/issues/245) | Board Administrator can actually edit locked records; Auditor sees write buttons the database will reject | P0 | M |
| [#246](https://github.com/zakk-io/govoo/issues/246) | Portal voting flow gives no voting-weight disclosure, no resolution text, and no submission confirmation | P0 | M |
| [#247](https://github.com/zakk-io/govoo/issues/247) | Board Packs list and Audit Ledger/AI Request Log columns show no usable, human-readable content | P0 | M |
| — | ~~Issue 8 — Dashboard is identical for every role~~ | — | — | **Not filed — absorbed into #252** |
| [#248](https://github.com/zakk-io/govoo/issues/248) | Chatter and Audit Ledger show zero real user attribution for statutory record changes | P1 | L |
| [#249](https://github.com/zakk-io/govoo/issues/249) | Director can view meetings and board packs of committees they are not a member of | P0 | M |

## Track B — Clagov Brand & UX Uplift (6 filed)

| # | Title | Priority | Effort |
|---|---|---|---|
| [#250](https://github.com/zakk-io/govoo/issues/250) | Epic P1 — No Clagov brand identity exists anywhere in the product | P1 | L |
| [#251](https://github.com/zakk-io/govoo/issues/251) | Epic P2 — Kanban cards are text-only; lists lack status colour, widgets, default sort/group | P2 | L |
| [#252](https://github.com/zakk-io/govoo/issues/252) | Epic P3 — No governance dashboards exist; home screen not role-aware (absorbs Issue 8) | P1 | L |
| [#253](https://github.com/zakk-io/govoo/issues/253) | Epic P4 — Forms lack ribbons/tooltips, lists lack default filters, calendars unbranded | P2 | M |
| [#254](https://github.com/zakk-io/govoo/issues/254) | Epic P5 — Portal and PDF reports carry no Clagov brand (blocked by #246, #249) | P2 | L |
| [#255](https://github.com/zakk-io/govoo/issues/255) | Epic P6 — No systematic verification pass for dark mode, mobile, accessibility, i18n | P2 | M |

## Scope notes

- **Native GitHub sub-issues were not created.** Each parent issue above includes its full
  sub-issue breakdown as a markdown checklist in the issue body (5–11 items each, ~115 items
  total across all 15 issues). Filing each of those as a separate, natively-linked GitHub
  sub-issue was judged out of scope for this pass given the resulting object count; happy to
  promote any specific parent's checklist items to real linked sub-issues on request.
- **No milestone was attached.** The GitHub MCP tools available in this session can attach an
  issue to an existing milestone by number but cannot create one. Create a "GRC UX Audit —
  2026-10-06" milestone in the GitHub UI and I can attach all 15 issues to it in a follow-up pass.
- **Dependency notes are expressed as issue-number cross-references** in the relevant bodies
  (#251 depends on #244/#247; #252 absorbs the evidence from the unfiled Issue 8; #254 is
  blocked by #246/#249; #255 closes out #250–#254) rather than GitHub's native "blocked
  by"/"tracked by" relationships, since those also require the sub-issue API this session's
  tools don't expose for creation.
- All evidence screenshots are embedded directly in each issue body via raw GitHub URLs pointing
  at the `ux-audit-evidence` branch (e.g.
  `https://raw.githubusercontent.com/zakk-io/govoo/ux-audit-evidence/ux-audit/screenshots/...`).
  These stay live as long as that branch exists; if it's ever deleted, re-point the URLs at a
  tag or a later commit first.
