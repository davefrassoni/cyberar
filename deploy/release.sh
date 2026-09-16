#!/usr/bin/env bash
# Runs on the VPS as root; receives an archive uploaded by GitHub Actions.
set -euo pipefail
release_id=${1:?Missing release ID}
[[ "$release_id" =~ ^[0-9]+-[0-9]+$ ]]
APP=/var/www/cyberar
archive="/var/tmp/cyberar-${release_id}.tgz"
staging=$(mktemp -d /var/tmp/cyberar-release.XXXXXX)
trap 'rm -rf "$staging"; rm -f "$archive"' EXIT
test "$(id -u)" = 0
test -f /etc/cyberar.env
tar -xzf "$archive" -C "$staging"
test -f "$staging/frontend/dist/index.html"
test -f "$staging/backend/manage.py"
mkdir -p "$APP/backend" "$APP/deploy" "$APP/frontend/dist/assets"
# Keep previous hashed assets for clients that still have the previous page open.
rsync -a "$staging/frontend/dist/assets/" "$APP/frontend/dist/assets/"
rsync -a --delete --exclude '__pycache__/' --exclude '*.sqlite3' "$staging/backend/" "$APP/backend/"
rsync -a "$staging/deploy/" "$APP/deploy/"
install -m 0644 "$staging/frontend/dist/index.html" "$APP/frontend/dist/index.html"
bash "$APP/deploy/install.sh"
status=$(curl -sS -o /dev/null -w '%{http_code}' -H 'Host: davefrassoni.com' http://127.0.0.1:8063/cyberar/api/state/)
test "$status" = 401
