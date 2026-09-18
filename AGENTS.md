# AGENTS.md

Guía para agentes de IA que trabajen en este repositorio.

## Git

- **Al terminar una tarea sobre `main`, comitear y pushear siempre**, sin esperar
  que se pida explícitamente. Solo omitir el push si el usuario pide
  explícitamente no hacerlo, o si el trabajo quedó incompleto/roto.
- Nunca commitear secretos reales (tokens, passwords, claves privadas, IPs o
  puertos de producción). Este repo es público — ver "Seguridad" abajo.
- Preferir commits nuevos a `--amend`; mensajes en español, cortos, explicando
  el porqué del cambio.

## Comandos

Backend (desde `backend/`):
```
DJANGO_DEBUG=true DJANGO_SECRET_KEY=test-only DATABASE_URL=sqlite:///:memory: python manage.py test tests -v 2
DJANGO_DEBUG=true DJANGO_SECRET_KEY=test-only DATABASE_URL=sqlite:///:memory: python manage.py makemigrations --check --dry-run
```

Frontend (desde `frontend/`):
```
npm ci
npm run build
```

Correr ambos antes de dar una tarea por terminada si se tocó backend o frontend.

## Seguridad / repo público

Este repositorio se publica públicamente (hackathon). Antes de commitear:

- Nunca incluir valores reales de `.env` — solo `.env.example` con placeholders.
- No pegar IPs, puertos SSH, usuarios de servidor, ni salidas de comandos `ssh`/
  `journalctl`/`manage.py shell` contra el VPS de producción en código, docs o
  mensajes de commit.
- `DF_AI_TOKEN`, `DF_AI_CALLBACK_TOKEN`, `DJANGO_SECRET_KEY`, credenciales de
  `CYBERAR_USER`/`CYBERAR_PASSWORD` de producción: nunca en el repo. Viven solo
  en `/etc/cyberar.env` en el servidor.
- Si se documenta el proceso de deploy (README, `deploy/`), usar placeholders
  genéricos (`<IP del VPS>`, `<puerto SSH>`) en vez de valores reales.

## Documentación que se desactualiza fácil

`pitch.md` y `research.md` describen el estado actual del simulador (guion de
demo y grounding en vectores de ataque reales). Si se cambia el motor de
simulación, el panel RED TEAM, o los controles del demo, revisar si alguno de
los dos quedó desactualizado.
