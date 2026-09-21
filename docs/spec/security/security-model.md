# Security Model — Overview

Source: §6 of the source spec ("Security Model (applies to every module)"). This is the top-level
security narrative; see `access-control.md` for the group/model access matrix,
`record-rules.md` for the record-rule specifications, `portal-security.md` for portal-specific
controls, and `privacy.md` for data-protection requirements.

## 1. Principles (source §6.2, restated as MUST rules)
1. **Multi-company:** every transactional model has `company_id` (with `check_company=True`) and
   standard multi-company record rules. A corporate-services firm administers many client entities
   in one database with **strict isolation**. See `access-control.md` §2, `record-rules.md` §1.
2. **Record rules (need-to-know):**
   - Director portal user sees only meetings/packs of committees they belong to.
   - Shareholder sees only their own `govoo.share.holding` and shareholder resolutions.
   - Auditor group: global read, no write.
   - Contract Viewer Portal sees only contracts where they are the counterparty or a named
     approver (`govoo_contracts` addendum, §4).
   See `record-rules.md` §2-4, §6b.
3. **Field-level:** sensitive PII (national ID, date of birth) restricted to Secretary/Admin
   groups. See `access-control.md` §4.
4. **Separation of duties:** Secretary/Admin prepare; Directors approve/vote/sign; Admins cannot
   vote. See `access-control.md` §5.
5. **Audit:** every transactional model inherits `mail.thread` + `mail.activity.mixin`; statutory
   fields use `tracking=True`. See `data-model/entities.md` and each `modules/*.md` file.

## 2. Portal access (source §6.3)
Portal users have no internal licence. Expose records via `portal.mixin`, `_compute_access_url`,
and controllers. **Never expose by URL guessing — use access tokens and the record rules above.**
See `portal-security.md`.

## 3. Security groups (source §6.1)
Six groups, all defined in `govoo_base`, per the source spec. The `govoo_contracts` addendum adds
three more (Contract Manager, Contract Approver, Contract Viewer Portal) — see `access-control.md`
§1 for the full, current group list (nine groups as of this addendum).

## 4. Non-functional security requirements (source §10.2)
- MFA/SSO (OAuth2/SAML/LDAP) for internal users; access tokens for portal.
- Encryption in transit and at rest.
- Penetration test before go-live.
- Immutable audit logs.
- ACL test coverage.
See `devops/environments.md` and `testing/security-tests.md`.

## 5. What "security by default" means in practice for an implementer
No PR that adds a model may merge without, in the same PR:
- an `ir.model.access.csv` row for every relevant group (see `access-control.md`),
- a record rule if the model holds per-company or need-to-know data (see `record-rules.md`),
- `mail.thread` inheritance and `tracking=True` on statutory fields,
- at least one security test proving isolation/restriction where applicable
  (see `testing/security-tests.md`).

This is restated as Definition-of-Done criterion 3 (source §11) and enforced per-module in
`implementation/module-checklists.md`.
