#!/usr/bin/env bash
# Run as root on the VPS after uploading backend, frontend/dist and deploy.
set -euo pipefail
APP=/var/www/cyberar
test "$(id -u)" = 0
test -f "$APP/frontend/dist/index.html"
test -f /etc/cyberar.env
if [ ! -x "$APP/.venv/bin/python" ]; then python3 -m venv "$APP/.venv"; fi
chown -R deploy:www-data "$APP"
runuser -u deploy -- "$APP/.venv/bin/pip" install --disable-pip-version-check -r "$APP/backend/requirements.lock.txt"
set -a
. /etc/cyberar.env
set +a
cd "$APP/backend"
runuser -u deploy -- "$APP/.venv/bin/python" manage.py check
runuser -u deploy -- "$APP/.venv/bin/python" manage.py migrate --noinput
install -m 0644 "$APP/deploy/cyberar-web.service" /etc/systemd/system/
install -m 0644 "$APP/deploy/cyberar-simulator.service" /etc/systemd/system/
install -m 0644 "$APP/deploy/cyberar.nginx.conf" /etc/nginx/snippets/cyberar.conf
python3 - <<'PY'
from pathlib import Path
paths = {Path('/etc/nginx/sites-available/davefrassoni').resolve(), Path('/etc/nginx/sites-enabled/davefrassoni').resolve()}
anchor = '    root /var/www/davefrassoni;'
line = '    include /etc/nginx/snippets/cyberar.conf;'
for path in paths:
    content = path.read_text()
    if line not in content:
        if content.count(anchor) != 1:
            raise SystemExit(f'No se encontró un único punto de inserción en {path}')
        backup_dir = Path('/var/backups/cyberar')
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / (path.parent.name + '-' + path.name + '.conf')
        if not backup.exists(): backup.write_text(content)
        path.write_text(content.replace(anchor, line + '\n' + anchor))
PY
nginx -t
systemctl daemon-reload
systemctl enable --now cyberar-web cyberar-simulator
systemctl restart cyberar-web cyberar-simulator
for attempt in {1..20}; do
    if curl -fsS -H 'Host: davefrassoni.com' http://127.0.0.1:8063/cyberar/ >/dev/null; then break; fi
    [ "$attempt" = 20 ] && exit 1
    sleep 1
done
systemctl reload nginx
systemctl is-active cyberar-web cyberar-simulator
