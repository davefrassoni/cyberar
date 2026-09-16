# Verificación de la entrega 0.1

- 17 pruebas automáticas aprobadas en SQLite local (Python 3.12) y PostgreSQL 17.10 del VPS (Python 3.14).
- Build Vue/Vite aprobado; sin recursos externos de mapas o fuentes.
- Migraciones verificadas sin diferencias pendientes.
- Prueba HTTPS/WSS en `davefrassoni.com/cyberar/`: acceso anónimo rechazado, login con CSRF, sesión, origen WebSocket ajeno rechazado, stream de estado, reloj de servidor, velocidad, pausa, interferencia, reset y logout.
- Nginx validado sin advertencias; ambos servicios systemd activos.
- La consulta pública requiere un User-Agent explícito para evitar que la protección existente del sitio bloquee el cliente de pruebas Python. No se cambió esa protección.
- Inspección DOM de la pantalla de login realizada a 1920×1080. La revisión visual e interacción completa quedaron bloqueadas por el panel de otra extensión de Chrome; no se considera completada esa validación.

`deploy/smoke.py` utiliza credenciales cargadas por variables de entorno y no las imprime. Genera su propia sesión y la cierra. No invoca DF AI.
