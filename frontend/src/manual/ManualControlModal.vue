<script setup>
import { computed, ref } from "vue";
import { command } from "../stores/mission";
import { MANUAL_FEED_URL } from "../services/manualFeed";

const props = defineProps({ state: Object });
const emit = defineEmits(["close"]);

const videoEl = ref(null);
const loading = ref(true);
const error = ref("");

const drone = computed(() => props.state.drones?.[0] || {});
// Dial: 0m -> -120°, 1500m -> 120°, tope visual de la escala del altímetro.
const altitudeAngle = computed(() =>
  Math.max(-120, Math.min(120, (drone.value.altitude || 0) / 1500 * 240 - 120)),
);
// Dial: 0km/h -> -120°, 160km/h -> 120°, tope visual de la escala de velocidad.
const speedAngle = computed(() =>
  Math.max(-120, Math.min(120, (drone.value.speed || 0) / 160 * 240 - 120)),
);

function onLoadedMetadata() {
  // Arranca desde la mitad del clip: al principio el UAV real está en tierra,
  // y acá se busca ambientar la cabina en pleno vuelo.
  const video = videoEl.value;
  if (video && Number.isFinite(video.duration)) video.currentTime = video.duration / 2;
  loading.value = false;
}
function onCanPlay() {
  loading.value = false;
}
function onError() {
  loading.value = false;
  error.value = "No se pudo cargar el video de referencia.";
}
function releaseAutonomy() {
  command("set_control_mode", "AUTONOMOUS_ROUTE");
  emit("close");
}
</script>
<template>
  <div class="modal-backdrop cockpit-backdrop" role="dialog" aria-modal="true" aria-label="Control manual del dron">
    <section class="cockpit">
      <video
        ref="videoEl"
        :src="MANUAL_FEED_URL"
        class="cockpit-feed"
        autoplay
        muted
        loop
        playsinline
        preload="auto"
        @loadedmetadata="onLoadedMetadata"
        @canplay="onCanPlay"
        @error="onError"
      />
      <div v-if="loading || error" class="cockpit-feed-placeholder">
        <span v-if="loading && !error" class="loader" />
        <p v-else-if="error">
          ⚠ {{ error }}
          <a :href="MANUAL_FEED_URL" target="_blank" rel="noopener">Abrir video en otra pestaña</a>
        </p>
      </div>
      <div class="cockpit-vignette" />
      <button class="cockpit-close" aria-label="Cerrar control manual" @click="$emit('close')">×</button>
      <div class="cockpit-hud-top">
        <span class="cockpit-tag">● CONTROL MANUAL A DISTANCIA</span>
        <span class="cockpit-tag orange">{{ drone.id || "UAV-01" }} <small>SIMULADO</small></span>
      </div>
      <div class="cockpit-hud-bottom">
        <div class="cockpit-dial">
          <svg viewBox="-60 -60 120 120">
            <circle r="54" class="dial-face" />
            <g v-for="n in 9" :key="n" :transform="`rotate(${-120 + n * 30})`">
              <line x1="0" y1="-54" x2="0" y2="-46" class="dial-tick" />
            </g>
            <line x1="0" y1="0" x2="0" y2="-42" class="dial-needle" :transform="`rotate(${altitudeAngle})`" />
            <circle r="3" class="dial-pivot" />
          </svg>
          <label>ALTÍMETRO</label>
          <strong>{{ Math.round(drone.altitude || 0) }}<small>m</small></strong>
        </div>
        <div class="cockpit-controls">
          <div class="dpad">
            <button aria-label="Cabeceo arriba">▲</button>
            <div>
              <button aria-label="Guiñada izquierda">◀</button>
              <button aria-label="Centrar">●</button>
              <button aria-label="Guiñada derecha">▶</button>
            </div>
            <button aria-label="Cabeceo abajo">▼</button>
          </div>
          <div class="throttle">
            <button aria-label="Acelerar">THROTTLE +</button>
            <button aria-label="Desacelerar">THROTTLE −</button>
          </div>
        </div>
        <div class="cockpit-dial">
          <svg viewBox="-60 -60 120 120">
            <circle r="54" class="dial-face" />
            <g v-for="n in 9" :key="n" :transform="`rotate(${-120 + n * 30})`">
              <line x1="0" y1="-54" x2="0" y2="-46" class="dial-tick" />
            </g>
            <line x1="0" y1="0" x2="0" y2="-42" class="dial-needle" :transform="`rotate(${speedAngle})`" />
            <circle r="3" class="dial-pivot" />
          </svg>
          <label>VELOCIDAD</label>
          <strong>{{ drone.speed || 0 }}<small>km/h</small></strong>
        </div>
      </div>
      <div class="cockpit-hud-side">
        <div><label>RUMBO</label><strong>{{ drone.heading || 0 }}°</strong></div>
        <div><label>BATERÍA</label><strong>{{ Math.round(drone.battery || 0) }}%</strong></div>
        <div><label>GPS</label><strong class="green">{{ drone.gps_status || "ONLINE" }}</strong></div>
      </div>
      <button class="cockpit-release" @click="releaseAutonomy">
        ↺ DEVOLVER CONTROL AUTÓNOMO
      </button>
    </section>
  </div>
</template>
