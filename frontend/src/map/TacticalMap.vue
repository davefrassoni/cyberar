<script setup>
import { computed, ref } from "vue";
import { command } from "../stores/mission";
defineEmits(["select-ugv", "select-drone"]);
const props = defineProps({ state: Object });
const showZones = ref(true);
const zoom = ref(1);
const worldRef = ref(null);
const dragIndex = ref(null);
const dragPoint = ref(null);
const scenarioKey = computed(() => props.state.scenario_meta?.key || "atlantic");
const vehicleType = computed(() => props.state.scenario_meta?.vehicle_type || "FIXED_WING");
const editable = computed(() => props.state.phase === "PREPARING" && !props.state.running);
const route = computed(() => props.state.route.map((p) => `${p.x},${p.y}`).join(" "));
const trailFor = (drone) =>
  [...props.state.route.slice(0, drone.checkpoint_index + 1), drone]
    .map((p) => `${p.x},${p.y}`)
    .join(" ");
const checkpointPosition = (cp, i) =>
  dragIndex.value === i ? dragPoint.value : cp;
function toWorldPoint(evt) {
  const ctm = worldRef.value?.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  const point = new DOMPoint(evt.clientX, evt.clientY).matrixTransform(ctm.inverse());
  return { x: point.x, y: point.y };
}
function onCheckpointDown(evt, index) {
  if (!editable.value || index === 0) return;
  evt.target.setPointerCapture?.(evt.pointerId);
  dragIndex.value = index;
  dragPoint.value = toWorldPoint(evt);
}
function onCheckpointMove(evt) {
  if (dragIndex.value === null) return;
  dragPoint.value = toWorldPoint(evt);
}
function onCheckpointUp() {
  if (dragIndex.value === null) return;
  const index = dragIndex.value;
  const point = dragPoint.value;
  dragIndex.value = null;
  dragPoint.value = null;
  command("set_checkpoint", { index, x: Math.round(point.x * 10) / 10, y: Math.round(point.y * 10) / 10 });
}
</script>
<template>
  <section class="map-panel">
    <div class="map-top">
      <div>
        <span class="eyebrow">01 / TEATRO DE OPERACIONES</span>
        <h2>{{ state.scenario_meta?.label?.toUpperCase() || "OPERACIÓN ATLÁNTICO" }} <span>{{ state.scenario_meta?.subtitle }}</span></h2>
      </div>
      <span class="map-live"><i class="dot" /> ESCENARIO SIMULADO</span>
    </div>
    <div class="map-viewport">
      <div v-if="editable" class="map-edit-banner">
        ✎ MODO EDICIÓN DE RUTA <small>Arrastrá los checkpoints (excepto la base) para reubicarlos antes de iniciar</small>
      </div>
      <div v-else class="map-edit-banner map-edit-banner-locked">
        🔒 RUTA BLOQUEADA <small>Reiniciá la demo (↺ REINICIAR DEMO) para poder editar los checkpoints</small>
      </div>
      <svg
        class="tactical-map"
        viewBox="0 0 1100 650"
        role="img"
        aria-label="Mapa ficticio del teatro de operaciones con la ruta y posición de la flota"
        @pointermove="onCheckpointMove"
        @pointerup="onCheckpointUp"
        @pointercancel="onCheckpointUp"
      >
        <defs>
          <pattern id="grid" width="55" height="50" patternUnits="userSpaceOnUse">
            <path d="M55 0H0V50" fill="none" stroke="#1b252b" stroke-width=".7" />
          </pattern>
          <pattern id="land" width="7" height="7" patternUnits="userSpaceOnUse" patternTransform="rotate(35)">
            <path d="M0 0V7" stroke="#233038" stroke-width=".7" />
          </pattern>
          <pattern id="steppe" width="26" height="26" patternUnits="userSpaceOnUse">
            <circle cx="4" cy="4" r="1.1" fill="#3a2f22" /><circle cx="17" cy="14" r="1.1" fill="#3a2f22" />
            <circle cx="10" cy="22" r="1.1" fill="#3a2f22" />
          </pattern>
          <pattern id="riverbank" width="9" height="9" patternUnits="userSpaceOnUse" patternTransform="rotate(20)">
            <path d="M0 4.5H9" stroke="#20362a" stroke-width=".8" />
          </pattern>
          <radialGradient id="coverage">
            <stop offset="0" stop-color="#58bba8" stop-opacity=".07" />
            <stop offset="1" stop-color="#58bba8" stop-opacity="0" />
          </radialGradient>
          <radialGradient id="disruption">
            <stop offset="0" stop-color="#ff824d" stop-opacity=".14" />
            <stop offset="1" stop-color="#ff824d" stop-opacity="0" />
          </radialGradient>
        </defs>
        <rect width="1100" height="650" :fill="scenarioKey === 'vaca-muerta' ? '#241d15' : scenarioKey === 'triple-frontera' ? '#0f1f16' : '#0c1416'" />
        <rect width="1100" height="650" fill="url(#grid)" />
        <g class="coordinates">
          <text v-for="(x, i) in [110, 330, 550, 770, 990]" :key="x" :x="x" y="25">{{ 67 - i * 2 }}° O</text>
          <text v-for="(y, i) in [100, 250, 400, 550]" :key="y" x="1060" :y="y">{{ 48 + i }}° S</text>
        </g>
        <g :transform="`translate(${550 * (1 - zoom)} ${325 * (1 - zoom)}) scale(${zoom})`" ref="worldRef">
          <!-- Atlántico: costa e islas ficticias -->
          <template v-if="scenarioKey === 'atlantic'">
            <rect width="1100" height="650" fill="url(#land)" opacity=".18" />
            <g class="landmass">
              <path d="M0 0H204L209 31 187 53 214 82 202 101 225 128 216 151 240 163 234 185 208 191 213 214 195 230 204 244 178 260 164 288 173 309 149 323 143 352 124 368 131 393 104 411 98 439 68 448 78 472 49 498 62 522 33 549 31 573 8 592 0 613Z" />
              <path d="M651 224L672 207 696 218 709 202 724 208 719 226 741 222 749 236 728 248 733 259 713 270 723 286 707 295 700 318 683 324 675 303 655 320 643 310 659 289 640 283 647 263 632 253 649 243Z" />
              <path d="M773 234L791 225 806 240 829 229 839 244 858 242 867 260 851 273 872 282 885 279 903 297 885 310 893 328 872 335 852 318 842 337 822 341 825 322 805 325 811 302 790 309 775 295 788 281 768 270 782 256Z" />
              <path d="M742 334l12-9 14 8-6 12-18 2Z M792 354l10-4 7 10-14 7Z M617 298l12-5 4 10-13 6Z" />
            </g>
            <g class="terrain">
              <path d="M34 35L128 108 104 157 149 183 131 231 103 280 66 321 85 359 38 405M80 56L157 118 135 161 176 185M660 250l29-17 17 21-24 38M793 251l35 10 1 27 32 16" />
            </g>
            <text class="sea-label" x="450" y="160">O C É A N O A T L Á N T I C O</text>
            <text class="geo-label" x="37" y="190">COSTA ARGENTINA</text>
            <text class="geo-sub" x="37" y="207">BASE COSTERA / SIMULADA</text>
            <text class="geo-label" x="623" y="370">ISLA OESTE</text>
            <text class="geo-label" x="831" y="365">ISLA ESTE</text>
            <text class="geo-sub" x="710" y="195">ARCHIPIÉLAGO FICTICIO / ZONA DE RECONOCIMIENTO</text>
          </template>
          <!-- Cuenca Neuquina: estepa, pozos petroleros y ductos -->
          <template v-else-if="scenarioKey === 'vaca-muerta'">
            <rect width="1100" height="650" fill="url(#steppe)" opacity=".5" />
            <g class="terrain" stroke="#5a4a30">
              <path d="M40 60H1050M40 620H1050" stroke-dasharray="2 10" opacity=".3" />
            </g>
            <g class="well-pads">
              <g v-for="cp in state.route.slice(1, 6)" :key="'pad-' + cp.id" :transform="`translate(${cp.x} ${cp.y})`">
                <path d="M-16 8L-8-8H8L16 8Z" fill="none" stroke="#8a6a3c" stroke-width="1.4" />
                <line x1="0" y1="-8" x2="0" y2="-24" stroke="#8a6a3c" stroke-width="2" />
              </g>
            </g>
            <path class="pipeline" :d="'M' + state.route.slice(0, -1).map((cp) => `${cp.x} ${cp.y}`).join(' L ')" fill="none" stroke="#c98a3f" stroke-width="2" stroke-dasharray="10 6" opacity=".55" />
            <g class="landmass" transform="translate(860 380)">
              <rect x="-38" y="-30" width="76" height="60" rx="3" fill="none" stroke="#c98a3f" stroke-width="1.6" />
              <path d="M-20-30V-46M0-30V-52M20-30V-40" stroke="#c98a3f" stroke-width="2" />
            </g>
            <text class="sea-label" x="380" y="130">C U E N C A · N E U Q U I N A</text>
            <text class="geo-label" x="37" y="470">BASE OPERATIVA</text>
            <text class="geo-sub" x="37" y="487">CAMPAMENTO / SIMULADO</text>
            <text class="geo-label" x="770" y="335">COMPRESORA-01</text>
            <text class="geo-sub" x="700" y="200">CORREDOR DE DUCTOS / ZONA DE PATRULLA</text>
          </template>
          <!-- Triple Frontera: confluencia de ríos y pasos fronterizos -->
          <template v-else-if="scenarioKey === 'triple-frontera'">
            <rect width="1100" height="650" fill="url(#riverbank)" opacity=".35" />
            <g class="landmass">
              <path d="M0 0H460L440 90 480 160 430 230 470 300 400 340 0 340Z" opacity=".5" />
              <path d="M1100 0H620L660 100 610 190 660 260 700 360 1100 360Z" opacity=".5" />
            </g>
            <path class="river" d="M0 260Q260 200 430 300T760 340T1100 300" fill="none" stroke="#3f6f8a" stroke-width="10" opacity=".45" />
            <path class="river" d="M430 300Q470 420 420 560T340 650" fill="none" stroke="#3f6f8a" stroke-width="8" opacity=".4" />
            <path class="border-line" d="M0 340H430L620 190" fill="none" stroke="#d4c26a" stroke-width="1.4" stroke-dasharray="3 8" opacity=".7" />
            <g class="border-posts">
              <g v-for="cp in state.route.slice(1, 6)" :key="'post-' + cp.id" :transform="`translate(${cp.x} ${cp.y})`">
                <path d="M0-22V6" stroke="#d4c26a" stroke-width="2" />
                <path d="M0-22L14-16 0-10Z" fill="#d4c26a" opacity=".8" />
              </g>
            </g>
            <text class="sea-label" x="360" y="120">T R I P L E · F R O N T E R A</text>
            <text class="geo-label" x="37" y="120">MARGEN NORTE</text>
            <text class="geo-sub" x="37" y="137">BASE FRONTERIZA / SIMULADA</text>
            <text class="geo-label" x="640" y="270">CONFLUENCIA</text>
            <text class="geo-sub" x="700" y="440">RIBERA SUR / ZONA DE PATRULLA FLUVIAL</text>
          </template>
          <g v-if="state.ugv && state.scenario_meta?.has_ugv" class="ugv-overview">
            <polyline :points="state.ugv.route.map((p) => `${p.x},${p.y}`).join(' ')" fill="none" stroke="#8dd4bd" stroke-width="2" stroke-dasharray="2 4" />
            <g :transform="`translate(${state.ugv.position.x} ${state.ugv.position.y})`" role="button" tabindex="0" :aria-label="`Seleccionar ${state.ugv.asset}`" @click="$emit('select-ugv')" @keydown.enter="$emit('select-ugv')" @keydown.space.prevent="$emit('select-ugv')" style="cursor:pointer">
              <circle r="20" fill="#152e28" stroke="#8dd4bd" /><rect x="-11" y="-8" width="22" height="16" rx="3" fill="#8dd4bd" /><path d="M-14-10H14M-14 10H14" stroke="#e3f5e7" stroke-width="3" /><text x="25" y="4" fill="#b9e6d1" font-size="11">{{ state.ugv.asset }}</text>
            </g>
          </g>
          <g v-if="showZones" class="zones">
            <circle :cx="state.route[0].x" :cy="state.route[0].y" r="230" fill="url(#coverage)" />
            <circle :cx="state.route[0].x" :cy="state.route[0].y" r="230" />
            <circle :cx="state.route[0].x" :cy="state.route[0].y" r="145" />
            <circle :cx="state.route[4].x" :cy="state.route[4].y" r="135" />
            <circle :cx="state.route[4].x" :cy="state.route[4].y" r="138" stroke-dasharray="1 12" />
          </g>
          <g v-for="jammer in state.jammers || []" :key="jammer.id" :class="['jammer', jammer.kind.toLowerCase(), { active: jammer.active }]">
            <template v-if="jammer.active">
              <circle :cx="jammer.x" :cy="jammer.y" r="120" fill="url(#disruption)" />
              <circle :cx="jammer.x" :cy="jammer.y" r="85" />
              <circle :cx="jammer.x" :cy="jammer.y" r="120" stroke-dasharray="3 9" />
            </template>
            <g :transform="`translate(${jammer.x} ${jammer.y})`">
              <circle r="14" class="jammer-halo" />
              <path v-if="jammer.kind === 'GROUND'" d="M0-11 9 8H-9Z M0-4V9M-6 9H6" class="jammer-icon" />
              <path v-else d="M0-10 3-2 11 1 11 3 3 1 3 6 6 8 6 9 0 7-6 9-6 8-3 6-3 1-11 3-11 1-3-2Z" class="jammer-icon" />
              <text x="16" y="4">{{ jammer.label }}<tspan>{{ jammer.active ? " · ACTIVO" : "" }}</tspan></text>
            </g>
          </g>
          <polyline :points="route" class="planned-route" />
          <polyline
            v-for="(drone, i) in state.drones"
            :key="'trail-' + drone.id"
            :points="trailFor(drone)"
            :class="['flown-route', { 'flown-route-2': i === 1, 'flown-route-3': i === 2 }]"
          />
          <g
            v-for="(cp, i) in state.route.slice(0, -1)"
            :key="i"
            :class="['checkpoint', { reached: i <= state.checkpoint_index, draggable: editable && i !== 0, dragging: dragIndex === i }]"
            @pointerdown="onCheckpointDown($event, i)"
          >
            <circle
              v-if="editable && i !== 0"
              :cx="checkpointPosition(cp, i).x"
              :cy="checkpointPosition(cp, i).y"
              r="18"
              class="checkpoint-hit-area"
            />
            <circle
              :cx="checkpointPosition(cp, i).x"
              :cy="checkpointPosition(cp, i).y"
              :r="i === 0 ? 9 : editable && i !== 0 ? 8 : 5"
            />
            <circle v-if="i === 0" :cx="cp.x" :cy="cp.y" r="16" class="base-ring" />
            <text :x="checkpointPosition(cp, i).x + 12" :y="checkpointPosition(cp, i).y - 13">{{ cp.id }}</text>
          </g>
          <g
            v-for="(drone, i) in state.drones"
            :key="drone.id"
            :class="['uav', { 'uav-secondary': i > 0 }]"
            :transform="`translate(${drone.x} ${drone.y})`"
            role="button"
            tabindex="0"
            :aria-label="`Seleccionar ${drone.id}`"
            style="cursor:pointer"
            @click="$emit('select-drone', i)"
          >
            <circle r="27" class="uav-halo" />
            <circle r="17" class="uav-ring" />
            <g v-if="vehicleType === 'QUADCOPTER'" :transform="`rotate(${drone.heading})`" class="quad-body">
              <path d="M-11-11L11 11M11-11L-11 11" stroke-width="2.4" />
              <circle cx="-11" cy="-11" r="5" class="rotor" /><circle cx="11" cy="-11" r="5" class="rotor" />
              <circle cx="-11" cy="11" r="5" class="rotor" /><circle cx="11" cy="11" r="5" class="rotor" />
              <rect x="-6" y="-5" width="12" height="10" rx="2" />
            </g>
            <path v-else d="M0-14 4-3 14 4 14 7 3 4 3 10 7 13 7 15 0 13-7 15-7 13-3 10-3 4-14 7-14 4-4-3Z" :transform="`rotate(${drone.heading})`" />
            <g transform="translate(30,-53)">
              <rect width="128" height="39" rx="2" />
              <text x="10" y="15">{{ drone.id }}<tspan>●</tspan></text>
              <text x="10" y="30" class="uav-meta">{{ drone.altitude }} m / {{ drone.speed }} km/h</text>
            </g>
          </g>
        </g>
        <g class="compass" transform="translate(1030,555)">
          <circle r="26" />
          <path d="M0-21 5 6 0 1-5 6Z" />
          <text y="-35" text-anchor="middle">N</text>
          <path d="M-37 0h10m54 0h10M0 27v10" />
        </g>
        <g class="scale" transform="translate(45,596)">
          <path d="M0-5v5h100v-5M50 0v-5" />
          <text y="19">0</text>
          <text x="70" y="19">50 km*</text>
        </g>
      </svg>
      <div class="map-tools">
        <button aria-label="Acercar mapa" @click="zoom = Math.min(1.5, zoom + 0.25)">+</button
        ><button aria-label="Alejar mapa" @click="zoom = Math.max(1, zoom - 0.25)">−</button
        ><button :class="{ selected: showZones }" aria-label="Mostrar zonas de comunicación" :aria-pressed="showZones" @click="showZones = !showZones">◎</button>
      </div>
      <div v-if="state.interference >= 60" class="map-alert">
        <span>△</span> INTERFERENCIA DETECTADA
        <small>SNR EN DESCENSO · ENLACE RF DEGRADADO</small>
      </div>
    </div>
    <div class="map-bottom">
      <div class="legend">
        <span><i class="legend-line orange" /> TRAYECTORIA</span
        ><span><i class="legend-line dashed" /> RUTA PLANIFICADA</span
        ><span><i class="legend-circle" /> COBERTURA</span>
      </div>
      <span>* COORDENADAS Y ESCALA FICTICIAS</span>
    </div>
  </section>
</template>
