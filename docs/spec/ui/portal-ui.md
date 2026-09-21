# UI — Portal

Source: §6.2, §6.3 of the source spec. See `security/portal-security.md` for the access-control
detail this UI must respect; this file covers the presentation layer only.

## 1. Director Portal ("My Governance" area)
| Page | Content | Record rule applied |
| --- | --- | --- |
| My meetings | List of meetings for committees the portal user belongs to, upcoming first | `security/record-rules.md` §2 |
| Meeting detail | Agenda, board pack (redacted per this recipient), minutes (once approved/signed) | Same, plus `govoo.board.pack` redaction |
| My votes | Open resolutions eligible to vote on; cast-vote widget (for/against/abstain, optional conflict declaration) | `security/record-rules.md` §4 |
| My appointment | Own appointment particulars, read-only | `partner_id = user.partner_id` |

## 2. Shareholder Portal ("My Holdings" area)
| Page | Content | Record rule applied |
| --- | --- | --- |
| My holdings | Own `govoo.share.holding` rows across all classes, with percentage/voting power | `security/record-rules.md` §3 |
| My votes | Open shareholder-type resolutions eligible to vote on; cast-vote widget | `security/record-rules.md` §4 |
| My register entry | Own `govoo.register.member` entry, read-only | `partner_id = user.partner_id` |

## 2b. Contract Viewer Portal ("My Contracts" area — addendum §3.2 CM-F16)
| Page | Content | Record rule applied |
| --- | --- | --- |
| My contracts | List of contracts where the portal user is counterparty or a named approver | `security/record-rules.md` §6b |
| Contract detail | Terms, executed document (once `state = 'executed'`), obligations/milestones | Same rule |
| My obligations | Outstanding obligations/milestones across the user's own contracts | Same rule, via `contract_id` |

## 3. Portal UI conventions
- Simplified, read-mostly presentation — no Odoo backend chrome (standard `portal.mixin` layout).
- Vote-casting is the only meaningful "write" action exposed to portal users (plus, optionally,
  attendance confirmation — `[ENGINEERING DETAIL]`, see `workflows/meetings.md`).
- Every page/record link is generated via `_compute_access_url()` with an access token — never a
  raw sequential ID exposed in a way that invites guessing (`security/portal-security.md`).
- Board-pack redaction is enforced server-side before the PDF/content reaches the portal response —
  the portal UI never receives, and therefore cannot accidentally render, a confidential item the
  viewer isn't authorized for.
- No portal page ever offers an action (button/link) the underlying access rules would reject — see
  `security/access-control.md` §4 note on hiding vs. enforcement; hiding here is a courtesy on top
  of, never instead of, the enforced rule.

## 4. What is explicitly NOT in the portal (non-goals)
- No statutory register editing.
- No compliance-instance management (internal-only workflow, `workflows/compliance.md`).
- No evaluation-campaign administration (portal users only respond to their own survey invite via
  standard Surveys portal flow, not a Govoo-specific evaluation UI).
- No contract authoring, approval routing, or delegation-of-authority configuration (internal-only
  workflow, `workflows/contracts.md`) — Contract Viewer Portal is read-mostly, same as every other
  portal role, with e-signature (where enabled/confirmed) as the only meaningful write action.
