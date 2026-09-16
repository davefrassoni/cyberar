"""One-time provisioning on the VPS as root. Never prints credentials."""
import os
import secrets
import subprocess
from pathlib import Path

env = Path('/etc/cyberar.env')
if os.geteuid() != 0:
    raise SystemExit('Ejecutar como root')
if env.exists():
    raise SystemExit('/etc/cyberar.env ya existe; no se reemplaza')
password = secrets.token_hex(32)
sql = f"""
CREATE ROLE cyberar LOGIN PASSWORD '{password}';
CREATE DATABASE cyberar OWNER cyberar;
"""
subprocess.run(['runuser', '-u', 'postgres', '--', 'psql', '-v', 'ON_ERROR_STOP=1'], input=sql, text=True, check=True, stdout=subprocess.DEVNULL)
content = f"""DJANGO_DEBUG=false
DJANGO_SECRET_KEY={secrets.token_hex(48)}
DJANGO_ALLOWED_HOSTS=davefrassoni.com,127.0.0.1
DJANGO_CSRF_TRUSTED_ORIGINS=https://davefrassoni.com
DATABASE_URL=postgresql://cyberar:{password}@127.0.0.1:5432/cyberar
CYBERAR_USER=admin
CYBERAR_PASSWORD={secrets.token_urlsafe(24)}
CYBERAR_SESSION_SECONDS=7200
CYBERAR_DEMO_DURATION=150
CYBERAR_DEMO_MODE=true
CYBERAR_AI_ENABLED=false
CYBERAR_AI_TIMEOUT=15
DF_AI_URL=http://127.0.0.1:8050
DF_AI_TOKEN=
DF_AI_PRIORITY=1
"""
fd = os.open(env, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as file: file.write(content)
print('Base aislada y /etc/cyberar.env creados; credenciales generadas fuera del repositorio.')
