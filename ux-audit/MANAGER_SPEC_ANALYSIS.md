# Analysis: Clagov UI/UX Improvement Specification v1.0 vs. the UX Audit

This document reconciles the manager-provided `Clagov_UIUX_Improvement_Specification.md` (a
brand/presentation-layer uplift spec) with the independent UX audit already completed in this
folder (40 findings, `findings.csv` / `UX_AUDIT_REPORT.md` / `ISSUES_PLAN.md`). Its job is to
decide, before any GitHub issue is filed, which items are genuinely new work, which overlap, and
where filing both as separate issues would create conflicting or duplicated instructions for
whoever implements them.

## 1. Fact-checking the spec against the live codebase

The spec is well-researched and its technical claims check out against the actual repo:

| Claim in the spec | Verified | Note |
|---|---|---|
| 7 kanban views exist | Confirmed | `govoo_compliance` (instance), `govoo_board` (meeting, vote, resolution), `govoo_contracts` (contract, contract obligation), `govoo_portal` (one portal-side kanban template). |
| "(add) committees, appointments, share classes" kanbans | Confirmed accurate | These three models currently have **no** kanban view at all — the spec correctly distinguishes "redesign" (6 models) from "add new" (3 models). |
| No custom frontend assets / SCSS / theme | Essentially confirmed | Only exception: `govoo_ai/static/src/ai_chat_widget/*.scss`, a small unrelated widget — immaterial to the "no design system exists" claim. |
| View-type counts (33 list / 30 form / 17 search / 7 kanban / 3 calendar / 2 pivot / 2 graph) | Close but not exact | Live count: 41 list, 37 form, 18 search, 7 kanban, 3 calendar, 2 pivot, 2 graph. Likely drifted since the spec's August 2026 snapshot (the suite has grown — e.g. this session alone added `govoo.governance.config`'s form view). Not materially different; doesn't change any conclusion in the spec. |

No red flags. The spec's "Current-State Assessment" is accurate, and its scope statement —
*"This is a presentation-layer uplift: it changes how Clagov looks and feels, not how it
governs… all data models, security rules and workflows remain unchanged"* — is an explicit,
self-declared boundary, not an oversight.

## 2. The one real tension: presentation-only vs. the audit's non-cosmetic findings

That self-declared boundary is exactly where the two documents need reconciling. Several of the
audit's **critical** findings are not cosmetic — they are access-control and data-integrity
defects:

- **BOA-001** (Board Administrator can actually write to locked meeting/resolution records)
- **BOA-004** (live test fixture in the real, legally authoritative Register of Charges)
- **DIR-001** (director can read other committees' confidential meetings/board packs)
- **AUD-001** (write-capable buttons rendered for a database-enforced read-only role)
- **Issue 6** (binding votes cast with no weight disclosure, no resolution text, no confirmation)

None of these are addressed anywhere in the spec, and none of them can be fixed by "presentation
only" changes — BOA-001 and DIR-001 specifically require **security/access-control** changes,
which the spec's own Non-Functional Requirements section explicitly rules out of its scope
("Security — presentation only; never alter record rules, groups, or multi-company rules").

**Conclusion:** these are not competing priorities to choose between — they are two different
layers of the same product, and both need to ship. But sequencing matters: shipping a beautifully
rebranded login page and rich kanban cards on top of an admin role that can silently corrupt
board minutes, or a portal that lets a director read another committee's confidential meetings,
would make the product *look* more trustworthy while *being* less trustworthy — the worst
possible combination for a governance product. **Recommendation: the audit's 10 governance-
critical fixes (Track A, unchanged from the existing `ISSUES_PLAN.md`) should be scheduled first,
or at minimum start in parallel with the spec's P1 — not after it.**

## 3. Where the two documents describe the *same* work (merge, don't duplicate)

Three of the audit's Top 10 fixes are not separate from the spec's phases — they are the same
surface, described from two different angles (the audit found it as a defect; the spec frames it
as a planned enhancement). Filing both as independent issues would give two different people
contradictory instructions for the same screen. These are merged below, not duplicated:

| Audit finding | Spec section | Resolution |
|---|---|---|
| **Issue 8** — Dashboard is identical for every role and collapses on mobile | §6 Governance Dashboards (Clagov Home/Overview) | **Merged into EPIC P3.** The audit's finding becomes a *hard acceptance criterion* of the new Home/Overview dashboard (must be role-aware from day one; must not show a voting CTA to non-voters; must work at 390px), not a separate issue to file alongside a parallel dashboard rebuild. Issue 8 is marked **superseded by EPIC P3** below. |
| **Issue 2** — Governance Settings' statutory-deadline fields show developer jargon, no plain-language signal | §5.3 Form views ("help tooltips on statutory/legal fields") | **Folded into EPIC P4** as its first concrete, already-scoped deliverable (it's a quick win regardless of the rest of P4's scope). Not filed twice. |
| **Issue 7** (Board Packs list / Audit Ledger / AI Request Log show raw IDs) and **Issue 4** (records show `model,id` instead of a name) | §5.1 Kanban redesign + §5.2 List views | **Explicit dependency, not a merge.** A rich kanban card or enriched list column is worthless if the field it binds to resolves to "govoo.minutes,4" or a bare row number. **EPIC P2 (kanban/list overhaul) is sequenced after Issues 4 and 7**, and P2's acceptance criteria below say so explicitly, so whoever picks up P2 doesn't rebuild a kanban card around a broken title field. |
| **Issue 6** (no vote confirmation, no weight disclosure) and **Issue 10** (cross-committee confidentiality leak) | §7.1 Portal branding | **Explicit prerequisite, not a merge.** EPIC P5 (portal branding) must not ship a prettier version of a page that still has zero vote confirmation or a confidentiality leak. P5's scope note says Issues 6 and 10 are a blocking prerequisite. |
| Root cause: no list ships a default "my open items" filter (SEC-006, BOA-010, DIR-005, AUD-005 — not one of the Top 10, folded into root cause discussion only) | §5.4 Search & filters | **Feeds EPIC P4** as supporting evidence; not a separate issue, since the spec already scopes exactly this work. |

## 4. Genuinely new work the spec introduces (not touched by the audit at all)

The audit never looked at branding, since "the color is purple instead of navy" was explicitly
out of scope for a defect-finding pass. Everything else in the spec is net-new backlog:

- A brand-new `govoo_theme` module (SCSS tokens, backend skin, branded login, dark-mode values)
- OCA module adoption (`web_responsive` confirmed; 4 others marked "confirm on 19.0" by the spec
  itself — see §5 below, this needs real verification, not just trust)
- Rich kanban cards for 6 existing + 3 new models
- 4 of the 5 planned dashboards that aren't the Home/Overview one (Compliance RAG, Board calendar,
  Cap table, Contracts)
