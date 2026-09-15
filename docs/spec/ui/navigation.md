# UI — Navigation

Derived from the module/model set in §7 of the source spec and the role set in §6.1. Source does
not prescribe an exact menu tree — this is `[ENGINEERING DETAIL]`, derived from the workflows to
give an AI coding agent an unambiguous starting menu structure. Do not invent unrelated menu items.

## Top-level app menu (as implemented)
`[ENGINEERING DETAIL — reconciled]` the tree below is what was actually built
(`govoo_base.govoo_menu_root`, named "Governance" rather than "Govoo", with a flat set of
top-level categories rather than nesting Appointments/Committees/Meetings under one "Governance"
sub-category and renaming "Shares & Cap Table" to "Ownership"). Since this file itself carries no
prescriptive weight from the source spec, and the flatter structure is functionally equivalent
(every model is reachable, drill-downs still work) with no spec basis to prefer one arrangement
over the other, this doc was updated to match the implementation rather than the other way around
(issue #52) — reorganizing six modules' menu XML and renaming the app for a purely cosmetic
difference wasn't judged worth the churn.
```
Governance                              (app root, govoo_base.govoo_menu_root)
|-- Appointments                        (govoo.appointment)
|-- Committees                          (govoo.committee)
|-- Statutory Registers
|   |-- Register of Directors           (govoo.register.director)
|   |-- Register of Members             (govoo.register.member)
|   |-- Register of Beneficial Owners   (govoo.register.beneficial.owner)
|   |-- Register of Charges             (govoo.register.charge)
|   `-- Audit Ledger                    (govoo.register.entry)
|
|-- Shares & Cap Table
|   |-- Share Classes                   (govoo.share.class)
|   |-- Allotments                      (govoo.share.allotment)
|   |-- Transfers                       (govoo.share.transfer)
|   `-- Cap Table                       (govoo.share.holding, read-mostly dashboard view)
|
|-- Board & Meetings
|   |-- Meetings                        (govoo.meeting)
|   |-- Board Packs                     (govoo.board.pack)
|   |-- Minutes                         (govoo.minutes)
|   |-- Resolutions                     (govoo.resolution)
|   `-- Votes                           (govoo.vote)
|
|-- Compliance
|   |-- Obligations                     (govoo.compliance.obligation)  -- Secretary/Admin only
|   `-- Instances                       (govoo.compliance.instance)
|
|-- Evaluations
|   |-- Campaigns                       (govoo.evaluation.campaign)
|   `-- Results                         (govoo.evaluation.result, aggregate dashboard)
|
|-- Rwanda
|   `-- Retention Rules                 (govoo.rw.retention)
|
`-- Configuration                        -- Board Administrator only
    `-- Companies                       (res.company govoo_* fields)
```

## Menu visibility by group
| Menu | Governance User | Secretary | Admin | Auditor |
| --- | --- | --- | --- | --- |
| Appointments | Read | Full | Read | Read |
| Committees | Read | Full | Read/Write | Read |
| Statutory Registers | Read (except Beneficial Ownership) | Full | Read | Read |
| Shares & Cap Table | Read | Full | Read | Read |
| Board & Meetings | Read | Full | Read | Read |
| Compliance | Read (instances only) | Full | Full (catalogue) | Read |
| Evaluations | — | Full | Config | — |
| Rwanda | — | Read | Full | — |
| Configuration | — | — | Full | — |

Portal users (Director, Shareholder) do not see this backend menu at all — they use the portal
"My Governance" area (see `ui/portal-ui.md`).

## Breadcrumb / drill-down expectations
- Committee → Meetings (filtered) → Agenda/Pack/Minutes/Resolutions (drill-down from the meeting
  form, not separate top-level navigation for agenda items).
- Share Class → Allotments/Transfers (filtered) → Holdings (smart button on the class form showing
  current holders).
- Compliance obligation → Instances (smart button showing generated instances for that obligation).
