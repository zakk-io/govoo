# Workflow: Committees

Source: §7.1.4. Requirement: FR-BASE-004. Model: `govoo.committee`.

## Actor
Company Secretary, Board Administrator.

## Trigger
A board or sub-committee is established, restructured, or its chair/terms of reference change.

## Steps
1. Secretary/Admin creates a `govoo.committee`: `name`, `company_id`, optionally
   `parent_committee_id` (leave unset for the main board; set for sub-committees, e.g. Audit
   Committee under the Board).
2. System validates no cycle is introduced and that `parent_committee_id.company_id ==
   company_id`.
3. `chair_partner_id` is set (should correspond to a partner with an active `govoo.appointment` at
   this committee, though this is not enforced as a hard constraint by the source — `[ENGINEERING
   DETAIL]` consider a soft warning if the chair has no active appointment record).
4. Membership is managed via `govoo.appointment` records referencing this `committee_id`
   (FR-BASE-003) — not by editing a `member_ids` field directly on the committee (it is a resolved
   read of appointments, per module boundary rule in `modules/govoo_base.md`).
5. Optionally attach `terms_of_reference_id` (feature-flagged document).

## Validation
- No cycles in `parent_committee_id` chain; same-company constraint (BR-BASE-004).

## Database changes
- Insert/update on `govoo.committee`.

## Notifications
- `mail.thread` message; `[RECOMMENDED]` notify newly added members.

## Documents generated
- Terms of reference document (feature-flagged).

## Audit events
- `mail.thread` entry on the committee record; membership changes are audited via the underlying
  `govoo.appointment` records' own audit trail (FR-BASE-003), not duplicated here.

## Portal behavior
- Director Portal users see committees they belong to (via the `govoo.meeting` record rule chain in
  `security/record-rules.md` §2) — the committee record itself is not necessarily directly portal-
  browsable; meetings/packs are the portal-facing surface.

## Failure scenarios
- Cyclical `parent_committee_id` → `ValidationError`.
- Cross-company `parent_committee_id` → `ValidationError`.

## Completion criteria
- Committee exists; `member_ids` resolves correctly from appointments; hierarchy (if any) is
  well-formed.

## Acceptance criteria
- *Given* a committee with three active appointments referencing it, *when* the committee form is
  opened, *then* all three members are listed (FR-BASE-004 acceptance criterion).
