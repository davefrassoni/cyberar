<script setup>
import { ref, watch } from "vue";
import { command } from "../stores/mission";
const props = defineProps({ state: Object });
const visible = ref(false);
const applied = ref(null);
const degraded = ref(null);

function dismiss() {
  visible.value = false;
}

function startAlert(channel) {
  const alternatives = (props.state.channels || [])
    .filter((c) => c.id !== channel.id && c.available)
    .sort((a, b) => b.signal_quality - a.signal_quality);
  if (!alternatives.length) return;
  degraded.value = channel;
  applied.value = alternatives[0];
  visible.value = true;
  // El failover es automático: no hay countdown ni opción de cancelar —
  // el sistema ya conmutó, el modal solo informa qué pasó.
  command("set_channel", alternatives[0].id);
}

// Solo dispara con una degradación *nueva*. No se auto-cierra cuando el
// canal activo deja de estar degradado — eso pasa en el próximo tick,
// apenas conmuta, y cerraría el modal antes de que se llegue a leer. Cierra
// únicamente el botón CERRAR.
watch(
  () => props.state?.channels?.find((c) => c.id === props.state.active_channel)?.status,
  (current, previous) => {
    if (current === "DEGRADED" && previous && previous !== "DEGRADED") {
      const active = props.state.channels.find((c) => c.id === props.state.active_channel);
      if (active) startAlert(active);
    }
  },
);
</script>
<template>
  <div v-if="visible && applied && degraded" class="comms-modal-overlay" role="alertdialog" aria-modal="true" aria-label="Alerta de degradación de comunicaciones">
    <div class="comms-modal">
      <span class="comms-modal-icon">△</span>
      <h3>DEGRADACIÓN DE ENLACE DETECTADA</h3>
      <div class="comms-modal-row">
        <span>PROBLEMA DETECTADO</span>
        <b>{{ degraded.id }} degradado · calidad {{ Math.round(degraded.signal_quality) }}%</b>
      </div>
      <div class="comms-modal-row">
        <span>ACCIÓN TOMADA</span>
        <b>Conmutado automáticamente a {{ applied.id }} <small>({{ Math.round(applied.signal_quality) }}% calidad)</small></b>
      </div>
      <div class="comms-modal-actions">
        <button class="primary" @click="dismiss">CERRAR</button>
      </div>
    </div>
  </div>
</template>
