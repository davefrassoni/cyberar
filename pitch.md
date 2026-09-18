# CYBER.AR — Guion de pitch (5 minutos)

Guion minuto a minuto para demostrar en vivo las funcionalidades del simulador: multi-escenario, edición de checkpoints, flota de drones, inyección de fallas, comunicaciones resilientes con popup de degradación, y debriefing con insight de IA. Cada bloque tiene **DECIR** (lo que se dice) y **HACER** (los clics exactos). Los tiempos son orientativos — practicá una vez y ajustá.

## Antes de arrancar (no cronometrado)

- Tené el navegador ya abierto en la pantalla de login, con `npm run build` corriendo del lado del frontend y el backend levantado (`manage.py runserver` + `run_simulator` si querés que el broker DF AI esté activo; si `CYBERAR_AI_ENABLED` está en `false`, el debriefing funciona igual con el insight local — mencionalo como una fortaleza, no la escondas).
- Verificá que el escenario esté en estado `PREPARING` (usá "REINICIAR DEMO" si alguien tocó algo antes).
- Tené a mano una pestaña con `research.md` por si alguien pregunta "¿de dónde sacaron esto?".

## 0:00–0:20 — Apertura

**DECIR:** "Esto es CYBER.AR: un simulador 100% software de misiones con drones, pensado para mostrar cómo se construye resiliencia real contra fallas y ataques — sin necesitar hardware de RF ni drones físicos. Todo lo que van a ver corre en un motor determinístico en el backend."

**HACER:** Login con las credenciales de demo. Esperar a que cargue el dashboard.

## 0:20–1:05 — Multi-escenario

**DECIR:** "Lo primero: esto no es un solo mapa fijo. Tenemos tres teatros de operación distintos, cada uno con su propio dron, su propia flota terrestre y sus propios checkpoints." 

**HACER:**
1. Mostrar el escenario **ATLÁNTICO** (default): reconocimiento marítimo, dron ala fija.
2. Click en **CUENCA NEUQUINA** — señalar el cambio de fondo (estepa, pozos petroleros, ducto punteado) y que el dron ahora es un **quadcóptero** (mostrar el ícono en el mapa).
3. Click en **TRIPLE FRONTERA** — señalar los ríos, la línea de frontera punteada y los puestos.
4. Volver a **CUENCA NEUQUINA** (el escenario donde vamos a correr el resto de la demo).

**DECIR (mientras cambia):** "Cada escenario re-tematiza también el vehículo terrestre — en Cuenca Neuquina es un rover inspector de ductos, en la Triple Frontera es una patrulla fronteriza. Es la misma arquitectura, distintos teatros."

## 1:05–1:35 — Checkpoints editables

**DECIR:** "Antes de iniciar la misión, los checkpoints se pueden arrastrar directamente sobre el mapa — para adaptar la ruta a la infraestructura real sin tocar una línea de código."

**HACER:** Arrastrar uno de los checkpoints (por ej. POZO-02) a una nueva posición. Señalar el banner "MODO EDICIÓN DE RUTA" que aparece mientras la misión no arrancó.

## 1:35–2:00 — Flota de drones

**DECIR:** "Ahora la parte central de la demo: no volamos un solo dron, sino una flota de hasta tres, todos sobre la misma ruta, escalonados en el tiempo — como iría una formación real."

**HACER:**
1. Click en el selector de flota → **3×**.
2. Señalar que ahora hay `UAV-01`, `UAV-02`, `UAV-03` en el mapa.
3. Abrir **△ RED TEAM** (se abre como panel centrado) → en la sección de falla de sensor (abajo del todo, solo visible con flota &gt;1) elegir `UAV-02`, nivel alto (~80%), click **APLICAR FALLA**.

**DECIR:** "Le acabo de inyectar una falla simulada al sensor de altitud de UAV-02. Los tres drones van a volar exactamente la misma trayectoria — pero uno de ellos va a *mentir* sobre su altitud. Guardénse ese dato, porque en un minuto el sistema lo va a encontrar solo."

## 2:00–2:15 — Arrancar la misión

**HACER:** Subir la velocidad a **4×**, click **▷ INICIAR**.

**DECIR:** "Aceleramos el reloj de simulación para no hacerlos esperar — el motor sigue siendo el mismo, determinístico, corriendo en el servidor."

## 2:15–3:00 — Comunicaciones resilientes (mientras la flota vuela)

**DECIR:** "Mientras vuela, miremos comunicaciones. El dron no depende de un solo enlace: tiene RF primario, RF direccional, óptico y satelital de respaldo."

