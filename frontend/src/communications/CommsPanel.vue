<script setup>
import { computed } from "vue";
import { command, store } from "../stores/mission";
const props = defineProps({ state: Object });
const active = computed(() =>
  props.state.channels.find((c) => c.id === props.state.active_channel),
);
</script>
<template>
  <section class="side-panel comms">
    <div class="panel-heading">
      <h3><span>03</span> COMUNICACIONES</h3>
      <span
        :class="['tiny', active.signal_quality < 55 ? 'orange-text' : 'green']"
        >{{ active.signal_quality < 55 ? "DEGRADADO" : "ESTABLE" }}</span
      >
    </div>
    <div class="active-channel">
      <div>
        <label>ENLACE ACTIVO</label><strong>{{ active.id }}</strong>
      </div>
      <span class="encryption">▣ AES–256 <small>SIMULADO</small></span>
    </div>
    <div class="quality">
      <label>CALIDAD DE ENLACE</label
      ><b :class="{ 'orange-text': active.signal_quality < 55 }"
        >{{ Math.round(active.signal_quality) }}<small>%</small></b
      >
      <div class="quality-track">
        <i
          v-for="n in 30"
          :key="n"
          :class="{
            lit: n <= active.signal_quality * 0.3,
            degraded: active.signal_quality < 55,
          }"
        />
      </div>
    </div>
    <div class="comms-grid">
      <div>
        <label>SNR</label><b>{{ active.snr }} <small>dB</small></b>
      </div>
      <div>
        <label>PACKET LOSS</label
        ><b :class="{ 'orange-text': active.packet_loss > 20 }"
          >{{ active.packet_loss }}<small>%</small></b
        >
      </div>
      <div>
        <label>LATENCIA</label><b>{{ active.latency }} <small>ms</small></b>
      </div>
      <div>
        <label>THROUGHPUT</label
        ><b>{{ active.bandwidth }} <small>Mbps</small></b>
      </div>
    </div>
    <div class="channel-list">
      <button
        v-for="channel in state.channels"
        :key="channel.id"
        type="button"
        class="channel-row"
        :disabled="store.busy || channel.id === active.id || !channel.available"
        :aria-pressed="channel.id === active.id"
        @click="command('set_channel', channel.id)"
      >
        <span
          ><i :class="['dot', { dim: channel.id !== active.id }]" />{{
            channel.id
          }}</span
        ><b>{{ channel.id === active.id ? "ACTIVO" : channel.available ? "CONMUTAR" : "NO DISPONIBLE" }}</b>
      </button>
    </div>
  </section>
</template>
