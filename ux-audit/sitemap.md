# Govoo Sitemap (as discovered per role)

Built strictly from each role's `menus_seen` list in the raw capture data. Backend roles (Company Secretary, Board Administrator, Auditor) see the same Odoo backend menu structure, but with real differences in what each submenu actually renders or permits — noted inline. Portal roles (Director, Shareholder) see an entirely separate, narrow portal menu.

## Backend menu tree — Company Secretary (fullest observed tree)

```
Dashboard
Statutory Registers
├── Register of Directors
├── Register of Members
├── Register of Beneficial Owners
├── Register of Charges
└── Audit Ledger
Shares & Cap Table
├── Share Classes
├── Allotments
├── Transfers
└── Cap Table
Board & Meetings
├── Appointments
│   └── All Appointments
├── Committees
│   └── All Committees
├── Meetings
├── Board Packs
├── Minutes
├── Resolutions
└── Votes
Contract Management
├── Contracts
├── Types
├── Delegation of Authority
├── Templates
├── Clauses
└── Obligations
Compliance
├── Obligations
└── Instances
Evaluations
├── Campaigns
└── Results
AI
├── Search
└── Request Log
Configuration
├── Companies
├── Governance Settings
└── AI Configuration
```

## Backend menu tree — Board Administrator

Identical top-level structure to Company Secretary, **except**:
- `Configuration > AI Configuration` is **not present** in this role's `menus_seen` (Company Secretary has it; Board Administrator's list stops at `Configuration > Governance Settings`). This is either a genuine permission gate or an omission in this pass — worth confirming, since AI Configuration arguably belongs with the rest of Configuration for an admin-focused role.
- **Role-gating that does NOT match the app's intended design:** every item under `Board & Meetings` (Meetings, Resolutions, Board Packs, Minutes) is reachable and **fully editable** for this role (see BOA-001), even though the role is meant to be read-only here. The menu structure looks identical to Company Secretary's, but the underlying write permissions behind it are not — the menu alone does not communicate this, which is itself the finding.

```
Dashboard
Statutory Registers  (same 5 submenus as Company Secretary)
Shares & Cap Table  (same 4 submenus)
Board & Meetings  (same 7 submenus — ⚠️ writable when it should be read-only, see BOA-001)
Contract Management  (same 6 submenus)
Compliance  (same 2 submenus)
Evaluations  (same 2 submenus)
AI  (same 2 submenus)
Configuration
├── Companies
└── Governance Settings   (⚠️ AI Configuration not seen in this role's menu list)
```

## Backend menu tree — Auditor (Read-only)

Same top-level items as the other backend roles, but two top-level menus render as **interactive dead ends** — they highlight as active but produce an empty dropdown with zero child items:

```
Dashboard
Statutory Registers  (same 5 submenus — populates correctly)
Shares & Cap Table  (same 4 submenus — populates correctly)
Board & Meetings  (same 7 submenus — populates correctly)
Contract Management  ⚠️ top-level item renders, dropdown is EMPTY (AUD-004)
Compliance  (same 2 submenus — populates correctly)
Evaluations  ⚠️ top-level item renders, dropdown is EMPTY (AUD-004)
AI  — not listed in this role's menus_seen at all (Search/Request Log absent)
Configuration  — not listed in this role's menus_seen at all
```

**Role-gating mismatch vs. expectation:** an auditor plausibly *should* have zero access to Contract Management/Evaluations (fine), but the menu item should then be hidden entirely rather than rendered as a clickable, highlighted, functionless button (AUD-004). The complete absence of a `Configuration` menu for the Auditor (vs. Company Secretary and Board Administrator both seeing it) is a correctly-scoped difference — auditors should not configure the system — but it was not deliberately announced or explained anywhere in the UI (no "you have read-only access" banner), which the Dashboard's AUD-005 finding also calls out.

Additionally, **every workflow/header action button that should be gated off for this role is NOT** (AUD-001) — this is the opposite failure mode from AUD-004: here the UI offers an action it should refuse (write), whereas AUD-004 is the UI refusing silently without saying why access was denied.

## Portal menu tree — Director

```
Home (top nav)
Contact us (top nav)
[Grace Uwimana] user menu
├── My Account
└── Logout
Quick Links (home page body)
├── My Meetings
├── My Votes
└── My Appointment
```

No Configuration, no Statutory Registers, no backend modules — correctly scoped to a narrow self-service set. **Role-gating defect found despite the narrow menu:** within "My Meetings", committee-level filtering is NOT enforced — a director appointed only to the "Board of Directors" committee can open full detail pages for Audit Committee and Risk & Compliance Committee meetings (DIR-001). The menu *looks* correctly scoped; the underlying data access behind "My Meetings" is not.

## Portal menu tree — Shareholder

```
Home (top nav)
Contact us (top nav)
Account/company switcher (top-right)
Quick Links (home page body)
├── My Holdings
├── My Votes
└── My Register
```

Also correctly narrow in structure. "My Register" was visible but out of this pass's task scope (coverage gap, not a defect). No cross-tenant or cross-shareholder data leakage was found in this pass (unlike the Director's committee-leakage issue) — though `/my/register` was not opened, so this is not a complete clearance.

## Summary of role-gating anomalies found

| Observation | Expected | Actual | Finding |
|---|---|---|---|
| Board Administrator's Board & Meetings menus | Read-only | Fully writable incl. workflow buttons | BOA-001 (critical) |
| Auditor's Contract Management / Evaluations top menus | Hidden if no access | Visible, clickable, empty dropdown | AUD-004 |
| Auditor's workflow/header buttons on Meeting/Compliance/Resolution forms | Disabled/invisible | Fully enabled | AUD-001 |
| Director's "My Meetings" committee scope | Only own committee(s) | All committees' meetings visible and openable | DIR-001 (critical) |
| Dashboard "Open Resolutions Requiring My Vote" widget | Role-aware (voters only) | Shown identically to Company Secretary, Board Administrator, and Auditor, none of whom cast votes in that capacity | SEC-010, BOA-007, AUD-005 |
