# Workflow (End-to-End) Tests

Source: workflow narratives in §7 and the master-prompt "Workflow Specifications" section. These
tests exercise a full lifecycle across states/models within one workflow, as opposed to
`unit-tests.md`'s single-model/method scope.

| Test ID | Workflow | Scenario | Expected result |
| --- | --- | --- | --- |
| TC-WF-BOARD-001 | Meetings (`workflows/meetings.md`) | Meeting created → scheduled → held → minuted → closed, with agenda items and a linked resolution throughout | Every transition succeeds in order; meeting cannot reach `closed` while a linked resolution is still non-terminal |
| TC-WF-BOARD-002 | Board packs (`workflows/board-packs.md`) | Pack compiled for a meeting with one confidential and one non-confidential agenda item, two recipients (one authorized for the confidential item, one not) | Authorized recipient's pack includes both items; unauthorized recipient's pack excludes the confidential item |
| TC-WF-BOARD-003 | Minutes (`workflows/minutes.md`) | Minutes drafted → for_approval → approved, `retention_until` computed | `retention_until` equals creation date + 10 years (from `govoo_rw` config, not a literal) |
| TC-WF-BOARD-004 | Resolutions + voting (`workflows/resolutions.md`, `workflows/voting.md`) | Board resolution opened, 3 directors vote (2 for, 1 against), quorum met, simple majority | `result` computed correctly; `state == 'passed'` |
| TC-WF-BOARD-005 | Resolutions + voting, shareholder | Shareholder resolution opened, votes weighted by `voting_power`, one vote flagged `is_conflicted` | Conflicted vote excluded from tally per applicable rule; result reflects remaining weighted votes |
| TC-WF-SHARE-001 | Share management (`workflows/share-management.md`) | Class created (authorized 1000) → allot 600/400 to two partners → transfer 200 from one to a third partner → register | Final holdings: 400/400/200, percentages sum to 100% |
| TC-WF-SEC-001 | Statutory registers (`workflows/statutory-registers.md`) | Appointment created → resigned; holding created → reduced to zero | Register of Directors and Register of Members both reflect ceased status correctly; ledger entries recorded for both |
| TC-WF-COMP-001 | Compliance (`workflows/compliance.md`) | Obligation activated → cron generates instance → reminders staged → instance goes `late` → filed | State progression correct; reminders created at configured offsets; late escalation fires once, not repeatedly, per overdue instance `[ENGINEERING DETAIL — de-duplication of repeated escalation not specified in source; recommend testing that escalation activity is not duplicated on every cron run for the same instance]` |
| TC-WF-EVAL-001 | Evaluation (`workflows/` — not a dedicated workflow file, covered by FR-EVAL-001/002) | Campaign opened → responses collected → closed → results aggregated | Aggregates correct; individual responses inaccessible to non-authorized participants |
| TC-WF-CM-001 | Contracts (`workflows/contracts.md`) | Contract drafted from template → submitted for approval → board-approval gate check → delegation-of-authority check → related-party check → approved → executed (signed) → active → obligation reminders fire → renewed or terminated | Every transition succeeds in order and only when its gating condition (BR-CM-001..006) is satisfied; a contract failing any gate cannot advance past `in_approval` |

## Portal-inclusive workflow tests (use `HttpCase` or equivalent to exercise the controller layer,
not just the ORM)
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-WF-PORTAL-001 | Director Portal user views their committee's meeting, casts a vote on an eligible resolution | Vote recorded with correct `voter_id`, `weight = 1.0` |
| TC-WF-PORTAL-002 | Shareholder Portal user views own holdings, casts a vote on an eligible shareholder resolution | Vote recorded with `weight` sourced from their `voting_power` |
| TC-WF-PORTAL-003 | Contract Viewer Portal user (named counterparty) views their own contract and its obligations by direct portal URL | Own contract/obligations visible; a different counterparty's contract is denied by direct URL, not merely hidden from the list (BR-CM-007) |
