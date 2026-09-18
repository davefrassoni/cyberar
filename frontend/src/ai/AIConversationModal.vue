<script setup>
import { computed } from "vue";
const props = defineProps({ state: Object });
defineEmits(["close"]);

const ugv = computed(() => props.state.ugv);
const analysis = computed(() => ugv.value?.analysis);
const detector = computed(() => ugv.value?.detector);

const ACTION_LABELS = {
  CONTINUE_MONITORING: "Seguir monitoreando",
  MARK_SIGNAL_UNTRUSTED: "Marcar señal como no confiable",
  ISOLATE_SIGNAL: "Aislar señal CAN SPEED",
  REDUCE_SPEED: "Reducir velocidad",
  SAFE_STOP: "Detener en zona segura",
  RETURN_TO_BASE: "Regresar a base",
};
const STATUS_LABELS = {
  IDLE: "Sin evidencia todavía",
  PENDING: "Encolado · prioridad P1",
  SUBMITTING: "Enviando al broker DF AI…",
  WAITING: "Esperando respuesta del modelo…",
  REJECTED: "Respuesta descartada (esquema inválido)",
  COMPLETED: "Respondido",
};
const waiting = computed(() => ["PENDING", "SUBMITTING", "WAITING"].includes(analysis.value?.status));
const result = computed(() => analysis.value?.result);
// Resguardo de UI: el backend siempre debería resolver esto en ~8s (respaldo
// local si el broker no contesta), pero si por lo que sea sigue "esperando"
// mucho más que eso mientras la misión corre, no tiene sentido dejar el
// spinner girando en medio de una demo — se avisa en vez de parecer roto.
const stalled = computed(() => {
  const requestedAt = analysis.value?.requested_at;
  return waiting.value && props.state.running && typeof requestedAt === "number" &&
    props.state.elapsed - requestedAt >= 20;
});
</script>
<template>
  <div class="modal-backdrop" @click.self="$emit('close')">
    <section class="ai-conversation">
      <div class="panel-heading">
        <h3>💬 CONSULTA A DF AI</h3>
        <button aria-label="Cerrar consulta a la IA" @click="$emit('close')">×</button>
      </div>
      <template v-if="!state.scenario_meta?.has_ugv">
        <p class="ai-conversation-empty">
          Este escenario no tiene vehículo terrestre con análisis CAN en curso. La consulta a DF AI
          está disponible en el debriefing, al finalizar la misión.
        </p>
      </template>
      <template v-else-if="analysis?.status === 'IDLE'">
        <p class="ai-conversation-empty">
          Todavía no hay evidencia suficiente para consultar a la IA. En cuanto el detector CAN
          acumule anomalía sostenida, acá va a aparecer la consulta en vivo.
        </p>
      </template>
      <template v-else>
        <div class="ai-bubble ai-bubble-out">
          <span class="ai-bubble-from">CYBER.AR → DF AI</span>
          <p>
            Evidencia: CAN reporta <b>{{ detector.sample.can }} km/h</b>, GPS <b>{{ detector.sample.gps }} km/h</b>,
            IMU <b>{{ detector.sample.imu }} km/h</b> (residual {{ detector.sample.residual }}). Anomaly score
            <b>{{ detector.score }}%</b> sobre umbral {{ ugv.threshold }}%. Correlación GPS↔IMU:
            <b>{{ detector.correlation.gps_imu ? "consistente" : "inconsistente" }}</b>.
          </p>
          <p class="ai-bubble-question">¿La señal CAN SPEED es confiable? ¿Qué acción recomendás?</p>
        </div>
        <div class="ai-bubble ai-bubble-in" :class="{ waiting }">
          <span class="ai-bubble-from">{{ analysis.source === "DF AI" ? "DF AI" : "RESPALDO LOCAL" }} → CYBER.AR</span>
          <p v-if="waiting && !state.running" class="ai-conversation-status">
            ⏸ Misión en pausa · el análisis se retoma al reanudar (▷ INICIAR)
          </p>
          <p v-else-if="stalled" class="ai-conversation-status">
            Sin respuesta del broker · continuidad sostenida por el respaldo local
            (GPS/IMU consistentes, señal aislada se mantiene).
          </p>
          <p v-else-if="waiting" class="ai-conversation-status">
            <span class="loader small" /> {{ STATUS_LABELS[analysis.status] }}
          </p>
          <p v-else-if="analysis.status === 'REJECTED'" class="ai-conversation-status">
            {{ STATUS_LABELS.REJECTED }} · se sostiene el respaldo local
          </p>
          <template v-else-if="result">
            <p>{{ result.assessment }}</p>
            <div class="ai-bubble-verdict">
              <span :class="['severity-tag', result.severity.toLowerCase()]">{{ result.severity }}</span>
              <span>{{ ACTION_LABELS[result.recommended_action] || result.recommended_action }}</span>
              <span class="ai-confidence">{{ Math.round(result.confidence * 100) }}% confianza</span>
            </div>
          </template>
        </div>
      </template>
    </section>
  </div>
</template>
