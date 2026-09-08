# Workflow: Appointments

Source: §7.1.3. Requirement: FR-BASE-003. Model: `govoo.appointment`.

## Actor
Company Secretary (primary); Board Administrator (configuration only, not typical day-to-day use).

## Trigger
A person is appointed to a role (director, secretary, chair, MD, committee member) at a company, or
an existing appointment ends (resignation).

## Steps
1. Secretary creates a `govoo.appointment` record: selects `partner_id` (creating a new
   `res.partner` first if the person is not yet in the system), `company_id`, `role`, optionally
   `committee_id`, and `date_appointed`.
2. System computes `state = 'active'` (since `date_resigned` is unset).
3. If the appointment implies a role flag on the partner not yet set (e.g. `role = 'director'` but
   `res.partner.govoo_is_director = False`), the Secretary is prompted to also set the corresponding
   flag `[ENGINEERING DETAIL — automatic flag-sync on appointment save is a UX nicety, not stated in
   source; decide whether to automate or merely prompt]`.
4. On resignation: Secretary sets `date_resigned`. System validates `date_resigned >= date_appointed`
   and recomputes `state = 'resigned'`.
5. If the appointment references a `committee_id`, the committee's resolved `member_ids` view
   (FR-BASE-004) immediately reflects the change (no separate save needed on the committee record).

## Validation
- `date_resigned >= date_appointed` (BR-BASE-003 context; hard constraint, see
  `data-model/constraints.md`).
- `date_appointed` required.

## Database changes
- Insert/update on `govoo.appointment`.
- Downstream: `govoo.register.director` (FR-SEC-001) reflects the change as a curated view;
  `govoo.register.entry` (FR-SEC-005) records a `create`/`update`/`cease` ledger entry.

## Notifications
- `mail.thread` message on the appointment record; `[RECOMMENDED]` notify the appointee (if they
  have portal access) and the company's Board Administrator group on new appointment or
  resignation.

## Documents generated
- Optional `appointment_document_id` (feature-flagged, Documents/Enterprise) — e.g. a signed letter
  of appointment.

## Audit events
- `mail.thread` entry; `govoo.register.entry` entry (via `govoo_secretarial`'s register-of-directors
  logic, FR-SEC-005).

## Portal behavior
- The appointee, if a Director Portal user, can read their own appointment particulars (record
  rule: `partner_id = user.partner_id`), but cannot edit them.

## Failure scenarios
- Invalid date ordering → `ValidationError`, record not saved.
- Attempt to set `committee_id` to a committee in a different company than `company_id` →
  `ValidationError` (consistency with BR-BASE-004).

## Completion criteria
- Appointment record exists with correct computed `state`; register-of-directors reflects it;
  register-entry ledger has a corresponding entry.

## Acceptance criteria (see also FR-BASE-003)
- *Given* an appointment with `date_appointed` in the past and no `date_resigned`, *when* read,
  *then* `state = 'active'`.
- *Given* `date_resigned` set to a past date, *when* recomputed, *then* `state = 'resigned'` and the
  register of directors shows the person as ceased as of that date.
