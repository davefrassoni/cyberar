import { reactive } from "vue";
import { request, socketURL } from "../services/api";
export const store = reactive({
  authenticated: false,
  loading: true,
  state: null,
  connected: false,
  error: "",
  busy: false,
  lastFrame: 0,
  stale: false,
  debrief: null,
});
let socket,
  retry,
  watchdog,
  debriefPoll,
  attempts = 0,
  generation = 0;
function apply(data) {
  if (!data.mission_id) return;
  if (
    !store.state ||
    data.mission_id !== store.state.mission_id ||
    data.revision >= store.state.revision
  )
    store.state = data;
  store.lastFrame = Date.now();
  store.stale = false;
}
export async function bootstrap() {
  try {
    store.authenticated = (await request("session")).authenticated;
    if (store.authenticated) await loadMission();
  } catch (error) {
    store.error = error.message;
  } finally {
    store.loading = false;
  }
}
export async function login(username, password) {
  store.error = "";
  store.busy = true;
  try {
    await request("login", { username, password });
    store.authenticated = true;
    await loadMission();
  } catch (error) {
    store.error = error.message;
  } finally {
    store.busy = false;
  }
}
async function loadMission() {
  apply(await request("state"));
  connect();
}
function connect() {
  const current = ++generation;
  clearTimeout(retry);
  clearInterval(watchdog);
  if (socket) {
    socket.onclose = null;
    socket.close();
  }
  socket = new WebSocket(socketURL());
  socket.onopen = () => {
    store.connected = true;
    attempts = 0;
    store.lastFrame = Date.now();
  };
  socket.onmessage = (event) => {
    try {
      apply(JSON.parse(event.data));
    } catch {
      store.error = "Estado recibido inválido";
    }
  };
  socket.onclose = async (event) => {
    if (current !== generation) return;
    store.connected = false;
    if (!store.authenticated) return;
    if (event.code === 4401) {
      store.authenticated = false;
      store.state = null;
      return;
    }
    // Handshake rejection often surfaces as 1006, including expired sessions.
    try {
      if (!(await request("session")).authenticated) {
        store.authenticated = false;
        store.state = null;
        return;
      }
    } catch {}
    retry = setTimeout(connect, Math.min(15000, 1000 * 2 ** attempts++));
  };
  watchdog = setInterval(() => {
    store.stale = Date.now() - store.lastFrame > 5000;
  }, 2000);
}
export async function command(action, value) {
  if (store.busy) return;
  store.busy = true;
  store.error = "";
  try {
    apply(await request("control", { action, value }));
  } catch (error) {
    store.error = error.message;
    if (error.status === 401) store.authenticated = false;
  } finally {
    store.busy = false;
  }
}
export async function loadDebrief() {
  store.debrief = await request("debrief");
  return store.debrief;
}
export async function requestDebrief() {
  await command("request_debrief");
  await loadDebrief();
  clearInterval(debriefPoll);
  let attempts = 0;
  debriefPoll = setInterval(async () => {
    attempts += 1;
    if (attempts > 20 || store.debrief?.status === "DONE") {
      clearInterval(debriefPoll);
      return;
    }
    try {
      await loadDebrief();
    } catch {
      clearInterval(debriefPoll);
    }
  }, 3000);
}
export async function logout() {
  try {
    await request("logout", {});
    store.authenticated = false;
    store.state = null;
    store.debrief = null;
    generation++;
    clearTimeout(retry);
    clearInterval(watchdog);
    clearInterval(debriefPoll);
    socket?.close();
    await request("session");
  } catch (error) {
    store.error = error.message;
  }
}
export const phaseLabel = (phase) =>
  ({
    PREPARING: "LISTA PARA INICIAR",
    TAKEOFF: "DESPEGUE",
    TRANSIT: "EN TRÁNSITO",
    RECON: "RECONOCIMIENTO",
    RETURN: "REGRESANDO A BASE",
    LANDED: "EN TIERRA",
    MISSION_COMPLETE: "MISIÓN COMPLETADA",
  })[phase] || phase;
export const clock = (seconds) =>
  `${String(Math.floor(seconds / 60)).padStart(2, "0")}:${String(seconds % 60).padStart(2, "0")}`;
export const CONTROL_MODES = [
  { id: "AUTONOMOUS_ROUTE", label: "AUTÓNOMO", detail: "Ruta de vuelo precargada" },
  { id: "MANUAL_REMOTE", label: "MANUAL", detail: "Control remoto a distancia" },
  { id: "AUTONOMOUS_AI_VISION", label: "AUTÓNOMO IA", detail: "Video procesado con modelo interno" },
];
export const controlModeLabel = (mode) =>
  CONTROL_MODES.find((m) => m.id === mode)?.label || "CONTROL DESCONOCIDO";
export const COMM_TYPES = [
  { id: "RF-PRIMARY", label: "RF" },
  { id: "RF-DIRECTIONAL", label: "RF DIRECCIONAL" },
  { id: "SATELLITE-FALLBACK", label: "SATELITAL" },
  { id: "OPTICAL-LINK", label: "LÁSER" },
  { id: "TETHERED-FIBER", label: "FIBRA (CABLE)" },
];
