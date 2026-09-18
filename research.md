# Investigación: vectores de ataque contra UAV/UGV y mitigaciones

Documento de research interno para sustentar la narrativa de seguridad del pitch de CYBER.AR. No es un paper académico ni tiene pretensión de exhaustividad formal: reúne vectores de ataque reales contra drones (UAS) y vehículos terrestres no tripulados (UGV), con ejemplos conocidos y las mitigaciones que la industria recomienda, para justificar por qué el simulador está diseñado como está.

## 1. GPS spoofing (suplantación satelital) y meaconing

Consiste en transmitir señales GNSS falsas, más potentes que las legítimas, para que el receptor calcule una posición o una hora incorrecta. El *meaconing* es la variante que retransmite señales reales con retardo para lograr el mismo efecto sin generar la señal desde cero.

Es uno de los vectores más documentados. Según GPS World y varios papers de survey (arXiv, PeerJ), ya en 2012 investigadores de la Universidad de Texas demostraron en vivo la captura de un UAV civil mediante spoofing GPS, forzándolo a descender. Irán afirmó en 2011 haber combinado jamming y spoofing para forzar el aterrizaje de un RQ-170 estadounidense en su territorio (hecho debatido, porque ese drone debía usar GPS militar cifrado). Más recientes y mejor verificados son los casos de la guerra Rusia-Ucrania, donde el spoofing GNSS se usa de forma sistemática contra UAVs para hacerles perder posición y facilitar su captura o caída.

**Mitigaciones:** GNSS multi-constelación y multi-banda, RAIM (chequeo de consistencia entre satélites), antenas de array (detectan que todas las señales llegan del mismo ángulo, lo cual es sospechoso), y sobre todo **fusión sensorial**: comparar la posición GNSS contra IMU, odometría y visión. Este es exactamente el principio que el proyecto aplica en la pestaña UGV-01: la velocidad reportada por CAN se contrasta contra GPS e IMU, y una divergencia sostenida dispara la alerta.

## 2. Jamming del enlace GPS y del enlace de mando (C2)

El jamming no falsea la señal, la ahoga con ruido en la misma frecuencia. Contra GNSS, deja al drone sin posición; contra el enlace de control, lo deja sin telemetría ni comandos.

El caso más grande y mejor documentado en 2024-2025 es el jamming ruso sobre el mar Báltico: según el reporte de los estados bálticos ante la OACI, cerca de 123.000 vuelos fueron afectados en los primeros cuatro meses de 2025, con hasta el 27% de los vuelos de la región interferidos en un solo mes. Estonia, Lituania, Letonia, Suecia y Alemania lo calificaron formalmente como guerra híbrida rusa, con origen rastreado a Kaliningrado y San Petersburgo. En Ucrania, el jamming de enlaces C2 de drones FPV es una práctica de contrainsurgencia cotidiana en el frente.

**Mitigaciones:** salto de frecuencia (frequency hopping), potencia adaptativa, antenas direccionales, y la mitigación arquitectónica central de este proyecto: **comunicaciones resilientes multicanal con failover automático**. Si un canal RF se degrada o se interfiere, el sistema debe poder migrar a un canal óptico o satelital menos vulnerable a ese jammer específico, en vez de depender de que un único enlace sea perfecto.

## 3. Deautenticación, secuestro (hijacking) y MITM/inyección de comandos en el enlace de control

Un atacante envía tramas de deautenticación Wi-Fi (o su equivalente en otros protocolos) para forzar la desconexión del drone de su controlador legítimo, y luego se hace pasar por la estación de control (spoofing de identidad) o inyecta/repite comandos capturados previamente (replay). El resultado es la toma de control ("cyber-takeover") del vehículo.

Es la base de casi toda la tecnología comercial de "captura" de drones civiles: varios sistemas C-UAS, según literatura de counter-UAS, imitan la estación de tierra para forzar un aterrizaje controlado. MAVLink, el protocolo más usado en drones civiles y de hobby, careció durante años de autenticación nativa, lo que hizo trivial este ataque en configuraciones sin cifrado.

**Mitigaciones:** autenticación mutua y cifrado del enlace (WPA2/3 con clave robusta, MAVLink2 firmado), detección de anomalías en el patrón de reconexión, y de nuevo, **failover a un canal alternativo** cuando el canal primario muestra comportamiento anómalo, para no depender de un solo punto de confianza.

