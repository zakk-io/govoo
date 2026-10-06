# Govoo UX Audit Report — First Pass

**Scope:** Company Secretary, Board Administrator, Director (Portal), Shareholder (Portal), Auditor (Read-only)
**Findings analyzed:** 40 across 5 roles | **Viewports:** Desktop 1440x900, Mobile 390x844 (where tested) | **Locale:** en_US only
**Date:** 2026-10-06

---

## Executive Summary

Govoo's governance workflows are conceptually sound — the menu structure, the registers, the meeting-to-minutes pipeline, and the voting mechanics all map correctly onto how a company secretary, board, and shareholder base actually operate. The problem this audit surfaces is not "the wrong features exist," it's that **the product does not yet consistently prove it can be trusted with the governance record it holds.**

Five findings are rated **critical**, and all five point at the same underlying theme — the system sometimes lets people do things, or shows people things, that their role should not permit:

1. A **Board Administrator**, who should only be able to view configuration, can in fact silently rename meetings, edit attendees, and progress a meeting's or resolution's workflow status with no warning and no access-control error.
2. A live **test/QA record** ("[LIVE-TEST #236] Reminder Fixture Partner") was found sitting inside the company's real, legally authoritative Register of Charges.
3. A **Director** restricted to the Board of Directors committee can open full meeting detail — and, once distributed, full board packs — for the Audit Committee and the Risk & Compliance Committee, committees they do not sit on.
4. A **Shareholder** casting a binding vote is never shown their own voting weight (how many shares, what percentage) before they submit — a transparency gap in the product's core weighted-voting mechanism.

Beyond these five, a further 14 high-severity and 12 medium-severity findings show two recurring, cross-cutting weaknesses: **the audit trail is not trustworthy** (every one of 26 sampled statutory register changes, and every vote-reminder activity sampled across three roles, is attributed to the system "OdooBot" account rather than a real person), and **no role's home screen tells that role what actually needs their attention today** (every one of the five roles audited saw the same generic dashboard, including an "Open Resolutions Requiring My Vote" panel shown to people — secretaries, administrators, auditors — who have no voting rights at all).

None of this means the underlying architecture is wrong. The data model, the registers, and the workflow states are all present and mostly connected correctly — this is a polish, access-control, and trust-signaling gap on top of a workable foundation, not a rebuild. The "Top 10 Fixes" and accompanying GitHub issue plans in this package are scoped to close that gap, starting with the cheapest, highest-impact item: a configuration-only data cleanup (the test fixture in the Register of Charges) that should be done before any external party — an auditor, a regulator, a real director — is given a login.

**Known scope limitations** (pre-agreed, not defects) are listed in their own section below; in short, this pass did not test fr/rw/ar translation (only en_US is live), did not test a Laptop (1280x720) viewport, did not cover the Procurement Officer or AI personas, and does not score Risk/Controls/Attestation rubric items because Govoo has no such module.

---

## Scorecard: Rubric Items Evaluated

Scored 1 (poor) – 5 (excellent), grounded in the findings actually raised against each item. Rubric A10 (Multilingual/RTL) and all Risk/Controls/Attestation items are stated once here as **not scored** — see Known Scope Limitations.

### A — General Usability

