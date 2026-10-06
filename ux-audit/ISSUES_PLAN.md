# GitHub Issues Plan — Track A (Governance-Critical Fixes) + Track B (Clagov Brand & UX Uplift)

Planning only. Nothing in this file has been filed on GitHub. Each entry is a draft parent issue, ready to be filed once reviewed and approved.

This plan now has two tracks, reconciled in `MANAGER_SPEC_ANALYSIS.md` (read that first for the
reasoning behind the merges/sequencing noted inline below):

- **Track A — Governance-Critical Fixes** (Issues 1–10): correctness/security/audit-trail defects
  found by the independent UX audit. Recommended to start immediately, in parallel with Track B.
- **Track B — Clagov Brand & UX Uplift** (Epics P1–P6): the manager-provided branding/theme/
  dashboard/portal program (`Clagov_UIUX_Improvement_Specification.md`), restructured into the
  same issue template. Three of Track A's findings are merged into or block specific Track B
  epics rather than being filed twice — see the "Superseded by" / "Blocked by" notes on Issues 2,
  6, 8, and 10, and on Epics P2, P3, and P5.

Label taxonomy used below:
- **type:** ux / accessibility / performance / workflow / reporting / content / i18n / rtl / mobile / bug
- **odoo:** odoo:config / odoo:view / odoo:model / odoo:security / odoo:owl / odoo:report / odoo:portal
- **grc domain:** grc:board / grc:compliance (grc:risk, grc:audit-engagement skipped — not applicable, no such module)
- **role:** role:cosec / role:board / role:director-portal / role:shareholder-portal / role:audit
- **priority:** P0–P3
- **effort:** effort:S / effort:M / effort:L
- **meta:** ux-audit, epic, quick-win (if applicable), foundational (if applicable), needs-functional-review (if applicable)

---

## Issue 1 — Purge test/QA fixture data from the live Register of Charges

**Title:** [UX][grc:compliance] Statutory Register of Charges contains visible test/QA fixture data

- **Problem (role-specific experience):** A Board Administrator (and anyone else with Statutory Registers access — Company Secretary, Auditor) opening Register of Charges sees a record named "[LIVE-TEST #236] Reminder Fixture Partner" (RWF 5,000,000, Satisfied) sitting alongside genuine Bank of Kigali Plc charges, with no visual distinction between real and fabricated data.
- **Evidence:**
  - Screenshot: `screenshots/board_admin/board_admin_statutoryregisters_registerofcharges_list_desktop_en.png`, annotated: `screenshots/board_admin/BOA-004_annotated.png`
  - Finding ID: BOA-004
  - Steps to reproduce: Log in as Board Administrator → Statutory Registers → Register of Charges → observe row "[LIVE-TEST #236] Reminder Fixture Partner"
  - Affected roles/modules/views/viewports: Board Administrator (confirmed); Company Secretary and Auditor have the same menu and are very likely to see the same record (not independently confirmed by their captures this pass) — `govoo_base`, list view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** Rubric A6/C5 — statutory register completeness and accuracy expected under Companies Act/RERA statutory register requirements and ISA audit-evidence sufficiency standards.
