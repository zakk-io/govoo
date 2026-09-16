# clagov Manager Demo Script

## Why this demo exists

Most companies run governance across different disconnected tools: 
for statutory registers they use Word or Excel,
for board packs they emailed them as PDFs, 
meeting votes collected by phone or email,
a cap table in spreadsheet someone
and compliance deadlines tracked in someone's calendar. 
using these tools data Will get lost or get accessed by someone who shouldn't see them.

**clagov replaces all these tools with one system**


## Setup

**Company used in demo:** Kivu Capital Holdings Plc
**URL:** http://localhost:8069
**Shared demo password (all accounts below):** `Demo12345!`

| Login | Name | Role |
|---|---|---|
| `e.mugisha@kivucapital.rw` | Eric Mugisha | Board Administrator (backend) |
| `a.mukamana@kivucapital.rw` | Aline Mukamana | Company Secretary (backend) |
| `r.nkurunziza@kivucapital.rw` | Robert Nkurunziza | Director (portal) |
| `p.uwase@rwandaudit.rw` | Providence Uwase | Auditor, read-only (backend) |
| `ir@kigaligrowthpartners.rw` | Kigali Growth Partners Ltd | Shareholder (portal) |

Log in as each user fresh via "Use another user" on the login screen, rather than trying to switch roles mid-session.



## Scene 1 — The single pane of glass ★

**User and role:** Eric Mugisha, Board Administrator
**Action:** Log in and land on the Dashboard.
**Navigate:** clagov → Dashboard (default landing page)
**Why is the action:** This is the first thing any manager sees — it has to answer "what needs my attention today" in one glance: upcoming meetings, resolutions still open for a vote, and compliance filings by red/amber/green status. It sets the frame for everything else in the demo: nothing that matters is buried in a spreadsheet or someone's inbox.


---


## Scene 3 — Committees don't compose themselves by accident

**User and role:** Aline Mukamana, Company Secretary
**Action:** Open the Audit Committee, show its member list, and point out that the Secretary's own appointment does not appear as a voting committee member even though she's active in the system.
**Navigate:** clagov → Committees → Audit Committee
**Why is the action:** Committee composition rules (e.g. "the Company Secretary attends but is not a member," "only active appointments count") are usually informal knowledge someone has to police manually. Here they're structural: the membership list is computed from a rule, not typed in by hand — so it can't quietly drift out of compliance with the committee's own charter.


---

## Scene 4 — The statutory backbone ★

**User and role:** Aline Mukamana, Company Secretary
**Action:** Open the Register of Directors, then the Register of Members, and point out entries are locked once created (no silent edits to legal history).
**Navigate:** clagov → Statutory Registers → Register of Directors / Register of Members
**Why is the action:** Every company must maintain these registers by law. Managers need to see that clagov treats them as an immutable audit trail, not an editable Excel sheet — this is the difference between "a system of record" and "a filing cabinet."



---

## Scene 5 — Cap table without spreadsheet errors ★

**User and role:** Aline Mukamana, Company Secretary
**Action:** Open Shares & Cap Table, show current holdings by shareholder, then open one Share Allotment record to show how a holding was created.
**Navigate:** clagov → Shares & Cap Table
**Why is the action:** Cap tables are usually the first thing to drift out of sync with reality in a spreadsheet world. Here, holdings are automatically recomputed from allotments and transfers — nobody can update a total without the underlying transaction existing. This directly answers a manager's "can I trust this number" question.


---

## Scene 6 — Building a board pack with confidentiality built in ★

**User and role:** Aline Mukamana, Company Secretary
**Action:** Open "Board Meeting - Q4 2026" (still in Scheduled status, pack not yet compiled), show the agenda including a confidential item restricted to specific directors, then click Compile Board Pack live.
**Navigate:** clagov → Board & Meetings → Board Meeting - Q4 2026
**Why is the action:** This is the core workflow the whole product exists for. Showing that a confidential agenda item is genuinely excluded from an unauthorized director's copy — not just hidden behind a checkbox — is the single strongest trust-building moment in the demo. It's a real security guarantee enforced when the PDF is generated, not a UI convenience that a determined person could bypass.

---

## Scene 7 — Distributing the pack ★

**User and role:** Aline Mukamana, Company Secretary
**Action:** Click Distribute on the compiled pack.
**Navigate:** clagov → Board & Meetings → (pack) Distribute
**Why is the action:** This closes the loop on "did the board actually get their papers" — a real, timestamped accountability record of who received it, when. It's the moment a pack stops being a draft and becomes something the board is officially working from.

---

## Scene 8 — Tracking compliance ★

**User and role:** Aline Mukamana, Company Secretary
**Action:** Navigate to Compliance and show the RAG-colored obligation list (e.g. RSSB Contribution, CIT Quarterly Instalment, CMA Governance Self-Assessment).
**Navigate:** clagov → Compliance
**Why is the action:** This pivots straight into the other half of a Secretary's job — regulatory filings — using the same red/amber/green pattern just seen on the dashboard and the pack distribution status. Consistency across features signals a well-designed product, not a bolted-together one.

---





## Scene 12 — Transparency for external stakeholders ★

**User and role:** Kigali Growth Partners Ltd, Shareholder (portal)
**Goal:** Show that shareholders get appropriate visibility without needing backend access.
**Action:** Log in and show the shareholder's own portal view (their holdings, relevant company filings).
**Navigate:** /my
**Why is the action:** Investors and institutional shareholders increasingly expect self-service visibility instead of asking the Secretary for updates. This scene shows clagov scales trust outward to people outside the company, not just inward to the board.

> **Feature spotlight:** a shareholder portal login sees only their own holdings and what's been explicitly shared with them — never the full cap table, never other shareholders' data.
> **Pain point solved:** the recurring "can you send me my shareholding certificate / latest position" email to the Secretary.


