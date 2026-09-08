# Access Control — Groups and Model Access Matrix

Source: §6.1, §6.2 of the source spec.

## 1. Security groups (defined in `govoo_base`, source §6.1)
| Group | XML id | Purpose |
| --- | --- | --- |
| Governance User | `govoo_base.group_govoo_user` | Base access (read own-company governance data) |
| Company Secretary | `govoo_base.group_govoo_secretary` | Power user; create/manage all governance records |
| Board Administrator | `govoo_base.group_govoo_admin` | Config, users, groups; cannot cast board votes |
| Director (Portal) | `govoo_base.group_govoo_director_portal` | External director self-service |
| Shareholder (Portal) | `govoo_base.group_govoo_shareholder_portal` | External shareholder self-service |
| Auditor (read-only) | `govoo_base.group_govoo_auditor` | Global read, no write |

`[ENGINEERING DETAIL]` Recommended group implication hierarchy (not stated explicitly in source,
but consistent with "power user" language): `group_govoo_secretary` implies `group_govoo_user`;
`group_govoo_admin` implies `group_govoo_user` (not `group_govoo_secretary`, since Admin's remit is
config, not governance authorship — keep these independent so an Admin who is *not* also a
Secretary cannot silently gain register-editing rights). Portal groups (`director_portal`,
`shareholder_portal`) do **not** imply and are **not** implied by any internal group — they are a
strictly separate, portal-only track (source §6.3: "Portal users have no internal licence").

## 2. Access matrix — `ir.model.access.csv` level (Read / Create / Write / Delete)
`U`=Governance User, `S`=Company Secretary, `A`=Board Administrator, `DP`=Director Portal,
`SP`=Shareholder Portal, `AU`=Auditor. `-` = no access at this level (may still be restricted
further by a record rule even where marked yes). All rows are additionally company-scoped per
`record-rules.md` §1.

| Model | U | S | A | DP | SP | AU | Special rules |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `res.partner` (`govoo_*` fields) | R (non-PII) | RWCD | RWC | R (own) | R (own) | R | PII fields (`govoo_national_id`, `govoo_date_of_birth`) restricted to S/A only — field-level, not row-level |
| `res.company` (`govoo_*` fields) | R | RW | RWCD | - | - | R | Company creation/deletion restricted to Admin |
| `govoo.appointment` | R | RWCD | R | R (own) | - | R | Company-scoped |
| `govoo.committee` | R | RWCD | RW | R (own, via membership) | - | R | Company-scoped |
| `govoo.register.director` | R | RWCD | R | R (own) | - | R | Company-scoped; curated from appointments |
| `govoo.register.member` | R | RWCD | R | - | R (own) | R | Company-scoped |
| `govoo.register.beneficial.owner` | - | RWCD | R | - | - | R | Highest sensitivity — Governance User has NO access, not even read |
| `govoo.register.charge` | R | RWCD | R | - | - | R | Company-scoped; no delete for anyone (satisfied flag instead) |
| `govoo.register.entry` | - | RC (create only, via system) | RC (create only, via system) | - | - | R | **No write/unlink for ANY group, including Admin** |
| `govoo.share.class` | R | RWCD | RW | - | R (own company's classes, read-only) | R | Company-scoped |
| `govoo.share.allotment` | R | RWCD | R | - | R (own) | R | Company-scoped |
| `govoo.share.transfer` | R | RWCD | R | - | R (own, as party) | R | Company-scoped |
| `govoo.share.holding` | R | RWCD (recompute triggers) | R | - | R (own only) | R | Shareholder Portal record rule: own partner_id only |
| `govoo.meeting` | R | RWCD | RW | R (own committee) | - | R | Director Portal record rule: committee membership |
| `govoo.agenda.item` | R | RWCD | RW | R (own committee) | - | R | Inherits meeting scoping |
| `govoo.board.pack` | R | RWCD | R | R (own committee, redacted) | - | R | Redaction applied before distribution |
| `govoo.minutes` | R | RWC (D restricted post-approval) | R | R (own committee) | - | R | No delete once `state != draft` |
| `govoo.resolution` | R | RWCD (draft/open only) | R | R (own committee) | R (shareholder-type, own eligibility) | R | Board Admin explicitly excluded from voting-related write actions (see §5 below) |
| `govoo.vote` | R (aggregate only, not others' raw choice where conflicted) | RC (facilitate, cannot cast on behalf without documented authority) | - (no create) | C (own vote, own committee) | C (own vote, shareholder-type) | R | **Board Administrator has no create access** (BR-SEC-004) |
| `govoo.compliance.obligation` | R | RWCD | RWCD | - | - | R | Config-level |
| `govoo.compliance.instance` | R | RWCD | RW | - | - | R | Company-scoped |
| `govoo.evaluation.campaign` | R | RWCD | RW | R (own, as participant) | - | R | Company/committee-scoped |
| `govoo.evaluation.result` | - (aggregate only, via UI not raw access) | RWCD | R | - | - | R | Individual `survey.user_input` NOT exposed — see `record-rules.md` §5 |

## 3. Multi-company enforcement (source §6.2)
Every row above is additionally filtered by a company-scoped record rule
(`record-rules.md` §1) — the access matrix here governs *what a group can do to a model in
principle*; the record rule governs *which specific rows*. Both layers are required; neither
substitutes for the other.

## 4. Field-level restrictions (source §6.2)
| Field(s) | Model | Restricted to |
| --- | --- | --- |
| `govoo_national_id`, `govoo_date_of_birth` | `res.partner` | Company Secretary, Board Administrator |
| `nature_of_control`, `evidence_document_id` | `govoo.register.beneficial.owner` | Company Secretary, Board Administrator (whole model already restricted; field-level restriction here is defense-in-depth for any future group added with partial model access) |
| Individual `survey.user_input` answers tied to a `govoo.evaluation.campaign` | `survey.user_input` | Company Secretary, Board Administrator, and the respondent's own input only |

Implementation: use Odoo's `groups=` attribute on the field definition (blocks the field from the
view entirely for unauthorized groups) **and** confirm via a security test that a direct
`read()`/RPC call by an unauthorized user does not leak the field either (view-level hiding alone is
not sufficient — see TC-SEC tests in `testing/security-tests.md`).

## 5. Separation of duties (source §6.1, §6.2)
| Actor | Prepares | Approves / Votes / Signs | Cannot |
| --- | --- | --- | --- |
| Company Secretary | Appointments, committees, registers, share transactions, meetings, agenda, packs, minutes (draft), resolutions (draft/open), compliance instances | Nothing binding — facilitates only | Cast a vote as if they were a director/shareholder (unless they hold that role themselves via their own `res.partner`/appointment, in which case they vote as that person, not as "Secretary") |
| Board Administrator | System configuration, groups, obligation catalogue | Nothing | **Cast any `govoo.vote`**, regardless of configuration privileges (BR-SEC-004) |
| Directors | — | Approve/sign minutes; vote on board/committee resolutions | Vote on shareholder-only resolutions unless also a shareholder |
| Shareholders | — | Vote on shareholder resolutions | Vote on board/committee-only resolutions unless also a director |

This maps directly to `ir.model.access.csv` for `govoo.vote`: `group_govoo_admin` has **no** `create`
permission on that model, full stop — this is not achievable via a record rule alone (a record rule
filters *which* rows, not *whether the model action is permitted at all*), so it must be enforced at
the access-rights level.
