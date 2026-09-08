# Environments

Source: §10.1, §10.2, §10.4 of the source spec.

## 1. Environment tiers
| Tier | Purpose | Data | Hosting constraint |
| --- | --- | --- | --- |
| Dev | Local/individual development | Synthetic only | No constraint (any host) |
| Staging | Pre-production validation, QA, UAT | Synthetic/anonymized only | May use Odoo.sh or any host, **provided no real personal data is loaded** |
| Production | Live client data | Real personal data | **Must be hosted in Rwanda or an NCSA-authorized location** `[CONFIRM exact wording/process with NCSA/counsel]`, including backups, encrypted at rest |

This maps directly to BR-NFR-001 in `requirements/business-rules.md` and `security/privacy.md` §1.

## 2. Data residency verification (`[RECOMMENDED]` process, since source states the constraint but
not the verification mechanism)
- Before any real personal data is loaded into an environment, confirm and document the physical
  hosting location and its NCSA-authorization status in `decisions/confirmed-decisions.md`.
- Add an automated check (`[RECOMMENDED]`) that fails deployment to an unverified host if a
  "production data" flag is set for that environment.

## 3. Access & authentication (source §10.2)
- MFA/SSO (OAuth2/SAML/LDAP) for internal users.
- Access tokens for portal users (standard `portal.mixin` mechanism, see
  `security/portal-security.md`).
- Encryption in transit (TLS) and at rest (database + backups) for every environment holding real
  data.

## 4. Pre-go-live checklist (source §10.2, §10.3)
- Penetration test completed and findings remediated.
- DPIA completed (source §10.3).
- Processor DPA signed between vendor and client.
- Breach-notification workflow defined and owners assigned.
- NCSA controller registration + DPP certificate obtained (source §10.1).

## 5. Environment promotion
- Standard dev → staging → production promotion via the CI/CD pipeline (`devops/ci-cd.md`); no
  direct production hotfixes outside a reviewed, tested change (`devops/deployment.md`).