| Item | Score | Justification |
|---|---|---|
| A1 — Findability/scannability of lists & screens | 2/5 | A critical failure (SEC-001, Board Packs list shows only raw database IDs) plus three further findability gaps (DIR-005, AUD-005, SHA-005) show this is a recurring weak point, not a one-off. |
| A2 — System status reflects actual user authority | 2/5 | AUD-001 (high): enabled write/workflow buttons are shown to a role with no write permission on three different models — status shown does not match status in effect. |
| A3 — Real-world/plain-language data representation | 3/5 | Only one finding (SHA-005, unformatted "30000.0" voting-power figure), isolated to shareholder holdings; no other field-formatting defects surfaced elsewhere. |
| A4 — Consistency of configuration/dashboard patterns | 2/5 | AI Configuration's empty-state inconsistency (SEC-009) plus the same dashboard wording inconsistency recurring across three different roles (SEC-010, BOA-007) shows this is systemic. |
| A5 — Error prevention/confirmation of consequential actions | 2/5 | Both portal voting flows — Director (DIR-002) and Shareholder (SHA-002) — give zero confirmation after a binding, one-time vote is submitted. |
| A6 — Validation clarity & access-control enforcement visible to the user | 1/5 | The single most severely cited item: unenforced write-access for an admin role (BOA-001, critical), live test data in a statutory register (BOA-004, critical), zero voting-weight disclosure before a binding vote (SHA-001, critical), plus weaker deadline/validation gaps (SEC-007, BOA-003, DIR-004, DIR-007). |
| A7 — Accessibility (target size, labeling, grouping) | 3/5 | No blocking accessibility failures found, but three low/medium gaps recur across both portal roles (tap target size, missing fieldset/legend, color-only error state). |
| A8 — Responsive/mobile layout | 2/5 | The one mobile layout fully tested end-to-end (the Company Secretary dashboard) failed severely (SEC-005); this score reflects a real high-severity defect in the case tested, not a broad mobile sweep, since mobile coverage was intentionally limited this pass. |
| A9 — No raw technical identifiers/internal jargon shown to end users | 1/5 | The single most pervasive defect in the whole audit — 8 findings (SEC-002, SEC-003, BOA-002, BOA-005, BOA-009, DIR-007, AUD-003, SHA-005) across at least 4 different models and 3 different roles. |
| A10 — Multilingual/RTL | **N/A — not scored** | Only en_US is active in this instance; no fr/rw/ar target exists to test against this pass. |

### B — Odoo-Specific

