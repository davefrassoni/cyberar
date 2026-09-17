<script setup>
import { computed } from 'vue';
const props = defineProps({ ugv: Object });
const sample = computed(() => props.ugv.detector.sample);
const analysisLabel = computed(() => ({ IDLE: 'ESPERANDO EVIDENCIA', PENDING: 'ANÁLISIS PENDIENTE', SUBMITTING: 'JOB P1 EN CURSO', REJECTED: 'RESPUESTA DESCARTADA', COMPLETED: 'ANÁLISIS COMPLETADO' })[props.ugv.analysis.status]);
</script>
<template>
  <section class="side-panel ugv-instruments">
    <div class="panel-heading"><h3>UGV-01 / RED INTERNA</h3><span :class="['asset-status', { warning: ugv.detector.score >= 40 }]">{{ ugv.status }}</span></div>
    <p class="detection-stage" aria-live="polite">{{ ugv.stage }}</p>
    <div class="score-heading"><label>ANOMALY SCORE</label><strong>{{ ugv.detector.score }}<small>%</small></strong></div>
    <meter class="can-meter" min="0" max="100" :value="ugv.detector.score" :aria-label="`Anomaly score ${ugv.detector.score}%`" />
    <p class="signal-caption">Umbral de intervención: {{ ugv.threshold }}%</p>
    <div class="sensor-table">
      <div v-for="[key, title] in [['gps','GPS'], ['imu','IMU'], ['can','CAN SPEED']]" :key="key" :class="{ suspect: key === 'can' && (!ugv.detector.correlation.gps_can || ugv.untrusted) }">
        <span>{{ title }}</span><b>{{ sample[key] }} <small>km/h</small></b><span>{{ key !== 'can' || (ugv.detector.correlation.gps_can && !ugv.untrusted) ? '✓' : '⚠' }}</span>
      </div>
    </div>
    <label>CORRELACIÓN DE SENSORES</label>
    <div class="correlation-row" v-for="[key, label] in [['gps_imu','GPS ↔ IMU'],['gps_can','GPS ↔ CAN'],['imu_can','IMU ↔ CAN']]" :key="key"><span>{{ label }}</span><b :class="{ warning: !ugv.detector.correlation[key] }">{{ ugv.detector.correlation[key] ? 'CONSISTENTE' : 'INCONSISTENTE' }}</b></div>
    <div class="trust-row"><label>CONFIANZA CAN</label><b>{{ ugv.untrusted ? 0 : ugv.detector.trust }}%</b></div>
    <progress max="100" :value="ugv.untrusted ? 0 : ugv.detector.trust" aria-label="Confianza CAN" />
    <div v-if="ugv.untrusted" class="isolated-signal"><b>FUENTE DESCARTADA · CAN SPEED ⚠</b><p>Fuentes confiables: GPS ✓ / IMU ✓</p><p>Movimiento estimado: {{ ugv.speed }} km/h</p></div>
    <details class="can-evidence"><summary>EVIDENCIA · {{ ugv.detector.evidence.length }} señales</summary><p v-for="e in ugv.detector.evidence" :key="e">{{ e }}</p><p v-if="!ugv.detector.evidence.length">Sin inconsistencias.</p></details>
    <details class="can-evidence"><summary>TRÁFICO CAN FICTICIO · {{ ugv.messages.length }} MENSAJES</summary>
      <div class="can-frame" v-for="message in ugv.messages" :key="message.can_id"><b>{{ message.can_id }} / {{ message.source }}</b><span>{{ message.value }} · {{ message.frequency }} Hz · T+{{ message.timestamp }} s</span><small>Rango esperado: {{ message.expected_range.join(' a ') }}</small></div>
    </details>
  </section>
  <section class="side-panel ugv-analysis">
    <div class="panel-heading"><h3>{{ ugv.analysis.source === 'DF AI' ? 'DF AI / P1' : 'RESPALDO LOCAL' }}</h3><span class="tiny">{{ analysisLabel }}</span></div>
    <p>{{ ugv.analysis.result?.assessment || 'El detector acumula evidencia de forma independiente. DF AI analiza después; SafetyValidator valida cada acción.' }}</p>
    <span v-if="ugv.analysis.source === 'LOCAL'" class="signal-caption">Reglas determinísticas · no es una respuesta de DF AI</span>
  </section>
</template>