## 4. Inyección y spoofing en el bus CAN (vector propio de la historia UGV)

El CAN bus fue diseñado en los 80 para tolerancia a fallas, no para seguridad: no tiene autenticación de origen ni cifrado nativo, y cualquier nodo con acceso físico (o comprometido) puede inyectar tramas con un ID legítimo. Un atacante que logra acceso al bus (por una ECU comprometida, un puerto OBD, o firmware alterado) puede spoofear el ID de un sensor de velocidad y reportar un valor falso que contradiga la realidad física del vehículo.

Según literatura reciente de seguridad automotriz (datasets como CAN-MIRGU, papers de intrusion detection en arXiv), los ataques de inyección/spoofing sobre CAN son la familia más estudiada, y el mitigador estándar que adoptó la industria es SecOC (Secure Onboard Communication) de AUTOSAR, que agrega un código de autenticación de mensaje a las tramas críticas. En drones y UGVs la mayoría de estos ataques requieren compromiso físico o de firmware previo, pero una vez con acceso al bus, la manipulación es silenciosa: el resto de las ECUs no tiene forma nativa de saber que el dato es falso.

**Mitigaciones:** SecOC/MAC en tramas críticas, segmentación de bus con gateways, y —el enfoque que este proyecto demuestra— **detección por consistencia cruzada**: comparar el valor CAN contra fuentes independientes (GPS, IMU) que no comparten el mismo bus ni el mismo canal de compromiso. Si CAN dice 40 km/h y GPS+IMU coinciden en 9 km/h, la contradicción es la señal de alerta, no un umbral fijo sobre el valor CAN en sí.

## 5. Spoofing de sensores (IMU, altímetro, flujo óptico)

Además del GNSS, otros sensores son atacables: giroscopios e IMUs son sensibles a resonancia acústica (demostrado en papers académicos con parlantes ultrasónicos que inducen lecturas falsas), altímetros barométricos pueden ser engañados con cambios de presión localizados, y sistemas de flujo óptico pueden confundirse con patrones visuales adversariales. **Mitigación:** fusión multisensor con detección de residuos (Kalman) y validación cruzada entre sensores de naturaleza física distinta —el mismo principio aplicado al caso CAN.

## 6. Firmware tampering, actualizaciones OTA inseguras y riesgo de cadena de suministro

Si las actualizaciones de firmware no están firmadas criptográficamente, un atacante en la red o en la cadena de distribución puede empujar código malicioso que altere el comportamiento de vuelo o desactive funciones de seguridad. A nivel de cadena de suministro, componentes falsificados pueden llegar pre-flasheados con malware: un estudio citado en la literatura de seguridad embebida demostró una hélice visualmente idéntica a la original que hacía caer el drone al despegar.

**Mitigaciones:** secure boot, firmas de firmware verificadas antes de aplicar una actualización, SBOM (inventario de componentes de software) y abastecimiento de proveedores certificados. Vector fuera del alcance de una demo puramente de software.

## 7. Interceptación de video y telemetría (downlink no cifrado)

El caso más citado en la literatura de seguridad de drones militares es el de los feeds de video de los Predator estadounidenses en Irak y Afganistán, interceptados por insurgentes con SkyGrabber, una herramienta rusa de 26 dólares, porque el tramo final de la retransmisión satelital hacia la estación de tierra viajaba sin cifrar (el Pentágono conocía el problema desde Bosnia, en los 90). Reveló información de inteligencia sobre qué objetivos se estaban vigilando.

**Mitigaciones:** cifrado de extremo a extremo en todo el downlink (no solo en el tramo satelital), rotación de claves, y monitoreo de anomalías en el consumo de ancho de banda del canal.

## 8. Captura física y manipulación directa

Un drone o UGV recuperado, caído o capturado puede ser desarmado y analizado por un adversario con acceso físico, extrayendo claves, firmware o configuraciones. Es el escenario final de casi todos los vectores anteriores cuando tienen éxito. **Mitigaciones:** cifrado de almacenamiento en reposo y borrado seguro ante pérdida de contacto prolongada.

