# Backup & Recovery

Source: §10.4 of the source spec (verbatim, near-total content of this section).

## 1. Requirements
- Backups must be stored in Rwanda (or an NCSA-authorized location), encrypted, matching the
  production data-residency constraint (`devops/environments.md` §1, `security/privacy.md` §1).
- **A backup is only valid if a restore has been tested** (BR-NFR-002) — an untested backup is not
  considered a compliant backup for the purposes of this system's DR posture.
- RPO (Recovery Point Objective) and RTO (Recovery Time Objective) are `[CONFIRM]` per tier — the
  source does not specify numeric targets; these must be agreed with the client/sponsor before
  go-live (source §13 item 8).

## 2. Backup cadence (`[RECOMMENDED]`, pending RPO confirmation)
- Until an RPO is confirmed, default to a conservative daily full backup + continuous WAL archiving
  (PostgreSQL) as a placeholder posture — **do not treat this default as the confirmed RPO/RTO**;
  update this file once `decisions/open-decisions.md` item 8 is resolved.

## 3. Restore testing
- Schedule periodic restore drills (`[RECOMMENDED]` quarterly, pending client agreement) that
  restore a backup to an isolated environment and verify data integrity — this is the mechanism
  that makes BR-NFR-002 verifiable, not just aspirational.
- Record each restore test's outcome (date, backup tested, success/failure, time taken) as an input
  to confirming/adjusting the RTO once real numbers are available.

## 4. Relationship to retention/disposal (`govoo_rw`)
Backups containing personal data are in scope for the same retention/erasure reconciliation as live
data (`data-model/constraints.md` §3, FR-RW-002/BR-RW-003) — a data-subject erasure request or the
end of a statutory retention period has implications for backup handling that must be addressed in
the DPIA (`security/privacy.md` §2), not just in the live database.