| Item | Score | Justification |
|---|---|---|
| B1 — Menu/navigation structure correctness | 3/5 | Overall structure is clean and correctly role-scoped in nearly every case; two isolated gaps (AUD-004's dead-end empty dropdown, SHA-007's missing portal sibling nav) keep this below a top score. |
| B2 — Views show task-relevant content, not ORM defaults | 2/5 | Recurring pattern of views built from the data model rather than the task, most severely the Board Packs list (SEC-001, critical) showing nothing but a raw ID column; also DIR-003, SHA-004, SHA-005, SEC-009. |
| B3 — Sensible default filters/search views | 2/5 | No list view audited in this pass — backend or portal — ships a default "upcoming/actionable" filter (SEC-006, BOA-010, DIR-005), a consistent gap across three roles. |
| B4 — Security group/ir.rule correctness | 2/5 | The underlying database permission (perm_write=False for Auditor) is in fact correctly configured; the score reflects that this correct configuration is invisible/contradicted at the UI layer (see B7), confirmed by direct Postgres query in AUD-001. |
| B5 — Breadcrumb/record navigation | 3/5 | One low-severity gap found (SHA-007); breadcrumbs otherwise function mechanically, aside from the naming-quality issue captured separately under A9. |
| B6 — Automated activities target real accountable users | 1/5 | Every single voting-reminder activity sampled across three different roles and resolutions (SEC-004, BOA-006, BOA-008, AUD-006) is assigned to "OdooBot" instead of a real director — a systemic automation defect, not an isolated bug. |
| B7 — View-level access control enforcement & clear access-denied states | 1/5 | The lowest-scoring Odoo-specific item: two independent *critical* access-control failures (BOA-001: an admin role that can write; DIR-001: a director who can read other committees' meetings) plus two further partial gaps (DIR-004, AUD-004, AUD-001). |

### C — GRC-Specific

| Item | Score | Justification |
|---|---|---|
| C1 — Role-based home surfaces "what needs my attention" | 1/5 | Every one of the 5 roles audited failed this check in some form (SEC-005/010, BOA-007, DIR home-landing assessment, SHA-003, AUD-005) — the dashboard is not role-aware anywhere in the product; the single most consistent finding of the entire audit. |
| C2 — Cross-record traceability (e.g. resolution ↔ meeting) | 2/5 | Both the backend chain (SEC-008: an orphaned resolution with no meeting link) and the portal chain (DIR-003: no vote-to-resolution-text link) have at least one real break. |
| C4 — Informed, accountable voting/decision-making flow | 1/5 | Voting — arguably the single most consequential action the product supports — lacks voting-weight disclosure (SHA-001, critical), resolution text (DIR-003, SHA-004), submission confirmation (DIR-002, SHA-002), and reliable reminder targeting (SEC-004), across both board and shareholder voting. |
| C5 — Audit trail/accountability of who-did-what-when | 1/5 | The most-cited rubric item in the entire audit (10 findings): chatter shows no transition history on any record sampled (AUD-002), 100% of 26 sampled Audit Ledger entries are attributed to OdooBot (BOA-006), and vote confirmations are silent (DIR-002, SHA-002). |
| C6 — Audit evidence usability for an external reviewer | 2/5 | Only one dedicated finding, but it is severe: the Audit Ledger — the one screen purpose-built for this — is unusable without separately knowing Odoo's internal technical model names (BOA-005). |
| C7 — Committee/board confidentiality segregation | 1/5 | The only finding against this item is critical (DIR-001): a director can read full meeting detail, and eventually full board packs, for committees they do not sit on. |
| C8 — Power-user efficiency/frequency fit | 2/5 | A consistent but lower-severity pattern across 5 findings (SEC-006, SEC-010, BOA-007, BOA-010, AUD-005) — no list view ships a default actionable filter, adding a repeated manual step for every frequent user. |
| Risk/Controls/Attestation items (heat maps, KRI trends, RCM/Finding chains) | **N/A — not scored** | Govoo has no Risk, Controls, or Attestation module; these rubric items do not apply to this product. |

---

## Scorecard: Per Role

| Role | Score | Why |
|---|---|---|
| Company Secretary | 2/5 | Core secretarial workflows (board pack retrieval, reading governance settings, verifying who voted) are broken, confusing, or give false answers out of the gate; the dashboard additionally fails badly on mobile. |
| Board Administrator | 1/5 | Two independent *critical* defects — an admin role that can silently edit statutory board records (BOA-001), and a live QA test fixture inside the real Register of Charges (BOA-004) — make this the lowest-scoring role of the audit. |
| Director (Portal) | 2/5 | A critical committee-confidentiality breach (DIR-001) undermines an otherwise reasonably functional, narrowly-scoped portal; the voting flow itself lacks confirmation and decision-relevant context. |
| Shareholder (Portal) | 2/5 | The home screen and holdings view are usable at a basic level, but the portal's single most important governance action — casting a weighted vote — omits voting-weight disclosure and post-submit confirmation. |
| Auditor (Read-only) | 2/5 | No critical defects were found, but two high-severity findings (enabled write-capable buttons on a read-only session, and an audit trail with zero real change history) directly undermine the one thing this role exists to verify. |

---

## Root Causes

Five findings-worth of symptoms keep tracing back to a small number of underlying design decisions. Four are marked **FOUNDATIONAL** — a single fix to the underlying pattern would resolve multiple surface findings at once, rather than needing a one-off patch per screen.

1. **[FOUNDATIONAL] Forms and lists are built from the data model, not the user's task.** The Board Packs list showing only a raw ID column (SEC-001), three different models surfacing "model,id" as their title (SEC-002/BOA-002/AUD-003), the Audit Ledger showing raw technical model names (BOA-005), the AI Request Log showing internal ticket codes (BOA-009), and the portal vote-cast form showing a bare title with no resolution text or voting weight (DIR-003, SHA-001, SHA-004) are all the same underlying problem wearing different clothes: whoever built each screen exposed whatever field Odoo defaulted to, rather than designing for what that screen's actual reader needs to see.

2. **[FOUNDATIONAL] No role-based home dashboard exists.** Every role in this audit — Company Secretary, Board Administrator, Director, Shareholder, Auditor — lands on the same generic three-widget Dashboard, including a voting call-to-action shown to roles that cannot vote (SEC-010, BOA-007, AUD-005), and with no "what's overdue / what needs configuring / what's pending my review" framing tailored to any of them (SEC-005, DIR home-landing, SHA-003). A single piece of work — making the dashboard composition role-aware — would resolve all of these at once.

3. **[FOUNDATIONAL] Automated reminders and audit-trail authorship default to the system account instead of the real actor.** Vote-reminder activities assigned to "OdooBot" instead of the actual director (SEC-004, BOA-008, AUD-006) and 100% of sampled Audit Ledger entries attributed to "OdooBot" instead of any real user (BOA-006) are almost certainly the same piece of code — an automation or seeding routine that runs as a system/bot user and never gets corrected to attribute the action to the person who actually triggered it.

4. **[FOUNDATIONAL] Access control is enforced only at the data layer (if at all), never reflected in the UI.** A Board Administrator can actually write to records that should be locked (BOA-001) — a true permission gap; an Auditor sees fully-enabled write buttons that the database will in fact reject (AUD-001) — a UI/permission mismatch; two top-level menus silently render as dead ends with no explanation (AUD-004); and a stale/out-of-scope portal link silently redirects home with no message (DIR-004). All four are variations on the same gap: the interface does not communicate, in real time, what the signed-in user is and is not allowed to do.

5. **Unconfirmed legal/statutory values are shipped with no in-UI signal distinguishing them from real configured data.** The four statutory deadline fields on Governance Settings read "0" with no banner explaining they are deliberately-unset `[CONFIRM]` placeholders pending legal sign-off (SEC-003, BOA-003), and the underlying `[CONFIRM]`/spec-file jargon is visible verbatim to end users in field tooltips. This is narrower than the items above (it is scoped to one form) and is **not** marked foundational, but it is a direct conflict with the project's own "no hard-coded legal values" rule and deserves early attention regardless.

---

## Top 10 Fixes

Each fix bundles one or more finding IDs into a single user-facing problem. Priority score = `(severity weight × reach count) / effort weight`, using **severity weights** critical=4, high=3, medium=2, low=1; **effort weights** S=1, M=2, L=3; and **reach count** = number of distinct audited roles the problem was observed to affect. Ranked highest priority first.

| # | Fix | Finding IDs | Severity | Reach | Effort | Priority |
|---|---|---|---|---|---|---|
| 1 | Purge test/QA fixture data from the live Register of Charges | BOA-004 | Critical | 3 roles (Secretary, Board Admin, Auditor all have this register in their menu) | S | **12.0** |
| 2 | Add a visible plain-language disclaimer to unconfirmed statutory-deadline fields | SEC-003, BOA-003 | High | 2 (Secretary, Board Admin) | S | **6.0** |
| 3 | Fix vote-reminder activities so they target the real director, not OdooBot | SEC-004, BOA-008, AUD-006 | High | 3 (Secretary, Board Admin, Auditor) | M | **4.5** |
| 4 | Give records a real display name instead of "model,id" | SEC-002, BOA-002, AUD-003 | High | 3 (Secretary, Board Admin, Auditor) | M | **4.5** |
| 5 | Make write-restricted roles' UI actually block write access | BOA-001, AUD-001 | Critical | 2 (Board Admin, Auditor) | M | **4.0** |
| 6 | Give directors and shareholders the context and confirmation a binding vote requires | SHA-001, SHA-002, SHA-004, DIR-002, DIR-003 | Critical | 2 (Director, Shareholder) | M | **4.0** |
| 7 | Rebuild key list/detail views around task-relevant fields, not raw IDs | SEC-001, BOA-005, BOA-009 | Critical | 2 (Secretary, Board Admin) | M | **4.0** |
| 8 | Make the home dashboard role-aware (content + mobile layout) | SEC-005, SEC-010, BOA-007, SHA-003, AUD-005 | High | 4 (Secretary, Board Admin, Shareholder, Auditor) | L | **4.0** |
| 9 | Make the statutory/audit-trail chatter and Audit Ledger show real change history | AUD-002, BOA-006 | High | 2 (Board Admin, Auditor) | L | **2.0** |
| 10 | Restrict a director's portal meeting access to their own committee(s) | DIR-001 | Critical | 1 (Director) | M | **2.0** |

### Fix detail

**1. Purge test/QA fixture data from the live Register of Charges** — *Before:* `screenshots/board_admin/board_admin_statutoryregisters_registerofcharges_list_desktop_en.png` shows "[LIVE-TEST #236] Reminder Fixture Partner" (RWF 5,000,000, Satisfied) sitting next to two genuine Bank of Kigali Plc charges in the company's real statutory register.

**2. Add a visible plain-language disclaimer to unconfirmed statutory-deadline fields** — *Before:* `screenshots/secretary/secretary_configuration_governance_settings_form_desktop_en.png` shows all four statutory deadlines at "0" with the only explanation (raw `[CONFIRM] BR-BOARD-008 / open-decisions.md`-style developer jargon) hidden inside a hover tooltip.

**3. Fix vote-reminder activities so they target the real director, not OdooBot** — *Before:* `screenshots/secretary/secretary_board_resolution_form_passed_votetally_desktop_en.png` shows a "Vote on resolution" reminder, 20 days overdue, assigned to "OdooBot" on a resolution three named directors actually voted on.

**4. Give records a real display name instead of "model,id"** — *Before:* `screenshots/secretary/secretary_board_minutes_form_draft_desktop_en.png` shows the breadcrumb and tab title reading "govoo.minutes,4" instead of a meeting-identifying name.

**5. Make write-restricted roles' UI actually block write access** — *Before:* `screenshots/board_admin/board_admin_board_meeting_form_scheduled_desktop_en.png` shows a Board Administrator's edit to "Meeting Name" saving successfully with zero access-control error.

**6. Give directors and shareholders the context and confirmation a binding vote requires** — *Before:* `screenshots/shareholder_portal/shareholder_portal_votes_cast_form_desktop_en.png` shows the Cast Vote screen with no voting-weight figure, no resolution text, and (per SHA-002/DIR-002) no confirmation after Submit.

**7. Rebuild key list/detail views around task-relevant fields, not raw IDs** — *Before:* `screenshots/secretary/secretary_board_packs_list_desktop_en.png` shows the entire Board Packs list as a single column of raw database row numbers (265, 266, 267, 8, 7, 6, 4, 3, 2).

**8. Make the home dashboard role-aware (content + mobile layout)** — *Before:* `screenshots/secretary/secretary_dashboard_home_mobile_en.png` shows the mobile Dashboard with only the title column of each widget visible; Status, Result, and Due Date are scrolled entirely out of view.

**9. Make the statutory/audit-trail chatter and Audit Ledger show real change history** — *Before:* `screenshots/board_admin/board_admin_statutoryregisters_auditledger_list_desktop_en.png` shows all 26 rows attributing "Changed By" to "OdooBot" and the "Register" column showing raw strings like "govoo.register.charge".

**10. Restrict a director's portal meeting access to their own committee(s)** — *Before:* `screenshots/director_portal/director_portal_meeting_crosscommittee_exposure_mobile_en.png` shows a director appointed only to "Board of Directors" viewing full detail for an Audit Committee meeting.

---

## Quick Wins

Of the Top 10, two fixes are effort **S** and can be shipped through configuration or XML-view inheritance alone — no Python/model changes, no security-group redesign:

- **Fix 1 — Purge the test fixture from the Register of Charges.** This is a one-time data cleanup (delete/archive the offending `govoo.register.charge` record), not a code change at all; it should happen before this environment is shown to anyone external, independent of when the rest of the backlog ships. (The CI guard to prevent recurrence is a small additional script, not a UI fix, and can follow separately.)
- **Fix 2 — Add a plain-language disclaimer to unconfirmed statutory-deadline fields.** The jargon currently sits in each field's `help=` attribute and can be overridden directly in an inherited form view (`<field name="charge_registration_deadline_days" help="Not yet confirmed by legal counsel..."/>`), and an on-form warning banner can be added the same way other informational banners in this app already are (e.g. the Minutes "has not been drafted yet" banner) — both achievable by inheriting the existing `govoo.governance.config` form view's XML, with no Python changes required.

The remaining eight fixes all require at least one Python/model change (a new security group or readonly rule, a computed display-name field, a controller-level access check, or a dashboard-widget visibility rule), so they are **M** or **L** effort and are not quick wins, even where their priority score is high.

---

## Known Scope Limitations

Stated here explicitly, as pre-agreed cuts for this first pass — not defects to remediate:

- **Only en_US is active in this instance.** fr/rw translation completeness and ar RTL layout were not tested, because there is no active target locale to test against. Rubric A10 is not scored for this reason.
- **No Laptop (1280x720) viewport was tested this pass.** Coverage was Desktop (1440x900) and Mobile (390x844) only.
- **Govoo has no Risk, Controls, or Attestation module.** GRC rubric items about risk heat maps, KRI trends, or Risk-Control-Test-Finding traceability chains are not applicable to this product and were not scored anywhere in this report.
- **Procurement Officer and AI personas were not covered this pass.** The focused first pass covered Company Secretary, Board Administrator, Director portal, Shareholder portal, and Auditor only.
- **Role-specific sub-scope gaps** (see `coverage.md` for the full breakdown): Board Administrator and Auditor were restricted to Desktop only per this pass's task scope; several backend modules (Shares & Cap Table, Contract Management, Evaluations) were opened but not scrutinized in depth for most roles; and the live click-through of AUD-001's enabled write buttons was deliberately not performed (the audit harness blocked it as a data-modification risk) — that specific behavior needs direct developer/QA verification.
