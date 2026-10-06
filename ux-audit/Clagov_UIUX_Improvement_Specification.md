# **Clagov \- UI/UX Improvement Specification**

**A branded, modern interface for the Clagov governance suite on Odoo 19 Community**

> * **Product:** Clagov \- "Govern with clarity."  
> * **Applies to:** the govoo\_\* module suite (govoo\_base, govoo\_board, govoo\_secretarial, govoo\_shares, govoo\_compliance, govoo\_contracts, govoo\_evaluation, govoo\_rw, govoo\_portal)  
> * **Platform:** Odoo 19.0 Community  
> * **Audience:** Development team (building with Claude Code)  
> * **Status:** v1.0, August 2026

## **0\. Executive Summary (read this first)**

The Clagov suite is functionally strong but visually generic. The backend works, follows Odoo conventions, and passes its tests but it currently ships no branding, no custom theme, no dashboards, and bare, text-only kanban cards, so it looks like a raw developer build rather than a finished commercial product.  
This document defines a massive, structured UI/UX uplift with one goal: make Clagov feel like a polished, branded governance product that a board director, company secretary or bank executive is comfortable using daily while staying 100% on Odoo 19 Community (no Enterprise licence).  
The work is organised as:

> 1. A new govoo\_theme module that applies the Clagov brand (navy \+ gold), a custom login, icons and a design system across the whole backend.  
> 2. A view-by-view redesign of the suite's lists, forms, kanbans, search and calendars.  
> 3. A set of governance dashboards (home overview, compliance RAG, board calendar, cap-table charts).  
> 4. Branded portal pages and branded PDF reports.  
> 5. A short, vetted set of OCA add-ons to fill Community gaps.

Important context: Odoo 19 already did half the job. Odoo 19 ships a modern base we build *on top of*, not around: a collapsible sidebar app navigation, native dark mode (every view type styled for light/dark), a mobile-first responsive layout engine, and a redesigned, \~40% faster web client. So we do not rebuild navigation or dark mode we invest effort where Clagov is actually weak: branding, view richness, and dashboards.  
*Sources: OCA/web 19.0 web\_responsive web\_responsive on Odoo Apps (19.0) Odoo 19 new features guide. Muk Backend Theme 19.0.*

## **1\. Current-State Assessment (what we found in the code)**

| Area | Current state | Verdict |
| :---- | :---- | :---- |
| **Custom frontend assets** | None no static/src, no SCSS, no JS, no OWL components in any module | X No branding, no visual identity |
| **Theme / colours** | Stock Odoo 19 default (purple accent) | X Not Clagov-branded |
| **Form views** | Correct structure: statusbar, stat buttons, groups, notebook, chatter, contextual alerts | ☑ Solid base, needs polish |
| **List views** | Plain; only a state badge with decorations | X Functional but flat |
| **Kanban views** | Text-only cards \- stacked fields, no colour bar, no avatar, no progress, no menu, no layout | X Weakest area |
| **Dashboards** | None (2 graph \+ 2 pivot views exist but no landing dashboard) | X No at-a-glance overview |
| **Navigation** | Single govoo root menu with flat per-module submenus | X Works, but no IA design |
| **Portal (govoo\_portal)** | Present but unbranded stock templates | A Needs brand pass |
| **PDF reports** | QWeb reports exist, default styling | X Not branded |
| **View-type coverage** | 33 list, 30 form, 17 search, 7 kanban, 3 calendar, 2 pivot, 2 graph | A Lists/forms good; kanban/analytics thin |

Bottom line: the problem is presentation, not architecture. We keep every model, view action and security rule; we re-skin and enrich the presentation layer only.

## **2\. Design Goals & Principles**

> * **Branded, not generic:** Clagov navy \+ gold everywhere: login, nav, buttons, badges, reports.  
> * **Glanceable:** a user sees status (compliance RAG, meeting state, contract expiry) through colour and shape before reading text.  
> * **Consistent:** one design system; every kanban, list and form follows the same patterns.  
> * **Community-only:** no Enterprise dependency; use Odoo 19 natives \+ OCA \+ custom SCSS/OWL.  
> * **Non-destructive:** presentation changes only; never weaken record rules, multi-company isolation or the human-in-the-loop controls.  
> * **Performant & responsive:** build on Odoo 19's mobile-first engine; no heavy custom JS that slows the client.  
> * **Localised:** all new UI strings translatable (EN/FR/Kinyarwanda), RWF and DD/MM/YYYY respected.

