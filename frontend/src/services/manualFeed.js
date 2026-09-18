// Video de referencia para la cabina de control manual: un archivo compartido
// desde DF Drive (davefrassoni.com), servido vía el flujo público de descarga
// por job (creación → polling → contenido). En producción CYBER.AR corre bajo
// el mismo origen (davefrassoni.com/cyberar/), así que el fetch es same-origin;
// en desarrollo local puede fallar por CORS — se maneja como error recuperable.
const SHARE_BASE = "https://davefrassoni.com/drive/s/Bz05g6mSo_zJqeky0zeJzg";
const POLL_INTERVAL_MS = 700;
const POLL_TIMEOUT_MS = 30000;

async function pollJob(jobId, signal) {
  const deadline = Date.now() + POLL_TIMEOUT_MS;
  while (Date.now() < deadline) {
    const response = await fetch(`${SHARE_BASE}/jobs/${jobId}/`, { signal });
    if (!response.ok) throw new Error("No se pudo consultar el estado del video.");
    const data = await response.json();
    if (data.status === "completed" && data.content_url) return data;
    if (data.status === "failed") throw new Error(data.error || "Falló la carga del video.");
    await new Promise((resolve) => setTimeout(resolve, POLL_INTERVAL_MS));
  }
  throw new Error("Tiempo de espera agotado cargando el video.");
}

// El archivo pesa ~117 MB, así que se lee en streaming para poder reportar
// progreso real en vez de un spinner indefinido durante la descarga completa.
async function readWithProgress(response, onProgress) {
  const total = Number(response.headers.get("Content-Length")) || 0;
  if (!response.body || !total) return response.blob();
  const reader = response.body.getReader();
  const chunks = [];
  let received = 0;
  for (;;) {
    const { done, value } = await reader.read();
    if (done) break;
    chunks.push(value);
    received += value.length;
    onProgress?.(Math.round((received / total) * 100));
  }
  return new Blob(chunks);
}

// Devuelve una object URL reproducible en <video>. El llamador debe liberarla
// con URL.revokeObjectURL cuando ya no se use (al cerrar el modal).
export async function loadManualFeedVideo(signal, onProgress) {
  const start = await fetch(`${SHARE_BASE}/download/`, { signal });
  if (start.status === 403) throw new Error("El video compartido no permite descarga.");
  if (!start.ok) throw new Error("No se pudo iniciar la carga del video.");
  let data = await start.json();
  if (data.status !== "completed" || !data.content_url) data = await pollJob(data.job_id, signal);
  const content = await fetch(`https://davefrassoni.com${data.content_url}`, { signal });
  if (!content.ok) throw new Error("No se pudo descargar el video.");
  const raw = await readWithProgress(content, onProgress);
  // El share público sirve el archivo como adjunto genérico (octet-stream);
  // se re-envuelve con el tipo correcto para que <video> lo reproduzca inline.
  return URL.createObjectURL(new Blob([raw], { type: "video/mp4" }));
}

export const MANUAL_FEED_SHARE_URL = `${SHARE_BASE}/`;
