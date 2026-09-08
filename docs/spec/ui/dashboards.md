# UI — Dashboards

Source: §2 (dashboards row), §7.5.3 (compliance RAG), §7.6.2 (evaluation trends), §3.3 (Spreadsheet
Dashboards / Enterprise). This is the aggregation layer described in `modules/portal.md`.

## 1. Internal personalized dashboard (backend home / "Govoo" app landing page)
| Widget | Data source | Audience |
| --- | --- | --- |
| Upcoming meetings (next 30 days) | `govoo.meeting` | All internal roles (own-company) |
| Open resolutions requiring my vote | `govoo.resolution` + `govoo.vote` (absence of own vote row) | Directors, Board Administrator (visible but cannot act) |
| Compliance RAG summary | `govoo.compliance.instance` grouped by `state`/days-to-due | Secretary, Admin, responsible users |
| Cap-table snapshot | `govoo.share.holding` | Secretary, Admin, Auditor |
| Recent register changes | `govoo.register.entry` (latest N) | Secretary, Admin, Auditor |
| Evaluation trend (aggregate) | `govoo.evaluation.result` | Secretary, Admin |

## 2. Compliance RAG (red/amber/green) — source §7.5.3
- **Green:** `state = 'upcoming'`, more than `lead_time_days` from `due_date`.
- **Amber:** `state = 'upcoming'`/`in_progress`, within `lead_time_days` of `due_date`.
- **Red:** `state = 'late'`.
- **Grey/neutral:** `filed`, `waived` (out of the active RAG set — shown in a separate "completed"
  filter).
Implementation: Kanban view grouped by `state`, with a computed `days_to_due` field driving a color
badge (`[ENGINEERING DETAIL]` — the RAG coloring is a standard Odoo Kanban/decoration pattern, not a
new model).

## 3. Cap-table / ownership visualization
- Pivot/graph view over `govoo.share.holding` (`percentage`, grouped by `share_class_id`, then
  `partner_id`) `[RECOMMENDED]` — a pie/bar breakdown of ownership by class and holder.
- As-of-date snapshot report (see `ui/views.md` reports table).

## 4. Evaluation trend dashboard
- Aggregate `govoo.evaluation.result` scores over successive campaigns for the same
  `committee_id`/`evaluation_type`, shown as a trend line — never drilling into individual
  `survey.user_input` rows for non-authorized viewers (BR-EVAL-001).

## 5. Enterprise vs Community
- **Enterprise:** Spreadsheet Dashboards app — richer, drag-and-drop dashboard composition.
- **Community fallback:** OCA `spreadsheet_dashboard_oca`, or plain Odoo pivot/graph/Kanban views
  as listed above — the dashboard **content** (RAG, cap table, evaluation trend) must be available
  either way; only the presentation richness differs. See `architecture/technology-standards.md`
  §8 and `integrations/documents.md`-style feature-flag pattern.

## 6. Portal-facing dashboard ("My Governance")
- Director Portal: "My upcoming meetings," "My open votes," own appointment particulars.
- Shareholder Portal: "My holdings" (cap-table snapshot for their own `partner_id`), "My open
  votes" (shareholder resolutions they're eligible for).
See `ui/portal-ui.md`.
