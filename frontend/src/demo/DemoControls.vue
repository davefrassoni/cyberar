<script setup>
import { ref } from "vue";
import { command, COMM_TYPES, CONTROL_MODES } from "../stores/mission";
import ManualControlModal from "../manual/ManualControlModal.vue";
defineProps({ state: Object, busy: Boolean });
const redTeam = ref(false);
const manualControl = ref(false);
const faultDrone = ref(0);
const faultLevel = ref(60);
const jammerActive = (state, id) =>
  !!state.jammers?.find((j) => j.id === id)?.active;
const gpsSpoofed = (state) => (state.drone_faults?.["0"] || 0) > 0;
async function restoreAll() {
  await command("restore");
  await command("clear_drone_faults");
}
async function selectControlMode(modeId) {
  await command("set_control_mode", modeId);
  if (modeId === "MANUAL_REMOTE") manualControl.value = true;
}
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
  <div class="comm-control-bar">
    <div class="big-choice">
      <span class="control-label">ENLACE CON EL DRON</span>
      <div class="big-buttons">
        <button
          v-for="channel in COMM_TYPES"
          :key="channel.id"
          :class="{ selected: state.active_channel === channel.id }"
          :disabled="
            busy ||
            state.active_channel === channel.id ||
            !state.channels.find((c) => c.id === channel.id)?.available
          "
          @click="command('set_channel', channel.id)"
        >
          {{ channel.label }}
        </button>
      </div>
    </div>
    <div class="big-choice">
      <span class="control-label">MODO DE CONTROL</span>
      <div class="big-buttons">
        <button
          v-for="mode in CONTROL_MODES"
          :key="mode.id"
          :class="{ selected: state.control_mode === mode.id }"
          :disabled="busy"
          @click="selectControlMode(mode.id)"
        >
          {{ mode.label }}<small>{{ mode.detail }}</small>
        </button>
      </div>
    </div>
  </div>
  <div v-if="redTeam" class="modal-backdrop" @click.self="redTeam = false">
    <section class="red-team modal">
      <div class="panel-heading">
        <h3>△ RED TEAM · SIMULACIÓN DE ATAQUES</h3>
        <button aria-label="Cerrar panel red team" @click="redTeam = false">
          ×
        </button>
      </div>
      <p>Modifica únicamente las métricas del simulador. No hay hardware RF real.</p>
      <div class="red-attacks">
        <button
          :class="['attack-button', { selected: jammerActive(state, 'jam-rf-' + state.scenario_meta?.key) }]"
          :disabled="busy"
          @click="
            command('set_jammer', {
              id: 'jam-rf-' + state.scenario_meta?.key,
              active: !jammerActive(state, 'jam-rf-' + state.scenario_meta?.key),
            })
          "
        >
          📡 JAMMING RF <small>Fuente terrestre encubierta</small>
        </button>
        <button
          :class="['attack-button', { selected: jammerActive(state, 'jam-c2-' + state.scenario_meta?.key) }]"
          :disabled="busy"
          @click="
            command('set_jammer', {
              id: 'jam-c2-' + state.scenario_meta?.key,
              active: !jammerActive(state, 'jam-c2-' + state.scenario_meta?.key),
            })
          "
        >
          ✈ JAMMING C2 <small>Avión jammer en patrulla</small>
        </button>
        <button
          :class="['attack-button', { selected: gpsSpoofed(state) }]"
          :disabled="busy"
          @click="command('set_drone_fault', { drone: 0, level: gpsSpoofed(state) ? 0 : 70 })"
        >
          🛰 GPS / IMU SPOOFING <small>Sesga la altitud reportada</small>
        </button>
        <div v-if="state.ugv && state.scenario_meta?.has_ugv" class="attack-group">
          <span class="control-label">{{ state.ugv.asset }} / CAN SIMULADO</span>
          <button class="attack-button" :disabled="busy" @click="command('can_start')">
            🚌 INYECCIÓN CAN <small>Iniciar SILENT_CAN_MANIPULATION</small>
          </button>
          <div class="attack-subactions">
            <button :disabled="busy" @click="command('can_increase')">AUMENTAR</button>
            <button :disabled="busy" @click="command('can_restore')">RESTAURAR</button>
          </div>
        </div>
      </div>
      <button class="restore-all" :disabled="busy" @click="restoreAll">
        ✓ RESTAURAR TODOS LOS ENLACES Y SENSORES
      </button>
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
        </div>
      </div>
    </section>
  </div>
  <ManualControlModal v-if="manualControl" :state="state" @close="manualControl = false" />
</template>
