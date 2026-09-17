# Verificación de la entrega 0.1

- 19 pruebas automáticas aprobadas en PostgreSQL 17.10 del VPS (Python 3.14); las 17 independientes de PostgreSQL también se probaron con SQLite local (Python 3.12).
- Build Vue/Vite aprobado; sin recursos externos de mapas o fuentes.
- Migraciones verificadas sin diferencias pendientes.
- Prueba HTTPS/WSS en `davefrassoni.com/cyberar/`: acceso anónimo rechazado, login con CSRF, sesión, origen WebSocket ajeno rechazado, stream de estado, reloj de servidor, velocidad, pausa, interferencia, reset y logout.
- Exclusión de un segundo reloj validada por advisory lock, y liberación del liderazgo al detenerse el proceso.
- Nginx validado sin advertencias; ambos servicios systemd activos.
- La consulta pública requiere un User-Agent explícito para evitar que la protección existente del sitio bloquee el cliente de pruebas Python. No se cambió esa protección.
- Inspección DOM de la pantalla de login realizada a 1920×1080. La revisión visual e interacción completa quedaron bloqueadas por el panel de otra extensión de Chrome; no se considera completada esa validación.

`deploy/smoke.py` utiliza credenciales cargadas por variables de entorno y no las imprime. Genera su propia sesión y la cierra. No invoca DF AI.

## UGV y despliegue — 2026-09-17

- Pestaña UGV con animación SVG, trayectoria terrestre, historial GPS/IMU/CAN,
  evidencia progresiva, tráfico ficticio y controles independientes de RF.
- CI y despliegue en producción aprobados con Node 24 y Actions actualizadas.
  Se corrigió lectura de secretos SSH y una clave privada mal formada.
- Node del VPS actualizado a 24.21.0 (binarios oficiales con SHA-256 verificado,
  instalados en `/opt`, enlaces en `/usr/local/bin`; paquete del sistema conservado).
- Pruebas nuevas: detección por evidencia, progresión, fallback, restauración,
  validación de acciones, single-flight, retry idempotente, callbacks autenticados,
  rechazo de resultados tardíos después de reiniciar o restaurar CAN.
- Smoke HTTPS/WSS aprobado en producción: login, CSRF, stream, controles,
  aislamiento de sesión, reset y logout.
- Misión acelerada en producción: observación T+76, inconsistencia T+80,
  correlación T+84, alerta T+88, aislamiento T+96; continuación a 9 km/h.
- Proyecto `cyberar` registrado en el broker con prioridad 1 y callback autenticado.
  Credenciales exclusivamente en archivos del servidor y no en este repositorio.
- La validación visual en navegador sigue pendiente: no hay un navegador
  conectado en esta sesión. El build Vue/Vite y las verificaciones de API pasaron.
