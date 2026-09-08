# Data Model — Entities

Source: §5, §7 of the source spec. Full field-level detail lives in each `modules/*.md` file; this
file is the single-page domain overview.

## 1. Entity summary (source §5, Entity Summary table)
| Domain entity | Odoo model | Custom or standard | Owning module |
| --- | --- | --- | --- |
| Managed company/entity | `res.company` | standard (extended) | `govoo_base` |
| Person (director/shareholder/officer/BO) | `res.partner` | standard (extended) | `govoo_base` |
| Appointment (role over time) | `govoo.appointment` | custom | `govoo_base` |
| Board/committee | `govoo.committee` | custom | `govoo_base` |
| Meeting | `govoo.meeting` | custom (links `calendar.event`) | `govoo_board` |
| Agenda item | `govoo.agenda.item` | custom | `govoo_board` |
| Board pack | `govoo.board.pack` | custom | `govoo_board` |
| Minutes | `govoo.minutes` | custom | `govoo_board` |
| Resolution | `govoo.resolution` | custom | `govoo_board` |
| Vote | `govoo.vote` | custom | `govoo_board` |
| Statutory register entry (director/member/BO/charge) | `govoo.register.*` | custom | `govoo_secretarial` |
| Register audit ledger | `govoo.register.entry` | custom | `govoo_secretarial` |
| Share class | `govoo.share.class` | custom | `govoo_shares` |
| Allotment | `govoo.share.allotment` | custom | `govoo_shares` |
| Transfer | `govoo.share.transfer` | custom | `govoo_shares` |
| Holding (computed) | `govoo.share.holding` | custom | `govoo_shares` |
| Compliance obligation | `govoo.compliance.obligation` | custom | `govoo_compliance` |
| Compliance instance | `govoo.compliance.instance` | custom | `govoo_compliance` |
| Evaluation campaign | `govoo.evaluation.campaign` | custom (wraps `survey.survey`) | `govoo_evaluation` |
| Evaluation result | `govoo.evaluation.result` | custom | `govoo_evaluation` |
| Document | `documents.document` / `ir.attachment` | standard | reused everywhere |

## 2. Data ownership classification
| Class | Meaning | Examples |
| --- | --- | --- |
| **Source data** | Directly entered by a user, the authoritative record of a fact | `govoo.appointment`, `govoo.share.allotment`, `govoo.share.transfer`, `govoo.meeting`, `govoo.resolution`, `govoo.vote`, `govoo.register.charge`, `govoo.register.beneficial.owner` |
| **Derived data** | Computed from source data, never independently entered | `govoo.appointment.state`, `govoo.share.holding` (all fields), `govoo.meeting.quorum_met`, `govoo.resolution.result`, `govoo.minutes.retention_until`, `govoo.register.director` (curated view), `govoo.register.member` (curated from holdings) |
| **Cached/materialized data** | Derived data that is stored (not computed on the fly) for query performance | `govoo.share.holding` (stored computed fields), aggregate fields on `govoo.evaluation.result` |
| **External data** | Data whose authoritative source is outside Govoo | Government filing acknowledgement numbers (`reference_no`) once filed — Govoo records the acknowledgement but is not the source of truth for the filing itself |
| **Documents/files** | Binary/file content | `documents.document` / `ir.attachment` records referenced by `*_document_id` fields throughout |
| **Audit records** | Immutable history | `mail.message` (via `mail.thread` on every transactional model), `govoo.register.entry` (independent, append-only ledger) |

## 3. Entities NOT modeled as custom (deliberately reused, source §3.1 "reuse before build")
| Concept | Reused as | Why not custom |
| --- | --- | --- |
| Person | `res.partner` (extended) | No duplicate contact data; source explicit rule |
| Company/entity | `res.company` (extended) | Same |
| Meeting scheduling/reminders | `calendar.event`, linked from `govoo.meeting` | Odoo's Calendar app already solves scheduling |
| Board evaluation question authoring | `survey.survey`, wrapped by `govoo.evaluation.campaign` | Odoo's Surveys app already solves this |
| Onboarding/training | eLearning app | No governance-specific need identified |
| Document storage | `documents.document` (Enterprise) / `ir.attachment` (Community fallback) | Odoo already solves file storage/versioning |
| E-signature | `sign.request` (Enterprise, feature-flagged, legal-validity `[CONFIRM]`) | Odoo already solves e-signature workflow |
