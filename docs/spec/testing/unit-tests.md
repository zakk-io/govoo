# Unit Tests

Source: §9, §7 (per-model detail) of the source spec. Every test below maps to a requirement
(`FR-*`)/business rule (`BR-*`) in `requirements/`. Expected results are stated explicitly per
source §18 instruction.

## govoo_base
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-BASE-001 | Non-privileged user reads a partner with `govoo_national_id` set | Field not present in the read result |
| TC-BASE-002 | `res.company` saved without `govoo_financial_year_end` | Save succeeds (field optional at this layer); downstream FYE-relative compliance generation is separately tested in TC-COMP-002 |
| TC-BASE-003 | Appointment created with past `date_appointed`, no `date_resigned` | `state == 'active'` |
| TC-BASE-003b | Appointment `date_resigned` set to a past date | `state == 'resigned'` |
| TC-BASE-003c | Appointment `date_resigned` set earlier than `date_appointed` | `ValidationError` raised |
| TC-BASE-004 | Committee with 3 active appointments referencing it | `member_ids` (resolved) contains exactly those 3 |
| TC-BASE-004b | Committee `parent_committee_id` set to create a cycle | `ValidationError` raised |
| TC-BASE-005 | Documents app not installed; a workflow needing `*_document_id` runs | Falls back to `ir.attachment`; no unhandled exception |

## govoo_secretarial
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-SEC-STAT-001 | Appointment resigned | Register of Directors reflects the person as ceased as of `date_resigned` |
| TC-SEC-STAT-002 | Partner's aggregate holding across all classes reaches zero after a transfer | `govoo.register.member.date_ceased` set |
| TC-SEC-STAT-003 | `govoo.register.beneficial.owner` created with unconfirmed `nature_of_control` category | Record flagged provisional in read/report output |
| TC-SEC-STAT-004 | Charge marked `satisfied = True` | Record still present and printable, not deleted |
| TC-SEC-STAT-005 | Any user (incl. Board Administrator) attempts `write()`/`unlink()` on an existing `govoo.register.entry` | Operation rejected for all groups |

## govoo_shares
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-SHARE-001 | Allotment quantity + existing allotments would exceed `total_authorised` | `ValidationError`, record not saved |
| TC-SHARE-002 | Transfer `quantity` exceeds transferor's current holding at registration | `ValidationError` at `approved → registered` transition |
| TC-SHARE-003 | Allotment created | `govoo.share.holding` for `(partner, class)` recomputes correctly |
| TC-SHARE-004 | Allotments to 3 partners, then one transfer registered | Resulting holdings' `percentage` sum to exactly 100% |
| TC-SHARE-005 | Allotment/transfer registered with GL hook not explicitly enabled | No `account.move` created |

## govoo_board
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-BOARD-001 | Meeting with `quorum_required = 3`, 4 confirmed attendees | `quorum_met == True` |
| TC-BOARD-001b | Meeting state transition attempted out of order (e.g. `draft → held`) | Rejected |
| TC-BOARD-002 | 3 agenda items with sequences 1,2,3 | Displayed/ordered 1,2,3 |
| TC-BOARD-003 | Confidential agenda item, recipient not authorized | Pack for that recipient excludes the item's content |
| TC-BOARD-004 | Minutes state transitions `draft → for_approval → approved` | Each transition succeeds in order; skipping is rejected |
| TC-BOARD-005 | Resolution `open` with quorum met and majority achieved | `state == 'passed'`, `result` reflects the tally |
| TC-BOARD-006 | Shareholder resolution vote cast | `weight` sourced from voter's `govoo.share.holding.voting_power`, not hard-coded to 1.0 |
| TC-BOARD-006b | Board Administrator (no appointment) attempts to create a `govoo.vote` | Rejected at access-rights layer |
| TC-BOARD-006c | Vote with `is_conflicted = True` | Excluded from tally where the applicable rule requires exclusion |

## govoo_compliance
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-COMP-001 | Active obligation, `basis = 'fixed_date'`, cron runs | Instance generated with correct `due_date` |
| TC-COMP-002 | Active obligation, `basis = 'fye_relative'`, company has no `govoo_financial_year_end` | No instance generated for that company; logged |
| TC-COMP-003 | Active obligation, `basis = 'fye_relative'`, company has FYE set | Instance generated with `due_date` computed from FYE |
| TC-COMP-004 | Instance `due_date` in the past, `state` not `filed`/`waived`, cron runs | `state` transitions to `late` |

## govoo_rw
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-RW-001 | Fresh `govoo_rw` install | Currency configured RWF, 0 decimals |
| TC-RW-002 | Retention config read for `govoo.minutes` | `retention_until` computed as `create_date` + 10 years |
| TC-RW-003 | Fresh `govoo_rw` install, obligation catalogue inspected | Every Rwanda-seeded template has `active == False` |
| TC-RW-004 | `govoo.rw.governance.checklist.item` created against a CMA governance self-assessment instance | Item persists; status `explain` without an `explanation` is rejected (apply-and-explain, FR-RW-004) |
| TC-RW-005 | Fresh `govoo_rw` install, all five retention categories inspected | Each category (`minutes`, `resolutions`, `accounts`, `auditor_reports`, `board_reports`) has at least one active retention rule |

## govoo_evaluation
| Test ID | Scenario | Expected result |
| --- | --- | --- |
| TC-EVAL-001 | Campaign closed with N responses | `govoo.evaluation.result` aggregates computed correctly |
| TC-EVAL-002 | Non-Secretary/Admin participant reads another participant's `survey.user_input` | Access denied |
| TC-EVAL-003 | Campaign created with empty `participant_ids` | Rejected |
| TC-EVAL-004 | Campaign created with a participant who isn't a committee member (board/committee/peer evaluation types) | Rejected |
