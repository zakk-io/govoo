### 3. Contract Management

#### 3.1 Purpose & positioning
clagov_contracts
A governance-grade Contract Lifecycle Management (CLM) module. Its differentiator over generic CLM tools is
deep wiring into Clagov's governance machinery: board approval, delegation-of-authority, related-party checks,
and the compliance-calendar reminder engine.

#### 3.2 Functional requirements (by lifecycle stage)

| ID | Feature | Description |
| :--- | :--- | :--- |
| CM-F01 | Contract register | Central clagov.contract with counterparty, entity, type, value, status, linked documents |
| CM-F02 | Types & tagging | Officer/service agreements, NDAs, shareholder agreements, related-party, leases, supplier, engagement letters, SLAS |
| CM-F03 | Version control | Every draft/executed version retained (via Documents) |
| CM-F04 | Template & clause library | Templates + reusable clauses with merge fields from partner/company data |
| CM-F05 | Generate from template | Produce a contract (QWeb) in EN/FR/Kinyarwanda |
| CM-F06 | Approval routing | Configurable legal finance → board routing |
| CM-F07 | Board-approval linkage | Contracts above a threshold / of a defined type require a linked clagov.resolution before execution [CONFIRM thresholds] |
| CM-F08 | Delegation-of-authority matrix | Who may sign what type/value; block execution outside authority [CONFIRM matrix] |
| CM-F09 | Related-party check | Cross-reference counterparty against directors' interests register; flag conflicts |
| CM-F10 | E-signature | Execute via Odoo Sign (ordered signing, audit trail); locked executed PDF [CONFIRM Rwanda e-sig validity] |
| CM-F11 | Key-date tracking | Start/end/renewal/notice dates auto-create compliance reminders |
| CM-F12 | Auto-renewal & notice alerts | Evergreen tracking; alert before notice windows lapse |
| CM-F13 | Obligation & milestone tracking | Deliverables and payment schedule with owners/status |
| CM-F14 | Renewal/termination workflow | Guided renew, renegotiate or terminate |
| CM-F15 | Financial linkage (optional) | Value + payment schedule in RWF; optional link to Odoo Accounting behind a flag |
| CM-F16 | Portal access | Counterparties/approvers see only their contracts (record rules) |
| CM-F17 CM-F18 | Dashboards Retention | Register, expiry/renewal calendar, obligations status, spend by counterparty Align to statutory retention rules in clagov_rw |
| CM-F19 | Al extraction | Pull key termsdates//obligations from legacy contracts (human-confirmed) uses clagov_ai |
| CM-F20 | Al summarize / risk/ Q&A | Summarize, flag risky/missing clauses, detect template deviation, Q&A over contracts uses clagov_ai |

Clagov Al & Contract Management v1.0 Confidential Page 6

#### 3.3 Data models

**clagov.contract** (inherits mail.thread, mail.activity.mixin)
| Field | Type | Notes |
| :--- | :--- | :--- |
| name/reference | Char | contract title / number |
| company_id | m20 res.company | managing entity |
| counterparty_id | m20 res.partner | other party |
| contract_type_id | m2o clagov.contract.type | |
| value | Monetary | contract value |
| currency_id | m20 res.currency | RWF default |
| date_start/ date_end | Date | term |
| renewal_type | Selection | none/manual/auto (evergreen) |
| notice_period_days | Integer | drives alerts |
| resolution_id | m20 clagov.resolution | board approval (CM-F07) |
| is_related_party | Boolean | computed (CM-F09) |
| sign_request_id | m20 sign.request | execution |
| document_ids | m2m documents.document | versions |
| obligation_ids | 02m clagov.contract.obligation | |
| state | Selection | draft/in_approval / approved / executed/active/ expired/ terminated |

`clagov.contract.type` - category + rules (approval threshold, mandatory clauses, retention).
`clagov.contract.template` - template body + merge fields + language. `clagov.contract.clause`
library (standard vs optional, mandatory flag).

**clagov.contract.obligation**
| Field | Type | Notes |
| :--- | :--- | :--- |
| contract_id | m2o clagov.contract | |
| name | Char | obligation/milestone |
| due_date | Date | → creates compliance reminder |
| responsible_id | m2o res.users | |
| amount | Monetary | payment schedule (optional) |
| state | Selection | open/done/overdue / waived |

reusable clause
`clagov.contract.milestone` - deliverable/payment milestone (date, value, status).

#### 3.4 Governance integration (the differentiator)
• CM-F07 links high-value or defined-type contracts to a board clagov.resolution; execution is blocked until
the resolution is passed.
• CM-F08 enforces a delegation-of-authority matrix (signing limits by role/value) approved by the board.

Clagov Al & Contract Management v1.0 Confidential Page 7

• CM-F09 reconciles the counterparty against the directors' interests / related-party register and forces a
conflict declaration before approval.
• CM-F11 feeds the existing clagov_compliance reminder engine, so contract dates are governed by the
same calendar as statutory deadlines.

#### 3.5 MOSCOW
• Must: CM-F01, CM-F02, CM-F03, CM-F06, CM-F07, CM-F08, CM-F10, CM-F11, CM-F16.
• Should: CM-F04, CM-F05, CM-F09, CM-F12, CM-F13, CM-F14, CM-F17, CM-F18.
• Could: CM-F15, CM-F19, CM-F20.

