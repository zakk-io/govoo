# Privacy & Data Protection

Source: §10.1, §10.3, §10.5 of the source spec.

## 1. Data residency (hard constraint, source §10.1)
- Rwanda's data-protection law requires personal data to be stored in Rwanda unless cross-border
  authorization is obtained. `[CONFIRM exact wording and process with NCSA/counsel]`.
- Every environment holding real personal data — **including backups** — must be hosted in Rwanda
  and encrypted at rest.
- Build/staging may use Odoo.sh (or any non-Rwanda host) **only with synthetic/anonymized data**.
  Production for real data runs in-country (or an NCSA-authorized location). The PO must confirm a
  compliant in-country host exists before real data is loaded anywhere.
- Register the controller with NCSA and obtain the DPP (data protection & privacy) certificate;
  assign responsibility for this between client and vendor.
- See `devops/environments.md` for how this constraint maps onto dev/staging/production.

## 2. Data protection workflow (source §10.3)
- **DPIA** (Data Protection Impact Assessment) required before go-live with real personal data.
- **Processor DPA** (Data Processing Agreement) between vendor and client.
- **Breach-notification workflow** — defined process, owners, and timelines for notifying affected
  parties/regulators.
- **Retention/disposal engine** reconciling the 10-year statutory retention (source §8.2, FR-RW-002)
  with data-subject erasure rights — the disposal job must check for legal holds or open erasure
  requests before deleting a record whose retention period has technically elapsed
  (BR-RW-003) `[CONFIRM exact reconciliation process with legal/DPO]`.

## 3. KYC/CDD (source §10.5)
- Capture identity/CDD (Customer Due Diligence) data on directors, shareholders, and beneficial
  owners **at onboarding**. This overlaps with, but is a distinct requirement from, the PII fields
  on `res.partner` (FR-BASE-001) and the beneficial-ownership register (FR-SEC-003) —
  `[ENGINEERING DETAIL]` confirm whether CDD capture is a checklist/workflow on top of existing PII
  fields or requires additional fields not itemized in §7; source does not give a field-level CDD
  spec.

## 4. Sensitive data inventory (for DPIA scoping — derived, not exhaustive in source)
| Category | Fields/models | Sensitivity |
| --- | --- | --- |
| National identity | `res.partner.govoo_national_id` | High |
| Date of birth | `res.partner.govoo_date_of_birth` | High |
| Nationality | `res.partner.govoo_nationality_id` | Medium |
| Beneficial ownership control data | `govoo.register.beneficial.owner.*` | High |
| Financial (allotment/transfer pricing, charge amounts) | `govoo.share.allotment.price_per_share`, `govoo.share.transfer.price`, `govoo.register.charge.amount` | Medium |
| Board evaluation individual responses | `survey.user_input` (tied to `govoo.evaluation.campaign`) | High (confidentiality-critical, BR-EVAL-001) |
| Meeting minutes content | `govoo.minutes.body` | Medium-High (may contain sensitive deliberations) |

## 5. What implementers must NOT do
- Log PII fields (national ID, date of birth) in plaintext application logs.
- Include PII in error messages surfaced to non-authorized users.
- Store EBM/VSDC or any third-party integration credentials in code or version control — use
  Odoo's standard secrets/config-parameter mechanisms, environment variables, or a secrets manager
  per `devops/environments.md`.
- Treat "the record rule hides it from the UI" as sufficient for a DPIA — the DPIA must assess
  actual data flows, including exports, reports, and backups, not just screen visibility.
