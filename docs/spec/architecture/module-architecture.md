# Module Architecture

Source: §3.2, §3.3, §7, §12 of the source spec.

## 1. Custom modules
| Module | Purpose | Depends on (Odoo) | Depends on (custom) |
| --- | --- | --- | --- |
| `govoo_base` | Shared security groups, `res.partner`/`res.company` extensions, `govoo.appointment`, `govoo.committee` | `base`, `mail`, `contacts` | — |
| `govoo_secretarial` | Statutory registers (directors, members, beneficial owners, charges, append-only entry ledger) | `base`, `mail`, `documents` (feature-flagged) | `govoo_base` |
| `govoo_shares` | Cap table / share register: classes, allotments, transfers, computed holdings | `base`, `mail` | `govoo_secretarial` |
| `govoo_board` | Meetings, agenda items, board packs, minutes, resolutions, e-voting | `base`, `mail`, `calendar`, `documents` (flag), `sign` (flag) | `govoo_base`, `govoo_shares` (for weighted shareholder votes) |
| `govoo_compliance` | Obligation catalogue, compliance instances, cron reminder engine, filing-pack export | `base`, `mail` | `govoo_base` |
| `govoo_rw` | Rwanda localization: currency/language/locale config, register mapping, retention rules, provisional compliance-deadline templates, CMA governance-code checklist | `base` | `govoo_secretarial`, `govoo_shares`, `govoo_board`, `govoo_compliance` |
| `govoo_contracts` *(addendum)* | Contract register, template/clause library, approval routing linked to board approval and delegation-of-authority, related-party conflict checks, e-signature execution, obligation/milestone/renewal tracking | `base`, `mail`, `documents` (flag), `sign` (flag) | `govoo_base`, `govoo_compliance` (reminder reuse), `govoo_board` (resolution linkage) |
| `govoo_evaluation` | Board evaluation campaigns and results, thin wrapper over Surveys | `base`, `survey` | `govoo_base` |
| Portal + Dashboard | External self-service + personalized dashboard (not a single module; portal views/controllers ship inside each module, dashboard aggregation is a thin layer) | `portal`, `website`, Spreadsheet Dashboards (Enterprise) or OCA `spreadsheet_dashboard_oca` | all of the above |
| `govoo_rw_accounting` *(optional)* | Rwanda chart of accounts + tax codes (no official `l10n_rw`) | `account` | `govoo_rw` |
| `govoo_rw_ebm` *(optional)* | RRA EBM/VSDC e-invoicing connector | `account`, `govoo_rw_accounting` | `govoo_rw_accounting` |

## 2. Standard Odoo apps reused (source §3.3)
| Area | Odoo app | Edition | Community fallback | Feature flag needed? |
| --- | --- | --- | --- | --- |
| Document repository & board packs | Documents | Enterprise | OCA `dms` / `ir.attachment` | Yes |
| E-signature | Sign | Enterprise | OCA `sign_oca` | Yes |
| Board evaluations & quizzes | Surveys | Community | — | No |
| Onboarding/training (LMS) | eLearning | Community | — | No |
| Meeting scheduling | Calendar | Community | — | No |
| Reminders / recurring jobs | `mail.activity`, `ir.cron` | Community | — | No |
| Directory | Contacts, HR | Community | — | No |
| External access | Portal, Website | Community | — | No |
| Dashboards | Spreadsheet Dashboards | Enterprise | OCA `spreadsheet_dashboard_oca` | Yes |
| Approvals/workflow | Approvals | Enterprise | Custom `state` fields (already the design in `govoo_board`/`govoo_compliance`) | Yes |

`[CONFIRM]` (source §3.3): Enterprise vs Community + OCA must be decided before build starts — it
affects licensing cost and the self-host/data-residency setup. Custom modules must remain
edition-agnostic: wrap every Documents/Sign/Dashboards/Approvals call behind a feature flag (see
`architecture/technology-standards.md` §5 and `integrations/`) so the suite still installs and
functions (with reduced UX) on Community.

## 3. Module boundaries — what each module owns vs. must NOT own
| Module | Owns | Must NOT own |
| --- | --- | --- |
| `govoo_base` | Security groups; `govoo.appointment`; `govoo.committee`; PII fields on `res.partner`; entity fields on `res.company` | Register content, share data, meetings, compliance data |
| `govoo_secretarial` | Register-of-directors view, register of members, beneficial ownership register, register of charges, append-only `govoo.register.entry` ledger | Share allotment/transfer transactional logic (owned by `govoo_shares`, which feeds the member register) |
| `govoo_shares` | Share classes, allotments, transfers, computed holdings, cap-table/voting-power outputs | Statutory register presentation (owned by `govoo_secretarial`, which consumes `govoo.share.holding`) |
| `govoo_board` | Meetings, agenda, packs, minutes, resolutions, votes | Compliance deadlines (a resolution may trigger a filing obligation, but the obligation itself is `govoo_compliance`'s) |
| `govoo_compliance` | Obligation catalogue, instances, reminder cron, filing-pack export | Statutory register content; Rwanda-specific deadline values (owned as data by `govoo_rw`) |
| `govoo_rw` | Locale/currency config, register-to-law mapping, retention rules, provisional deadline template **data**, CMA checklist | Any hard-coded rate/date/threshold; any core transactional model |
| `govoo_contracts` *(addendum)* | Contract register, templates/clauses, approval routing, delegation-of-authority enforcement, related-party checks, obligations/milestones, e-signature execution | Board-resolution mechanics (consumes `govoo_board`'s resolution, doesn't reimplement voting/quorum); reminder/cron mechanics (reuses `govoo_compliance`'s engine, doesn't reimplement it); AI extraction/summarization (out of scope — `govoo_ai`, unspecced) |
| `govoo_evaluation` | Evaluation campaigns, result aggregation, confidentiality rules over survey inputs | Survey question authoring (delegated to standard Surveys UI) |

## 4. Build order
See `implementation/build-sequence.md` for the full phased roadmap. Summary (source §12, extended
per the Contract Management addendum §8): `govoo_base` → `govoo_secretarial` → `govoo_shares` →
`govoo_board` → `govoo_compliance` → `govoo_contracts` *(addendum, new — depends on `govoo_base`,
`govoo_compliance`, `govoo_board`)* → `govoo_rw` → `govoo_evaluation` (parallelizable after
`govoo_base`) → Portal + dashboard → optional `govoo_rw_accounting` / `govoo_rw_ebm`. The unspecced
`govoo_ai` and "Contract intelligence" steps from the addendum's own build sequence are out of scope
for this repository (see `integrations/future-integrations.md`).
