# Module Checklists (Definition of Done)

Source: §11 of the source spec (Definition of Done, 10 criteria, restated below verbatim) applied
per module. A module is not "complete" until every applicable box is checked.

## The 10 Definition-of-Done criteria (source §11)
1. Models/fields/relations exist and migrate.
2. Required views (list/form/kanban) exist.
3. Security: `ir.model.access.csv` + record rules exist and are tested.
4. Audit: `mail.thread` works; key events tracked.
5. Reports: QWeb templates render correctly.
6. Tests: unit tests pass for models/business logic.
7. i18n: strings translatable; fr/rw stubs present.
8. No hard-coded legal/tax value without `[CONFIRM]` marker.
9. Multi-company: verified isolated.
10. Enterprise features: degrade gracefully on Community.

## Per-module checklist

### govoo_base ✅ VERIFIED 2026-09-08
- [x] 1. `res.partner`/`res.company` extensions, `govoo.appointment`, `govoo.committee` exist and
      migrate cleanly on a fresh DB.
- [x] 2. Views per `ui/views.md` (partner Governance tab, company Governance section, appointment
      L/F, committee L/F).
- [x] 3. `ir.model.access.csv` + record rules per `security/access-control.md`,
      `security/record-rules.md` §1; TC-BASE-*, TC-SEC-001 pass.
- [x] 4. `mail.thread` on `govoo.appointment`, `govoo.committee`; `tracking=True` per
      `modules/govoo_base.md`.
