# Open Decisions

Source: §13 of the source spec ("Open Decisions Requiring Stakeholder Input") plus items
identified during decomposition and flagged `[ENGINEERING DETAIL — ... CONFIRM]` throughout this
repository. Every item here is unresolved. **None may be treated as decided anywhere in this
repository or in the implementation until it is moved to `decisions/confirmed-decisions.md` with a
recorded confirmation.**

## From the source spec (§13, verbatim items)
1. **Edition (Enterprise vs Community + OCA).**
   Owner: technical sponsor. Affects: `architecture/technology-standards.md` §1,
   `architecture/module-architecture.md` §2 (every Enterprise-app dependency).
   (The Odoo *version* half of this item is resolved — see
   `decisions/confirmed-decisions.md` entry [1]: shipped as Odoo 19.)
2. **In-Rwanda / NCSA-authorized hosting for real personal data.**
   Owner: client + counsel + NCSA. Affects: `devops/environments.md` §1,
   `security/privacy.md` §1.
3. **Legal validity of e-signature and electronic/written resolutions under Rwandan law and the
   client's articles of association.**
   Owner: Rwandan legal advisor. Affects: `modules/govoo_board.md` (BR-BOARD-008),
   `integrations/sign.md`.
4. **Beneficial-ownership control thresholds and exact statutory register contents.**
   Owner: Rwandan legal advisor. Affects: `modules/govoo_secretarial.md` FR-SEC-003,
   BR-SEC-STAT-003.
5. **Exact annual-return filing window; CIT/VAT/PAYE/WHT/RSSB rates and statutory article numbers.**
   Owner: tax/legal advisor. Affects: `modules/govoo_rw.md` §3, `data-model/constraints.md` §3.
6. **Whether RDB/Irembo exposes any public filing API.**
   Owner: technical sponsor + RDB liaison. Affects: `modules/govoo_compliance.md` FR-COMP-004,
   `integrations/future-integrations.md`.
7. **GL posting policy for capital events (default: off).**
   Owner: client accounting team. Affects: `modules/govoo_shares.md` FR-SHARE-005,
   BR-SHARE-004.
8. **RPO/RTO targets and backup location.**
   Owner: DevOps + sponsor. Affects: `devops/backup-recovery.md`.

## Additional items surfaced during decomposition (`[ENGINEERING DETAIL — ... CONFIRM]` markers)
| # | Item | Where flagged | Owner (recommended) |
| --- | --- | --- | --- |
| 9 | Whether `govoo.meeting` `held` transition is hard-blocked when `quorum_met = False`, or an overridable warning | `data-model/state-machines.md` (`govoo.meeting.state`), `modules/govoo_board.md` FR-BOARD-001 | Product owner / company secretary practice |
| 10 | Whether a second `govoo.vote` from the same voter on the same resolution is rejected or overwrites the first | `data-model/state-machines.md`, `workflows/voting.md`, `modules/govoo_board.md` FR-BOARD-006 | Product owner |
| 11 | Exact majority-threshold percentages per `resolution_type` (ordinary vs special) | `data-model/state-machines.md` (`govoo.resolution.state`), BR-BOARD-005 | Client articles of association + Rwandan law |
| 12 | Whether parent-committee visibility cascades to Director Portal users viewing a sub-committee's parent board meetings | `security/record-rules.md` §2 | Product owner |
| 13 | Exact reconciliation process between 10-year statutory retention and data-subject erasure rights | `data-model/constraints.md` §3, `security/privacy.md` §2, BR-RW-003 | Legal/DPO |
| 14 | Escalation recipient for `late` compliance instances | `modules/govoo_compliance.md` FR-COMP-003, BR-COMP-003 | Product owner |
| 15 | Exact statutory particulars required on the printed Register of Directors extract | `modules/govoo_secretarial.md` FR-SEC-001 | Legal advisor |
| 16 | Exact validation rule for "registered office must be in Rwanda" | `modules/govoo_base.md` FR-BASE-002, BR-BASE-002 | Legal advisor |
| 17 | Whether unauthenticated, token-only portal share links are in scope, or portal access is always authenticated | `security/portal-security.md` §2 | Product owner |
| 18 | Single Odoo instance shared across a corporate-services firm's clients vs. one instance per client | `devops/deployment.md` §1 | Commercial/technical sponsor |
| 19 | Whether CDD/KYC capture (source §10.5) requires additional fields beyond the existing PII fields on `res.partner` | `security/privacy.md` §3 | Legal/compliance advisor |
| 20 | Exact applicability rule for the CMA Corporate Governance Code checklist (which entity types are in scope) | `modules/govoo_rw.md` §5, FR-RW-004 | Client / CMA guidance |
| 21 | Whether an event-relative compliance obligation's trigger is automated (cascades from another record) or manually created | `modules/govoo_compliance.md` FR-COMP-002 | Product owner |
| 22 | Exact per-recipient board-pack redaction data model (dedicated child model vs. dynamic rendering) | `modules/govoo_board.md` FR-BOARD-003 | Engineering decision, document once made |
| 23 | Actual CMA Corporate Governance Code 2024 provision text/numbering to populate `govoo.rw.governance.checklist.item` records against | `modules/govoo_rw.md` §5, FR-RW-004 | Legal advisor (gazetted code text) |

## How to use this file
- Never mark an item here as resolved by editing this file alone — resolution requires adding the
  corresponding entry to `decisions/confirmed-decisions.md` with who confirmed it and when, **and**
  updating every spec file that referenced the `[CONFIRM]`/`[ENGINEERING DETAIL]` marker.
- If, during implementation, a new ambiguity is discovered that isn't listed here, add it to this
  file (with an owner and affected-spec-file list) rather than resolving it unilaterally in code.
