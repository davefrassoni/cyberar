<script setup>
import { onMounted, ref, watch } from "vue";
import {
  store,
  bootstrap,
  login,
  logout,
  phaseLabel,
  clock,
  requestDebrief,
} from "./stores/mission";
import DebriefView from "./debrief/DebriefView.vue";
import TacticalMap from "./map/TacticalMap.vue";
import TelemetryPanel from "./telemetry/TelemetryPanel.vue";
import CommsPanel from "./communications/CommsPanel.vue";
import CommsAlert from "./communications/CommsAlert.vue";
import AIPanel from "./ai/AIPanel.vue";
import EventLog from "./events/EventLog.vue";
import DemoControls from "./demo/DemoControls.vue";
import ScenarioControls from "./scenario/ScenarioControls.vue";
import UGVPanel from "./ugv/UGVPanel.vue";
import UGVView from "./ugv/UGVView.vue";
const activeAsset = ref("UAV");
const activeDrone = ref(0);
const showDebrief = ref(false);
const username = ref(""),
  password = ref("");
async function submitLogin() {
  await login(username.value, password.value);
  password.value = "";
}
async function openDebrief() {
  await requestDebrief();
  showDebrief.value = true;
}
watch(
  () => store.state?.drones?.length,
  (length) => {
    if (length && activeDrone.value >= length) activeDrone.value = 0;
  },
);
onMounted(bootstrap);
</script>
<template>
  <div class="app-shell">
    <header class="main-header">
      <a class="brand" href="/cyberar/" aria-label="CYBER.AR inicio"
        ><span class="brand-mark">⌖</span> CYBER<span class="orange-text"
          >.AR</span
        ><small>2026</small></a
      >
      <div class="header-title">
        SISTEMA DE COMUNICACIONES RESILIENTES
        <span>PLATAFORMA DE SIMULACIÓN UAV</span>
      </div>
      <div class="header-status">
        <span class="simulation-tag">● 100% SOFTWARE</span
        ><span
          v-if="store.authenticated"
          :class="['connection', { offline: !store.connected || store.stale }]"
          ><i class="dot" />
          {{
            store.connected && !store.stale
              ? "SISTEMA EN LÍNEA"
              : "RECONECTANDO"
          }}</span
        ><button
          v-if="store.authenticated"
          class="logout"
          @click="logout"
          aria-label="Cerrar sesión"
        >
          SALIR ↗
        </button>
      </div>
    </header>
    <div v-if="store.error" class="error-banner" role="alert">
      {{ store.error }}
      <button @click="store.error = ''" aria-label="Cerrar error">×</button>
    </div>
    <div v-if="store.loading" class="loading">
      INICIALIZANDO SISTEMAS<span class="loading-dot">…</span>
    </div>
    <main v-else-if="!store.authenticated" class="login-screen">
      <div class="login-grid" />
      <div class="login-orbit orbit-one" />
      <div class="login-orbit orbit-two" />
      <div class="login-copy">
        <span class="eyebrow orange-text">CYBER.AR 2026 / ATLÁNTICO SUR</span>
        <h1>La misión<br />continúa<span>.</span></h1>
        <p>Un enlace puede fallar.<br />Un sistema resiliente se adapta.</p>
        <div class="principles">
          <span>01 DETECTAR</span><span>02 ANALIZAR</span><span>03 ADAPTAR</span
          ><span>04 CONTINUAR</span>
        </div>
      </div>
      <form class="login-card" @submit.prevent="submitLogin">
        <span class="eyebrow">ACCESO RESTRINGIDO / DEMOSTRACIÓN</span>
        <h2>Centro de operaciones</h2>
        <p>Identificate para acceder al simulador.</p>
        <label for="username">USUARIO</label
        ><input
          id="username"
          v-model="username"
          autocomplete="username"
          required
          autofocus
        /><label for="password">CONTRASEÑA</label
        ><input
          id="password"
          v-model="password"
          autocomplete="current-password"
          type="password"
          required
        /><button class="primary" :disabled="store.busy">
          {{ store.busy ? "VERIFICANDO…" : "INGRESAR AL SISTEMA →" }}
        </button>
        <div class="login-note">
          ▣ SESIÓN SEGURA <span>SOLO PERSONAL AUTORIZADO</span>
        </div>
      </form>
      <div class="login-bottom">
        SIMULACIÓN 100% SOFTWARE · SIN HARDWARE NI EMISIONES RF
        <span>PROTOTIPO / V0.1</span>
      </div>
    </main>
    <main v-else-if="store.state" class="dashboard">
      <CommsAlert :state="store.state" />
      <section class="mission-bar">
        <div class="mission-title">
          <span class="eyebrow">MISIÓN 001 / {{ store.state.scenario_meta?.subtitle?.toUpperCase() }}</span>
          <h1>{{ store.state.scenario_meta?.label?.toUpperCase() }}</h1>
        </div>
        <div class="mission-meta">
          <div>
            <label>ESTADO DE MISIÓN</label
            ><b class="green"
              ><i class="dot" />{{ phaseLabel(store.state.phase) }}</b
            >
          </div>
          <div>
            <label>TIEMPO DE MISIÓN</label
            ><b class="mission-clock"
              >T+{{ clock(store.state.elapsed)
              }}<small> / {{ clock(store.state.duration) }}</small></b
            >
          </div>
          <div>
            <label>CHECKPOINT</label
            ><b
              >{{ store.state.drones[0].current_checkpoint }}
              <span class="muted"
                >→ {{ store.state.drones[0].next_checkpoint }}</span
              ></b
            >
          </div>
        </div>
        <button v-if="store.state.phase === 'MISSION_COMPLETE'" class="debrief-button" :disabled="store.busy" @click="openDebrief">
          ▤ VER DEBRIEFING
        </button>
        <span class="mission-number">{{ (store.state.scenario_meta?.key || "").slice(0, 3).toUpperCase() }} / 01</span>
      </section>
      <div v-if="store.stale" class="stale-banner" role="status">
        DATOS SIN ACTUALIZAR · Esperando conexión con el servidor
      </div>
      <ScenarioControls :state="store.state" :busy="store.busy" />
      <DemoControls :state="store.state" :busy="store.busy" />
      <nav class="asset-tabs" aria-label="Activos de la misión">
        <span class="eyebrow">ACTIVOS</span>
        <button :class="{ selected: activeAsset === 'UAV' }" :aria-pressed="activeAsset === 'UAV'" @click="activeAsset = 'UAV'">⌖ FLOTA UAV <small>● {{ store.state.drones.length }} EN VUELO</small></button>
        <button :class="{ selected: activeAsset === 'UGV' }" :aria-pressed="activeAsset === 'UGV'" @click="activeAsset = 'UGV'">▰ {{ store.state.ugv?.asset || 'UGV-01' }} <small>● {{ store.state.ugv?.status || 'OPERATIVO' }}</small></button>
      </nav>
      <nav v-if="activeAsset === 'UAV' && store.state.drones.length > 1" class="asset-tabs drone-tabs" aria-label="Drones de la flota">
        <span class="eyebrow">DRON ACTIVO</span>
        <button v-for="(drone, i) in store.state.drones" :key="drone.id" :class="{ selected: activeDrone === i }" :aria-pressed="activeDrone === i" @click="activeDrone = i">{{ drone.id }}</button>
      </nav>
      <div :class="['workspace', { 'ugv-workspace': activeAsset === 'UGV' }]">
        <TacticalMap v-if="activeAsset === 'UAV'" :state="store.state" @select-ugv="activeAsset = 'UGV'" @select-drone="(i) => (activeDrone = i)" />
        <UGVView v-else-if="store.state.ugv" :state="store.state" />
        <aside v-if="activeAsset === 'UAV'">
          <TelemetryPanel :telemetry="store.state.drones[activeDrone] || store.state.drones[0]" /><CommsPanel
            :state="store.state"
          /><AIPanel :state="store.state" />
        </aside>
        <aside v-else-if="store.state.ugv"><UGVPanel :ugv="store.state.ugv" /></aside>
      </div>
      <section v-if="store.state.ugv?.untrusted" class="resilience-summary">
        <div><span>FLOTA UAV / CAPA EXTERNA</span><b>COMUNICACIONES {{ store.state.interference ? 'EN OBSERVACIÓN' : 'OPERATIVAS ✓' }}</b></div>
        <div><span>{{ store.state.ugv.asset }} / CAPA INTERNA</span><b>ANOMALÍA AISLADA · MODO DEGRADADO ✓</b></div>
        <p>RESILIENCIA MULTICAPA · CAN aislado ✓ · Correlación de sensores ✓ · {{ store.state.ugv.analysis.source === 'DF AI' ? 'Análisis DF AI ✓' : 'Respuesta local ✓ / DF AI no confirmado' }}</p>
      </section>
      <EventLog
        :events="store.state.events"
      />
      <footer class="system-footer">
        <span
          ><i class="dot" /> MOTOR DE SIMULACIÓN V1 <b>/</b>
          {{
            store.state.automatic ? "ESCENARIO AUTOMÁTICO" : "CONTROL MANUAL"
          }}</span
        ><span
          >DETECTAR <b>→</b> ANALIZAR <b>→</b> ADAPTAR <b>→</b> CONTINUAR
          MISIÓN</span
        ><span>CYBER.AR // 2026</span>
      </footer>
      <DebriefView v-if="showDebrief" :state="store.state" :debrief="store.debrief" @close="showDebrief = false" />
    </main>
    <main v-else class="loading">
      No se pudo cargar la misión.
      <button @click="bootstrap">REINTENTAR</button>
    </main>
  </div>
</template>