## 9. Riesgos específicos de enjambres (swarms)

En un swarm descentralizado, los vehículos comparten posición y estado entre sí para mantener formación y coordinación. Según papers recientes (Inside GNSS, arXiv 2606.00904), basta comprometer o spoofear a **una sola unidad** para que el dato falso se propague al resto: la formación se rompe, hay riesgo de colisión o el grupo se desvía de la misión. Las estrategias de spoofing incluyen desplazamiento fijo, relativo (sutil, difícil de notar) o aleatorio, y ataques que desplazan la posición reportada gradualmente para no disparar alarmas.

**Mitigaciones:** validación cooperativa entre vehículos (por ejemplo, medición de distancia relativa vía UWB entre pares, independiente del GNSS de cada uno) y, sobre todo, **comparación post-misión entre vehículos hermanos que recorrieron la misma ruta**: si un sensor de una unidad diverge sistemáticamente del resto de la flota en el mismo tramo, es mucho más fácil identificarlo como comprometido por diferencia relativa que por análisis aislado de una sola unidad.

---

## Qué de esto demuestra el simulador de CYBER.AR

El proyecto es una demo 100% software (no transmite RF, no controla hardware real) pero su arquitectura sí modela, de forma simulada, varias de las mitigaciones de arriba:

- **Comunicaciones resilientes multicanal con degradación y restauración simulada** (RF primario, RF direccional, óptico/láser y satelital), pensadas para responder al escenario de jamming/interferencia de las secciones 1, 2 y 3. El panel RED TEAM expone estos ataques como botones grandes agrupados por vector; el jamming ya no es un control abstracto sino que se modela con **fuentes de interferencia posicionadas en el mapa** (un jammer terrestre encubierto y un avión jammer que patrulla en círculos sobre el teatro): la interferencia efectiva depende de la distancia real entre el UAV y la fuente activa, no de un slider desconectado de la física del escenario.
- **Detección por consistencia cruzada de sensores**: `CANAnomalyDetector` compara la velocidad reportada por CAN contra GPS e IMU, exactamente el mecanismo descrito en las secciones 4 y 5 para separar una lectura manipulada de la realidad física del vehículo. El botón GPS/IMU spoofing del panel RED TEAM sesga la altitud reportada de un UAV manteniendo su trayectoria real, para ilustrar el mismo principio en la capa GNSS/IMU.
- **Un validador de seguridad (`SafetyValidator`) que gatea cualquier acción automática**: el análisis externo (broker DF AI) nunca ejecuta una mitigación directamente; se valida fuente, confianza, acción y evidencia antes de aislar la señal sospechosa (CAN SPEED), y un respaldo heurístico local actúa igual si el broker no responde a tiempo.
- **Humano en el bucle / operador en control**: el sistema aísla la señal comprometida y sostiene el vehículo con las fuentes confiables restantes, pero no toma decisiones de misión sin trazabilidad ni sin que quede registrado el evento.
- **Comparación post-misión entre vehículos hermanos que recorrieron la misma ruta (sección 9)**: con una flota de hasta 3 UAV volando la misma ruta con offset, el debriefing posterior a la misión compara altitud/velocidad/batería entre unidades y señala, mediante un detector estadístico de outliers (con respaldo local instantáneo, confirmado o refinado después por el broker DF AI) qué dron y qué componente diverge del resto de la flota.

**Limitaciones conocidas, fuera de alcance de esta demo:**

- No hay hardware RF real: jamming, degradación de canales y failover son completamente simulados en el motor de escenario.
- No hay firmware ni cadena de suministro real (sección 6): no existe dispositivo embebido físico que actualizar o falsificar.
- No hay bus CAN físico ni interfaz a vehículos reales: `CANSimulationEngine` genera mensajes ficticios; la inyección de tramas en un bus físico no está implementada.
- La validación cooperativa entre vehículos es post-misión (debriefing), no una corrección en tiempo real durante el vuelo; no hay medición de distancia relativa entre unidades (p. ej. UWB) ni reasignación automática de ruta ante un dron sospechoso.
- Coordenadas, distancias y velocidades del teatro son ilustrativas; no hay cifrado, GPS ni RF reales en ningún punto del sistema, como el propio README documenta.
