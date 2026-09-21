# Module Checklists (Definition of Done)

Source: §11 of the source spec (Definition of Done, 10 criteria, restated below verbatim) applied
per module. A module is not "complete" until every applicable box is checked.

## History and honesty note (added 2026-09-15, issue #55)

Every module below was originally marked "✅ VERIFIED 2026-09-08" with all 10 criteria checked.
That sign-off was **not backed by an actual test run against the real implementation** — a
subsequent spec-vs-code audit (Phase 1, issues #32–#87) and the fix pass that followed (Phase 2,
52 merged PRs, `master` as of `ff7ac67f`) found and fixed roughly 30 real bugs across exactly these
"verified" modules, including several genuine security gaps (issue #110: an internal-user
confidentiality bypass in `govoo_evaluation`; issue #67/#68: multi-company and access-control
holes) and functional breakage (issue #12–#31 from an earlier pass: the entire Portal module was
non-functional). A document whose checkmarks don't reflect a real test run is worse than no
document — it manufactures false confidence.

This file is corrected below using **actual test runs performed on 2026-09-15** (command and
result cited per module, so it's independently reproducible — re-run the same command against
`master` at any later commit to re-verify). It intentionally does **not** re-list specific `TC-*`
test-case IDs per criterion the way the original did: several of those IDs were themselves found
mislabeled or aspirational during Phase 2 (e.g. issue #64 — `TC-RW-004` had been misassigned to a
test file that had nothing to do with it). The actual, current test-case catalogue lives in
`docs/spec/testing/unit-tests.md`, which is kept in sync with real test files as part of the normal
PR process — that is the source of truth for "does test case X exist and what does it check",
not this file.

**There is no CI system in this repository as of this writing.** These test runs are a manual,
one-time snapshot, not a continuously-enforced guarantee. Treat "✅" below as "passed when last
run on the stated date", not as a permanent property of the module. The next person to change a
"verified" module's code is responsible for re-running its suite before claiming it still holds.

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

