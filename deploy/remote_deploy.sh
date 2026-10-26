#!/usr/bin/env bash
# Deploys the current state of `master` to the demo server's running
# govoo-app/govoo-db containers. Run ON THE SERVER (the GitHub Actions
# workflow at .github/workflows/deploy-remote.yml SSHes in and invokes
# this script directly from the just-pulled repo checkout).
#
# DB credentials are deliberately never hardcoded here -- they're read
# back out of the already-running container's own startup command, so
# this script carries no secret of its own and stays safe to version
# control.
#
# Encodes the operational lessons learned deploying this project by hand
# this session:
#   - the first `-u`/`-i` right after a `docker restart` routinely hits a
#     transient `psycopg2.errors.SerializationFailure`; retrying once,
#     identically, after a short pause always resolves it.
#   - a plain `-u <module>` does not reliably force Odoo to recompile and
#     re-cache a changed SCSS-only asset bundle; a stale bundle can keep
#     being served until it's force-regenerated directly.
#   - any one-off `odoo-bin shell` script must call `env.cr.commit()`
#     explicitly, or every change it made is silently rolled back when
#     the process exits.
#   - `-u all` is NOT safe here: govoo_ai has an unmet Python dependency
#     (`fitz`/PyMuPDF missing from the image), and Odoo's `-u all`
#     refuses the whole upgrade outright if ANY installed module's
#     external dependency check fails, even one unrelated to what
#     actually changed. Confirmed live (2026-10-26) -- this is why the
#     upgrade list below is computed from the actual file diff between
#     deploys, not a blanket "upgrade everything" sweep. A future PR
#     that genuinely touches govoo_ai will still hit this and fail
#     loudly, which is correct (the missing dependency is a real,
#     separate, pre-existing gap in the image -- not something to
#     silently paper over here).
set -euo pipefail

REPO_DIR=/opt/govoo/repo
CONTAINER=govoo-app
DB_CONTAINER=govoo-db
ADDONS_DIR="$REPO_DIR/odoo-19.0/addons"

cd "$REPO_DIR"
OLD_HEAD="$(git rev-parse HEAD)"

echo "==> Pulling latest master"
git fetch origin master
git reset --hard origin/master
NEW_HEAD="$(git rev-parse HEAD)"
echo "    ${OLD_HEAD:0:12} -> ${NEW_HEAD:0:12}"

echo "==> Reading DB connection args from the running container's own command"
mapfile -t DB_ARGS < <(
    docker inspect "$CONTAINER" --format '{{json .Config.Cmd}}' | python3 -c '
import json, sys
argv = json.load(sys.stdin)
def opt(flag, default=""):
    for a in argv:
        if a.startswith(flag):
            return a[len(flag):]
    return default
db_name = argv[argv.index("-d") + 1] if "-d" in argv else ""
for v in (opt("--db_host="), opt("--db_port="), opt("--db_user="), opt("--db_password="), db_name):
    print(v)
'
)
DB_HOST="${DB_ARGS[0]}"; DB_PORT="${DB_ARGS[1]}"; DB_USER="${DB_ARGS[2]}"
DB_PASS="${DB_ARGS[3]}"; DB_NAME="${DB_ARGS[4]}"
echo "    db: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"

echo "==> Determining which modules need installing vs upgrading"
INSTALLED="$(docker exec "$DB_CONTAINER" psql -U "$DB_USER" -d "$DB_NAME" -t -c \
    "select name from ir_module_module where state in ('installed', 'to upgrade');")"

# Every govoo_*/clagov_*/zxs_entp_theme dir present on disk but not yet
# installed -- these are brand-new modules a merge added.
TO_INSTALL=()
while IFS= read -r dir; do
    mod="$(basename "$dir")"
    if ! echo "$INSTALLED" | grep -qw "$mod"; then
        TO_INSTALL+=("$mod")
    fi
done < <(find "$ADDONS_DIR" -maxdepth 1 -type d \( -name 'govoo_*' -o -name 'clagov_*' -o -name 'zxs_entp_theme' \))