## **3\. Theme Strategy**

### **Recommendation**

There are three ways to improve the look. We recommend a combination of B \+ C.

| Option | What it is | Pros | Cons | Verdict |
| :---- | :---- | :---- | :---- | :---- |
| **A. Buy a backend theme** | Install a paid theme (Muk, Clarity Pro, Community Backend Theme, Enterprise-style) | Fast, lots of toggles | Generic look shared with other Odoo sites; not your brand; licence per site; upgrade risk | Not for a product |
| **B. Custom govoo\_theme module** | Our own theme: SCSS brand variables, login, icons, fonts, component styles | True Clagov identity; owned; ships with the product; no per-site licence | Build effort | Recommended (core) |
| **C. OCA web \* add-ons** | Free community modules for backend UX niceties | Free (LGPL), maintained by OCA | Some overlap with Odoo 19 natives | Recommended (complement) |

Decision: build govoo\_theme as the product's own brand layer, and add a small, vetted set of OCA modules for UX gaps. Treat any paid theme only as a temporary shortcut for an internal demo, never as the shipped identity.

### **3.1 Recommended OCA/community add-ons**

| Module | Purpose | 19.0 status | Licence |
| :---- | :---- | :---- | :---- |
| web\_responsive (OCA/web) | Searchable app menu, sticky list header & form statusbar, keyboard shortcuts | Confirmed 19.0.1.0.1 (Dec 2025, stable) | LGPL-3 |
| web\_notify (OCA/web) | In-app toast notifications (great for compliance/contract alerts) | Confirm on OCA/web 19.0 | LGPL-3 |
| web\_tree\_dynamic\_colored\_field (OCA/web) | Colour list rows by state/risk | Confirm on OCA/web 19.0 | LGPL-3 |
| web\_field\_tooltip (OCA/web) | Rich help tooltips on fields | Confirm on OCA/web 19.0 | LGPL-3 |
| web\_chatter\_position (OCA/web) | Move chatter to the side for wide forms | Confirm on OCA/web 19.0 | LGPL-3 |

Do NOT add web\_dark\_mode \- Odoo 19 has native dark mode. Before pinning any OCA module, verify it exists on the OCA/web 19.0 branch and pin the exact version; where a module is not yet ported, achieve the effect in govoo\_theme instead. \[CONFIRM 19.0 availability per module\].

## **4\. Clagov Design System**

### **4.1 Colour tokens (SCSS variables)**

| Token | Value | Use |
| :---- | :---- | :---- |
| \$clagov-navy | \#1F3864 | Primary brand, nav accents, headers |
| \$clagov-navy-deep | \#001526 | Login background, dark surfaces |
| \$clagov-gold | \#C6A15B | Secondary accent, highlights, CTAs |
| \$clagov-cream | \#F5F1E8 | Light surface/wordmark on dark |
| \$o-brand-primary (override) | \$clagov-navy | Replaces Odoo default purple |
| State: success/info/warning/danger | green/navy/gold/red | Status badges & decorations |

Map these onto Odoo's own SCSS variables (\$o-brand-primary, \$o-brand-secondary, button and badge colours) so the entire backend not just Clagov screens adopts the brand.

### **4.2 Typography & spacing**

> * Headings: a clean serif or strong sans matching the logo wordmark; body: system sans for legibility.  
> * Consistent spacing scale; generous white space on forms; max content width on wide screens.

### **4.3 Iconography**

> * One coherent icon set for the menu and stat buttons (Font Awesome, already in Odoo).  
> * Assign a distinct, consistent icon per module and per key action (meetings, registers, shares, compliance, contracts).

### **4.4 Component patterns (used everywhere)**

> * Status: statusbar on forms, badge with decorations on lists/kanban.  
> * Smart buttons: statinfo stat buttons with brand icons.  
> * Ribbons: web\_ribbon for terminal states (Closed, Terminated, Expired, Archived).  
> * Empty states: branded o\_view\_nocontent with a helpful call to action for every action.