### 4. Security Model (additions)

New/extended security groups (in clagov_base):

| Group | Purpose |
| :--- | :--- |
| Al User | May invoke enabled Al features (subject to per-feature flags) |
| Al Administrator | Configures clagov.ai.config, keys, caps, residency |
| Contract Manager | Create/manage contracts, templates, clauses |
| Contract Approver | Approve within delegation-of-authority limits |
| Contract Viewer (Portal) | Counterparties/approvers see only their contracts |

Rules:
• Al retrieval and contract records honour the existing record rules, company scope and portal access
bypass.
• Confidential contracts restricted by record rule; executed documents are write-once.
Every Al action and contract state change is captured in mail.thread/clagov.ai.request.

### 5. Integration Points
• Documents - contract versions, executed PDFs, source documents for Al extraction.
• Sign - contract execution and (where enabled) resolution signing.
• clagov_board - board approval of contracts via resolutions.
• clagov_compliance - contract dates → reminder engine.
• clagov_ai - contract intelligence (CM-F19/F20) and all governance Al features.
• Accounting (optional) - contract value/payment schedule invoices/POs behind a flag.
• Al provider - via a swappable service interface with DPA/zero-retention; residency-aware.

### 6. Non-Functional Requirements
• Data residency - no Al processing and contract PII stored in Rwanda (or NCSA-authorized), backups included,
encrypted at rest. [CONFIRM]
• Auditability - full provenance on Al outputs and contract lifecycle changes.
• Retention - contracts and Al logs follow clagov_rw retention/disposal rules.
• Reliability - Al features degrade gracefully; contract workflows never depend on Al being available.
• Metering - Al token usage and contract counts feed the pricing add-ons.

Clagov Al & Contract Management v1.0 Confidential Page 8

### 7. Definition of Done (per module)
1. All models, fields and relationships in $\S2.3/\S3.3$ exist and migrate cleanly.
2. Views (list/form/calendar/Kanban) exist for each user-facing model.
3. ir.model.access.csv and record rules exist for every group in §4; access verified (portal user cannot read
another entity's data; Al cannot return out-of-scope data).
4. Human-in-the-loop enforced: no Al output auto-commits; no contract executes outside approval + authority.
5. Audit (mail.thread/clagov.ai.request) works; Al content labelled and version-tracked.
6. QWeb outputs (contract documents, register extracts) render correctly.
7. Unit tests pass; core logic (approval gating, related-party flag, reminder creation, permission-aware RAG)
covered.
8. Strings translatable; fr/rw stubs present.
9. No hard-coded legal/tax value; [CONFIRM] items resolved or defaulted inactive.
10. Feature flags: modules install and the suite runs with Al/contracts absent.

### 8. Build Sequence & Dependencies

| Step | Module | Depends on | Notes |
| :--- | :--- | :--- | :--- |
| 1 | clagov_ai | clagov_base | Service layer + audit + guardrails first; wire one consumer (e.g. Al- F08 search) to prove the pattern |
| 2 | clagov_contracts | clagov_base, clagov_compliance, clagov_board | Core register → approval e-sign → dates/reminders |
| 3 | Contract intelligence | clagov_ai, clagov_contracts | CM-F19/CM-F20 last, once both are stable |

### 9. Open Items to Confirm

| # | Item | Owner |
| :--- | :--- | :--- |
| 1 | Al provider, hosting region, DPA/zero-retention terms (AI-N01) | Tech lead + counsel + NCSA |
| 2 | Whether a self-hosted model is required for residency | Tech lead + counsel |
| 3 | e-signature legal validity for contracts under Rwandan law (CM-F10) | Legal advisor |
| 4 | Board-approval thresholds and contract types requiring a resolution (CM-F07) | Client board/counsel |
| 5 | Delegation-of-authority (signing) matrix (CM-F08) | Client board |
| 6 | Al token caps/pricing metering per tier | Commercial + tech lead |

### 10. Glossary (delta)

| Term | Meaning |
| :--- | :--- |
| RAG | Retrieval-augmented generation Al answers grounded in retrieved source records with citations. |
| Human-in-the-loop | A required human review/approval step before Al output becomes an official record. |
| CLM | Contract Lifecycle Management authoring, approval, execution, obligations and renewal of contracts. |
| Delegation of authority | Board-approved matrix defining who may commit/sign contracts of a given type or value. |

Clagov Al & Contract Management v1.0 Confidential Page 9

| Term | Meaning |
| :--- | :--- |
| Related-party contract | A contract with a counterparty connected to a director/officer, requiring conflict declaration. |
| Evergreen contract | A contract that auto-renews unless notice is given within a defined window. |
| Zero-retention | Provider setting under which prompts/outputs are not stored or used for model training. |

*End of addendum v1.0. All Rwanda legal/tax and residency items marked [CONFIRM] are provisional and must be
verified with a licensed Rwandan advocate and, for hosting, with NCSA before being treated as authoritative. Al is
assistive; a named human is accountable for every official record.*

Clagov Al & Contract Management v1.0 Confidential Page 10