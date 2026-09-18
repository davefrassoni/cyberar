<script setup>
import { command } from "../stores/mission";
defineProps({ state: Object, busy: Boolean });
const SCENARIOS = [
  { key: "atlantic", label: "ATLÁNTICO", subtitle: "Recon. marítimo" },
  { key: "vaca-muerta", label: "CUENCA NEUQUINA", subtitle: "Infraestructura petrolera" },
  { key: "triple-frontera", label: "TRIPLE FRONTERA", subtitle: "Patrulla fronteriza" },
];
</script>
<template>
  <section class="scenario-switcher">
    <span class="control-label">🗺 TEATRO DE OPERACIONES · ELEGIR ESCENARIO</span>
    <div class="scenario-buttons">
      <button
        v-for="s in SCENARIOS"
        :key="s.key"
        type="button"
        :class="['scenario-button', { selected: state.scenario_meta?.key === s.key }]"
        :aria-pressed="state.scenario_meta?.key === s.key"
        :disabled="busy"
        @click="command('select_scenario', s.key)"
      >
        <strong>{{ s.label }}</strong>
        <small>{{ s.subtitle }}</small>
      </button>
    </div>
  </section>
</template>