## **5\. View-by-View Improvements**

### **5.1 Kanban redesign (highest priority)**

Current cards are plain text. Rebuild every kanban \<t t-name="card"\> to a rich card:

> * A coloured left/top bar by state or risk (navy/gold/green/red).  
> * Title \+ subtitle hierarchy (e.g., meeting name over committee; contract over counterparty).  
> * Status badge, due-date chip (red when overdue), and where relevant a progress bar (e.g., resolution vote tally, contract obligations completed).  
> * A dropdown menu (:) for quick actions and a responsible avatar where a user is assigned.  
> * Apply to: meetings, resolutions, votes, compliance instances, contracts, contract obligations, (add) committees, appointments, share classes.

### **5.2 List views**

> * Add row colouring by state/risk (via decoration-\* and/or web\_tree\_dynamic\_colored\_field).  
> * Add optional columns (optional="hide") so power users can expand detail without clutter.  
> * Use the right widgets: monetary (RWF), progressbar, badge, handle for sequence, boolean\_toggle.  
> * Sensible default group-by per model (e.g., compliance by status, contracts by type).

### **5.3 Form views**

> * Keep the solid structure; add web\_ribbon for terminal states, help tooltips on statutory/legal fields, placeholders on inputs, and consistent chatter (side position on wide forms).  
> * Ensure every stat button has a brand icon and every contextual alert (already used on meetings) is reused across modules (e.g., "No minutes drafted yet").

### **5.4 Search & filters**

> * Standardise search views: common filters (my records, this entity, overdue, this quarter), rich group-by, and saved favourites.  
> * Add date-based filters for compliance and contract expiry.

### **5.5 Calendar**

> * Brand the meeting and compliance-deadline calendars; colour events by committee/type and by RAG status.

## **6\. Governance Dashboards (new)**

Community has no Enterprise Spreadsheet dashboards, so build dashboards as OWL client actions (or graph/pivot landing views) inside govoo\_theme / each module.

| Dashboard | Content |
| :---- | :---- |
| **Clagov Home / Overview** | KPI tiles (upcoming meetings, open resolutions, overdue filings, expiring contracts), quick links, recent activity the branded landing screen when you open the app. |
| **Compliance RAG** | Red/amber/green status of obligations per entity; overdue count; next deadlines; drill-down to instances. |
| **Board calendar & actions** | Upcoming meetings, pending minutes/resolutions, my action items. |
| **Cap table & ownership** | Ownership %, voting power, share-class breakdown (graph/pivot of govoo\_shares). |
| **Contracts** | Expiry/renewal pipeline, obligations due, spend by counterparty. |

Each tile is permission-aware (respects record rules and company scope) and localised.

## **7\. Portal & PDF Reports (external-facing \= brand-critical)**

### **7.1 Portal (govoo\_portal)**

> * Apply Clagov branding to portal templates (header, colours, logo, fonts).  
> * Clean card-based layouts for directors/shareholders: my meetings, my documents, my holdings, evaluations, contracts to sign.  
> * Mobile-first (directors use phones); accessible; EN/FR/RW.

### **7.2 QWeb PDF reports**

> * A shared branded report layout (navy/gold header band, Clagov logo, footer with entity \+ page number) applied to all statutory outputs: register extracts, minutes, resolutions, share certificates, contract documents, compliance letters.  
> * Consistent typography and table styling matching the design system.

## **8\. New Module govoo\_theme**

Purpose: carry the entire brand and design system; depend on it from the suite so the look ships with the product.

