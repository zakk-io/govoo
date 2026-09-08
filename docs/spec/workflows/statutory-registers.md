# Workflow: Statutory Registers

Source: §7.2 of the source spec. Requirements: FR-SEC-001..005. Models: `govoo.register.director`,
`govoo.register.member`, `govoo.register.beneficial.owner`, `govoo.register.charge`,
`govoo.register.entry`.

## Actor
Company Secretary (curates all four registers); Auditor (read); relevant portal user (read own
record, for director/member registers only).

## General pattern (applies to all four registers)
1. A change occurs in the underlying source data (appointment created/resigned for the director
   register; holding recomputed for the member register; a partner flagged as beneficial owner;
   a charge created/satisfied).
2. The register model reflects the change — either as a live curated view (director, member
   registers, which derive from `govoo.appointment`/`govoo.share.holding` respectively) or as
   directly-entered data with its own lifecycle (beneficial owner, charges).
3. **Every** create/update/cease on any of the four registers writes a corresponding
   `govoo.register.entry` row (`register_model`, `res_id`, `change_type`, `effective_date`,
   `user_id`) — this is the append-only audit ledger, independent of and in addition to the
   standard `mail.message` history (FR-SEC-005).

## A. Register of Directors
- Source: `govoo.appointment` records. No independent data entry — see
  `workflows/appointments.md`.
- Printable extract (QWeb report) shows current + optionally historical directors/secretaries with
  statutory particulars.

## B. Register of Members
- Source: `govoo.share.holding` (via `govoo_shares`). No independent data entry — see
  `workflows/share-management.md` §D.
- `date_ceased` set automatically when a partner's aggregate holding across all classes reaches
  zero; `date_entered` set on first holding.

## C. Beneficial Ownership Register (directly entered, highest scrutiny)
1. Secretary identifies a partner meeting beneficial-ownership control criteria (possibly informed
   by, but not automatically derived from, `govoo.share.holding` percentages — since control can
   arise from board-appointment power or "significant influence," not just shareholding).
2. Secretary sets `res.partner.govoo_is_beneficial_owner = True` and creates a
   `govoo.register.beneficial.owner` record: `nature_of_control` (from the provisional/configurable
   category list, `[CONFIRM per Rwanda law]`), `date_became_registrable`, `evidence_document_id`.
3. System flags the record as provisional in the UI/report wherever `nature_of_control` thresholds
   are unconfirmed (BR-SEC-STAT-003).

## D. Register of Charges (directly entered)
1. Secretary creates `govoo.register.charge` on creation/registration of a security interest:
   `chargee_partner_id`, `amount`, dates, `property_description`, `charge_document_id`.
2. On satisfaction, Secretary sets `satisfied = True` — the record is **never deleted**
   (BR-SEC-STAT-004); it remains visible on the printed register, marked satisfied.

## Validation
- Per-register field validation as listed in `data-model/constraints.md` §1.
- `govoo.register.entry` write-once enforcement (FR-SEC-005).

## Database changes
- Create/update on the relevant register model; a `govoo.register.entry` row for every change.

## Notifications
- `[RECOMMENDED]` notify Secretary/Admin of beneficial-ownership register changes given their
  sensitivity; no notification requirement stated explicitly in source beyond general
  `mail.thread` behavior.

## Documents generated
- Printable register extracts (QWeb) per register type; evidence/charge documents as attached.

## Audit events
- `mail.thread` on each register record; `govoo.register.entry` ledger (the primary audit
  mechanism for this subsystem).

## Portal behavior
- Director Portal: own director-register entry, read-only.
- Shareholder Portal: own member-register entry, read-only.
- Beneficial-ownership and charges registers are **not** portal-exposed (Secretary/Admin/Auditor
  only, per `security/access-control.md` §2).

## Failure scenarios
- Attempt to edit/delete an existing `govoo.register.entry` → rejected for every group, including
  Board Administrator (AC-08).

## Completion criteria
- All four registers accurately reflect current source data; every change has a corresponding
  ledger entry.

## Acceptance criteria
- See AC-03, AC-08 in `requirements/acceptance-criteria.md`.
