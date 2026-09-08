# UI — Navigation

Derived from the module/model set in §7 of the source spec and the role set in §6.1. Source does
not prescribe an exact menu tree — this is `[ENGINEERING DETAIL]`, derived from the workflows to
give an AI coding agent an unambiguous starting menu structure. Do not invent unrelated menu items.

## Top-level app menu: "Govoo"
```
Govoo
|-- Governance
|   |-- Directors & Officers        (govoo.appointment, govoo.register.director)
|   |-- Committees                  (govoo.committee)
|   |-- Meetings                    (govoo.meeting)
|   |-- Board Packs                 (govoo.board.pack)
|   |-- Minutes                     (govoo.minutes)
|   `-- Resolutions & Voting        (govoo.resolution, govoo.vote)
|
|-- Ownership
|   |-- Share Classes               (govoo.share.class)
|   |-- Allotments                  (govoo.share.allotment)
|   |-- Transfers                   (govoo.share.transfer)
|   |-- Cap Table                   (govoo.share.holding, read-mostly dashboard view)
|   `-- Register of Members         (govoo.register.member)
|
|-- Statutory Registers
|   |-- Register of Directors       (govoo.register.director)
|   |-- Register of Members         (link to Ownership > Register of Members)
|   |-- Beneficial Ownership        (govoo.register.beneficial.owner)
|   `-- Charges                     (govoo.register.charge)
|
|-- Compliance
|   |-- Obligation Catalogue        (govoo.compliance.obligation)  -- Secretary/Admin only
|   |-- Compliance Calendar         (govoo.compliance.instance, calendar + Kanban view)
|   `-- Filings                     (govoo.compliance.instance, list view filtered to filed/late)
|
|-- Evaluations
|   |-- Campaigns                   (govoo.evaluation.campaign)
|   `-- Results                     (govoo.evaluation.result, aggregate dashboard)
|
`-- Configuration                    -- Board Administrator only
    |-- Companies                   (res.company govoo_* fields)
    |-- Security Groups & Users
    |-- Compliance Obligation Templates (govoo_rw seed data, activation control)
    `-- Settings                    (currency/locale, feature flags)
```

## Menu visibility by group
| Menu | Governance User | Secretary | Admin | Auditor |
| --- | --- | --- | --- | --- |
| Governance | Read | Full | Config | Read |
| Ownership | Read | Full | Read | Read |
| Statutory Registers | Read (except Beneficial Ownership) | Full | Read | Read |
| Compliance | Read (instances only) | Full | Full (catalogue) | Read |
| Evaluations | — | Full | Config | — |
| Configuration | — | — | Full | — |

Portal users (Director, Shareholder) do not see this backend menu at all — they use the portal
"My Governance" area (see `ui/portal-ui.md`).

## Breadcrumb / drill-down expectations
- Committee → Meetings (filtered) → Agenda/Pack/Minutes/Resolutions (drill-down from the meeting
  form, not separate top-level navigation for agenda items).
- Share Class → Allotments/Transfers (filtered) → Holdings (smart button on the class form showing
  current holders).
- Compliance obligation → Instances (smart button showing generated instances for that obligation).