**HACER:**
1. Señalar los botones grandes **ENLACE CON EL DRON** (RF / RF DIRECCIONAL / SATELITAL / LÁSER) debajo de los controles de demo — click sobre uno distinto al activo (por ej. **SATELITAL**) para mostrar que se puede conmutar manualmente en cualquier momento.
2. Abrir **△ RED TEAM** → click **📡 JAMMING RF** (el botón se pone rojo/activo; en el mapa aparece la fuente terrestre encubierta con su zona de disrupción).
3. Señalar el **popup de alerta** que aparece: degradación detectada, canal recomendado, cuenta atrás de 3 segundos.
4. Dejar que el countdown llegue a cero (conmuta solo) — o, si querés mostrar el control manual, click **CANCELAR** y luego **CONMUTAR AHORA**.
5. Volver a **RED TEAM** → click **📡 JAMMING RF** de nuevo para desactivarlo (o **✓ RESTAURAR TODOS LOS ENLACES Y SENSORES**).

**DECIR:** "Esto es la resiliencia en acción: la interferencia no es un slider abstracto — viene de una fuente real posicionada en el mapa, a una distancia concreta del dron. El sistema detecta la degradación, recomienda una acción concreta y la ejecuta automáticamente si nadie decide lo contrario en tres segundos — pero el operador humano siempre puede cancelar."

## 3:00–3:30 — Capa interna: anomalía CAN (feature existente, repaso rápido)

**DECIR:** "Esto era la capa externa — el enlace. Pero hay otra capa: la integridad de los datos *dentro* del vehículo."

**HACER:** Click en la pestaña del vehículo terrestre (`ROV-01` en este escenario). Señalar el detector de anomalías CAN, la correlación GPS/IMU/CAN, y si ya se disparó, el aislamiento de señal por el `SafetyValidator`.

**DECIR:** "El bus CAN no tiene autenticación nativa — es un vector de ataque real, documentado en la industria automotriz. Acá lo resolvemos comparando la velocidad reportada contra GPS e IMU, fuentes independientes. Si CAN dice una cosa y el resto del vehículo dice otra, gana la evidencia, no el canal más ruidoso."

## 3:30–3:50 — Volver a la flota

**HACER:** Volver a la pestaña de la flota UAV. Mostrar las **tabs de dron activo** (`UAV-01` / `UAV-02` / `UAV-03`) y cambiar entre ellas para ver la telemetría de cada una en tiempo real.

**DECIR:** "Cada dron de la flota tiene su propia telemetría en vivo — y ya deberían estar llegando a destino."

## 3:50–4:40 — Debriefing + insight de IA

**HACER:** Cuando aparezca el botón **▤ VER DEBRIEFING** (fin de la misión), hacer click.

**DECIR (mientras carga):** "Esto es lo que más me gusta mostrar. Terminada la misión, comparamos los sensores de los tres drones que volaron la misma ruta."

**HACER:** Señalar el gráfico de altitud: las líneas de `UAV-01` y `UAV-03` se superponen, la de `UAV-02` diverge claramente.

**DECIR:** "Mismo camino, misma misión — pero un sensor reporta otra cosa. Eso, solo, ya es una señal. Pero además pasamos esos datos por un job de IA" 

**HACER:** Señalar el panel de insight: fuente (LOCAL o DF AI), el dron y componente señalados (`UAV-02 · SENSOR DE ALTITUD`), el nivel de confianza y los hallazgos.

**DECIR:** "...que confirma cuál dron y cuál componente específico está fallando, con nivel de confianza y evidencia. Si el broker de IA no responde a tiempo, ya tenían la respuesta local instantánea — nunca se bloquea esperando un modelo."

## 4:40–5:00 — Cierre

**DECIR:** "Todo esto — comunicaciones resilientes, integridad de datos internos, y ahora integridad cruzada entre vehículos de una flota — está grounded en vectores de ataque reales contra drones: spoofing GPS, jamming, inyección CAN, sensores comprometidos. Documentamos esa investigación en el repo. La idea no es simular un ataque de Hollywood: es mostrar cómo un sistema *detecta, analiza, se adapta y continúa* la misión, capa por capa. Gracias."

---

## Plan B / contingencias

- **Si un solo jammer no alcanza a degradar el canal activo** (la interferencia depende de la distancia real al UAV, así que cuanto más lejos de la base esté volando, menos pega): activar también **✈ JAMMING C2** además de **📡 JAMMING RF** — con los dos activos el popup dispara seguro. Practicá el timing una vez para saber en qué punto del vuelo conviene activarlo.
- **Si el broker DF AI está apagado:** el debriefing y la anomalía CAN muestran igual el insight local — decilo como feature ("nunca depende de que un modelo externo responda a tiempo"), no como limitación.
- **Si el drag de checkpoints no agarra bien en el mouse/trackpad del lugar:** mostralo de todos modos, es tolerante a reintentos; si falla, seguí — no es bloqueante para el resto del guion.
- **Si el tiempo se acorta:** el bloque recortable es el de "capa interna CAN" (3:00–3:30) — ya es una feature conocida, no la novedad de esta versión. El debriefing (4:40) es el cierre que nunca hay que sacrificar.
