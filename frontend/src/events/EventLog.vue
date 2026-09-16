<script setup>
import { ref, computed } from "vue";
import { clock } from "../stores/mission";
const props = defineProps({ events: Array });
const expanded = ref(false);
const recent = computed(() =>
  [...props.events].reverse().slice(0, expanded.value ? 30 : 3),
);
const labels = {
  SYSTEM: "SISTEMA",
  MISSION: "MISIÓN",
  WARNING: "ALERTA",
  COMMUNICATION: "COMMS",
  AI: "DF AI",
};
</script>
<template>
  <section :class="['event-log', { expanded }]">
    <button
      class="event-heading"
      @click="expanded = !expanded"
      :aria-expanded="expanded"
    >
      <span
        >⌁ &nbsp; REGISTRO DE EVENTOS
        <b>{{ events.length.toString().padStart(2, "0") }}</b></span
      ><span>{{ expanded ? "CONTRAER −" : "EXPANDIR +" }}</span>
    </button>
    <div class="log-lines" aria-live="polite">
      <div
        v-for="event in recent"
        :key="event.sequence"
        :class="{ warning: event.kind === 'WARNING' }"
      >
        <time>T+{{ clock(event.elapsed) }}</time
        ><span>{{ labels[event.kind] || event.kind }}</span>
        <p>{{ event.message }}</p>
        <i>···</i>
      </div>
    </div>
  </section>
</template>
