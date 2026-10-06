# UX Audit Coverage Matrix

Legend: ✅ tested, passed rubric check &nbsp;·&nbsp; ⚠️ tested, findings raised &nbsp;·&nbsp; ❌ not covered this pass (reason given)

This matrix is built strictly from `menus_seen`, `findings[]` and `coverage_gaps[]` in the raw capture data — a cell is only marked ✅ or ⚠️ if a role's menu/finding list shows it was actually opened.

## Company Secretary

| Module | View type | Viewport | Lang | Status |
|---|---|---|---|---|
| govoo_board (Board Packs) | list | Desktop 1440x900 | en_US | ⚠️ SEC-001 (unusable list columns) |
| govoo_board (Minutes) | form | Desktop 1440x900 | en_US | ⚠️ SEC-002 (raw model,id title) |
| govoo_base (Governance Settings) | form | Desktop 1440x900 | en_US | ⚠️ SEC-002, SEC-003 |
| govoo_board (Resolutions) | form | Desktop 1440x900 | en_US | ⚠️ SEC-004 (OdooBot activity) |
| govoo_board (Resolutions) | list | Desktop 1440x900 | en_US | ⚠️ SEC-008 (orphaned meeting link) |
| govoo_board (Meetings) | list | Desktop 1440x900 | en_US | ⚠️ SEC-006 (no default filter) |
| govoo_board (Meetings) | form | Desktop 1440x900 | en_US | ⚠️ SEC-007 (validation error UX) |
| govoo_compliance (Instances) | list | Desktop 1440x900 | en_US | ⚠️ SEC-006 (shared finding) |
| govoo_base (AI Configuration) | list/empty-state | Desktop 1440x900 | en_US | ⚠️ SEC-009 |
| govoo_portal (Dashboard) | dashboard | Desktop 1440x900 | en_US | ⚠️ SEC-010 (role-label mismatch) + horizontal-scroll issue noted in home_landing_assessment |
| govoo_portal (Dashboard) | dashboard | Mobile 390x844 | en_US | ⚠️ SEC-005 (critical mobile table overflow) |
| Statutory Registers (Directors/Members/Beneficial Owners/Charges/Audit Ledger) | list | Desktop 1440x900 | en_US | ❌ menu opened but not scrutinized in depth — "did not exhaustively open every register" (coverage_gaps) |
| Shares & Cap Table (all 4 submenus) | list/form | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| Board & Meetings > Appointments, Committees, Votes | list/form | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| Contract Management (all 5 submenus) | list/form | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| Evaluations (Campaigns, Results) | list/form | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| AI > Search | — | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| Configuration > Companies | form | Desktop 1440x900 | en_US | ❌ menu opened, not evaluated in depth this pass |
| Any module | any | Mobile 390x844 (beyond Dashboard) | en_US | ❌ not in focused-pass scope — only Dashboard was repeated on mobile |
| Any module | any | any | fr / rw | ❌ only en_US active in this instance — no target to test translation against |

## Board Administrator

