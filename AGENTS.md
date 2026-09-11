# AGENTS.md — Govoo

## What this is

Odoo 19 custom-module project for corporate governance in Rwanda. All 8 core modules have been implemented and verified:
1. `govoo_base` ✅
2. `govoo_secretarial` ✅
3. `govoo_shares` ✅
4. `govoo_board` ✅
5. `govoo_compliance` ✅
6. `govoo_rw` ✅
7. `govoo_evaluation` ✅
8. Portal + Dashboard ✅

Full spec tree is in `docs/spec/`. This repo is the single source of truth for implementation.

## Dev environment

- **Docker Compose** spins up PostgreSQL 16 (port 5433) and Odoo 19 (port 8069).
- `docker compose up --build` to start. Odoo auto-installs `muk_mcp` on first run.
- Config via `.env` (dev defaults committed; prod secrets are separate).
- MCP server configured at `localhost:8069/mcp` for direct Odoo interaction.

## Build order (strict)

Modules must be implemented in dependency order. Do not skip ahead:

1. `govoo_base` ← start here
2. `govoo_secretarial`
3. `govoo_shares`
4. `govoo_board`
5. `govoo_compliance`
6. `govoo_rw`
7. `govoo_evaluation` (can parallel after `govoo_base`)
8. Portal + Dashboard
9. Optional: `govoo_rw_accounting` / `govoo_rw_ebm`

## Module conventions

- **Modules:** `govoo_*` naming, placed in `odoo-19.0/addons/govoo_*/`
- **Models:** `govoo.*` (e.g. `govoo.share.allotment`)
- **Standard Odoo model extensions:** prefix fields with `govoo_` (e.g. `govoo_is_director` on `res.partner`)
- **Layout per module:**
  ```
  govoo_<name>/
  |-- __init__.py, __manifest__.py
  |-- models/, views/, security/, data/, report/, tests/, i18n/
  ```
- **`__manifest__.py` depends list** must reference custom deps, not assume Odoo loads them automatically.

## Hard rules

- **Security with every model.** Every model ships `security/ir.model.access.csv` + record rules in the same PR that introduces it. No exceptions.
- **No hard-coded legal values.** Rates, dates, thresholds go in data records (`active=False` by default), never as Python literals. Mark `[CONFIRM]` in code comments.
- **Enterprise feature flags.** Every Documents/Sign/Dashboards/Approvals call is guarded to degrade on Community. Test the fallback path.
- **Multi-company isolation.** Every transactional model gets `company_id` with `check_company=True` plus a company-scoped record rule.
- **Audit trail.** Every transactional model inherits `mail.thread`. `tracking=True` on all statutory fields. EXCEPTION: computed/aggregate models (e.g. `govoo.evaluation.result`) may omit `mail.thread` if no individual record editing.
- **Money fields.** Use Odoo `Monetary` + `currency_id`, never plain `Float`. RWF has 0 decimal places.
- **Translations.** `_()` on all user-facing strings. Ship `.po` stubs for `fr` and `rw`.
- **Github issue** create an issue in the repo when it needs and do not close it until I close it myself.

## Spec reading order (per module)

1. `docs/spec/modules/<module>.md`
2. Relevant files in `docs/spec/data-model/`, `security/`, `workflows/`, `ui/`, `testing/`, `integrations/`
3. `docs/spec/requirements/traceability.md` — verify traceability before marking done
4. `docs/spec/implementation/module-checklists.md` — Definition of Done checklist

## Open decisions (never hardcode)

Items marked `[CONFIRM]` in specs are unresolved. Do not implement as authoritative values.
Full list: `docs/spec/decisions/open-decisions.md`.

## Linting

- **ruff** config in `odoo-19.0/ruff.toml` (target: py310, Odoo-standard isort sections).
- CI runs flake8/pylint-odoo against changed modules (per `docs/spec/devops/ci-cd.md`).

## Testing

- **Run tests:** `docker exec govoo-app /opt/odoo/odoo-bin -d odoo --test-enable -i <module_name> --stop-after-init`
- **Single test class:** Add `--test-tags /<class_name>` to the command above
- **HTTP port for tests:** Use `--http-port=8099` to avoid conflicts with running Odoo on 8069
- **Test database connection:** `--db_host=db --db_port=5432 --db_user=odoo --db_password=odoo`
- **After fixes:** All 8 modules pass: 66 tests, 0 failures, 0 errors

## Verification Status

All verification waves passed:
- **Waves 1-3**: Basic user setup, company creation, governance data seeding ✅
- **Waves 4-9**: Compliance lifecycle, statutory registers, board packs, minutes lifecycle, evaluation, share class/allotment ✅ (31/31 tests pass)
- **Wave 10**: Portal testing with multi-MCP (Playwright + Chrome-devtools + Skyvern + Postgres) ✅

Last updated: 2026-09-09

## Deployment rules (critical)

- **`docker restart` does NOT deploy XML changes.** It only reloads the server process; `ir.ui.view` records stay stale. Always use `-u`:
  ```
  docker exec govoo-app /opt/odoo/odoo-bin --config=/etc/odoo/odoo.conf \
    --db_host=db --db_port=5432 --db_user=odoo --db_password=odoo \
    -d odoo -u <module_list> --stop-after-init
  ```
- **DB host is `db`** (not `odoo-db`) — the Docker Compose service name.
- **odoo-bin path:** `/opt/odoo/odoo-bin` (not on PATH).
- **Verify DB records after upgrade** before restarting — query `ir.ui.view.arch` directly.
- **Restart is only safe after DB is confirmed correct.**

## Odoo 19 view conventions

- **Chatter:** Use `<chatter/>` (self-closing). Do NOT use `<div class="oe_chatter">` with explicit `<field>` children — Odoo 19 OWL chatter widget fails to mount with that pattern.
- Every model with chatter must inherit `mail.thread` (and optionally `mail.activity.mixin`).
- Every form view with chatter must have `</sheet>` immediately followed by `<chatter/>` (no `<div>` wrapper).

## MCP servers available

- **odoo** (remote): Direct Odoo interaction at `localhost:8069/mcp`
- **playwright** (local): Browser automation via `@playwright/mcp@latest`
- **postgres** (local): Direct DB queries via `crystaldba/postgres-mcp`

## Common mistakes to avoid

1. **Don't skip security:** Every model needs `ir.model.access.csv` in the same PR
2. **Don't hard-code legal values:** Use data records with `active=False` and mark `[CONFIRM]`
3. **Don't ignore multi-company:** Add `company_id` with `check_company=True` to all transactional models
4. **Don't forget translations:** Wrap all user-facing strings in `_()`
5. **Don't assume Enterprise features:** Guard all Documents/Sign/Dashboards calls
