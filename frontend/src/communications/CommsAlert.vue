<script setup>
import { onBeforeUnmount, ref, watch } from "vue";
import { command } from "../stores/mission";
const props = defineProps({ state: Object });
const visible = ref(false);
const countdown = ref(3);
const recommended = ref(null);
const degraded = ref(null);
let timer = null;
function clearTimer() {
  if (timer) {
    clearInterval(timer);
    timer = null;
  }
}
function dismiss() {
  visible.value = false;
  clearTimer();
}
function applyNow() {
  if (recommended.value) command("set_channel", recommended.value.id);
  dismiss();
}
function startAlert(channel) {
  const alternatives = (props.state.channels || [])
    .filter((c) => c.id !== channel.id && c.available)
    .sort((a, b) => b.signal_quality - a.signal_quality);
  if (!alternatives.length) return;
  degraded.value = channel;
  recommended.value = alternatives[0];
  visible.value = true;
  countdown.value = 3;
  clearTimer();
  timer = setInterval(() => {
    countdown.value -= 1;
    if (countdown.value <= 0) applyNow();
  }, 1000);
}
watch(
  () => props.state?.channels?.find((c) => c.id === props.state.active_channel)?.status,
  (current, previous) => {
    if (current === "DEGRADED" && previous && previous !== "DEGRADED") {
      const active = props.state.channels.find((c) => c.id === props.state.active_channel);
      if (active) startAlert(active);
    } else if (current !== "DEGRADED") {
      dismiss();
    }
  },
);
onBeforeUnmount(clearTimer);
</script>
<template>
  <div v-if="visible && recommended && degraded" class="comms-modal-overlay" role="alertdialog" aria-modal="true" aria-label="Alerta de degradación de comunicaciones">
    <div class="comms-modal">
      <span class="comms-modal-icon">△</span>
      <h3>DEGRADACIÓN DE ENLACE DETECTADA</h3>
      <div class="comms-modal-row">
        <span>PROBLEMA DETECTADO</span>
        <b>{{ degraded.id }} degradado · calidad {{ Math.round(degraded.signal_quality) }}%</b>
      </div>
      <div class="comms-modal-row">
        <span>SOLUCIÓN A APLICAR</span>
        <b>Conmutar a {{ recommended.id }} <small>({{ Math.round(recommended.signal_quality) }}% calidad)</small></b>
      </div>
      <div class="comms-modal-countdown">
        Aplicando automáticamente en <span class="countdown-number">{{ countdown }}</span>
      </div>
      <div class="comms-modal-actions">
        <button class="primary" @click="applyNow">CONMUTAR AHORA</button>
        <button @click="dismiss">CANCELAR</button>
      </div>
    </div>
  </div>
</template>
