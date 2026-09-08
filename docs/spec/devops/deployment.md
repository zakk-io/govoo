# Deployment

Source: §10.1 (hosting), §10.4 (backup/recovery) of the source spec, plus general Odoo deployment
practice `[ENGINEERING DETAIL]` where the source is silent.

## 1. Deployment target
- Single Odoo instance per tenant (or per client, depending on the commercial model
  `[CONFIRM — source does not specify single-tenant-per-client vs. one shared instance serving a
  corporate-services firm's many client companies via multi-company; §6.2's "administers many
  client entities in one DB" implies the latter is at least supported]`).
- Production hosting location constrained per `devops/environments.md` §1 (Rwanda /
  NCSA-authorized).

## 2. Deployment process (`[RECOMMENDED]`, standard Odoo practice)
1. Build artifact (module set at a pinned version) produced by CI (`devops/ci-cd.md`).
2. Deploy to staging; run the full acceptance suite (`testing/acceptance-tests.md`) against
   staging with synthetic data.
3. Manual sign-off (UAT) before promotion to production.
4. Deploy to production during a defined maintenance window; run smoke tests
   (a minimal subset of `TC-ACC-*` against production, read-only where possible).
5. Rollback plan: retain the previous module version and a pre-deployment database backup
   (see `devops/backup-recovery.md`) so a failed deployment can be reverted.

## 3. Configuration management
- Environment-specific configuration (feature flags for Enterprise/Community, data-residency
  confirmation, `govoo_rw` obligation-template activation state) is tracked per environment — a
  template activated in staging for testing purposes is **not** automatically activated in
  production; production activation requires the documented advisor confirmation described in
  `data-model/constraints.md` §3.

## 4. Secrets management
- No credentials (Sign/EBM integration keys, SMTP, etc.) in source control — environment variables
  or a secrets manager, per `security/privacy.md` §5.
