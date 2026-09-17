<script setup>
import { computed, ref } from "vue";
defineEmits(["select-ugv"]);
const props = defineProps({ state: Object });
const showZones = ref(true);
const zoom = ref(1);
const route = computed(() =>
  props.state.route.map((p) => `${p.x},${p.y}`).join(" "),
);
const trail = computed(() =>
  [
    ...props.state.route.slice(0, props.state.checkpoint_index + 1),
    props.state.telemetry,
  ]
    .map((p) => `${p.x},${p.y}`)
    .join(" "),
);
</script>
<template>
  <section class="map-panel">
    <div class="map-top">
      <div>
        <span class="eyebrow">01 / TEATRO DE OPERACIONES</span>
        <h2>ATLÁNTICO SUR <span>SECTOR A–07</span></h2>
      </div>
      <span class="map-live"><i class="dot" /> ESCENARIO SIMULADO</span>
    </div>
    <div class="map-viewport">
      <svg
        class="tactical-map"
        viewBox="0 0 1100 650"
        role="img"
        aria-label="Mapa ficticio del Atlántico Sur con la ruta y posición del UAV"
      >
        <defs>
          <pattern
            id="grid"
            width="55"
            height="50"
            patternUnits="userSpaceOnUse"
          >
            <path
              d="M55 0H0V50"
              fill="none"
              stroke="#1b252b"
              stroke-width=".7"
            />
          </pattern>
          <pattern
            id="land"
            width="7"
            height="7"
            patternUnits="userSpaceOnUse"
            patternTransform="rotate(35)"
          >
            <path d="M0 0V7" stroke="#233038" stroke-width=".7" />
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
        <rect width="1100" height="650" fill="url(#grid)" />
        <g class="coordinates">
          <text
            v-for="(x, i) in [110, 330, 550, 770, 990]"
            :key="x"
            :x="x"
            y="25"
          >
            {{ 67 - i * 2 }}° O
          </text>
          <text v-for="(y, i) in [100, 250, 400, 550]" :key="y" x="1060" :y="y">
            {{ 48 + i }}° S
          </text>
        </g>
        <g
          :transform="`translate(${550 * (1 - zoom)} ${325 * (1 - zoom)}) scale(${zoom})`"
        >
          <g class="landmass">
            <path
              d="M0 0H204L209 31 187 53 214 82 202 101 225 128 216 151 240 163 234 185 208 191 213 214 195 230 204 244 178 260 164 288 173 309 149 323 143 352 124 368 131 393 104 411 98 439 68 448 78 472 49 498 62 522 33 549 31 573 8 592 0 613Z"
            />
            <path
              d="M651 224L672 207 696 218 709 202 724 208 719 226 741 222 749 236 728 248 733 259 713 270 723 286 707 295 700 318 683 324 675 303 655 320 643 310 659 289 640 283 647 263 632 253 649 243Z"
            />
            <path
              d="M773 234L791 225 806 240 829 229 839 244 858 242 867 260 851 273 872 282 885 279 903 297 885 310 893 328 872 335 852 318 842 337 822 341 825 322 805 325 811 302 790 309 775 295 788 281 768 270 782 256Z"
            />
            <path
              d="M742 334l12-9 14 8-6 12-18 2Z M792 354l10-4 7 10-14 7Z M617 298l12-5 4 10-13 6Z"
            />
          </g>
          <g v-if="state.ugv" class="ugv-overview">
            <polyline :points="state.ugv.route.map(p => `${p.x},${p.y}`).join(' ')" fill="none" stroke="#8dd4bd" stroke-width="2" stroke-dasharray="2 4" />
            <g :transform="`translate(${state.ugv.position.x} ${state.ugv.position.y})`" role="button" tabindex="0" aria-label="Seleccionar UGV-01" @click="$emit('select-ugv')" @keydown.enter="$emit('select-ugv')" @keydown.space.prevent="$emit('select-ugv')" style="cursor:pointer">
              <circle r="20" fill="#152e28" stroke="#8dd4bd"/><rect x="-11" y="-8" width="22" height="16" rx="3" fill="#8dd4bd"/><path d="M-14-10H14M-14 10H14" stroke="#e3f5e7" stroke-width="3"/><text x="25" y="4" fill="#b9e6d1" font-size="11">UGV-01</text>
            </g>
          </g>
          <g class="terrain">
            <path
              d="M34 35L128 108 104 157 149 183 131 231 103 280 66 321 85 359 38 405M80 56L157 118 135 161 176 185M660 250l29-17 17 21-24 38M793 251l35 10 1 27 32 16"
            />
          </g>
          <g v-if="showZones" class="zones">
            <circle cx="195" cy="230" r="230" fill="url(#coverage)" />
            <circle cx="195" cy="230" r="230" />
            <circle cx="195" cy="230" r="145" />
            <path d="M195 0V460M0 230H425" />
            <circle cx="780" cy="300" r="135" />
            <circle cx="780" cy="300" r="138" stroke-dasharray="1 12" />
          </g>
          <g v-if="state.interference > 0" class="interference-zone">
            <circle cx="585" cy="345" r="120" fill="url(#disruption)" />
            <circle cx="585" cy="345" r="85" />
            <circle cx="585" cy="345" r="120" stroke-dasharray="3 9" />
            <path d="M577 345h16m-8-8v16" />
            <text x="525" y="485">INTERFERENCIA {{ state.interference }}%</text>
          </g>
          <text class="sea-label" x="450" y="160">
            O C É A N O A T L Á N T I C O
          </text>
          <text class="geo-label" x="37" y="190">COSTA ARGENTINA</text>
          <text class="geo-sub" x="37" y="207">BASE COSTERA / SIMULADA</text>
          <text class="geo-label" x="623" y="370">ISLA OESTE</text>
          <text class="geo-label" x="831" y="365">ISLA ESTE</text>
          <text class="geo-sub" x="710" y="195">
            ARCHIPIÉLAGO FICTICIO / ZONA DE RECONOCIMIENTO
          </text>
          <polyline :points="route" class="planned-route" />
          <polyline :points="trail" class="flown-route" />
          <g
            v-for="(cp, i) in state.route.slice(0, -1)"
            :key="i"
            :class="['checkpoint', { reached: i <= state.checkpoint_index }]"
          >
            <circle :cx="cp.x" :cy="cp.y" :r="i === 0 ? 9 : 5" />
            <circle
              v-if="i === 0"
              :cx="cp.x"
              :cy="cp.y"
              r="16"
              class="base-ring"
            />
            <text :x="cp.x + 12" :y="cp.y - 13">{{ cp.id }}</text>
          </g>
          <g
            :transform="`translate(${state.telemetry.x} ${state.telemetry.y})`"
            class="uav"
          >
            <circle r="27" class="uav-halo" />
            <circle r="17" class="uav-ring" />
            <path
              d="M0-14 4-3 14 4 14 7 3 4 3 10 7 13 7 15 0 13-7 15-7 13-3 10-3 4-14 7-14 4-4-3Z"
              :transform="`rotate(${state.telemetry.heading})`"
            />
            <g transform="translate(30,-53)">
              <rect width="128" height="39" rx="2" />
              <text x="10" y="15">
                UAV–01
                <tspan>●</tspan>
              </text>
              <text x="10" y="30" class="uav-meta">
                {{ state.telemetry.altitude }} m /
                {{ state.telemetry.speed }} km/h
              </text>
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
        <button
          aria-label="Acercar mapa"
          @click="zoom = Math.min(1.5, zoom + 0.25)"
        >
          +</button
        ><button
          aria-label="Alejar mapa"
          @click="zoom = Math.max(1, zoom - 0.25)"
        >
          −</button
        ><button
          :class="{ selected: showZones }"
          aria-label="Mostrar zonas de comunicación"
          :aria-pressed="showZones"
          @click="showZones = !showZones"
        >
          ◎
        </button>
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
