# System Architecture

Source: §1, §3 of the source spec.

## 1. System style
Govoo is a **modular monolith built on Odoo** (single Odoo instance/database per deployment tenant),
not a microservices system, not a bespoke backend with a separate database. Custom Odoo modules
extend the standard Odoo data model (`res.partner`, `res.company`, `mail.thread`,
`mail.activity.mixin`, `calendar.event`, `survey.survey`, `documents.document`, `sign.request`)
rather than duplicating equivalent concepts.

## 2. Guiding principles (source §3.1 — MUST be honored by every module)
| Principle | Meaning for implementation |
| --- | --- |
| Build on the Odoo backbone | Every director/shareholder/officer/beneficial owner is a `res.partner`. Every managed legal entity is a `res.company`. No parallel "person" or "company" table is ever created. |
| Reuse before build | Custom models are built **only** where Odoo has no genuine equivalent: registers, cap table, meetings/resolutions/e-voting, compliance calendar. Everything else (contacts, calendar, documents, e-signature, surveys, eLearning, dashboards, approvals) is reused via standard or OCA modules. |
| Configuration over code | Statutory rules, deadlines, rates, thresholds are **data records** (obligation templates, config settings), never Python literals, so they survive regulatory change without a code deploy. |
| Security by default | Every model has `ir.model.access.csv` entries and, where needed, record rules and company-scoping. No model ships without access control. |
| Auditable | Every transactional model inherits `mail.thread` (+ `mail.activity.mixin` where reminders apply) for a timestamped, user-attributed history. |

## 3. High-level system boundary
```
                    +-------------------------------------------------+
                    |                  Odoo instance                  |
                    |                                                 |
  Internal users -> |  govoo_base / govoo_secretarial / govoo_shares  |
  (Secretary,       |  govoo_board / govoo_compliance / govoo_rw      | <- ir.cron (reminders,
   Admin, Auditor)  |  govoo_evaluation                               |    compliance instance gen)
                    |        |              |              |          |
                    |  res.partner   res.company     mail.thread      |
                    |        |              |              |          |
                    |  calendar.event  documents.document  sign.request (feature-flagged)
                    |        |              |              |          |
                    +--------|--------------|--------------|----------+
                             |              |              |
                    +--------v--------------v--------------v----------+
                    |         Portal (portal.mixin, access tokens)     |
  External users -> |   Director Portal - Shareholder Portal           |
                    +---------------------------------------------------+
```

## 4. Deployment shape
- Single Odoo instance, multi-company (`res.company`) — a corporate-services firm can administer
  many client entities in one database with strict company-level isolation (§6.2 of source; see
  `security/`).
- Environments: dev → staging → production (source §10; see `devops/environments.md`).
- Data residency is a **hard constraint**: production environments holding real personal data,
  including backups, must be hosted in Rwanda or an NCSA-authorized location `[CONFIRM]`. Build/staging
  may use non-Rwanda hosting (e.g. Odoo.sh) **only** with synthetic/anonymized data. See
  `devops/environments.md` and `decisions/open-decisions.md` item 2.

## 5. What this system explicitly is NOT (source §1.2 — non-goals, v1)
- Not a native mobile app — responsive web + portal only.
- Not an AI minute-drafting tool.
- Not a group/multi-entity consolidation reporting system.
- Not a tax engine by default — `govoo_rw_accounting` / `govoo_rw_ebm` are optional, separately
  installed modules outside the governance core (source §8.4).
- Not a system with a confirmed government filing API — RDB/Irembo API availability is `[CONFIRM]`
  (source §13 item 6); the system instead produces filing-pack exports for manual submission
  (`workflows/compliance.md`).

## 6. Cross-cutting concerns and where they live
| Concern | Owning spec |
| --- | --- |
| Security groups, record rules, field-level PII restriction | `security/` |
| Multi-company isolation | `security/access-control.md`, `security/record-rules.md` |
| Audit trail (`mail.thread`) | `data-model/entities.md`, each `modules/*.md` |
| Data residency, backups, DR | `devops/` |
| Statutory/legal value configurability | `data-model/constraints.md`, `modules/govoo_rw.md` |
| Feature flags for Enterprise-only integrations | `integrations/`, `architecture/technology-standards.md` |