| Module | View type | Viewport | Lang | Status |
|---|---|---|---|---|
| govoo_board (Meetings) | form | Desktop 1440x900 | en_US | ⚠️ BOA-001 (critical — read-only role can edit/save/progress workflow) |
| govoo_board (Resolutions) | form | Desktop 1440x900 | en_US | ⚠️ BOA-001 (Tally Votes/Withdraw exposed), BOA-007, BOA-008 |
| govoo_base (Governance Settings) | form | Desktop 1440x900 | en_US | ⚠️ BOA-002 (raw title), BOA-003 (0-day deadlines) |
| Statutory Registers > Register of Charges | list | Desktop 1440x900 | en_US | ⚠️ BOA-004 (critical — test fixture in live register) |
| Statutory Registers > Audit Ledger | list | Desktop 1440x900 | en_US | ⚠️ BOA-005 (raw model names), BOA-006 (100% OdooBot authorship) |
| govoo_portal (Dashboard) | dashboard | Desktop 1440x900 | en_US | ⚠️ BOA-007 (role-mismatched "my vote" framing), noted in home_landing_assessment |
| AI > Request Log | list | Desktop 1440x900 | en_US | ⚠️ BOA-009 (raw feature codes/model strings) |
| govoo_board (Meetings, Resolutions) | list | Desktop 1440x900 | en_US | ⚠️ BOA-010 (no default filter) |
| Statutory Registers > Directors, Members, Beneficial Owners | list | Desktop 1440x900 | en_US | ❌ spot-checked only (Charges, Audit Ledger prioritized); not covered in depth — coverage_gaps |
| Shares & Cap Table (all submenus) | list/form | Desktop 1440x900 | en_US | ❌ not covered in depth this pass — coverage_gaps |
| Contract Management (all submenus) | list/form | Desktop 1440x900 | en_US | ❌ not covered in depth this pass — coverage_gaps |
| Compliance > Obligations, Instances | list/form | Desktop 1440x900 | en_US | ❌ not covered in depth this pass — coverage_gaps |
| Evaluations (Campaigns, Results) | list/form | Desktop 1440x900 | en_US | ❌ not covered in depth this pass — coverage_gaps |
| AI > Search | — | Desktop 1440x900 | en_US | ❌ not covered in depth this pass |
| Any module | any | Mobile 390x844 | en_US | ❌ not in scope — task explicitly restricted this role to Desktop 1440x900 only |
| Any module | any | any | fr / rw | ❌ only en_US active — no target to test |
| Risk / Controls / Attestation | any | any | — | ❌ module doesn't exist in Govoo |

## Director (Portal)

| Module | View type | Viewport | Lang | Status |
|---|---|---|---|---|
| Portal home (/my) | portal home | Desktop 1440x900 | en_US | ⚠️ fails C1 "what needs my attention" — see home_landing_assessment |
| /my/meetings | portal list | Desktop 1440x900 | en_US | ⚠️ DIR-005 (no filter/grouping) |
| /my/meetings/<id> | portal detail | Mobile 390x844 | en_US | ⚠️ DIR-001 (critical — cross-committee confidentiality breach) |
| /my/meetings/<id> (out-of-scope id) | portal detail | Desktop 1440x900 | en_US | ⚠️ DIR-004 (silent access-denied redirect) |
| /my/votes/<id>/cast | portal form | Desktop 1440x900 | en_US | ⚠️ DIR-002 (no confirmation), DIR-003 (no resolution text/cross-link) |
| /my/votes/<id>/cast | portal form | Mobile 390x844 | en_US | ⚠️ DIR-006 (tap-target size) |
| /web/login account switcher | portal/base login | Desktop 1440x900 | en_US | ⚠️ DIR-007 (credential pre-fill) |
| My Account | portal page | — | en_US | ❌ confirmed to exist in user dropdown only, not opened — outside explicit task list |
| Any portal page | any | any | fr / rw / ar (RTL) | ❌ only en_US active — no target to test |
| Risk / Controls / Attestation | any | any | — | ❌ module doesn't exist in Govoo |

## Shareholder (Portal)

| Module | View type | Viewport | Lang | Status |
|---|---|---|---|---|
| Portal home (/my) | portal home | Desktop 1440x900 | en_US | ⚠️ SHA-003 (no pending-vote callout); passes basic 5-second orientation otherwise |
| /my/holdings | portal list | Desktop 1440x900 | en_US | ⚠️ SHA-005 (unformatted voting power, no heading) |
| /my/holdings/votes/<id>/cast | portal form | Desktop 1440x900 | en_US | ⚠️ SHA-001 (critical — no voting-weight disclosure), SHA-004 (no resolution text), SHA-006 (fieldset/legend a11y) |
| /my/holdings/votes | portal list | Desktop 1440x900 | en_US | ⚠️ SHA-002 (no post-vote confirmation) |
| /my/holdings/votes | portal list (empty state, post-vote) | Mobile 390x844 | en_US | ✅ empty state rendered correctly; cast-vote form itself could not be re-exercised on mobile — only one open resolution existed (coverage_gaps) |
| /my/holdings | portal list | Mobile 390x844 | en_US | ❌ not explicitly screenshotted/scored in findings; only desktop analyzed in depth |
| Portal navigation (sidebar/breadcrumb across My Holdings/Votes/Register) | shared layout | Desktop + Mobile | en_US | ⚠️ SHA-007 (no sibling sub-nav) |
| /my/register | portal list | — | en_US | ❌ visible as Quick Link but outside assigned task list — not screenshotted/evaluated |
| Multi-share-class weighted voting | portal form | — | en_US | ❌ shareholder holds only one class (Ordinary, 1:1 ratio) — could not observe weighted arithmetic across classes |
| Any portal page | any | any | fr / rw / ar (RTL) | ❌ only en_US active — no target to test |
| Risk / Controls / Attestation | any | any | — | ❌ module doesn't exist in Govoo |

