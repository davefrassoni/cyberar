<script setup>
defineProps({ state: Object });
</script>
<template>
  <section class="side-panel ai-panel">
    <div class="panel-heading">
      <h3><span>04</span> DF AI</h3>
      <span class="tiny">ANÁLISIS UAV PENDIENTE</span>
    </div>
    <div class="ai-status">
      <span class="ai-symbol">⌘</span>
      <div>
        <strong>MOTOR LOCAL ACTIVO</strong>
        <p v-if="state?.scenario_meta?.has_ugv">
          Comunicaciones UAV: escenario determinístico.
          El análisis DF AI de anomalías CAN está en la pestaña {{ state?.ugv?.asset || "UGV-01" }}.
        </p>
        <p v-else>
          Comunicaciones UAV: escenario determinístico. El debriefing posterior a la misión
          compara los sensores de la flota y aplica el mismo análisis DF AI.
        </p>
      </div>
    </div>
    <div class="ai-footer" v-if="state?.scenario_meta?.has_ugv">
      <span>ANÁLISIS CAN ENVIADOS</span><b>{{ state.ugv?.analysis_runs || 0 }}</b><span>PRIORIDAD</span><b>P1</b>
    </div>
    <div class="ai-footer" v-else>
      <span>ANÁLISIS</span><b>DEBRIEFING</b><span>PRIORIDAD</span><b>P2</b>
    </div>
  </section>
</template>
