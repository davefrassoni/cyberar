<script setup>
import { computed } from 'vue';
const props = defineProps({ state: Object });
const ugv = computed(() => props.state.ugv);
const point = p => ({ x: 110 + (p.x - 660) * 10, y: 100 + (p.y - 232) * 5 });
const route = computed(() => ugv.value.route.map(p => { const q = point(p); return `${q.x},${q.y}`; }).join(' '));
const position = computed(() => point(ugv.value.position));
const trail = computed(() => [...ugv.value.route.slice(0, Math.floor(ugv.value.progress)+1), ugv.value.position].map(p => { const q = point(p); return `${q.x},${q.y}`; }).join(' '));
const plot = key => ugv.value.history.map((s,i) => `${30+i*740/39},${160-s[key]*3.5}`).join(' ');
</script>
<template>
  <section class="ugv-view">
    <div class="map-top"><div><span class="eyebrow">02 / PATRULLA TERRESTRE</span><h2>ISLA AURORA <span>UGV-01</span></h2></div><span class="tiny">100% SIMULADO</span></div>
    <div class="ground-scene">
      <svg viewBox="0 0 800 480" role="img" aria-label="UGV-01 animado recorriendo su patrulla en la isla Aurora">
        <defs><pattern id="ground-grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="#263d36" stroke-width=".6"/></pattern><radialGradient id="ground-glow"><stop stop-color="#173a2d"/><stop offset="1" stop-color="#0c1716"/></radialGradient></defs>
        <rect width="800" height="480" fill="url(#ground-glow)"/><rect width="800" height="480" fill="url(#ground-grid)"/>
        <g fill="none" stroke="#46634e" opacity=".4"><path d="M0 170Q170 20 330 110T800 40M0 205Q170 55 330 145T800 75M0 240Q170 90 330 180T800 110M0 275Q170 125 330 215T800 145M0 400Q250 490 410 395T800 380M0 430Q250 520 410 425T800 410"/></g>
        <text x="35" y="40" fill="#728d7c" font-size="10" letter-spacing="3">SECTOR TERRESTRE / A–07</text><text x="720" y="45" fill="#aac4b6" font-size="18">N ↑</text>
        <polyline :points="route" fill="none" stroke="#527f75" stroke-width="3" stroke-dasharray="5 8"/>
        <polyline :points="trail" fill="none" stroke="#8dd4bd" stroke-width="3"/>
        <g v-for="(cp,i) in ugv.route.slice(0,-1)" :key="cp.id" :transform="`translate(${point(cp).x} ${point(cp).y})`"><circle r="7" fill="#122622" :stroke="ugv.progress >= i ? '#b1e7ce' : '#5c8474'" stroke-width="2"/><text x="12" y="-14" fill="#adccba" font-size="11">{{ cp.id }}</text></g>
        <g class="ground-vehicle" :style="{ transform: `translate(${position.x}px, ${position.y}px)`, '--travel-duration': `${1/state.speed}s` }">
          <circle class="ugv-radar" r="39" fill="#8dd4bd0a" stroke="#8dd4bd55" :class="{ moving: state.running }"/>
          <g :class="{ 'vehicle-moving': state.running && ugv.speed > 0 }"><rect x="-20" y="-19" width="40" height="10" rx="3" fill="#314a43" stroke="#a3bbac"/><rect x="-20" y="9" width="40" height="10" rx="3" fill="#314a43" stroke="#a3bbac"/><path d="M-17-11H14L24 0 14 11H-17Z" :fill="ugv.untrusted ? '#d4a461' : '#8dd4bd'" stroke="#e7f4db"/><rect x="-10" y="-6" width="18" height="12" rx="2" fill="#234f40"/><circle cx="0" cy="0" r="4" fill="#c6ebd6"/></g>
          <text x="-23" y="-48" fill="#deeadf" font-size="12" font-weight="bold">UGV-01</text>
        </g>
        <g transform="translate(28 441)"><rect width="260" height="25" fill="#0a1412"/><text x="12" y="17" fill="#94b6a5" font-size="10">{{ ugv.speed }} km/h · DESTINO {{ ugv.checkpoint }}</text></g>
      </svg>
    </div>
    <div class="sensor-history"><div class="history-heading"><span>VELOCIDAD / HISTORIAL RECIENTE</span><span><i class="gps-key"/> GPS <i class="imu-key"/> IMU <i class="can-key"/> CAN</span></div><svg viewBox="0 0 800 180" role="img" aria-label="Historial comparado de velocidades GPS, IMU y CAN"><path d="M30 20V160H780M30 90H780" fill="none" stroke="#283c36"/><polyline v-for="[key,color] in [['gps','#8dd4bd'],['imu','#86b9ef'],['can','#fa8855']]" :key="key" :points="plot(key)" fill="none" :stroke="color" stroke-width="2" :stroke-dasharray="key === 'imu' ? '6 4' : undefined"/></svg></div>
    <p class="ugv-motto">Una señal válida no necesariamente contiene información confiable.</p>
  </section>
</template>