# Every already-installed module whose own directory had a file change
# between the previously-deployed commit and this one. Deliberately NOT
# "-u all": see the fitz/govoo_ai note above.
TO_UPGRADE=()
if [ "$OLD_HEAD" != "$NEW_HEAD" ]; then
    while IFS= read -r mod; do
        [ -z "$mod" ] && continue
        if echo "$INSTALLED" | grep -qw "$mod"; then
            TO_UPGRADE+=("$mod")
        fi
    done < <(git diff --name-only "$OLD_HEAD" "$NEW_HEAD" -- "odoo-19.0/addons" \
        | awk -F/ '{print $3}' | sort -u)
fi

INSTALL_ARGS=()
if [ "${#TO_INSTALL[@]}" -gt 0 ]; then
    joined="$(IFS=,; echo "${TO_INSTALL[*]}")"
    echo "    new modules to install: $joined"
    INSTALL_ARGS=(-i "$joined")
else
    echo "    no new modules"
fi
if [ "${#TO_UPGRADE[@]}" -gt 0 ]; then
    joined_u="$(IFS=,; echo "${TO_UPGRADE[*]}")"
    echo "    changed modules to upgrade: $joined_u"
    INSTALL_ARGS+=(-u "$joined_u")
else
    echo "    no changed installed modules"
fi

if [ "${#TO_INSTALL[@]}" -eq 0 ] && [ "${#TO_UPGRADE[@]}" -eq 0 ]; then
    echo "==> Nothing addon-related changed, nothing to redeploy"
    exit 0
fi

run_upgrade() {
    docker exec "$CONTAINER" /opt/odoo/odoo-bin \
        --config=/etc/odoo/odoo.conf \
        --db_host="$DB_HOST" --db_port="$DB_PORT" \
        --db_user="$DB_USER" --db_password="$DB_PASS" \
        -d "$DB_NAME" "${INSTALL_ARGS[@]}" --stop-after-init
}

echo "==> Restarting container before upgrade"
docker restart "$CONTAINER"
sleep 6

echo "==> Running module install/upgrade"
if run_upgrade > /tmp/govoo_deploy_upgrade.log 2>&1; then
    echo "    upgrade OK on first attempt"
else
    echo "    first attempt failed (checking for the known transient SerializationFailure)"
    if grep -q "SerializationFailure" /tmp/govoo_deploy_upgrade.log; then
        echo "    confirmed transient, retrying once"
        sleep 3
        run_upgrade > /tmp/govoo_deploy_upgrade.log 2>&1
        echo "    retry OK"
    else
        echo "    non-transient failure, aborting deploy"
        tail -60 /tmp/govoo_deploy_upgrade.log
        exit 1
    fi
fi
if grep -iE "error|traceback" /tmp/govoo_deploy_upgrade.log | grep -v -i pdfminer | grep -q .; then
    echo "WARNING: errors found in upgrade log:"
    grep -iE "error|traceback" /tmp/govoo_deploy_upgrade.log | grep -v -i pdfminer
fi

echo "==> Forcing CSS/JS asset bundle regeneration (stale-bundle lesson above)"
cat <<PYEOF | docker exec -i "$CONTAINER" /opt/odoo/odoo-bin shell \
    --config=/etc/odoo/odoo.conf --db_host="$DB_HOST" --db_port="$DB_PORT" \
    --db_user="$DB_USER" --db_password="$DB_PASS" -d "$DB_NAME" --no-http
env = env
for bundle in ['web.assets_backend', 'web.assets_frontend']:
    try:
        env['ir.qweb']._get_asset_bundle(bundle, css=True, js=False).css()
    except Exception as e:
        print('bundle regen warning:', bundle, repr(e))
env.cr.commit()
print('asset bundles regenerated and committed')
PYEOF

echo "==> Restarting container to pick up the fresh registry"
docker restart "$CONTAINER"
sleep 10

echo "==> Health check"
STATUS="$(curl -sS -o /dev/null -w '%{http_code}' http://localhost:8069/web/login)"
ERRORS="$(docker logs "$CONTAINER" --since 1m 2>&1 | grep -iE 'error|traceback' | grep -v -i pdfminer || true)"
if [ "$STATUS" = "200" ] && [ -z "$ERRORS" ]; then
    echo "==> Deploy succeeded (login page HTTP $STATUS, no errors in recent logs)"
else
    echo "==> DEPLOY COMPLETED WITH WARNINGS"
    echo "    login page HTTP status: $STATUS"
    [ -n "$ERRORS" ] && echo "    recent log errors:" && echo "$ERRORS"
    exit 1
fi
