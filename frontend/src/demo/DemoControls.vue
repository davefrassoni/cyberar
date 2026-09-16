<script setup>
import { ref } from "vue";
import { command } from "../stores/mission";
defineProps({ state: Object, busy: Boolean });
const redTeam = ref(false);
</script>
<template>
  <div class="demo-controls">
    <span class="control-label">CONTROL DE DEMO</span
    ><button
      class="primary"
      :disabled="busy"
      @click="command(state.running ? 'pause' : 'start')"
    >
      {{ state.running ? "Ⅱ PAUSAR" : "▷ INICIAR" }}</button
    ><button :disabled="busy" @click="command('reset')">
      ↺ REINICIAR DEMO
    </button>
    <div class="speed-controls">
      <button
        v-for="speed in [1, 2, 4]"
        :key="speed"
        :class="{ selected: state.speed === speed }"
        :disabled="busy"
        @click="command('speed', speed)"
      >
        {{ speed }}×
      </button>
    </div>
    <button
      class="auto-demo"
      :disabled="busy"
      @click="command('automatic_demo')"
    >
      ↗ DEMO AUTOMÁTICA</button
    ><button
      :class="['red-button', { selected: redTeam }]"
      @click="redTeam = !redTeam"
      :aria-expanded="redTeam"
    >
      △ RED TEAM
    </button>
  </div>
  <section v-if="redTeam" class="red-team">
    <div class="panel-heading">
      <h3>INTERFERENCIA SIMULADA</h3>
      <button aria-label="Cerrar panel red team" @click="redTeam = false">
        ×
      </button>
    </div>
    <p>Modifica únicamente las métricas del simulador.</p>
    <label class="toggle"
      ><input
        type="checkbox"
        :checked="state.automatic"
        :disabled="busy"
        @change="command('automatic', $event.target.checked)"
      />
      Eventos automáticos</label
    ><label class="slider-label"
      >NIVEL DE INTERFERENCIA <b>{{ state.interference }}%</b
      ><input
        aria-label="Nivel de interferencia"
        type="range"
        min="0"
        max="100"
        step="1"
        :value="state.interference"
        :disabled="busy"
        @change="command('interference', Number($event.target.value))"
    /></label>
    <div class="red-actions">
      <button :disabled="busy" @click="command('interference', 35)">
        DEGRADAR RF</button
      ><button :disabled="busy" @click="command('interference', 100)">
        INTERRUMPIR RF</button
      ><button :disabled="busy" @click="command('restore')">
        RESTAURAR ENLACES
      </button>
    </div>
  </section>
</template>