> * govoo\_theme/  
  * \_\_manifest\_\_.py *(\# depends: web, govoo\_base; (optional) web\_responsive)*  
  * static/src/scss/  
    * variables.scss *(\# brand tokens; overrides \$o-brand-primary etc.)*  
    * backend.scss *(\# nav, buttons, badges, list/kanban/form skin)*  
    * kanban.scss *(\# rich card styles)*  
    * login.scss *(\# branded login/sign-in page)*  
  * static/src/js/  
    * dashboards/... *(\# OWL dashboard components \+ any small widgets)*  
  * static/src/img/ *(\# logo, wordmark, favicon, login art)*  
  * static/description/ *(\# app store icon \+ screenshots)*  
  * views/  
    * assets.xml *(\# register SCSS/JS into web.assets\_backend)*  
    * login\_templates.xml *(\# branded login)*  
    * dashboard\_actions.xml *(\# menu re-org, web\_icon, report layout)*  
  * data/

Register assets into the web.assets\_backend (and web.assets\_frontend for portal) bundles. Keep it additive and override-based so Odoo 19 upgrades don't break it.

## **9\. Non-Functional Requirements**

> * **No Enterprise dependency** \- Community \+ OCA \+ custom only.  
> * **Upgrade-safe** \- prefer SCSS variable overrides and XML view inheritance (xpath) over replacing core templates.  
> * **Performance** \- lazy-load dashboard components; no blocking JS; keep asset bundle lean.  
> * **Accessibility** \- sufficient colour contrast (navy/gold must pass WCAG AA for text), keyboard navigation, ARIA on custom OWL components.  
> * **Responsive** \- verify every redesigned view on mobile (Odoo 19 is mobile-first; don't regress it).  
> * **Dark mode** \- ensure brand tokens have dark-mode values so Clagov looks right in Odoo 19's native dark theme.  
> * **i18n** \- all new strings translatable; ship FR/RW stubs.  
> * **Security** \- presentation only; never alter record rules, groups, or multi-company rules.

## **10\. Implementation Plan (phased)**

| Phase | Scope | Outcome |
| :---- | :---- | :---- |
| **P1 Brand foundation** | govoo\_theme: SCSS tokens, backend skin, branded login, app icon, menu re-org, OCA web\_responsive | Whole backend instantly looks like Clagov |
| **P2 Kanban & list overhaul** | Rich kanban cards \+ list decorations/widgets/optional columns across all modules | Glanceable status everywhere |
| **P3 Dashboards** | Home overview \+ Compliance RAG \+ Board \+ Cap-table \+ Contracts dashboards (OWL) | At-a-glance governance cockpit |
| **P4 Forms, search, calendar polish** | Ribbons, tooltips, standardized search/filters, branded calendars, empty states | Consistent, guided forms |
| **P5 Portal & reports** | Branded portal templates \+ shared QWeb report layout | Brand-consistent external touchpoints |
| **P6 QA** | Cross-view consistency, dark mode, mobile, accessibility, EN/FR/RW, performance | Production-ready polish |

Build order rationale: P1 delivers the biggest perceived change for the least effort (one theme module re-skins everything); P2-P3 deliver the day-to-day usability gains; P5 protects the brand where clients and directors actually see it.

## **11\. Definition of Done**

> * govoo\_theme installed → entire backend uses Clagov navy/gold, branded login, app icon, and brand-consistent buttons/badges in both light and dark mode.  
> * Every kanban uses a rich card (colour bar, title/subtitle, badge, date chip, menu); no text-only cards remain.  
> * Every list has appropriate decorations/widgets and a sensible default group-by; key lists support optional columns.  
> * The five dashboards exist, are permission-aware, localised, and load quickly.  
> * Portal and all QWeb reports carry the Clagov brand layout.  
> * No Enterprise dependency; all OCA modules pinned to verified 19.0 versions.  
> * No regression to record rules, multi-company isolation, or human-in-the-loop controls (existing tests still pass).  
> * Verified on desktop \+ mobile, light \+ dark, in EN/FR/RW.

## **12\. Open Items to Confirm**

| \# | Item | Owner |
| :---- | :---- | :---- |
| **1** | Final brand assets: logo SVG, wordmark, favicon, login artwork, exact hex values | Design / brand |
| **2** | Confirm 19.0 availability \+ pin versions for each OCA web\_\* module (only web\_responsive verified) | Tech lead |
| **3** | Dashboards as OWL client actions vs graph/pivot landing views (effort vs richness) | Tech lead |
| **4** | Whether to also offer a paid theme for internal demos while govoo\_theme is built | PM |
| **5** | Heading font licence (if a non-system font is used) | Design / legal |

*End of UI/UX Improvement Specification v1.0.* *This is a presentation-layer uplift: it changes how Clagov looks and feels, not how it governs.* *All data models, security rules and workflows defined in the main Clagov specification remain unchanged.* *OCA module availability on the 19.0 branch must be verified and versions pinned before build.*
