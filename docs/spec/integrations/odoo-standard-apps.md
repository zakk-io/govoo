# Integration: Odoo Standard Apps (overview)

Source: §3.3 of the source spec. Detailed per-integration specs are in the sibling files in this
directory (`documents.md`, `sign.md`, `surveys.md`, `calendar.md`). This file is the index +
common integration-spec template.

## Reused apps and where each is detailed
| App | Edition | Detail file |
| --- | --- | --- |
| Documents | Enterprise (OCA `dms` / `ir.attachment` fallback) | `integrations/documents.md` |
| Sign | Enterprise (OCA `sign_oca` fallback) | `integrations/sign.md` |
| Surveys | Community | `integrations/surveys.md` |
| Calendar | Community | `integrations/calendar.md` |
| eLearning | Community | not separately detailed — reused as-is for onboarding/training, no
  Govoo-specific customization identified in source §3.3 beyond "reuse" |
| Contacts, HR | Community | reused via `res.partner`/`govoo_base` extensions, not a separate
  integration surface |
| Portal, Website | Community | `security/portal-security.md`, `ui/portal-ui.md` |
| Spreadsheet Dashboards | Enterprise (OCA `spreadsheet_dashboard_oca` fallback) | `ui/dashboards.md` §5 |
| Approvals | Enterprise | `integrations/future-integrations.md` (not required for v1 workflows,
  which use custom `state` fields instead — see rationale below) |

## Why Approvals is not a core integration for v1
The source's meeting/resolution/compliance workflows are already modeled as explicit state machines
on custom models (`govoo.meeting.state`, `govoo.resolution.state`, `govoo.compliance.instance.state`
— see `data-model/state-machines.md`). These give full control over the specific transitions,
conditions, and audit requirements this domain needs, which the generic Approvals app would not
add value over. `[RECOMMENDED]` do not introduce Approvals as a dependency unless a future
requirement needs generic multi-step sign-off outside the modeled state machines.

## Common per-integration spec template (used in the sibling files)
```
Purpose
Integration owner (which govoo_* module calls it)
Direction (Govoo -> app, app -> Govoo, or both)
Data exchanged
Trigger
Failure behavior
Feature flag (how the code detects the app is available)
Community fallback
Enterprise dependency
Security
Testing
```
