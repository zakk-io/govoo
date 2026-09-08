# Security Tests

Source: §6, §10.2 of the source spec. Maps to `security/` specs and acceptance scenarios AC-05
through AC-08 in `requirements/acceptance-criteria.md`.

| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-SEC-001 | Fresh install; inspect `res.groups` | All six groups from `security/access-control.md` §1 exist with the specified XML IDs |
| TC-SEC-002 | User with access only to Company X attempts to read/list a Company Y record on every model in `data-model/entities.md` | Denied for every model (cross-company isolation, BR-SEC-001) |
| TC-SEC-002b | User with access only to Company X attempts to navigate directly by ID/URL to a Company Y record | Denied, not merely absent from lists (portal and backend) |
| TC-SEC-003 | Governance User (non-Secretary/Admin) reads a partner with `govoo_national_id`/`govoo_date_of_birth` set | Fields not present in the result (field-level restriction, BR-SEC-003) |
| TC-SEC-004 | Board Administrator (no director/shareholder appointment) attempts to create a `govoo.vote` on any resolution | Denied regardless of configuration privileges (BR-SEC-004) |
| TC-SEC-005 | Director Portal user belonging only to Committee A attempts to open a Committee B meeting by direct portal URL (guessed/reused ID) | Denied at record-rule/token level, not merely hidden from menu (BR-SEC-006, AC-07) |
| TC-SEC-005b | Shareholder Portal user attempts to read another shareholder's `govoo.share.holding` row | Denied |
| TC-SEC-006 | Any user, including Board Administrator, attempts `write()`/`unlink()` on an existing `govoo.register.entry` | Rejected in all cases (AC-08) |
| TC-SEC-007 | Auditor group user attempts any `create`/`write`/`unlink` on any governance model | Denied at the access-rights layer (global read, no write) |
| TC-SEC-008 | Non-Secretary/Admin participant of an evaluation campaign reads another participant's raw `survey.user_input` | Denied (AC-10, BR-EVAL-001) |
| TC-SEC-009 | Documents/Sign/Dashboards not installed (Community); a workflow using them runs | Completes via Community fallback without an unhandled error, and without exposing any elevated access as a side effect of the fallback path (AC-09) |

## Non-functional security checks (tracked, not automated in the same suite)
- Penetration test scheduled before go-live, explicitly scoped to include portal record-rule/token
  bypass attempts (`security/portal-security.md` §5) — tracked in `devops/environments.md`, not a
  `TC-*` unit test.
- MFA/SSO configuration verified per environment (`devops/environments.md`).
