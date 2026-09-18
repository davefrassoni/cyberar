<script setup>
import { ref } from "vue";
import { command } from "../stores/mission";
defineProps({ state: Object, busy: Boolean });
const redTeam = ref(false);
const faultDrone = ref(0);
const faultLevel = ref(60);
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
      class="add-drone"
      :disabled="busy || (state.drones?.length || 1) >= 3 || state.phase === 'MISSION_COMPLETE'"
      :title="state.phase === 'MISSION_COMPLETE' ? 'Reiniciá la demo para agregar más UAV' : (state.drones?.length || 1) >= 3 ? 'La flota ya alcanzó el máximo de 3 UAV' : 'Despega otro UAV desde la base'"
      @click="command('add_drone')"
    >
      ＋ AGREGAR UAV <small>{{ state.drones?.length || 1 }}/3</small></button
    ><button
      :class="['red-button', { selected: redTeam }]"
      @click="redTeam = !redTeam"
      :aria-expanded="redTeam"
    >
      △ RED TEAM
    </button>
  </div>
  <div class="can-controls" v-if="state.ugv && state.scenario_meta?.has_ugv">
    <span class="control-label">{{ state.ugv.asset }} / CAN SIMULADO</span>
    <button :disabled="busy" @click="command('can_start')">INICIAR ANOMALÍA CAN</button>
    <button :disabled="busy" @click="command('can_increase')">AUMENTAR ANOMALÍA</button>
    <button :disabled="busy" @click="command('can_restore')">RESTAURAR CAN</button>
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
    <div v-if="state.drones?.length > 1" class="fault-injection">
      <p>Sesga únicamente la altitud reportada por el dron elegido (misma trayectoria real) para simular un sensor fallado.</p>
      <div class="fault-controls">
        <select v-model.number="faultDrone" :disabled="busy">
          <option v-for="(drone, i) in state.drones" :key="drone.id" :value="i">{{ drone.id }}</option>
        </select>
        <label class="slider-label"
          >NIVEL DE FALLA <b>{{ faultLevel }}%</b
          ><input
            aria-label="Nivel de falla de sensor"
            type="range"
            min="0"
            max="100"
            step="1"
            v-model.number="faultLevel"
            :disabled="busy"
        /></label>
        <button :disabled="busy" @click="command('set_drone_fault', { drone: faultDrone, level: faultLevel })">
          APLICAR FALLA
        </button>
        <button :disabled="busy" @click="command('clear_drone_faults')">
          RESTAURAR SENSORES
        </button>
      </div>
    </div>
  </section>
</template>
