# Acceptance Tests

Source: business-level scenarios consolidated from §7 and the master prompt's acceptance-criteria
instruction. Each row maps 1:1 to a scenario in `requirements/acceptance-criteria.md` — this file
gives each one a stable `TC-*` ID and states the expected result explicitly, so it can be tracked
in `implementation/module-checklists.md` and `requirements/traceability.md`.

| Test ID | Acceptance scenario | Maps to | Expected result |
| --- | --- | --- | --- |
| TC-ACC-001 | Board-meeting-to-minutes end-to-end | AC-01 | Quorum computed correctly; resolution passes/fails correctly per tally; minutes reach approved/signed; retention set |
| TC-ACC-002 | Cap table integrity across allotment and transfer | AC-02 | Final holdings and percentages correct; register of members updated |
| TC-ACC-003 | Beneficial ownership register remains provisional until confirmed | AC-03 | No specific percentage threshold presented as authoritative before confirmation |
| TC-ACC-004 | Compliance instance generation respects unconfirmed deadlines | AC-04 | No instance from an unconfirmed (`active=False`) template; correct generation once activated |
| TC-ACC-005 | Multi-company isolation holds across every governance model | AC-05 | Access denied cross-company on every model, including via portal token misuse |
| TC-ACC-006 | Separation of duties holds for voting | AC-06 | Board Administrator cannot cast a vote under any configuration |
| TC-ACC-007 | Portal record-rule enforcement, not menu-hiding | AC-07 | Direct-URL access outside scope denied |
| TC-ACC-008 | Register append-only ledger cannot be altered | AC-08 | No group, including Board Administrator, can edit/delete an existing ledger entry |
| TC-ACC-009 | Enterprise feature graceful degradation | AC-09 | Workflows complete on Community without unhandled errors |
| TC-ACC-010 | Evaluation confidentiality holds under aggregation | AC-10 | Only aggregates visible to non-authorized participants |
| TC-ACC-011 | Contract approval respects board-approval and delegation-of-authority gates | AC-11 | Contract cannot reach `approved` without a linked passed resolution (where required) or via an under-authorized approver |
| TC-ACC-012 | Contract Viewer Portal isolation and write-once executed documents | AC-12 | Non-party portal access denied by direct URL; executed document cannot be edited/deleted by any group |

## How acceptance tests differ from workflow tests
`testing/workflow-tests.md` (`TC-WF-*`) exercises the mechanics of a single workflow in detail
(every intermediate state). This file's tests (`TC-ACC-*`) are the business-readable, end-to-end
scenarios a non-technical stakeholder (or the source spec's own "Definition of Done" reviewer) would
recognize as proof the system does what was asked. Where they overlap (e.g. TC-ACC-001 and
TC-WF-BOARD-001..004 both touch the meeting-to-minutes flow), the acceptance test may be
implemented as a thin composition that calls the same underlying fixtures/helpers as the workflow
tests, rather than being duplicated from scratch.

## Running acceptance tests
`[RECOMMENDED]` run the full `TC-ACC-*` suite as a required CI gate before any module is marked
Done in `implementation/module-checklists.md`, since these are the tests most directly traceable to
"does this satisfy the source specification."
