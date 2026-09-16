# Decisiones de la primera iteración

## Inspección previa

Repositorio CYBER.AR vacío, remoto `davefrassoni/cyberar`. Proyecto vecino `davefrassoni`: Django 5.2, Vue 3.5, Vite 6, PostgreSQL; convenciones de servicios independientes para aplicaciones bajo prefijos. VPS: Python 3.14.4, Django 5.2.16, PostgreSQL servidor 17.10 (cliente psql 18.6), Redis disponible. Sitio principal WSGI en 8050, sin Channels/Uvicorn en su entorno. DF AI: broker en Django, ejecución del worker en máquina aparte.

## Decisiones

- Servicio separado bajo `/cyberar/`, base/rol y entorno Python propios. No convertir el servidor principal a ASGI ni añadir apps a sus settings.
- Django sin DRF: seis endpoints pequeños no justifican otra dependencia.
- SVG propio sin Leaflet: teatro ficticio, sin tiles externos, control de estética y cero dependencias de mapas.
- Channels para conexiones autenticadas. La lectura interna a 1 Hz desde DB evita Redis para una demo pequeña y admite múltiples workers web. Migrar a publish/subscribe cuando la escala lo justifique.
- Un reloj de servidor independiente: la UI no ejecuta la simulación. Advisory lock de PostgreSQL en conexión dedicada y transacciones para evitar relojes simultáneos o aceleración por múltiples pestañas.
- Dos conceptos separados: fase de vuelo y degradación del enlace. La adaptación autónoma y su submáquina se implementan en la etapa 2.
- No enviar jobs de prueba al broker compartido ni declarar que hay IA conectada. El panel muestra claramente el estado real de integración.

## Riesgos y límites

- Las coordenadas, velocidades y distancias son ilustrativas; el tiempo de demo es comprimido.
- PostgreSQL coordina un solo reloj por base. SQLite utiliza exclusión por archivo, limitada al mismo host.
- SQLite sirve localmente; usar PostgreSQL en producción para bloqueo de filas.
- En reinicio del proceso se continúa desde el último tick confirmado; no se adelanta el reloj por tiempo de caída.
- Reset conserva ID y aumenta revision para rechazar frames anteriores. Los futuros jobs tendrán un ID de ejecución adicional.
- Mantener ruta y cookies bajo el prefijo; comprobar también WebSocket y assets después de Nginx.
- La base guarda historial discreto. Antes de uso sostenido, definir retención de misiones/eventos y limpieza programada de sesiones.
- No afirmar que cifrado, GPS o RF son reales: todos son atributos simulados.

## Referencias de implementación

- https://channels.readthedocs.io/en/stable/topics/security.html
- https://channels.readthedocs.io/en/stable/topics/sessions.html
- https://vite.dev/guide/build#public-base-path

## Próxima entrega

Cliente broker + mock, cola single-flight persistida, debounce, timeout, idempotencia, callback autenticado, breaker, validación de enum y reglas determinísticas; después cambio de canal, store-and-forward y transmisión progresiva. No existe todavía un endpoint de jobs expuesto por CYBER.AR.