- Branded QWeb PDF report layout
- Calendar branding/colour-coding
- Dark-mode token values, i18n stubs (FR/RW)

These become EPICs P1, P2 (minus the dependency above), P3 (minus the Home/Overview merge above),
P5 (minus the portal-prerequisite note), and P6, drafted in `ISSUES_PLAN.md` below, in the same
parent/sub-issue template already used for the audit's Track A issues.

## 5. Claims in the spec that need verification before anyone commits to them

The spec itself flags most of these as open items — this section just converts "open item" into
an actual, assignable task rather than leaving it as a question mark:

1. **OCA module 19.0 availability.** The spec states `web_responsive` is "Confirmed 19.0.1.0.1
   (Dec 2025, stable)" but marks `web_notify`, `web_tree_dynamic_colored_field`,
   `web_field_tooltip`, and `web_chatter_position` as "confirm on OCA/web 19.0" — i.e.
   unverified, by the spec's own admission. I have not independently checked any of these five
   against the live OCA/web GitHub repository. **This must be a real verification task (first
   sub-issue of EPIC P1), not an assumption carried into implementation.**
2. **Dashboard architecture (OWL vs. graph/pivot).** Spec Open Item #3, explicitly unresolved.
   My non-binding read: the Home/Overview and Compliance RAG tiles need cross-model KPI
   aggregation (upcoming meetings + overdue filings + open resolutions in one glance), which a
   single graph/pivot view can't express — those two likely need a lightweight OWL component.
   Cap Table and Contracts are each naturally a single model's data and may be well served by a
   graph/pivot landing action with less engineering effort. **This is a recommendation for the
   tech lead to confirm, not a decision I'm making unilaterally.**
3. **Brand assets** (logo SVG, wordmark, favicon, login artwork) — Spec Open Item #1, owned by
   Design. The exact hex values ARE already given in §4.1 despite the open-items table still
   listing them as pending — I'm treating the hex values as final and only the asset *files* as
   outstanding.
4. **Font licensing** — Spec Open Item #5, owned by Design/Legal. Not something I can resolve.
5. **Paid theme for internal demos** — Spec Open Item #4, a PM/business decision, not a UX or
   engineering question.
6. **`govoo_ai` and `govoo_procurement` are absent from the spec's module list** (it only names
   `govoo_base, govoo_board, govoo_secretarial, govoo_shares, govoo_compliance, govoo_contracts,
   govoo_evaluation, govoo_rw, govoo_portal`). Both modules exist in the live system today and
   were also outside the audit's first-pass scope. **Open question for the user/manager: should
   the brand/theme rollout (govoo_theme's SCSS, kanban/list treatment) extend to these two
   modules, or are they deliberately excluded?** Not assumed either way below.

## 6. Net result

`ISSUES_PLAN.md` is restructured into two tracks:

- **Track A — Governance-Critical Fixes** (Issues 1–10, already drafted, unchanged, P0/P1
  priority): correctness, security, and audit-trail defects found by the audit. Recommended to
  start immediately / in parallel with Track B.
- **Track B — Clagov Brand & UX Uplift** (EPICs P1–P6, newly drafted below, following the
  manager spec's own phase structure): the branding/theme/dashboard/portal program, with the
  three merge points and two prerequisite notes above baked directly into the relevant epics'
  acceptance criteria so no one implements a conflicting version of the same screen twice.

Both tracks use the identical issue template and label taxonomy already established, so the
final GitHub backlog reads as one coherent plan authored by one process — not two documents
stapled together.
