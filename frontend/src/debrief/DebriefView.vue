<script setup>
import { computed } from "vue";
defineEmits(["close"]);
const props = defineProps({ state: Object, debrief: Object });
const FIELDS = [
  { key: "altitude", label: "ALTITUD", unit: "m", max: 1450 },
  { key: "speed", label: "VELOCIDAD", unit: "km/h", max: 90 },
  { key: "battery", label: "BATERÍA", unit: "%", max: 100 },
];
const COLORS = ["#fa8855", "#86b9ef", "#d4a461"];
const componentLabels = {
  ALTITUDE_SENSOR: "SENSOR DE ALTITUD", GPS: "GPS", BATTERY: "BATERÍA",
  SPEED_SENSOR: "SENSOR DE VELOCIDAD", NONE: "NINGUNO",
};
const series = computed(() => props.debrief?.series || []);
const fleetSize = computed(() => props.state?.scenario_meta?.fleet_size || 1);
const droneIds = computed(() =>
  Array.from({ length: fleetSize.value }, (_, i) => `UAV-${String(i + 1).padStart(2, "0")}`),
);
const maxElapsed = computed(() => series.value.at(-1)?.elapsed || 1);
function plot(fieldKey, max, droneIndex) {
  const points = [];
  for (const point of series.value) {
    const drone = point.drones[droneIndex];
    if (!drone) continue;
    const x = 30 + (point.elapsed / maxElapsed.value) * 740;
    const y = 170 - Math.min(1, drone[fieldKey] / max) * 150;
    points.push(`${x},${y}`);
  }
  return points.join(" ");
}
const result = computed(() => props.debrief?.result);
const suspectLabel = computed(() =>
  result.value && result.value.suspect_drone !== "NONE"
    ? `${result.value.suspect_drone} · ${componentLabels[result.value.suspect_component]}`
    : null,
);
</script>
<template>
  <div class="debrief-overlay" role="dialog" aria-modal="true" aria-label="Debriefing de la misión">
    <div class="debrief-panel">
      <div class="debrief-header">
        <div>
          <span class="eyebrow">DEBRIEFING · {{ state.scenario_meta?.label }}</span>
          <h2>Comparación de flota <small>{{ droneIds.length }} dron{{ droneIds.length > 1 ? "es" : "" }} · T+{{ maxElapsed }}s</small></h2>
        </div>
        <button class="debrief-close" aria-label="Cerrar debriefing" @click="$emit('close')">×</button>
      </div>
      <div class="debrief-body">
        <div class="debrief-charts">
          <div v-for="field in FIELDS" :key="field.key" class="debrief-chart">
            <div class="debrief-chart-heading">
              <span>{{ field.label }} ({{ field.unit }})</span>
              <span class="debrief-legend">
                <i v-for="(id, i) in droneIds" :key="id" :style="{ color: COLORS[i] }">● {{ id }}</i>
              </span>
            </div>
            <svg viewBox="0 0 800 180" role="img" :aria-label="`Comparación de ${field.label} entre drones`">
              <path d="M30 20V170H780M30 95H780" fill="none" stroke="#283c36" />
              <polyline
                v-for="(id, i) in droneIds"
                :key="id"
                :points="plot(field.key, field.max, i)"
                fill="none"
                :stroke="COLORS[i]"
                stroke-width="2"
              />
            </svg>
          </div>
        </div>
        <aside class="debrief-insight">
          <div class="panel-heading">
            <h3>INSIGHT {{ debrief?.source === "DF AI" ? "· DF AI" : "· LOCAL" }}</h3>
            <span class="tiny">{{ debrief?.status === "DONE" && debrief?.source === "DF AI" ? "CONFIRMADO" : debrief?.status === "WAITING" ? "DF AI EN CURSO…" : "RESPALDO LOCAL" }}</span>
          </div>
          <p v-if="result">{{ result.overall_assessment }}</p>
          <p v-else class="muted">Generando insight…</p>
          <div v-if="suspectLabel" class="debrief-suspect">
            <span>COMPONENTE SOSPECHOSO</span><b>{{ suspectLabel }}</b>
          </div>
          <div v-if="result" class="trust-row"><label>CONFIANZA</label><b>{{ Math.round(result.confidence * 100) }}%</b></div>
          <progress v-if="result" max="100" :value="result.confidence * 100" aria-label="Confianza del insight" />
          <ul v-if="result?.findings?.length" class="debrief-findings">
            <li v-for="finding in result.findings" :key="finding">{{ finding }}</li>
          </ul>
        </aside>
      </div>
    </div>
  </div>
</template>
