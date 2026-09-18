<script setup>
import { onBeforeUnmount, ref, watch } from "vue";
import { command } from "../stores/mission";
const props = defineProps({ state: Object });
const visible = ref(false);
const countdown = ref(3);
const recommended = ref(null);
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
  <div v-if="visible && recommended" class="comms-alert" role="alertdialog" aria-live="assertive">
    <span class="comms-alert-icon">△</span>
    <div class="comms-alert-body">
      <strong>DEGRADACIÓN DE ENLACE DETECTADA</strong>
      <p>Se recomienda conmutar a <b>{{ recommended.id }}</b>. Aplicando en <b>{{ countdown }}s</b>…</p>
    </div>
    <div class="comms-alert-actions">
      <button class="primary" @click="applyNow">CONMUTAR AHORA</button>
      <button @click="dismiss">CANCELAR</button>
    </div>
  </div>
</template>
