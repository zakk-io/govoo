# Workflow: Compliance

Source: §7.5 (compliance lifecycle summary in the master prompt). Requirements: FR-COMP-001..004,
FR-RW-002, FR-RW-003. Models: `govoo.compliance.obligation`, `govoo.compliance.instance`.

## Actor
System (`ir.cron`, instance generation + reminders); Company Secretary / responsible user (track,
file); Board Administrator (waive, configure catalogue).

## Lifecycle
```
obligation definition -> instance generation -> reminders -> filing -> acknowledgement -> completion
                                                                                          -> or overdue -> escalation
```

## Steps

### A. Obligation definition (one-time / infrequent, config-level)
1. Secretary/Admin defines or activates a `govoo.compliance.obligation`: `name`, `authority`,
   `frequency`, `basis`, `lead_time_days`, `applies_to_entity_type`.
2. If seeded from `govoo_rw`'s provisional Rwanda templates, `active = False` until a documented
   advisor confirmation is recorded (`decisions/confirmed-decisions.md`) and an administrator
   explicitly activates it (BR-COMP-001).

### B. Instance generation (recurring, cron-driven)
1. Daily (`[RECOMMENDED]` cadence) `ir.cron` run: for each active obligation and each company where
   it applies, compute whether a new `govoo.compliance.instance` is due to be generated for the
   current period.
2. Compute `due_date` per `basis`:
   - `fixed_date`: from the obligation's fixed calendar rule.
   - `fye_relative`: requires `res.company.govoo_financial_year_end` to be set — if missing, no
     instance is generated for that company this run (logged, not silently skipped without trace).
   - `event_relative`: triggered by an external event record (e.g. a resolution passing that
     creates a filing need) rather than the calendar cron — `[ENGINEERING DETAIL — exact
     event-trigger wiring not specified in source]`.
3. Create `govoo.compliance.instance` (`state = 'upcoming'`) if one does not already exist for
   `(obligation_id, company_id, period)`.

### C. Reminders (cron-driven, staged)
1. For each `upcoming`/`in_progress` instance, create staged `mail.activity` reminders at the
   obligation's configured lead-time offsets (e.g. -30/-7/-1 days) for `responsible_id`.
2. If `due_date` has passed and `state` is not `filed`/`waived`, transition to `late` and trigger
   escalation (BR-COMP-003) — escalation recipient `[CONFIRM]`.

### D. Filing
1. Responsible user transitions `upcoming/in_progress → in_progress` when starting work (if not
   already there).
2. User requests a filing pack (`action_generate_filing_pack()`), which assembles filing-ready
   documents from already-modeled register/compliance data — **no assumption of an automated
   RDB/Irembo submission API** (`[CONFIRM]`, BR-COMP-004).
3. User manually submits via the relevant government portal, then records `reference_no` and
   `filed_date` on the instance, transitioning to `filed`.

### E. Acknowledgement / completion, or overdue / escalation
- `filed`: terminal, successful path.
- `late → filed`: late but eventually completed.
- Any non-terminal state `→ waived`: Secretary/Admin marks not applicable this period.

## Validation
- No duplicate instance for `(obligation_id, company_id, period)`.
- `due_date` never a hard-coded literal — computed from configuration (BR-COMP-002).

## Database changes
- `govoo.compliance.instance` create/update; `mail.activity` creation for reminders.

## Notifications
- Staged reminder activities; escalation notification on `late`.

## Documents generated
- Filing-pack export bundle; stored acknowledgement reference.

## Audit events
- `mail.thread`; `tracking=True` on `state`.

## Portal behavior
- Not portal-exposed per the source's role definitions (internal-only workflow).

## Failure scenarios
- Missing FYE config → no instance generated for that company, logged (fail closed, FR-BASE-002
  acceptance criterion).
- Cron failure → must be logged/retried per standard `ir.cron` behavior; a missed run should not
  silently skip a reminder window without a catch-up mechanism `[RECOMMENDED]`.

## Completion criteria
- Instance reaches `filed` (on time or late) or `waived`.

## Acceptance criteria
- See AC-04 in `requirements/acceptance-criteria.md`.