- **User impact / Governance impact:** Damages confidence in the register's accuracy for any internal admin, and would constitute a misstatement in the statutory register if seen by an external auditor or regulator. Directly undermines audit-readiness and data quality of the single most sensitive register in the product.
- **Recommended solution:** Delete or archive the fixture record from this (and any other) environment that is presented as production-like before any external stakeholder review. **Alternative:** keep the record but tag it with a clearly visible "TEST DATA" banner/ribbon in the UI — trade-off: this is more engineering work for a worse outcome (test data still visible in a statutory register is never acceptable), so the direct-deletion path is strongly preferred.
- **Odoo implementation approach:** Config/data change — delete the `govoo.register.charge` record directly, or via a data-cleanup script. Follow-up: review how the `govoo_rw` email-reminder test suite (issue #236) creates fixtures, and ensure tests use Odoo's `TransactionCase` (auto-rollback) rather than writing into the demo/seed company's live register.
- **Acceptance criteria:**
  - [ ] No record with a test/QA-fixture naming pattern (`[LIVE-TEST`, `TEST`, `FIXTURE`, etc.) exists in `govoo.register.charge` (or any other statutory register) in any environment presented as production-like.
  - [ ] The test suite responsible for creating this fixture (issue #236 reminder tests) runs in an isolated transaction that rolls back, verified by re-running the test and confirming no residual record.
  - [ ] A data-integrity check (manual or automated) confirms the Register of Charges list for Board Administrator, Company Secretary, and Auditor roles shows only genuine charges.
- **Success metric:** Zero test-fixture-pattern records present in any statutory register, verified by a repeatable query.
- **Sub-issues:**
  - [ ] Config change: delete/archive the specific offending record in the current environment
  - [ ] Functional review (needs-functional-review): confirm with the test owner whether this record is still needed for issue #236 regression testing, and if so, relocate it to an isolated test DB
  - [ ] Python/model change: audit the `govoo_rw` reminder test fixtures for transaction-isolation correctness
  - [ ] Tests: add/adjust a CI check that fails module install or nightly build if a register record matches a test-fixture naming pattern
  - [ ] Before/after verification: re-screenshot Register of Charges for Board Administrator, Company Secretary, and Auditor and confirm no fixture data is visible
- **Labels:** `type:content`, `type:bug`, `odoo:config`, `grc:compliance`, `role:board`, `role:cosec`, `role:audit`, `priority:P0`, `effort:S`, `ux-audit`

---

## Issue 2 — Unconfirmed statutory-deadline fields give no plain-language signal they are placeholders

**Relationship to Track B:** this is the first concrete deliverable of **Epic P4** (Forms, Search,
Calendar Polish) below — Epic P4's spec section explicitly calls for "help tooltips on statutory/
legal fields." File this issue now as a standalone quick win; do not also redo this work inside P4.

**Title:** [UX][grc:compliance] Governance Settings shows statutory deadlines as "0" with no visible explanation they're unconfirmed

- **Problem (role-specific experience):** A Company Secretary or Board Administrator opening Governance Settings sees all four statutory deadline fields (Charge Registration, Beneficial Owner Declaration, Share Certificate Issuance, Share Transfer Registration) at "0" and an unchecked "E-Signature Legally Confirmed" box, with the only explanation (raw developer jargon referencing internal requirement IDs like "BR-BOARD-008" and a spec file "open-decisions.md") hidden inside a hover tooltip most users will never find.
- **Evidence:**
  - Screenshot: `screenshots/secretary/secretary_configuration_governance_settings_form_desktop_en.png`, annotated: `screenshots/secretary/SEC-003_annotated.png`
  - Finding IDs: SEC-003, BOA-003
  - Steps to reproduce: Log in as Company Secretary or Board Administrator → Configuration → Governance Settings → observe "0" values and hover the "?" icon on any deadline field
  - Affected roles/modules/views/viewports: Company Secretary, Board Administrator — `govoo_base`, form view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** AGENTS.md's own "No hard-coded legal values... Mark [CONFIRM] in code comments" hard rule, and rubric A6/A9/C5 (validation clarity, no developer jargon shown to end users, compliance-threshold integrity).
- **User impact / Governance impact:** A user could reasonably conclude the system is broken or misconfigured rather than realizing these are deliberately unset pending legal confirmation; worse, if compliance-reminder/RAG logic reads these thresholds literally, a "0-day" deadline could make every related obligation appear instantly overdue or silently skip the deadline calculation — risking missed real statutory deadlines (charge registration, UBO declaration, share certificate/transfer).
- **Recommended solution:** Replace the developer-facing help text with plain language (e.g. "Not yet confirmed by legal counsel. Leave at 0 to keep reminders off.") and add a visible on-form banner summarizing which statutory values are still unconfirmed placeholders, consistent with the existing Minutes "has not been drafted yet" banner pattern. **Alternative:** add an `@api.constrains` that blocks saving "0" and forces the admin to explicitly type a real value or check an "I understand this is unconfirmed" box — trade-off: more robust against the compliance-logic risk described above, but higher effort (Python + migration) and may block legitimate "intentionally disabled" configurations.
- **Odoo implementation approach:** XML-view-inheritance only for the immediate fix — override each field's `help=` attribute in an inherited `govoo.governance.config` form view (likely `govoo_base.view_governance_config_form` — confirm exact xml_id in code) and add a `<div class="alert alert-warning">` banner conditioned on any deadline field being 0. The constrains-based hardening (the alternative above) would be a separate, later Python/model change if the team wants belt-and-braces protection.
- **Acceptance criteria:**
  - [ ] No field `help=` text on the Governance Settings form references internal requirement IDs (e.g. "BR-BOARD-008") or spec filenames (e.g. "open-decisions.md") — only plain business language.
  - [ ] A visible on-form banner appears whenever any statutory deadline field is 0 or "E-Signature Legally Confirmed" is unchecked, explaining these are pending legal confirmation.
  - [ ] Internal requirement/spec references remain available to developers in code comments only, not in any user-facing string.
- **Success metric:** Zero support/confusion tickets referencing "why are the deadlines 0" after release; qualitative confirmation in next round of role-based testing that a non-technical user correctly identifies these as placeholders without hovering a tooltip.
- **Sub-issues:**
  - [ ] XML view change: identify and inherit the Governance Settings form view xml_id; override `help=` text on the 4 deadline fields and the e-signature field
  - [ ] XML view change: add a conditional warning banner (`invisible` domain keyed off the 4 fields being 0 and/or e-signature unconfirmed)
  - [ ] Needs-functional-review: confirm the actual, correct statutory deadline values (in days) for Rwanda with the firm's legal/compliance team before shipping real defaults
  - [ ] Config change: once legal values are confirmed, ship them as an `active=False` data record flagged `[CONFIRM]` per repo convention, rather than leaving 0 indefinitely
  - [ ] Tests: add a view-rendering test asserting the banner appears when fields are at default
  - [ ] Before/after verification: re-screenshot Governance Settings for Company Secretary and Board Administrator
- **Labels:** `type:content`, `odoo:view`, `grc:compliance`, `role:cosec`, `role:board`, `priority:P1`, `effort:S`, `ux-audit`, `quick-win`, `needs-functional-review`

---

## Issue 3 — Vote-reminder activities are assigned to OdooBot instead of the real director

**Title:** [UX][grc:board] Resolution vote-reminder activities are assigned to the system account, not the voting director

- **Problem (role-specific experience):** A Company Secretary, Board Administrator, or Auditor opening a resolution's Planned Activities panel sees a "Vote on resolution" reminder — sometimes 20+ days overdue — assigned to "OdooBot" rather than to any of the real directors who are actually expected to vote (and, on at least one resolution, did vote).
- **Evidence:**
  - Screenshots: `screenshots/secretary/secretary_board_resolution_form_passed_votetally_desktop_en.png`; `screenshots/board_admin/board_admin_board_resolution_form_openforvoting_desktop_en.png`; `screenshots/auditor/auditor_board_resolution_form_openvoting_desktop_en.png`
  - Finding IDs: SEC-004, BOA-008, AUD-006
  - Steps to reproduce: Open "Approve Revised Risk Management Policy" (Open for Voting) or "Award of Tender TND-2026-003" (Passed) → view Planned Activities / chatter → observe assignee "OdooBot"
  - Affected roles/modules/views/viewports: Company Secretary, Board Administrator, Auditor — `govoo_board`, form view (mail.activity), Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** Rubric B6/C4/C5 — activities should be personal, assignable tasks tied to a real accountable person; board voting accountability and the audit trail of who was asked to vote (and when they responded) is a core GRC requirement.
- **User impact / Governance impact:** Breaks individual director accountability for timely voting; an auditor reviewing the chatter to establish who was reminded and who closed out the reminder sees only "OdooBot," making it impossible to demonstrate accountability from the activity trail alone. Also means the organization's own recently-shipped email-reminder feature is very likely not notifying the actual responsible director.
- **Recommended solution:** When a resolution moves to "Open for Voting," create one `mail.activity` per eligible voter assigned to that director's `res.users` record. **Alternative:** keep a single activity but add a `partner_ids` or custom field listing all expected voters — trade-off: cheaper to build, but doesn't give each director their own overdue/done state in their personal activity list, which is the actual UX goal.
- **Odoo implementation approach:** Python/model change — audit the automation/cron that schedules "Vote on resolution" activities in `govoo_board` (the code that currently defaults to OdooBot, likely because it runs under the module-install/demo-data user context or `self.env.user` during a non-interactive trigger). Fix it to resolve `user_id` from the resolution's actual voter list (committee membership) rather than the triggering context's user.
- **Acceptance criteria:**
  - [ ] Moving a resolution to "Open for Voting" creates one `mail.activity` per eligible voter, each assigned to that voter's real `res.users` record.
  - [ ] No vote-reminder activity in a production-like dataset is assigned to OdooBot, the public user, or any other non-human account.
  - [ ] Activities correctly show as overdue/done per-director based on that director's own voting action, not a single shared activity.
- **Success metric:** 100% of vote-reminder activities in a fresh test dataset are assigned to real, named users; 0% assigned to OdooBot/system accounts.
- **Sub-issues:**
  - [ ] Python/model change: locate and fix the activity-scheduling logic for resolution voting in `govoo_board`
  - [ ] Tests: add a regression test asserting scheduled vote activities are never assigned to OdooBot/admin/public user
  - [ ] Config change: re-run data migration or a one-off script to reassign/close out existing mis-assigned activities in current environments
  - [ ] Before/after verification: re-open the "Approve Revised Risk Management Policy" and "Award of Tender" resolutions and confirm activities show real director names
- **Labels:** `type:workflow`, `type:bug`, `odoo:model`, `grc:board`, `role:cosec`, `role:board`, `role:audit`, `priority:P1`, `effort:M`, `ux-audit`, `foundational`

---

## Issue 4 — Records display raw "model,id" instead of a readable name

**Title:** [UX][grc:board] Minutes, Board Pack, and Governance Settings forms show raw technical identifiers as their title

- **Problem (role-specific experience):** A Company Secretary, Board Administrator, or Auditor opening Minutes, a Board Pack, or Governance Settings sees the breadcrumb and browser tab title read e.g. "govoo.minutes,4," "govoo.board.pack,8," or "govoo.governance.config,42" instead of a human-readable name — making multi-tab navigation unreliable and looking unfinished in front of a director or auditor.
- **Evidence:**
  - Screenshots: `screenshots/secretary/secretary_board_minutes_form_draft_desktop_en.png`; `screenshots/board_admin/board_admin_configuration_governance_settings_form_desktop_en.png`; `screenshots/auditor/auditor_board_minutes_form_approved_desktop_en.png`
  - Finding IDs: SEC-002, BOA-002, AUD-003
  - Steps to reproduce: Open any Minutes, Board Pack, or Governance Settings record as any backend role → observe breadcrumb/tab title
  - Affected roles/modules/views/viewports: Company Secretary, Board Administrator, Auditor — `govoo_board`, `govoo_base`, form view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** Rubric A9 — no raw technical identifiers in user-facing UI (Nielsen Norman microcopy heuristic).
- **User impact / Governance impact:** Confusing and unprofessional for non-technical users; makes multi-tab/multi-record navigation unreliable; a visible credibility issue if seen by a director or auditor during a screen-share of what is meant to be an audit/board-ready record.
- **Recommended solution:** Add a computed `display_name` (or stored `name` field set as `_rec_name`) to `govoo.minutes`, `govoo.board.pack`, and `govoo.governance.config`, composed from the related meeting name or company name (e.g. "Minutes - Annual General Meeting 2026"). **Alternative:** override only the view's `string` attribute to hide the technical title — trade-off: this would hide the symptom in the form view but leave the breadcrumb and any many2one reference elsewhere in the app (e.g. a resolution's "related minutes" smart button) still showing the raw identifier, so the compute-based fix is preferred as the complete solution.
- **Odoo implementation approach:** Python/model change — add `name = fields.Char(compute='_compute_name', store=True)` (or override `display_name`) on each of the three models and set `_rec_name = 'name'`.
- **Acceptance criteria:**
  - [ ] Opening any Minutes, Board Pack, or Governance Settings record shows a readable name (not `model,id`) in the breadcrumb, browser tab, and any many2one widget referencing it elsewhere.
  - [ ] The readable name updates automatically if the underlying meeting/company name changes (if stored, recompute on write; if related, confirm it tracks correctly).
  - [ ] No regression in existing many2one fields or smart buttons that reference these models.
- **Success metric:** 0 records of these 3 models display a raw `model,id` string anywhere in the UI, verified by a spot-check across all records in a seeded test dataset.
- **Sub-issues:**
  - [ ] Python/model change: add compute/display_name + `_rec_name` to `govoo.minutes`
  - [ ] Python/model change: same for `govoo.board.pack`
  - [ ] Python/model change: same for `govoo.governance.config`
  - [ ] Tests: unit test asserting `display_name` is non-default (not matching the `model,id` pattern) for a sample record of each model
  - [ ] Before/after verification: re-screenshot all three affected forms for Company Secretary, Board Administrator, and Auditor
- **Labels:** `type:content`, `type:ux`, `odoo:model`, `grc:board`, `role:cosec`, `role:board`, `role:audit`, `priority:P1`, `effort:M`, `ux-audit`, `foundational`

---

## Issue 5 — Write-restricted roles can act (or appear to act) as if they have write access

**Title:** [UX][grc:board] Board Administrator can actually edit locked records; Auditor sees write buttons the database will reject

- **Problem (role-specific experience):** A Board Administrator — intended to be config/admin-focused and read-only on meetings, minutes, resolutions, and board packs — can in fact edit every field, remove attendees, add agenda lines, and click "Mark as Held"/"Tally Votes"/"Withdraw," all of which save successfully with zero access-control error. Separately, an Auditor (whose role is correctly configured as read-only at the database level, `perm_write=False` confirmed via query) still sees these same workflow/header buttons rendered fully enabled, with no visual cue that a click will fail.
- **Evidence:**
  - Screenshots: `screenshots/board_admin/board_admin_board_meeting_form_scheduled_desktop_en.png`, annotated `screenshots/board_admin/BOA-001_annotated.png`; `screenshots/auditor/auditor_board_resolution_form_openvoting_desktop_en.png`, annotated `screenshots/auditor/AUD-001_annotated.png`
  - Finding IDs: BOA-001, AUD-001
  - Steps to reproduce (Board Administrator): Board & Meetings → Meetings → open "Board Meeting - Q1 2027" → edit Meeting Name → Save → observe successful save with chatter logging the change. Steps to reproduce (Auditor): open a Board Meeting (Held), a Compliance Instance (Late), and a Resolution (Open for Voting) → observe enabled "Mark as Minuted"/"Record Filing"/"Waive"/"Tally Votes"/"Withdraw" buttons.
  - Affected roles/modules/views/viewports: Board Administrator (actual write succeeds), Auditor (UI misrepresents actual, correctly-denied authority) — `govoo_board`, `govoo_compliance`, form view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** Rubric A6/B4/B7/C4 — segregation of duties expected under ISQM 1 access-control quality management and IPPF's principle that UI should reflect actual authority.
- **User impact / Governance impact:** A Board Administrator can silently corrupt statutory meeting/resolution records that should be secretary-controlled; a regulator or auditor reviewing RBAC configuration would flag this as a control deficiency. An Auditor who clicks a live-looking button (e.g. "Waive" on a late filing) gets a confusing raw access-denied error instead of understanding upfront that the action isn't available to them.
- **Recommended solution:** Add `groups="..."` (or an equivalent readonly/invisible domain keyed off a computed `is_readonly_role` field) to every statusbar and header action button across `govoo.board.meeting`, `govoo.board.resolution`, and `govoo.compliance.instance`, scoped so only the Company Secretary/Chair security group sees live buttons, mirroring the pattern already correctly applied to the mail composer's Send/Log/Activity buttons. **Alternative:** rely solely on a banner ("You have view-only access... contact the Company Secretary") without hiding the buttons — trade-off: cheaper, but leaves the actual Board Administrator write-access bug (BOA-001) completely unaddressed, since that one is a real permission gap, not just a misleading UI; the banner-only alternative is explicitly rejected for the Board Administrator half of this issue.
- **Odoo implementation approach:** Security change — define/verify a dedicated `govoo_board.group_board_admin` security group distinct from `govoo_board.group_board_secretary`; set `perm_write=0` in `ir.model.access.csv` for that group on the affected models (or add field-level `groups=` + `states`-based readonly in the view); add `groups="govoo_board.group_board_secretary"` to the workflow buttons so they are invisible — not just blocked — for both Board Administrator and Auditor.
- **Acceptance criteria:**
  - [ ] A Board Administrator can no longer edit Meeting Name, attendees, agenda lines, or any other field on `govoo.board.meeting`/`govoo.board.resolution`, and attempting to does not succeed.
  - [ ] Workflow buttons ("Mark as Held," "Tally Votes," "Withdraw," "Record Filing," "Waive," "Generate Filing Pack") are invisible (not just disabled) for Board Administrator and Auditor.
  - [ ] The "New" action is hidden from the Meetings/Resolutions list for both roles.
  - [ ] An automated UI test logs in as each read-only/admin-restricted role and asserts zero enabled write-triggering buttons are present on every affected form view.
- **Success metric:** 0 successful writes to `govoo.board.meeting`/`govoo.board.resolution`/`govoo.compliance.instance` by Board Administrator or Auditor test users in a regression suite; 0 enabled write buttons rendered for those roles.
- **Sub-issues:**
  - [ ] Security change: define/verify `govoo_board.group_board_admin` as distinct from `govoo_board.group_board_secretary`, with `perm_write=0` on the three affected models
  - [ ] XML view change: add `groups=` to statusbar/header buttons on the Meeting, Resolution, and Compliance Instance form views (name the specific view xml_ids once confirmed in code)
  - [ ] XML view change: hide the "New" action on the Meetings and Resolutions list/form actions for these groups
  - [ ] Needs-functional-review: confirm with the product owner the exact intended boundary between "Board Administrator" and "Company Secretary" permissions before locking the group definition
  - [ ] Tests: automated test asserting zero enabled write buttons per read-only/admin-restricted role across all affected views
  - [ ] Before/after verification: repeat the BOA-001 and AUD-001 edit/click steps and confirm they now fail cleanly with a clear message
- **Labels:** `type:workflow`, `type:bug`, `odoo:security`, `odoo:view`, `grc:board`, `grc:compliance`, `role:board`, `role:audit`, `priority:P0`, `effort:M`, `ux-audit`, `foundational`, `needs-functional-review`

---

## Issue 6 — Directors and shareholders cast binding votes without weight, context, or confirmation

**Relationship to Track B:** this is a **blocking prerequisite for Epic P5** (Portal & Reports
branding) below. Do not rebrand the vote-cast page before this ships — a visually polished page
that still has no weight disclosure, no resolution text, and no confirmation is a worse outcome
than the current plain one, because it looks more finished than it is.

**Title:** [UX][grc:board] Portal voting flow gives no voting-weight disclosure, no resolution text, and no submission confirmation

- **Problem (role-specific experience):** A Shareholder casting a weighted vote is never shown their own voting power (shares held / % of voting rights) before submitting. A Director or Shareholder casting any vote sees only a bare resolution title — no resolution text, no link to the originating meeting or board pack — and after clicking "Submit Vote," both roles are silently redirected with no success message, toast, or confirmation of what was recorded.
- **Evidence:**
  - Screenshots: `screenshots/shareholder_portal/shareholder_portal_votes_cast_form_desktop_en.png` (annotated `SHA-001_annotated.png`); `screenshots/shareholder_portal/shareholder_portal_votes_list_submitted_desktop_en.png` (annotated `SHA-002_annotated.png`); `screenshots/director_portal/director_portal_vote_submitted_no_confirmation_desktop_en.png` (annotated `DIR-002_annotated.png`); `screenshots/director_portal/director_portal_vote_form_desktop_en.png`
  - Finding IDs: SHA-001, SHA-002, SHA-004, DIR-002, DIR-003
  - Steps to reproduce: Log in as a Director or Shareholder → open an open resolution's vote-cast page → observe no voting-weight figure (shareholder) and no resolution text (both) → select a choice → Submit Vote → observe silent redirect with no confirmation
  - Affected roles/modules/views/viewports: Director Portal (Desktop + Mobile), Shareholder Portal (Desktop) — `govoo_shares`, `govoo_board`, portal controller/template, en_US
- **Standard/framework/pattern violated:** Rubric A5/B2/C2/C4 — error prevention/confirmation of consequential actions; informed, accountable decision-making; weighted-voting transparency at the point of decision.
- **User impact / Governance impact:** Shareholders cannot verify their voting weight before an irreversible action, undermining confidence in a weighted-voting mechanism core to the product. Directors and shareholders alike are asked to vote on a title alone, without the ability to review full resolution wording. Neither role gets confirmation their vote was recorded, which is especially risky for a conflict-of-interest declaration or a contested resolution, and could lead to disputes over whether a vote was actually cast.
- **Recommended solution:** Add a visible voting-weight summary line (e.g. "You are voting with 30,000 shares, 39.47% of Ordinary Shares") sourced from the same data already computed for the Holdings page; display the resolution's full text/body and a link back to its meeting and board pack; show an explicit confirmation message/page after submission (e.g. "Your vote (For) on '...' was recorded at <timestamp>"). **Alternative:** send the confirmation only by email (reusing the existing reminder-email infrastructure) without an in-page confirmation — trade-off: cheaper to build, but a shareholder/director still leaves the page unsure in the moment, so an in-page confirmation is preferred with email as a nice-to-have addition, not a replacement.
- **Odoo implementation approach:** Portal change — in the vote-cast controller/QWeb template, pass the shareholder's existing `govoo.share.allotment`-derived voting power into the render context and display it; extend the template to render the resolution's existing `description`/text field and a link to `meeting_id`; add a confirmation flash/page using Odoo's portal session-flash pattern before the post-submit redirect. No new models are required — this reuses fields that already exist on the backend records.
- **Acceptance criteria:**
  - [ ] The shareholder vote-cast page displays the shareholder's own share quantity and percentage/voting-weight before they can submit.
  - [ ] The vote-cast page (both roles) displays the resolution's full text and a working link to its meeting/board pack.
  - [ ] After clicking "Submit Vote," both roles see an explicit on-page confirmation naming their choice and a timestamp, not just a silent redirect.
  - [ ] Director's meeting detail agenda rows link forward to the corresponding open vote.
- **Success metric:** Post-release user testing confirms 100% of test voters can state their own voting weight and locate the full resolution text without leaving the vote-cast page; 0% report uncertainty about whether their vote was recorded.
- **Sub-issues:**
  - [ ] XML/portal template change: add voting-weight summary block to the shareholder vote-cast template
  - [ ] XML/portal template change: add resolution text + meeting/board-pack link to both director and shareholder vote-cast templates
  - [ ] Python/controller change: implement post-submit flash-confirmation (session-based) before redirect, for both portal controllers
  - [ ] XML/portal template change: add a "vote open" link/badge on the meeting-detail agenda row for directors
  - [ ] Needs-functional-review: confirm whether a vote receipt should also be emailed (reusing existing reminder-email infrastructure) as a secondary channel
  - [ ] Tests: portal controller test asserting the confirmation context/flash is set after a successful vote POST
  - [ ] Before/after verification: re-run the full vote-cast flow for both Director and Shareholder on Desktop and Mobile and confirm weight, text, and confirmation all appear
- **Labels:** `type:workflow`, `type:ux`, `odoo:portal`, `grc:board`, `role:director-portal`, `role:shareholder-portal`, `priority:P0`, `effort:M`, `ux-audit`, `foundational`

---

## Issue 7 — Key list/detail views show raw IDs and technical codes instead of task-relevant content

**Title:** [UX][grc:board] Board Packs list and Audit Ledger/AI Request Log columns show no usable, human-readable content

- **Problem (role-specific experience):** A Company Secretary opening Board & Meetings → Board Packs sees a list with only one column: raw database row numbers (265, 266, 267, 8, 7, 6, 4, 3, 2) — no meeting name, date, status, or document reference. A Board Administrator reviewing the Audit Ledger sees the "Register" column as raw technical model names (e.g. "govoo.register.charge") instead of "Register of Charges," and the AI Request Log's "Feature" column shows internal ticket codes ("AI-F07: Data Extraction") instead of a friendly label.
- **Evidence:**
  - Screenshots: `screenshots/secretary/secretary_board_packs_list_desktop_en.png` (annotated `SEC-001_annotated.png`); `screenshots/board_admin/board_admin_statutoryregisters_auditledger_list_desktop_en.png` (annotated `BOA-005_annotated.png`); `screenshots/board_admin/board_admin_ai_requestlog_list_desktop_en.png`
  - Finding IDs: SEC-001, BOA-005, BOA-009
  - Steps to reproduce: Board & Meetings → Board Packs (observe ID-only list); Statutory Registers → Audit Ledger (observe raw model names); AI → Request Log (observe raw feature codes)
  - Affected roles/modules/views/viewports: Company Secretary, Board Administrator — `govoo_board`, `govoo_base`, `govoo_rw_ai`, list view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** Rubric A1/A9/B2/C6 — findability/scannability; no raw technical identifiers shown to end users; views should show task-relevant content, not ORM defaults; audit-evidence usability for an external reviewer.
- **User impact / Governance impact:** A Company Secretary cannot identify which Board Pack belongs to which meeting without opening all 10 records one at a time — the power-user "assemble/distribute board packs" workflow is effectively unusable from the list view. The Audit Ledger — the one screen built specifically to let a Board Administrator or auditor trace statutory register changes — requires technical Odoo knowledge to even read, adding unnecessary friction to an audit procedure that samples this ledger as evidence.
- **Recommended solution:** Define an explicit `<list>` view for `govoo.board.pack` with Meeting, Pack Document, Status, and Distribution Date columns, default-sorted by meeting date. Add a computed label (via a lookup against `ir.model.name`) for the Audit Ledger's "Register" column, and strip the "AI-F0x:" prefix from the AI Request Log's Feature column (keeping it internally for traceability). **Alternative (Board Packs only):** leave the default list view but add a `default_order` and rely on the existing form view for identification — trade-off: this leaves the core findability problem unsolved, since the task is specifically to locate a pack from a list of many without opening each one.
- **Odoo implementation approach:** Python/model change (computed label) + XML view change (new list view). Add `register_label = fields.Char(compute='_compute_register_label')` on the Audit Ledger model (looking up `ir.model.name`); add a `selection`/computed display field for the AI Request Log's `feature`; define a new `<list>` view for `govoo.board.pack`.
- **Acceptance criteria:**
  - [ ] Board Packs list shows Meeting, Pack Document, Status, and Distribution Date columns, sorted by meeting date by default.
  - [ ] Audit Ledger's "Register" column shows a human-readable label (e.g. "Register of Charges"), not a raw model name, for all register types.
  - [ ] AI Request Log's "Feature" column shows a friendly label ("Data Extraction") with the internal code available only on hover/tooltip.
- **Success metric:** A Company Secretary can identify the correct Board Pack for a named upcoming meeting in 1 glance at the list (0 blind record-opens needed), down from up to 10 today.
- **Sub-issues:**
  - [ ] XML view change: author a new `<list>` view for `govoo.board.pack`
  - [ ] Python/model change: add `register_label` compute to the Audit Ledger model
  - [ ] Python/model change: add a friendly display label/mapping for AI Request Log's `feature` and `model_used` fields
  - [ ] Tests: view-rendering test asserting the new Board Pack list columns are present and populated
  - [ ] Before/after verification: re-screenshot Board Packs list, Audit Ledger list, and AI Request Log list
- **Labels:** `type:ux`, `type:reporting`, `odoo:view`, `odoo:model`, `grc:board`, `grc:compliance`, `role:cosec`, `role:board`, `priority:P0`, `effort:M`, `ux-audit`, `foundational`

---

## Issue 8 — Home dashboard is identical for every role and collapses on mobile

**SUPERSEDED BY EPIC P3 below — do not file this issue standalone.** The manager's spec
independently plans a full "Clagov Home / Overview" dashboard rebuild (§6) covering this exact
screen. Rather than file two parallel, potentially contradictory streams of work on the same
dashboard, this finding's content is carried forward as hard acceptance criteria inside Epic P3.
Kept here only as the evidence trail (screenshots, finding IDs) that justifies those criteria.

**Title:** [UX][grc:board] Dashboard is not role-aware and its widgets are unusable on a 390px viewport

- **Problem (role-specific experience):** Every role audited (Company Secretary, Board Administrator, Shareholder, Auditor) lands on the same three-widget Dashboard, including an "Open Resolutions Requiring My Vote" panel addressed to roles that have no voting rights at all (Company Secretary, Board Administrator, Auditor). None of the widgets are reframed per role to show "what needs my attention" for that role's actual job. On a 390px mobile viewport, the Company Secretary's dashboard additionally collapses: only the title column of each widget table is visible, with Status, Result, and Due Date scrolled entirely out of view behind a nested horizontal scrollbar.
- **Evidence:**
  - Screenshots: `screenshots/secretary/secretary_dashboard_home_mobile_en.png` (mobile collapse), `screenshots/secretary/secretary_dashboard_home_desktop_en.png`, `screenshots/board_admin/board_admin_dashboard_home_desktop_en.png`, `screenshots/auditor/auditor_dashboard_home_default_desktop_en.png`
  - Finding IDs: SEC-005, SEC-010, BOA-007, SHA-003, AUD-005
  - Steps to reproduce: Log in as any of the 4 affected roles → land on Dashboard → observe identical widget set and wording; repeat as Company Secretary on a 390x844 viewport → observe horizontal-scroll-only access to Status/Date columns
  - Affected roles/modules/views/viewports: Company Secretary (Desktop + Mobile), Board Administrator (Desktop), Shareholder (Desktop), Auditor (Desktop) — `govoo_portal`/dashboard, en_US
- **Standard/framework/pattern violated:** Rubric A4/A8/C1/C8 — configuration/labeling consistency; responsive mobile layout; role-based home surfacing what needs attention; power-user efficiency.
- **User impact / Governance impact:** The single most consistent finding across the entire audit — no role's home screen tells that role what actually needs doing today, and a Company Secretary checking their phone before a meeting cannot see status/urgency at all without discovering a hidden nested-scroll gesture. Reduces the practical reliability of the dashboard for monitoring overdue compliance items and pending votes, especially for on-the-go use.
- **Recommended solution:** Scope dashboard widget visibility and wording by the viewing user's security group — e.g. show "Open Resolutions Requiring My Vote" only to actual voters (Directors/Shareholders), and a neutral "Resolutions Open for Voting" read-only list to everyone else; replace the fixed-width mini-tables with a responsive stacked card layout below a mobile breakpoint, mirroring how the full Meetings list already reflows into kanban-style cards on mobile. **Alternative:** ship one shared dashboard but add a page-level role badge/banner without changing widget content — trade-off: cheaper, but does not fix the factually incorrect "my vote" framing shown to non-voters, so is not sufficient on its own.
- **Odoo implementation approach:** OWL/dashboard-widget change — add a `groups`-based or role-aware condition on each dashboard widget's definition; CSS/OWL change to switch the embedded list widgets to a responsive card layout under a breakpoint.
- **Acceptance criteria:**
  - [ ] "Open Resolutions Requiring My Vote" (or equivalent wording) is shown only to users with actual voting rights on resolutions; all other roles see a neutral, non-actionable equivalent.
  - [ ] On a 390px viewport, all three dashboard widgets display their Status/Result/Due-Date information without requiring a nested horizontal scroll.
  - [ ] Each role's dashboard surfaces at least one piece of role-relevant "needs attention" information beyond the current generic set (e.g. configuration gaps for Board Administrator, read-only banner for Auditor).
- **Success metric:** 5-second-test pass rate across all 5 roles goes from 0/5 (this pass) to 5/5 in the next round of role-based testing; mobile dashboard requires 0 nested-scroll gestures to read Status/Date.
- **Sub-issues:**
  - [ ] Design review: define per-role dashboard widget variants (content + wording) with the product owner
  - [ ] OWL/owl-component change: add role/group-based conditional rendering to the dashboard widget definitions
  - [ ] OWL/CSS change: implement responsive stacked-card layout for dashboard widgets below a mobile breakpoint
  - [ ] Needs-functional-review: confirm what "needs attention" content is appropriate per role (especially Board Administrator and Auditor, who have no existing equivalent today)
  - [ ] Tests: responsive-layout test at 390px asserting no nested horizontal scrollbar is required to view Status/Date
  - [ ] Before/after verification: re-screenshot the Dashboard for all 5 roles on both Desktop and Mobile
- **Labels:** `type:ux`, `type:mobile`, `odoo:owl`, `grc:board`, `role:cosec`, `role:board`, `role:shareholder-portal`, `role:audit`, `priority:P1`, `effort:L`, `ux-audit`, `foundational`

---

## Issue 9 — Audit trail shows no real change history; all authorship attributed to OdooBot

**Title:** [UX][grc:compliance] Chatter and Audit Ledger show zero real user attribution for statutory record changes

- **Problem (role-specific experience):** A Board Administrator or Auditor reviewing the Audit Ledger's "Changed By" column sees "OdooBot" on all 26 sampled entries (spanning Mar 2015–Oct 2026, across director/member/charge/beneficial-owner registers) — never a real named user, even though real users (Aline Mukamana, Eric Mugisha, Administrator) appear elsewhere in the system. Separately, an Auditor reviewing a Board Meeting's or AGM's chatter — a record that has passed through multiple status transitions (Draft → Scheduled → Held, or 5 statuses to Minuted) — sees only a single "created by OdooBot" entry, with no logged transition history at all.
- **Evidence:**
  - Screenshots: `screenshots/board_admin/board_admin_statutoryregisters_auditledger_list_desktop_en.png` (annotated `BOA-005_annotated.png`); `screenshots/auditor/auditor_board_meeting_form_held_desktop_en.png`
  - Finding IDs: BOA-006, AUD-002
  - Steps to reproduce: Statutory Registers → Audit Ledger → scan "Changed By" column (all rows read "OdooBot"); open a multi-transition Board Meeting or AGM → scroll chatter → observe only the initial creation entry
  - Affected roles/modules/views/viewports: Board Administrator, Auditor — `govoo_base` (audit ledger), `govoo_board` (mail.thread), list + form view, Desktop 1440x900, en_US
- **Standard/framework/pattern violated:** AGENTS.md hard rule ("Every transactional model inherits mail.thread. tracking=True on all statutory fields"); ISA 230 audit documentation; rubric C5/C6.
- **User impact / Governance impact:** The audit ledger and chatter — whose entire purpose is accountability — cannot answer "who did what and when." Any auditor testing register completeness/accuracy, or reviewing IT general controls, would flag a 100%-OdooBot-attributed ledger and a chatter with no transition history as a direct audit-trail integrity defect.
- **Recommended solution:** Ensure the audit-ledger entry creation logic (and `mail.thread` tracking) captures `self.env.user` — the real user who triggered the change — rather than defaulting to the data-seeding/automation user used when demo data was loaded; distinguish genuine seed/demo-data entries (acceptable to show as "System/Seed Data") from real user-triggered changes. **Alternative:** backfill historical entries with a generic "Unknown/Legacy" label instead of fixing root cause — trade-off: cosmetically better for old records, but does nothing to prevent the same defect recurring for every future change, so the root-cause fix is required regardless; backfill labeling can be a secondary cleanup step.
- **Odoo implementation approach:** Python/model change — in the `create`/`write` override (or dedicated logging method) populating the audit ledger, replace any hardcoded/default author with `self.env.user.id`; verify this isn't overwritten by `noupdate` data-file seeding running under the system/OdooBot context. Separately, verify `tracking=True` is genuinely set on the state/status fields of `govoo.meeting`, `govoo.minutes`, `govoo.resolution`, and `govoo.compliance.instance`, and that status-transition methods call `message_post()`/rely on automatic tracking rather than bypassing it (e.g. via `sudo().write()` without tracking context, or raw SQL).
- **Acceptance criteria:**
  - [ ] A real user action (e.g. a Company Secretary manually changing a register entry via the UI) produces an Audit Ledger entry attributed to that real user, not OdooBot.
  - [ ] A meeting or resolution's status transitions (e.g. Draft → Scheduled → Held) each produce a visible chatter tracking-message entry naming the real user and timestamp.
  - [ ] Genuine seed/demo-data entries are visually distinguishable from real user-triggered changes (e.g. labeled "System/Seed Data").
- **Success metric:** 100% of new (post-fix) register changes and status transitions in a test run are attributed to the real triggering user, verified by a repeatable test scenario.
- **Sub-issues:**
  - [ ] Python/model change: fix audit-ledger entry creation to use `self.env.user.id` instead of a default/seeding user
  - [ ] Python/model change: verify and, if missing, add `tracking=True` to statutory status/state fields on the four affected models
  - [ ] Python/model change: audit status-transition methods for `sudo()`/raw-SQL writes that bypass `mail.thread` tracking
  - [ ] Needs-functional-review: decide how to label/backfill historical OdooBot-attributed entries that predate the fix
  - [ ] Tests: regression test asserting a UI-triggered register change and a status transition both produce correctly-attributed log entries
  - [ ] Before/after verification: re-open the Audit Ledger and a multi-transition meeting/AGM and confirm real attribution appears
- **Labels:** `type:bug`, `type:reporting`, `odoo:model`, `grc:compliance`, `grc:board`, `role:board`, `role:audit`, `priority:P1`, `effort:L`, `ux-audit`, `foundational`

---

## Issue 10 — Director portal exposes other committees' confidential meetings

**Relationship to Track B:** this is a **blocking prerequisite for Epic P5** (Portal & Reports
branding) below, alongside Issue 6. Do not ship a rebranded portal meeting-detail page before
this confidentiality leak is closed.

**Title:** [UX][grc:board] Director can view meetings and board packs of committees they are not a member of

- **Problem (role-specific experience):** Grace Uwimana, a director appointed only to the "Board of Directors" committee (confirmed via her own `/my/appointment` record), can nonetheless open full detail pages on `/my/meetings` for Audit Committee and Risk & Compliance Committee meetings — committee name, date, status, location, agenda, and board-pack status — with no confidentiality cue, restriction notice, or filtering by her actual committee membership applied anywhere in the portal.
- **Evidence:**
  - Screenshot: `screenshots/director_portal/director_portal_meeting_crosscommittee_exposure_mobile_en.png`, annotated: `screenshots/director_portal/DIR-001_annotated.png`
  - Finding ID: DIR-001
  - Steps to reproduce: Log in as Grace Uwimana (Director, Board of Directors committee only) → navigate to `/my/meetings` → open "Audit Committee Meeting - Q4 2026" (`/my/meetings/9`) or a Risk & Compliance Committee meeting (`/my/meetings/7`, `/my/meetings/2680`) → observe full detail renders with no access restriction
  - Affected roles/modules/views/viewports: Director Portal, Mobile 390x844 (confirmed), likely also Desktop (not independently re-confirmed this pass) — `govoo_board`/portal controller, en_US
- **Standard/framework/pattern violated:** Rubric B7/C7 — committee-level confidentiality segregation expected for audit/risk committee governance structures.
- **User impact / Governance impact:** A director can read governance information — and, once distributed, full board packs with financials and resolutions — belonging to a committee they do not sit on. This breaks the confidentiality model that committee-restricted governance structures are meant to provide, and would be a finding in any external governance or security review; could expose commercially or legally sensitive committee deliberations to directors outside that committee.
- **Recommended solution:** Filter `/my/meetings` (list and direct `/my/meetings/<id>` access) to only meetings of committees the logged-in partner is an active member of, per `govoo.board.committee`/membership records; return the same access-denied page already used for out-of-scope meeting ids (see DIR-004 in the full findings) when a non-member director requests a meeting. **Alternative:** keep all meetings visible in the list but redact detail (agenda, board pack) for non-member committees — trade-off: more complex to build correctly and still leaks the existence/scheduling of confidential committee meetings, so full filtering is preferred.
- **Odoo implementation approach:** Python/portal-controller change — in the portal controller for meeting routes, add a domain/check against the committee membership model (e.g. `govoo.board.membership`) for `request.env.user.partner_id` before rendering `MeetingList`/`MeetingDetail`, mirroring the existing `access_token` validation pattern already used for other restricted records in the same controller.
- **Acceptance criteria:**
  - [ ] `/my/meetings` for a director lists only meetings of committees that director is an active member of.
  - [ ] Directly requesting `/my/meetings/<id>` for a non-member committee's meeting returns the same access-denied page used for other out-of-scope ids, not the full detail page.
  - [ ] A director who IS a member of multiple committees still correctly sees all of those committees' meetings (regression check — the fix must not over-restrict).
- **Success metric:** 0 cross-committee meeting-detail exposures in a regression test covering at least 2 directors with different, non-overlapping committee memberships.
- **Sub-issues:**
  - [ ] Python/portal-controller change: add committee-membership domain check to the meeting list and detail routes
  - [ ] Needs-functional-review: confirm with the governance/legal team whether any committee memberships should see cross-committee summaries (e.g. a board chair who sits on all committees) before finalizing the filter logic
  - [ ] Security change: verify the same membership check is applied consistently to any related board-pack or minutes portal route reachable from a meeting
  - [ ] Tests: regression test with 2+ directors of differing committee membership asserting correct, non-overlapping visibility
  - [ ] Before/after verification: repeat Grace Uwimana's exact DIR-001 steps and confirm the Audit/Risk & Compliance meetings are no longer reachable
- **Labels:** `type:bug`, `type:workflow`, `odoo:portal`, `odoo:security`, `grc:board`, `role:director-portal`, `priority:P0`, `effort:M`, `ux-audit`, `needs-functional-review`

---

# Track B — Clagov Brand & UX Uplift

Source: `Clagov_UIUX_Improvement_Specification.md` (manager-provided, v1.0, August 2026), reconciled
against the audit in `MANAGER_SPEC_ANALYSIS.md`. Each epic below follows the manager's own P1–P6
phase structure. Sub-issues are scoped at epic-creation granularity here; each will likely split
further once a developer picks it up, per the spec's own "prefer the lightest approach" principle.

Additional label categories used only in Track B (extending the taxonomy from the top of this
file): `type:workflow` reused for dashboard/portal; new `meta:needs-design` (visual design review
needed, distinct from `needs-functional-review`'s governance/legal sense); `odoo:owl` for OWL
client-action/component work.

---

## Epic P1 — Brand Foundation (`govoo_theme` module)

**Title:** [UX][epic] No Clagov brand identity exists anywhere in the product

- **Problem:** Every role sees stock Odoo 19 purple, no logo, no custom login, and no design
  system — confirmed in the audit's own scorecard (A4 Consistency: 2/5) and independently in the
  spec's current-state assessment. The product currently looks like a raw developer build.
- **Evidence:** `MANAGER_SPEC_ANALYSIS.md` §1 (fact-check confirms zero existing SCSS/theme
  assets suite-wide); every screenshot in `ux-audit/screenshots/` shows the default Odoo purple
  accent and stock login page.
- **Standard/framework/pattern violated:** Spec §2 Design Goals ("Branded, not generic");
  commercial-product credibility expectation for a paid governance SaaS product.
- **User impact / Governance impact:** Low governance risk, high commercial/adoption risk — a
  board director or bank executive evaluating the product on first impression sees an unbranded
  internal tool, not a finished product, which undermines trust before any functional evaluation
  happens.
- **Recommended solution:** Build `govoo_theme` exactly per spec §8's module layout: SCSS brand
  tokens (`$clagov-navy #1F3864`, `$clagov-navy-deep #001526`, `$clagov-gold #C6A15B`,
  `$clagov-cream #F5F1E8`) mapped onto Odoo's own `$o-brand-primary`/`$o-brand-secondary`
  variables so the whole backend adopts the brand via override, not replacement; branded login;
  app icon; menu reorg; OCA `web_responsive` once verified (see sub-issues). **Alternative:**
  adopt a paid theme (Muk/Clarity Pro) as a stopgap — spec explicitly rejects this as the shipped
  identity (Option A verdict: "Not for a product"), acceptable only as a short-lived internal-demo
  measure per Open Item #4, which is a PM decision, not an engineering one.
- **Odoo implementation approach:** New module, XML/SCSS only for the token/skin layer (upgrade-
  safe per spec §9 NFR: "prefer SCSS variable overrides... over replacing core templates"); OWL
  only for the dashboard components scoped under Epic P3, not needed for this epic.
- **Acceptance criteria:**
  - [ ] `govoo_theme` installs cleanly as a dependent of `govoo_base`, with `web` and (pending
        verification) `web_responsive` as dependencies.
  - [ ] Every backend screen (list, form, kanban, search, login) reflects the Clagov navy/gold
        palette in both light and native Odoo 19 dark mode.
  - [ ] Branded login page ships with the app icon and (placeholder, pending real assets per Open
        Item #1) login artwork.
  - [ ] No existing test in the 11-module cross-regression suite regresses (theme is additive
        only — see spec §9 NFR "Non-destructive").
- **Success metric:** A new user's first screen (login) and first authenticated screen (home) both
  show Clagov navy/gold with zero stock-purple elements remaining, verified by screenshot diff
  against this audit's existing baseline captures.
- **Sub-issues:**
  - [ ] **Verification (blocks the rest of this epic's OCA-dependent work):** check the OCA/web
        GitHub repository's 19.0 branch directly for `web_responsive`, `web_notify`,
        `web_tree_dynamic_colored_field`, `web_field_tooltip`, and `web_chatter_position`; record
        the exact confirmed version (or "not yet ported — build the effect in `govoo_theme`
        instead," per the spec's own fallback instruction) for each. The spec only claims
        `web_responsive` as confirmed; treat the other four as unverified until checked.
  - [ ] Config/module scaffold: create `govoo_theme/__manifest__.py`, directory structure per
        spec §8 (`static/src/scss/`, `static/src/js/dashboards/`, `static/src/img/`, `views/`,
        `data/`)
  - [ ] XML/SCSS change: `variables.scss` — brand tokens + `$o-brand-primary`/`$o-brand-secondary`
        overrides, including dark-mode token values (spec §9 NFR)
  - [ ] XML/SCSS change: `backend.scss` — nav, buttons, badges, list/kanban/form skin
  - [ ] XML view change: `login_templates.xml` — branded login (blocked on real brand assets,
        Open Item #1 — use placeholder navy/gold styling without a final logo until supplied)
  - [ ] Config change: register `web_responsive` once verified; evaluate menu reorg using its
        searchable app-menu feature
  - [ ] Needs-design: final logo SVG, wordmark, favicon, login artwork (Open Item #1, owner:
        Design/brand — blocking item, not an engineering task)
  - [ ] Needs-functional-review: heading font licensing if a non-system font is used (Open Item
        #5, owner: Design/Legal)
  - [ ] Translation: FR/RW `.po` stubs for any new user-facing strings this module introduces
  - [ ] Tests: visual-regression or asset-bundle-loads smoke test; full 11-module cross-regression
        run to confirm non-destructiveness
  - [ ] Before/after verification: re-screenshot login + one list/form/kanban per module and
        compare against this audit's baseline captures
- **Labels:** `type:ux`, `type:accessibility`, `odoo:view`, `odoo:config`, `meta:epic`,
  `meta:foundational`, `meta:needs-design`, `priority:P1`, `effort:L`, `ux-audit`

---

## Epic P2 — Kanban & List Overhaul

**Title:** [UX][epic] Kanban cards are text-only; lists lack status colour, widgets, and default sort/group

- **Problem:** The 6 existing kanban views (meeting, resolution, vote, compliance instance,
  contract, contract obligation) are plain stacked-text cards with no colour bar, status badge,
  date chip, progress indicator, or quick-action menu. Committees, appointments, and share classes
  have no kanban view at all. Lists generally lack row colouring, optional columns, and the right
  widgets (monetary/progressbar/badge/handle).
- **DEPENDS ON Issues 4 and 7 (Track A) — sequence this epic after them, not before.** A rich
  kanban card's title and a list's enriched columns are only as good as the underlying field they
  bind to. Issue 4 fixes `govoo.minutes`/`govoo.board.pack`/`govoo.governance.config` showing
  `model,id` instead of a name; Issue 7 fixes the Board Packs list, Audit Ledger, and AI Request
  Log showing raw IDs/technical codes instead of task-relevant columns. Building this epic's rich
  cards/columns on top of those unresolved defects means re-doing the work once Issues 4/7 land.
- **Evidence:** Audit screenshots `secretary_board_meetings_list_desktop_en.png`,
  `secretary_board_resolutions_list_desktop_en.png` (plain list, no decoration); spec §1 Current-
  State table ("Kanban views: Text-only cards... Weakest area").
- **Standard/framework/pattern violated:** Rubric A1/B2 (findability, task-relevant content);
  spec §2 "Glanceable: a user sees status... through colour and shape before reading text."
- **User impact / Governance impact:** Slower status scanning for power users (Company Secretary,
  Board Administrator) across their highest-frequency screens; low governance risk on its own,
  but compounds the audit's A1/B2 findings if shipped before Issues 4/7.
- **Recommended solution:** Per spec §5.1/§5.2 — coloured state/risk bar, title+subtitle
  hierarchy, status badge, due-date chip (red when overdue), progress bar where relevant
  (resolution vote tally, contract obligations completed), quick-action dropdown, responsible-
  user avatar; list row colouring via `decoration-*` and/or `web_tree_dynamic_colored_field`
  (pending OCA verification in Epic P1); `optional="hide"` columns; sensible default `group_by`
  per model (e.g. compliance by status, contracts by type).
- **Odoo implementation approach:** XML view inheritance only for existing 6 kanbans (new
  `<templates>` arch); new `<kanban>` view definitions for committees, appointments, share
  classes; list-view XML changes for decorations/widgets/optional columns. No Python/model
  changes required beyond what Issues 4/7 already specify.
- **Acceptance criteria:**
  - [ ] Issues 4 and 7 are resolved and verified before this epic's cards are built on
        `govoo.minutes`, `govoo.board.pack`, or any Audit-Ledger-adjacent model.
  - [ ] Every one of the 9 target models (6 existing + 3 new) has a kanban card with: state/risk
        colour bar, title+subtitle, status badge, due-date chip where applicable, quick-action
        menu.
  - [ ] Resolution and contract-obligation kanban cards show a progress bar (vote tally /
        obligations completed respectively).
  - [ ] Each of compliance, contracts, and board-meeting lists has a documented sensible default
        `group_by`.
  - [ ] No text-only kanban card remains anywhere in the suite (spec Definition of Done).
- **Success metric:** 9/9 target models have rich kanban cards (0/9 before); 0 kanban views remain
  default-ORM text-only, verified by a visual sweep matching the audit's screenshot methodology.
- **Sub-issues:**
  - [ ] XML view change: redesign kanban card template for `govoo.meeting`
  - [ ] XML view change: redesign kanban card template for `govoo.resolution` (+ progress bar)
  - [ ] XML view change: redesign kanban card template for `govoo.vote`
  - [ ] XML view change: redesign kanban card template for `govoo.compliance.instance`
  - [ ] XML view change: redesign kanban card template for `govoo.contract`
  - [ ] XML view change: redesign kanban card template for `govoo.contract.obligation` (+
        progress bar)
  - [ ] XML view change: new kanban view for `govoo.committee`
  - [ ] XML view change: new kanban view for `govoo.appointment`
  - [ ] XML view change: new kanban view for `govoo.share.class`
  - [ ] XML view change: list-view decorations/optional columns/default group-by pass across
        `govoo_board`, `govoo_compliance`, `govoo_contracts`, `govoo_shares`
  - [ ] Config change: adopt `web_tree_dynamic_colored_field` once verified in Epic P1, or
        implement row colouring via `decoration-*` if the OCA module isn't 19.0-ready
  - [ ] Tests: view-rendering smoke test per redesigned kanban/list
  - [ ] Before/after verification: re-screenshot all 9 kanban views and the 4 enriched list views
- **Labels:** `type:ux`, `odoo:view`, `meta:epic`, `priority:P2`, `effort:L`, `ux-audit`

---

## Epic P3 — Governance Dashboards

**Title:** [UX][epic] No governance dashboards exist beyond 2 graph + 2 pivot views; the one home screen that does exist is not role-aware

**ABSORBS Track A Issue 8.** This epic's Home/Overview dashboard is the same screen the audit
flagged as identical-for-every-role and broken on mobile. Issue 8's findings (SEC-005, SEC-010,
BOA-007, SHA-003, AUD-005) are carried forward below as non-negotiable acceptance criteria for
the Home/Overview dashboard specifically — this is not optional polish layered on later.

- **Problem:** Community has no Enterprise Spreadsheet dashboards, and the suite currently ships
  no landing dashboard at all beyond the generic 3-widget home screen the audit tested (which
  fails the 5-second test for every role and collapses on mobile — see Issue 8 for full evidence).
  Compliance RAG status, board calendar/actions, cap-table ownership, and contract
  expiry/renewal have no dedicated views; only raw graph/pivot actions exist for some of the
  underlying data.
- **Evidence:** Issue 8's full evidence (screenshots, finding IDs SEC-005/010, BOA-007, SHA-003,
  AUD-005); spec §6 dashboard content table.
- **Standard/framework/pattern violated:** Rubric C1 (role-based home — scored 1/5 in the audit,
  its single lowest-scoring item); spec §2 "Glanceable."
- **User impact / Governance impact:** The audit's single most consistent finding across all 5
  roles — no one's home screen tells them what needs attention today. This is the highest-reach
  item in the entire combined backlog (every role, every day, first thing they see).
- **Recommended solution:** Build all 5 dashboards per spec §6, each as either an OWL client
  action or a graph/pivot landing view (Open Item #3 — tech-lead decision; non-binding
  recommendation in `MANAGER_SPEC_ANALYSIS.md` §5.2 leans OWL for Home/Overview and Compliance
  RAG, graph/pivot for Cap Table and Contracts). Every tile must be permission-aware (respects
  record rules and company scope) and must satisfy Issue 8's acceptance criteria for the
  Home/Overview dashboard specifically. **Alternative:** ship only the Home/Overview dashboard
  first and defer the other 4 — reasonable sequencing within this epic (see sub-issues), but all
  5 remain in scope per the spec's Definition of Done.
- **Odoo implementation approach:** OWL client actions (primary recommendation for Home/Overview
  and Compliance RAG) and/or graph/pivot landing views (Cap Table, Contracts) — decision pending
  tech-lead confirmation of Open Item #3. No Python/model changes needed beyond what already
  exists; this is a presentation layer over existing fields, with one exception: role-aware tile
  visibility needs a `groups`/security-group check per tile.
- **Acceptance criteria:**
  - [ ] Home/Overview dashboard shows KPI tiles (upcoming meetings, open resolutions, overdue
        filings, expiring contracts) and recent activity, and is the branded landing screen on
        login.
  - [ ] **(from Issue 8)** "Open Resolutions Requiring My Vote" or equivalent wording is shown
        only to users with actual voting rights; all other roles see a neutral, non-actionable
        equivalent.
  - [ ] **(from Issue 8)** At 390px, all dashboard widgets display Status/Result/Due-Date without
        a nested horizontal scroll.
  - [ ] Compliance RAG dashboard shows red/amber/green status per entity, overdue count, next
        deadlines, with drill-down to instances.
  - [ ] Board calendar & actions dashboard shows upcoming meetings, pending minutes/resolutions,
        and the viewing user's own action items.
  - [ ] Cap table & ownership dashboard shows ownership %, voting power, share-class breakdown.
  - [ ] Contracts dashboard shows expiry/renewal pipeline, obligations due, spend by counterparty.
  - [ ] Every tile on every dashboard respects the viewing user's record rules and company scope
        (no data leakage across companies or restricted committees).
- **Success metric:** 5-second-test pass rate across all 5 audited roles goes from 0/5 to 5/5 on
  Home/Overview specifically (Issue 8's own success metric); all 5 dashboards load in line with
  spec §9's performance NFR (lazy-loaded, no blocking JS).
- **Sub-issues:**
  - [ ] Needs-functional-review (tech lead, Open Item #3): OWL vs. graph/pivot per dashboard —
        confirm before building
  - [ ] Design review: per-role Home/Overview widget variants (content + wording), carried over
        from Issue 8's own design-review sub-issue — do this once, not twice
  - [ ] OWL/component change: Home/Overview dashboard, role-aware, mobile-responsive (absorbs all
        of Issue 8's sub-issues)
  - [ ] OWL/component or graph-pivot change: Compliance RAG dashboard with drill-down
  - [ ] OWL/component or graph-pivot change: Board calendar & actions dashboard
  - [ ] Graph/pivot change: Cap table & ownership dashboard
  - [ ] Graph/pivot change: Contracts dashboard
  - [ ] Security change: permission-aware tile visibility per dashboard (groups-based)
  - [ ] Tests: responsive-layout test at 390px for Home/Overview (from Issue 8); permission test
        asserting no cross-company/cross-committee data leaks through any tile
  - [ ] Before/after verification: re-screenshot Home/Overview for all 5 roles, Desktop + Mobile;
        screenshot the other 4 dashboards once built
- **Labels:** `type:ux`, `type:mobile`, `odoo:owl`, `grc:board`, `grc:compliance`, `meta:epic`,
  `meta:foundational`, `priority:P1`, `effort:L`, `ux-audit`, `needs-functional-review`

---

## Epic P4 — Forms, Search & Calendar Polish

**Title:** [UX][epic] Forms lack ribbons/tooltips, lists lack default actionable filters, calendars are unbranded

**INCLUDES Track A Issue 2 as its first deliverable** (see note on Issue 2 above — file and ship
Issue 2 independently; don't redo it here).

- **Problem:** Forms have a solid structural base (statusbar, stat buttons, chatter — rubric B2
  scored 3/5, "needs polish" not "broken") but lack `web_ribbon` on terminal states, consistent
  help tooltips on statutory/legal fields (Issue 2 is the sharpest example), and placeholders.
  Search views lack standardised common filters — the audit independently found this exact gap
  across three roles without it rising to Top-10 severity (SEC-006, BOA-010, DIR-005, AUD-005,
  discussed under root cause C8 in `UX_AUDIT_REPORT.md` but not filed as its own issue). Calendars
  (3 exist: meetings + compliance-deadline types) carry no brand colour-coding by committee/type
  or RAG status.
- **Evidence:** `UX_AUDIT_REPORT.md` root-cause C8 discussion and its 5 supporting finding IDs;
  Issue 2's own evidence (see above).
- **Standard/framework/pattern violated:** Rubric B3 (sensible default filters — no list view
  audited ships one); spec §5.3/§5.4/§5.5.
- **User impact / Governance impact:** Adds a repeated manual filtering step for every frequent
  user (Company Secretary, Board Administrator) on every visit to a list screen; lower severity
  than Track A's access-control findings, but a real, measurable efficiency tax on the suite's
  heaviest users.
- **Recommended solution:** Per spec §5.3/§5.4/§5.5 — `web_ribbon` for terminal states (Closed,
  Terminated, Expired, Archived); help tooltips + placeholders on remaining statutory/legal
  fields beyond Issue 2's scope; standardised search filters (my records, this entity, overdue,
  this quarter) and rich group-by with saved favourites; date-based filters for compliance/
  contract expiry; branded, colour-coded calendars.
- **Odoo implementation approach:** XML view inheritance throughout — no Python/model changes
  expected, consistent with spec §9 NFR preferring XML/config over code.
- **Acceptance criteria:**
  - [ ] Every model with a genuine terminal state (contract Terminated/Expired, meeting Closed,
        resolution Withdrawn, etc.) shows a `web_ribbon`.
  - [ ] Every statutory/legal field across the suite (not just Governance Settings, which Issue 2
        already covers) has a plain-language help tooltip — no internal requirement IDs or spec
        filenames visible to end users anywhere.
  - [ ] Compliance and Contracts list views each ship a default "upcoming/overdue" filter and a
        "my records" filter where a responsible-user field exists.
  - [ ] All 3 calendars are colour-coded by committee/type and (for compliance) RAG status.
- **Success metric:** 0 statutory/legal fields anywhere in the suite show developer jargon in
  help text (extends Issue 2's metric suite-wide); every frequent-use list ships at least one
  default actionable filter, down from 0 today.
- **Sub-issues:**
  - [ ] (Filed and tracked separately) Issue 2 — Governance Settings plain-language disclaimer
  - [ ] XML view change: audit all statutory/legal fields suite-wide for jargon-free help text
  - [ ] XML view change: add `web_ribbon` to terminal states across `govoo_contracts`,
        `govoo_board`, `govoo_compliance`
  - [ ] XML view change: standardise search views (common filters + group-by + saved favourites)
        across `govoo_compliance`, `govoo_contracts`, `govoo_board`
  - [ ] XML view change: date-based overdue/expiry filters for compliance instances and contracts
  - [ ] XML view change: colour-code the 3 calendar views by committee/type/RAG status
  - [ ] Tests: view-rendering tests confirming ribbons/filters render under the right state
        conditions
  - [ ] Before/after verification: re-screenshot one list + one form + one calendar per affected
        module
- **Labels:** `type:ux`, `type:content`, `odoo:view`, `meta:epic`, `priority:P2`, `effort:M`,
  `ux-audit`

---

## Epic P5 — Portal & Reports Branding

**Title:** [UX][epic] Portal and PDF reports carry no Clagov brand, and the portal's core voting
flow has unresolved functional gaps

**BLOCKED BY Track A Issues 6 and 10.** Do not rebrand the vote-cast or meeting-detail portal
pages until the missing vote confirmation/weight disclosure (Issue 6) and the cross-committee
confidentiality leak (Issue 10) are fixed — see the notes on both issues above.

- **Problem:** `govoo_portal` uses stock, unbranded Odoo portal templates; QWeb PDF reports
  (register extracts, minutes, resolutions, share certificates, contract documents, compliance
  letters) use default Odoo report styling with no Clagov identity. These are the only two
  surfaces external parties (directors, shareholders, auditors, regulators) see directly, making
  them brand-critical per the spec's own framing (§7 heading: "external-facing = brand-critical").
- **Evidence:** All portal screenshots in `ux-audit/screenshots/director_portal/` and
  `shareholder_portal/` show stock Odoo portal chrome; no PDF report was captured with branding
  in this audit pass (not in original scope — flag as a coverage gap for the next audit round).
- **Standard/framework/pattern violated:** Spec §7 "external-facing = brand-critical"; rubric C6
  (audit evidence usability for an external reviewer, scored 2/5).
- **User impact / Governance impact:** A director, shareholder, or external auditor's entire
  impression of the product comes from these two surfaces; shipping brand everywhere else while
  leaving these stock would be backwards from a commercial-credibility standpoint.
- **Recommended solution:** Per spec §7.1/§7.2 — branded portal header/colours/logo/fonts; clean
  card-based layouts for "my meetings / my documents / my holdings / evaluations / contracts to
  sign"; mobile-first (directors use phones — reinforces Track A's existing mobile findings); a
  shared branded QWeb report layout (navy/gold header band, logo, footer with entity + page
  number) applied consistently across all statutory PDF outputs.
- **Odoo implementation approach:** XML/QWeb template inheritance for both portal pages and
  report layouts — no Python/model changes expected. Depends on `govoo_theme`'s asset bundle
  (Epic P1) being registered into `web.assets_frontend` as well as `web.assets_backend`.
- **Acceptance criteria:**
  - [ ] Issues 6 and 10 are resolved and verified before any portal page in their scope (vote-
        cast, meeting detail) is visually redesigned.
  - [ ] Portal header, colours, logo, and fonts match the Clagov brand on every `/my/*` page.
  - [ ] Director and Shareholder portal home pages use card-based layouts for their respective
        top tasks.
  - [ ] All statutory QWeb PDF reports (register extracts, minutes, resolutions, share
        certificates, contract documents, compliance letters) share one branded layout.
  - [ ] Portal is verified mobile-first on the same 390x844 viewport this audit already used.
- **Success metric:** 0 stock-Odoo-styled pages remain under `/my/*`; 100% of statutory PDF report
  types use the shared branded layout.
- **Sub-issues:**
  - [ ] (Dependency, filed and tracked separately) Issue 6 — vote weight/context/confirmation
  - [ ] (Dependency, filed and tracked separately) Issue 10 — committee confidentiality filtering
  - [ ] XML/QWeb template change: branded portal header/footer/colour across `govoo_portal`
  - [ ] XML/QWeb template change: card-based "my meetings/documents/holdings" portal home layouts
  - [ ] XML/QWeb template change: shared branded report layout (navy/gold header, logo, footer)
  - [ ] XML/QWeb template change: apply shared report layout to each of the 6 named statutory
        report types
  - [ ] Translation: FR/RW stubs for any new portal/report strings
  - [ ] Tests: portal page renders correctly after Issues 6/10 land + branding applied; PDF report
        generation smoke test for each of the 6 report types
  - [ ] Before/after verification: re-run this audit's exact portal screenshot set
        (Desktop + Mobile) and compare against the branded result; capture one sample of each PDF
        report type (coverage gap this pass — add to the next audit round)
- **Labels:** `type:ux`, `type:reporting`, `type:mobile`, `odoo:portal`, `odoo:report`,
  `meta:epic`, `priority:P2`, `effort:L`, `ux-audit`

---

## Epic P6 — Cross-Cutting QA

**Title:** [UX][epic] No systematic verification pass exists for dark mode, mobile, accessibility, or i18n across the brand uplift

- **Problem:** Epics P1–P5 each touch many views across many modules; without a dedicated
  cross-cutting QA pass, regressions in dark mode, mobile layout, accessibility, or translation
  completeness in any one epic's output would not be caught until a user finds them — exactly
  the failure mode this audit itself was commissioned to catch.
- **Evidence:** Spec §9 NFRs (dark mode, responsive, accessibility, i18n) and §10 phase table
  (P6 QA is the spec's own explicit closing phase); this audit's own scope-limitation note that
  only en_US/Desktop+Mobile were tested, leaving Laptop viewport and fr/rw/ar untested.
- **Standard/framework/pattern violated:** WCAG 2.2 AA (rubric A7); spec §9 NFR list in full.
- **User impact / Governance impact:** Without this gate, Epics P1–P5 could ship with new
  regressions the earlier, narrower audit never had the chance to catch (e.g. a new OWL dashboard
  component that fails WCAG contrast in dark mode, or a new kanban card whose date chip text is
  unreadable against the gold accent).
- **Recommended solution:** Run a QA pass structurally identical to this audit's own methodology
  (role × viewport × rubric) specifically against Epics P1–P5's output, plus the items this first
  pass explicitly could not cover: Laptop viewport (1280x720), dark mode across every redesigned
  view, and FR/RW translation completeness once those locales are actually activated (a
  prerequisite this epic should flag, not assume).
- **Odoo implementation approach:** Not a code change itself — a verification/testing epic. Any
  defects it finds become new, individually-scoped follow-up issues using this same template.
- **Acceptance criteria:**
  - [ ] Every view touched by Epics P1–P5 is verified in both light and native Odoo 19 dark mode.
  - [ ] Every view touched by Epics P1–P5 is verified at Desktop (1440x900), Laptop (1280x720),
        and Mobile (390x844).
  - [ ] FR and RW translations are activated in a test environment and spot-checked for
        completeness across all new/changed strings (requires Epic P1's i18n stubs to exist
        first).
  - [ ] A WCAG 2.2 AA contrast check is run against the navy (#1F3864) and gold (#C6A15B) brand
        tokens specifically, in both light and dark mode, per spec §9's own stated requirement.
  - [ ] The full 11-module automated test suite passes with zero regressions after all of Track
        B's changes (spec §9 NFR: "No regression to record rules, multi-company isolation, or
        human-in-the-loop controls — existing tests still pass").
- **Success metric:** 0 outstanding defects found in this pass that weren't already tracked as
  follow-up issues at sign-off; 100% of the automated suite green.
- **Sub-issues:**
  - [ ] Needs-functional-review: decide whether FR/RW are activated for this QA pass or deferred
        to a later localization milestone (today only en_US is active — see
        `MANAGER_SPEC_ANALYSIS.md` §5)
  - [ ] Accessibility: WCAG 2.2 AA contrast audit of brand tokens in light + dark mode
  - [ ] Mobile: full responsive sweep of every view touched by Epics P1–P5 at Mobile + Laptop
  - [ ] Dark mode: full sweep of every view touched by Epics P1–P5
  - [ ] i18n: FR/RW translation completeness spot-check (post-activation)
  - [ ] Tests: run and confirm the full 11-module cross-regression suite
  - [ ] Before/after verification: produce a final coverage.md matching this audit's format, now
        including Laptop viewport and (if activated) FR/RW
- **Labels:** `type:accessibility`, `type:mobile`, `type:i18n`, `type:rtl`, `meta:epic`,
  `priority:P2`, `effort:M`, `ux-audit`, `needs-functional-review`

---

## Open questions carried forward (not resolved by this plan — see `MANAGER_SPEC_ANALYSIS.md` §5)

1. OCA module 19.0 verification (web_notify, web_tree_dynamic_colored_field, web_field_tooltip,
   web_chatter_position) — first sub-issue of Epic P1, owner: whoever picks up P1.
2. Dashboard architecture, OWL vs. graph/pivot — Epic P3's first sub-issue, owner: Tech lead.
3. Final brand assets (logo/wordmark/favicon/login art) — Epic P1 sub-issue, owner: Design/brand.
4. Heading font licensing — Epic P1 sub-issue, owner: Design/Legal.
5. Paid theme for internal demos while `govoo_theme` is built — owner: PM, not filed as an
   engineering issue at all.
6. Should `govoo_ai` and `govoo_procurement` (absent from the manager's spec's module list) be
   included in the brand/theme rollout? — owner: user/manager, needs an explicit answer before
   Epic P2's kanban work or Epic P1's SCSS rollout decides a scope boundary by omission.
