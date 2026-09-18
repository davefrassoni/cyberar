<script setup>
import { command } from "../stores/mission";
defineProps({ state: Object, busy: Boolean });
const SCENARIOS = [
  { key: "atlantic", label: "ATLÁNTICO" },
  { key: "vaca-muerta", label: "CUENCA NEUQUINA" },
  { key: "triple-frontera", label: "TRIPLE FRONTERA" },
];
</script>
<template>
  <div class="demo-controls scenario-controls">
    <span class="control-label">ESCENARIO</span>
    <button
      v-for="s in SCENARIOS"
      :key="s.key"
      :class="{ selected: state.scenario_meta?.key === s.key }"
      :disabled="busy"
      @click="command('select_scenario', s.key)"
    >
      {{ s.label }}
    </button>
    <div class="speed-controls">
      <span class="control-label">FLOTA</span>
      <button
        v-for="n in [1, 2, 3]"
        :key="n"
        :class="{ selected: state.scenario_meta?.fleet_size === n }"
        :disabled="busy"
        @click="command('set_fleet_size', n)"
      >
        {{ n }}×
      </button>
    </div>
  </div>
</template>
