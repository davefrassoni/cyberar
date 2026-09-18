<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from "vue";
import { command } from "../stores/mission";
import { loadManualFeedVideo, MANUAL_FEED_SHARE_URL } from "../services/manualFeed";

const props = defineProps({ state: Object });
const emit = defineEmits(["close"]);

const videoUrl = ref("");
const loading = ref(true);
const progress = ref(0);
const error = ref("");
let objectUrl = "";
let controller = null;

const drone = computed(() => props.state.drones?.[0] || {});
// Dial: 0m -> -120°, 1500m -> 120°, tope visual de la escala del altímetro.
const altitudeAngle = computed(() =>
  Math.max(-120, Math.min(120, (drone.value.altitude || 0) / 1500 * 240 - 120)),
);
// Dial: 0km/h -> -120°, 160km/h -> 120°, tope visual de la escala de velocidad.
const speedAngle = computed(() =>
  Math.max(-120, Math.min(120, (drone.value.speed || 0) / 160 * 240 - 120)),
);

async function load() {
  loading.value = true;
  progress.value = 0;
  error.value = "";
  controller = new AbortController();
  try {
    objectUrl = await loadManualFeedVideo(controller.signal, (pct) => (progress.value = pct));
    videoUrl.value = objectUrl;
  } catch (err) {
    if (err.name !== "AbortError") error.value = err.message || "No se pudo cargar el video.";
  } finally {
    loading.value = false;
  }
}

function releaseAutonomy() {
  command("set_control_mode", "AUTONOMOUS_ROUTE");
  emit("close");
}

onMounted(load);
onBeforeUnmount(() => {
  controller?.abort();
  if (objectUrl) URL.revokeObjectURL(objectUrl);
});
</script>
<template>
  <div class="modal-backdrop cockpit-backdrop" role="dialog" aria-modal="true" aria-label="Control manual del dron">
    <section class="cockpit">
      <video
        v-if="videoUrl"
        :src="videoUrl"
        class="cockpit-feed"
        autoplay
        muted
        loop
        playsinline
      />
      <div v-else class="cockpit-feed cockpit-feed-placeholder">
        <template v-if="loading">
          <span class="loader" />
          <p class="cockpit-progress-label">CARGANDO FEED{{ progress ? ` · ${progress}%` : "…" }}</p>
          <div class="cockpit-progress-track"><i :style="{ width: progress + '%' }" /></div>
        </template>
        <p v-else>
          ⚠ {{ error }}
          <a :href="MANUAL_FEED_SHARE_URL" target="_blank" rel="noopener">Abrir video en otra pestaña</a>
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