## Auditor (Read-only)

| Module | View type | Viewport | Lang | Status |
|---|---|---|---|---|
| govoo_board (Meeting) | form | Desktop 1440x900 | en_US | ⚠️ AUD-001 (enabled write buttons), AUD-002 (no chatter history) |
| govoo_compliance (Instance) | form | Desktop 1440x900 | en_US | ⚠️ AUD-001 (shared finding) |
| govoo_board (Resolution) | form | Desktop 1440x900 | en_US | ⚠️ AUD-001, AUD-006 (OdooBot activity) |
| govoo_board (Minutes) | form | Desktop 1440x900 | en_US | ⚠️ AUD-003 (raw model,id title) |
| Statutory Registers > Register of Directors | list | Desktop 1440x900 | en_US | ✅ used as representative example; no findings raised |
| Top navigation (Contract Management, Evaluations) | menu | Desktop 1440x900 | en_US | ⚠️ AUD-004 (empty dead-end dropdown) |
| Dashboard | dashboard | Desktop 1440x900 | en_US | ⚠️ AUD-005 (not role-differentiated, false "my vote" prompt) |
| Compliance > Obligations, Instances | list | Desktop 1440x900 | en_US | ✅ opened per menus_seen; no additional findings beyond AUD-001 instance |
| Statutory Registers > Members, Beneficial Owners, Charges, Audit Ledger | list | Desktop 1440x900 | en_US | ❌ not opened in detail — task scope named Board & Meetings/Statutory Registers/Compliance, Register of Directors used as representative sample |
| Shares & Cap Table (all submenus) | list/form | Desktop 1440x900 | en_US | ❌ not in assigned task scope this pass |
| Live click-test of enabled write buttons (AUD-001) | form | Desktop 1440x900 | en_US | ❌ harness blocked the state-changing click as a data-modification risk; verified via read-only Postgres query instead — needs direct dev/QA verification |
| Formal WCAG 2.2 AA automated audit (axe/Lighthouse) | — | Desktop 1440x900 | en_US | ❌ not performed — only incidental observations during functional navigation |
| Any module | any | Mobile 390x844 | en_US | ❌ out of scope — task explicitly restricted this role to Desktop 1440x900 only |
| Any module | any | any | fr / rw | ❌ only en_US active — no target to test |
| Risk / Controls / Attestation | any | any | — | ❌ module doesn't exist in Govoo |

## Cross-cutting gaps (apply to every role above)

- **Laptop viewport (1280x720):** ❌ not tested this pass for any role — scope cut to Desktop 1440x900 + Mobile 390x844 only.
- **Procurement Officer / AI role personas:** ❌ not covered this pass — focused first pass covered Company Secretary, Board Administrator, Director portal, Shareholder portal, Auditor only.
- **fr / rw / ar translation + RTL layout:** ❌ not tested anywhere — only en_US is active in this instance, so there is no target locale to test against (not a defect, a scope cut).
- **Risk / Controls / Attestation rubric items** (risk heat maps, KRI trends, Risk-Control-Test-Finding chains): ❌ not applicable — Govoo has no Risk, Controls, or Attestation module. Not scored anywhere in this audit.
