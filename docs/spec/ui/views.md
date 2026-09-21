# UI — Views

Derived from the model set across all `modules/*.md` files. Every user-facing model gets the views
listed below; `[ENGINEERING DETAIL]` marks where the source does not itemize a specific view and one
is added for usability, kept minimal per source §26 ("do not over-engineer").

## Legend
L=List, F=Form, K=Kanban, C=Calendar, S=Search/filters, SB=Smart buttons, ST=Statusbar.

| Model | Views | Notes |
| --- | --- | --- |
| `res.partner` (Governance tab) | F (notebook page added to standard partner form) | PII fields group-restricted |
| `res.company` (Governance section) | F (section added to standard company form) | |
| `govoo.appointment` | L, F, S (filter: active/resigned, by company, by role) | SB on `res.partner`: "Appointments" |
| `govoo.committee` | L, F, S (filter: by company, board vs sub-committee) | SB: "Members", "Meetings" |
| `govoo.register.director` | L, F (read-mostly), report action for printable extract | |
| `govoo.register.member` | L, F (read-mostly), report action | SB from `govoo.share.class`: "Holders" |
| `govoo.register.beneficial.owner` | L, F, S (filter: provisional vs confirmed) | Highest-sensitivity — no Kanban (avoid casual browsing UX for this data) |
| `govoo.register.charge` | L, F, S (filter: satisfied/unsatisfied) | |
| `govoo.register.entry` | L (read-only, no F edit affordances beyond view) | Auditor-facing; filter by `register_model`, date range |
| `govoo.share.class` | L, F | SB: "Allotments", "Transfers", "Holders" |
| `govoo.share.allotment` | L, F, S (filter: by class, by partner) | |
| `govoo.share.transfer` | L, F (ST: draft/approved/registered), S | |
| `govoo.share.holding` | L (read-mostly, the "Cap Table" view), pivot/graph `[RECOMMENDED]` for ownership % visualization | |
| `govoo.meeting` | L, F (ST: draft/scheduled/held/minuted/closed), C (calendar view via `calendar_event_id`), K (by state) | SB: "Agenda", "Pack", "Minutes", "Resolutions" |
| `govoo.agenda.item` | Inline list on `govoo.meeting` form (one2many, editable list); no separate top-level menu needed | |
| `govoo.board.pack` | F (mostly generated/compiled, not manually authored) | Action button: "Compile & Distribute" |
| `govoo.minutes` | F (ST: draft/for_approval/approved/signed) | Action buttons per state transition |
| `govoo.resolution` | L, F (ST: draft/open/passed/failed/withdrawn), K (by state) | SB: "Votes" |
| `govoo.vote` | Inline list on `govoo.resolution` form; portal: a simple "cast your vote" widget, not a full list view | |
| `govoo.compliance.obligation` | L, F, S (filter: active/inactive, by basis) | Admin/Secretary only |
| `govoo.compliance.instance` | L, F (ST: upcoming/in_progress/filed/late/waived), C, K (RAG-colored by state) | Dashboard-worthy — see `ui/dashboards.md` |
| `govoo.evaluation.campaign` | L, F (ST: draft/open/closed) | |
| `govoo.evaluation.result` | L (aggregate only), graph/pivot `[RECOMMENDED]` | No raw `survey.user_input` browsing here |
| `govoo.contract` | L, F (ST: draft/in_approval/approved/executed/active/expired/terminated), K (by state), C (expiry/renewal calendar) | SB: "Obligations", "Milestones", "Documents" |
| `govoo.contract.type` | L, F | Admin/Contract Manager only |
| `govoo.contract.template` | L, F | Action button: "Generate Contract" |
| `govoo.contract.clause` | L, F, S (filter: mandatory/optional) | |
| `govoo.contract.obligation` | Inline list on `govoo.contract` form (one2many, editable list); also a top-level dashboard view (`ui/dashboards.md`) | |
| `govoo.contract.milestone` | Inline list on `govoo.contract` form | |

## Form-view conventions (apply to every custom model)
- Statusbar (`ST`) widget for every model with a `state` field, following the exact transitions in
  `data-model/state-machines.md` — no extra buttons for transitions not defined there.
- `mail.thread`/`mail.activity` chatter widget on every form (since every transactional model
  inherits these mixins).
- Monetary fields always paired with their `currency_id` widget, respecting RWF's 0-decimal
  convention where applicable (`architecture/technology-standards.md` §6).
- Fields restricted by group (`security/access-control.md` §4) are omitted from the view entirely
  for unauthorized groups via `groups=` attributes — not merely disabled/greyed out.

## Reports (QWeb, list only where not already covered in a `modules/*.md` file)
| Report | Source model | Notes |
| --- | --- | --- |
| Register of Directors extract | `govoo.register.director` | Printable, dated as-of |
| Register of Members extract | `govoo.register.member` | Printable, dated as-of |
| Beneficial Ownership extract | `govoo.register.beneficial.owner` | Printable, marked provisional where applicable |
| Register of Charges extract | `govoo.register.charge` | Printable, shows satisfied history |
| Cap table snapshot | `govoo.share.holding` | As-of date parameter |
| Board pack | `govoo.board.pack` | Merged, per-recipient redacted |
| Minutes document | `govoo.minutes` | |
| Resolution / voting summary | `govoo.resolution`, `govoo.vote` | |
| Filing pack | `govoo.compliance.instance` | Bundle for manual submission |
| Generated contract document | `govoo.contract.template` → `govoo.contract` | Merged from template + partner/company fields |
| Contract register extract | `govoo.contract` | Printable, dated as-of |