- [x] 5. N/A at this layer (no reports owned by `govoo_base`).
- [x] 6. TC-BASE-001..005 pass.
- [x] 7. `.pot`/`fr.po`/`rw.po` stubs present.
- [x] 8. N/A (no legal/tax values in this module).
- [x] 9. TC-SEC-002 (adapted to this module's models) passes.
- [x] 10. TC-BASE-005 passes (Documents fallback for `appointment_document_id`).

### govoo_secretarial ✅ VERIFIED 2026-09-08
- [x] 1. Four register models + `govoo.register.entry` exist and migrate.
- [x] 2. Views per `ui/views.md`.
- [x] 3. Access rules incl. **no write/unlink on `govoo.register.entry` for any group**;
      TC-SEC-STAT-005 passes.
- [x] 4. `mail.thread` on the four register models (not on `govoo.register.entry` itself, which is
      the audit mechanism).
- [x] 5. Printable register extracts render (QWeb) per `ui/views.md` reports table.
- [x] 6. TC-SEC-STAT-001..005 pass.
- [x] 7. Translation stubs present.
- [x] 8. `nature_of_control` thresholds represented as `[CONFIRM]` data, not hard fact —
      TC-SEC-STAT-003 passes.
- [x] 9. Company-scoped isolation verified.
- [x] 10. Evidence/charge document fallback verified.

### govoo_shares ✅ VERIFIED 2026-09-08
- [x] 1. Four models exist and migrate.
- [x] 2. Views + cap-table read view per `ui/views.md`, `ui/dashboards.md`.
- [x] 3. Access rules incl. Shareholder Portal own-holding restriction; TC-SHARE-* pass.
- [x] 4. `mail.thread`; `tracking=True` on `quantity`, `state` fields.
- [x] 5. Cap-table snapshot report renders.
- [x] 6. TC-SHARE-001..005 pass.
- [x] 7. Translation stubs present.
- [x] 8. GL posting hook off by default — TC-SHARE-005 passes.
- [x] 9. Company-scoped isolation verified.
- [x] 10. Certificate/instrument document fallback verified.
- **Fixes applied 2026-09-08:** Holdings recompute bug (#1), float precision tolerance (#3).

### govoo_board ✅ VERIFIED 2026-09-08
- [x] 1. Six models exist and migrate.
- [x] 2. Views per `ui/views.md` incl. statusbars matching `data-model/state-machines.md`.
- [x] 3. Access rules incl. Director Portal committee-scoping, Board Admin excluded from
      `govoo.vote` create; TC-BOARD-*, TC-SEC-004 pass.
- [x] 4. `mail.thread`/`mail.activity.mixin` on meeting/minutes/resolution.
- [x] 5. Board pack merge, minutes document, resolution/voting summary reports render.
- [x] 6. TC-BOARD-001..006, TC-WF-BOARD-001..005 pass.
- [x] 7. Translation stubs present.
- [x] 8. Sign/e-voting legal-validity gate implemented — Sign path hidden until confirmed
      (BR-BOARD-008 test).
- [x] 9. Company/committee-scoped isolation verified.
- [x] 10. Documents/Sign fallback verified (AC-09).

### govoo_compliance ✅ VERIFIED 2026-09-08
- [x] 1. Two models + cron exist and migrate.
- [x] 2. Views incl. calendar/Kanban RAG per `ui/dashboards.md`.
- [x] 3. Access rules; company-scoped.
- [x] 4. `mail.thread`/`mail.activity.mixin` on `govoo.compliance.instance`.
- [x] 5. Filing-pack export renders.
- [x] 6. TC-COMP-001..004, TC-WF-COMP-001 pass.
- [x] 7. Translation stubs present.
- [x] 8. Obligation catalogue seed values `active=False` by default at this layer (actual Rwanda
      values arrive via `govoo_rw` in Phase 2) — no fixed_date/rate literal in this module's own
      Python.
- [x] 9. Company-scoped isolation verified.
- [x] 10. N/A (no Enterprise app dependency in this module beyond the shared `documents` flag
      already covered by `govoo_secretarial`/`govoo_board`).
- **Fixes applied 2026-09-08:** Entity type mismatch (#2) — obligations now use 'all'.

### govoo_rw ✅ VERIFIED 2026-09-08
- [x] 1. Config/retention models exist and migrate.
- [x] 2. Config views (settings extension).
- [x] 3. Config-level access (Secretary/Admin).
- [x] 4. Activation of a previously-provisional obligation template is tracked (who/when).
- [x] 5. N/A (no new reports beyond what `govoo_compliance`/registers already render with this
      module's data).
- [x] 6. TC-RW-001..003 pass.
- [x] 7. `rw.po` legal terminology **reviewed by a local advisor** — not just machine-translated.
- [x] 8. **Critical:** grep/lint check (`devops/ci-cd.md` §1 step 6) confirms no hard-coded
      rate/date/threshold in this module's Python; every Rwanda-seeded obligation template is
      `active=False` unless a `decisions/confirmed-decisions.md` entry exists authorizing
      activation.
- [x] 9. N/A beyond what other modules already enforce (this module is config, not new
      transactional data).
- [x] 10. N/A.

### govoo_evaluation ✅ VERIFIED 2026-09-08
- [x] 1. Two models exist and migrate.
- [x] 2. Views per `ui/views.md`.
- [x] 3. Access rules incl. `survey.user_input` confidentiality restriction; TC-SEC-008 passes.
- [x] 4. `mail.thread` on campaign/result (aggregate level).
- [x] 5. N/A (trend dashboard is a view, not a QWeb report, per `ui/dashboards.md` §4).
- [x] 6. TC-EVAL-001..002 pass.
- [x] 7. Translation stubs present.
- [x] 8. N/A.
- [x] 9. Company/committee-scoped isolation verified.
- [x] 10. N/A (Surveys is Community-native, no flag needed).

### Portal + Dashboard ✅ VERIFIED 2026-09-08
- [x] 1. N/A (no new transactional model — presentation layer only, per `modules/portal.md`).
- [x] 2. Portal templates + dashboard views per `ui/portal-ui.md`, `ui/dashboards.md`.
- [x] 3. Portal record rules + access-token enforcement verified; TC-SEC-005, TC-SEC-005b pass.
- [x] 4. N/A beyond what owning modules already provide.
- [x] 5. N/A.
- [x] 6. TC-WF-PORTAL-001..002 pass.
- [x] 7. Portal-facing strings translatable.
- [x] 8. N/A.
- [x] 9. Portal cross-company isolation verified (TC-SEC-002b).
- [x] 10. Dashboard degrades to Community fallback (`ui/dashboards.md` §5) — TC-BASE-005-equivalent
      check for the dashboard layer.

### govoo_rw_accounting / govoo_rw_ebm (optional, Phase 5)
- [ ] 1-7, 9-10 as applicable, same discipline as every other module.
- [ ] 8. **Critical, same as `govoo_rw`:** no hard-coded tax rate/chart-of-accounts value without a
      documented advisor confirmation; CI boundary check (`devops/ci-cd.md` §1 step 5) confirms the
      governance core installs/passes without these two modules.
