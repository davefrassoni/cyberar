<script setup>
defineProps({ telemetry: Object });
</script>
<template>
  <section class="side-panel">
    <div class="panel-heading">
      <h3><span>02</span> TELEMETRÍA</h3>
      <span class="tiny green">GPS ONLINE</span>
    </div>
    <div class="telemetry-grid">
      <div>
        <label>ALTITUD</label
        ><strong
          >{{ telemetry.altitude.toLocaleString("es-AR")
          }}<small>m</small></strong
        >
      </div>
      <div>
        <label>VELOCIDAD</label
        ><strong>{{ telemetry.speed }}<small>km/h</small></strong>
      </div>
      <div>
        <label>RUMBO</label
        ><strong>{{ telemetry.heading }}<small>°</small></strong>
      </div>
      <div>
        <label>BATERÍA</label
        ><strong
          >{{ Math.round(telemetry.battery) }}<small>%</small
          ><span class="battery"
            ><i :style="{ width: telemetry.battery + '%' }" /></span
        ></strong>
      </div>
    </div>
    <div class="data-row">
      <span>POSICIÓN</span
      ><b
        >{{ Math.abs(telemetry.latitude).toFixed(4) }}° S /
        {{ Math.abs(telemetry.longitude).toFixed(4) }}° O</b
      >
    </div>
    <div class="data-row">
      <span>DISTANCIA A BASE</span><b>{{ telemetry.distance_to_base }} km</b>
    </div>
  </section>
</template>