### govoo_base — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_base,govoo_board --test-tags /govoo_base` (installed with `govoo_board` — see the
test-isolation caveat below) → **0 failed, 0 errors** (part of a 197-test combined run across 7
modules, 196 passing; the module's own reported count was 76 sub-tests).
- Criteria 1–4, 6, 9 are exercised directly by that suite (models, views load without error,
  access-control tests including the res.partner PII/access-matrix work from issues #34/#67/#70,
  `mail.thread` tracking tests, multi-company isolation tests).
- Criterion 5: N/A (no reports owned by this module).
- Criterion 7: `.pot`/`fr.po`/`rw.po` stubs present (not independently re-verified on 2026-09-15;
  carried over from the original 2026-09-08 note).
- Criterion 8: N/A (no legal/tax values in this module).
- Criterion 10: covered by `test_feature_flags.py`/`test_community_fallback.py`-style tests added
  across the govoo_base/govoo_board modules during Phase 2 (issue #47).
- **Known gap, not a regression:** issue #143 — this module's own test suite crashes with a
  `KeyError` if run in isolation *without* `govoo_board` also installed, because a stat-button
  compute unconditionally references `govoo.meeting` (a `govoo_board` model). Low priority: in
  every real deployment both modules are installed together, but it means "run govoo_base's tests
  alone" is not currently a safe thing to do — remember this the next time you're tempted to.

### govoo_secretarial — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_secretarial --test-tags /govoo_secretarial` → **0 failed, 0 errors**, 26 sub-tests
(part of the same 2026-09-15 combined run).
- Register models, views, access rules (including the beneficial-owner/register-entry access
  fixes from issues #67/#73/#77/#78), `mail.thread` on the four register models, and
  company-scoped isolation are all exercised by that suite.
- Criterion 5 (printable register extracts): not covered by an automated render test as of this
  writing — carried over as an open gap, not re-claimed as verified.
- Criterion 8: `nature_of_control` thresholds remain `[CONFIRM]`-marked data, not hard fact.

### govoo_shares — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_shares --test-tags /govoo_shares` → **0 failed, 0 errors**, 49 sub-tests.
- Models, holdings computation, allotment/transfer lifecycle, share-class access (issue #86's
  voting-eligibility fix), and multi-company isolation are covered.
- Criterion 5 (cap-table snapshot report): not covered by an automated render test as of this
  writing.

### govoo_board — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_board --test-tags /govoo_board` (in isolation) → **0 failed, 0 errors**, 68
sub-tests.
- Meeting/minutes/resolution/vote/board-pack models, views, statusbars, access rules (Director
  Portal committee-scoping, Board Admin vote-create exclusion — issues #34/#57/#75), quorum and
  majority-threshold tally logic (issues #69/#82/#83/#85), and the e-signature legal-validity
  gate (issue #33) are all covered.
- Criterion 5: `report_minutes`, `report_resolution_summary`, and `report_board_pack` now all
  actually render (issue #121 fixed a QWeb bug that had silently broken PDF generation for the
  first two since they were written — this file's 2026-09-08 claim that they "render correctly"
  was false at the time it was made).
- Criterion 10: Documents/Sign Community fallback covered by `test_community_fallback.py`.

### govoo_compliance — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_compliance --test-tags /govoo_compliance` → **0 failed, 0 errors**, 24 sub-tests.
- Obligation/instance models, cron, views, access rules, and company scoping are covered.
- Criterion 5 (filing-pack export): the same QWeb `t-set="o"` bug as govoo_board affected this
  report too — already fixed inline during issue #53's work, and now actually exercised by a
  render test.

### govoo_rw — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_rw --test-tags /govoo_rw` → **0 failed, 0 errors**, 26 sub-tests.
- Retention config, disposal cron (issues #39/#40/#41/#42/#81), currency config (issue #38), CMA
  governance checklist (issue #44), and the settings page (issues #43/#136 — `set_values()`
  previously crashed unconditionally on save; this is now covered end-to-end by
  `test_default_date_format_applies_to_res_lang`) are all covered.
- Criterion 8: no hard-coded rate/date/threshold confirmed via inspection during Phase 2; not
  re-verified by an automated lint/grep check as of this writing (the original claim that a
  "grep/lint check" exists was not backed by an actual CI step — none exists in this repo).

### govoo_evaluation — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_evaluation --test-tags /govoo_evaluation` → **0 failed, 0 errors**, 14 sub-tests.
- Campaign/result models, aggregation on close, and access rules are covered.
- Criterion 3: **this is the module where the original "VERIFIED" claim was most clearly wrong.**
  The 2026-09-08 sign-off asserted "`survey.user_input` confidentiality restriction ... passes",
  but issue #110 (found 2026-09-15) showed the restriction was silently bypassed for any internal
  user who also held `survey.group_survey_user` — a real, exploitable confidentiality hole in a
  governance product, not a cosmetic gap. Fixed in PR #144, with a regression test using the
  actual internal-user fixture that was previously affected by the bypass (not just a portal user
  that was never at risk).

### Portal + Dashboard — ✅ test suite passing as of 2026-09-15
Run: `-i govoo_portal --test-tags /govoo_portal` → **0 failed, 0 errors**, 9 sub-tests (HttpCase —
exercises real HTTP/controller behavior, not just ORM domain filtering).
- Portal routes, record-rule/access-token enforcement, and the vote-casting workflow are covered.
- **Known gap, not a regression:** issue #111 — `TestPortal`'s original `setUpClass` (superseded
  by the current HttpCase-based suite, but left as a cautionary note) created portal users via a
  group-less `create()` followed by a `write()` adding the portal group, which fails Odoo's
  disjoint-groups check in this version. Fixed pattern (`new_test_user(..., groups=...)`, group
  set atomically at creation) is what the current suite uses.

### govoo_contracts (addendum, Phase 2b) — not started
- [ ] 1-10, same discipline as every other module. **Not started** — the spec (`modules/govoo_contracts.md`, `workflows/contracts.md`) exists as of this addendum pass; no code, migration, or test run exists yet, so no criterion here may be checked based on the spec alone. Per this file's own 2026-09-15 history note, a checkmark not backed by an actual test run is worse than no checkmark — this entry deliberately stays all-unchecked until a real `-i govoo_contracts --test-tags /govoo_contracts` run is cited with a date and result, the same way every other module above is documented.
- [ ] 3, 9 (security, multi-company): particular attention needed for the three new groups (Contract Manager, Contract Approver, Contract Viewer Portal) and the record rule in `security/record-rules.md` §6b — this is new access-control surface, exactly the category of change that produced the confidentiality/isolation bugs (issues #67/#68/#110) found in the 2026-09-15 audit of other modules.
- [ ] 8 (no hard-coded legal/tax value): contract board-approval thresholds, delegation-of-authority limits, and `govoo.contract.type.retention_years` must all be configurable data, never a Python literal (BR-CM-001, BR-CM-002, FR-CM-18) — include `govoo_contracts` in the CI hard-coded-value lint check recommended in `data-model/constraints.md` §3 and `devops/ci-cd.md` §1 step 6 once that check exists (it does not exist yet for any module, per this file's own note that "there is no CI system in this repository as of this writing").
- [ ] 10 (Enterprise/Community degradation): Sign (contract e-signature) and Documents (generated/executed contract storage) fallbacks must be covered by the same style of `test_community_fallback.py` test used for `govoo_board`.
- CM-F15 (financial linkage) and CM-F19/CM-F20 (AI extraction/summarization) are `[OPTIONAL]`/out of scope for this module's own DoD — their absence must not block marking `govoo_contracts` itself Done, per `modules/govoo_contracts.md`'s "Out of scope for this module" section.

### govoo_rw_accounting / govoo_rw_ebm (optional, Phase 5)
- [ ] 1-7, 9-10 as applicable, same discipline as every other module.
- [ ] 8. **Critical, same as `govoo_rw`:** no hard-coded tax rate/chart-of-accounts value without a
      documented advisor confirmation; CI boundary check (`devops/ci-cd.md` §1 step 5) confirms the
      governance core installs/passes without these two modules. Not started (Phase 5, out of
      current scope).
