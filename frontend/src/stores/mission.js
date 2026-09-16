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
});
let socket,
  retry,
  watchdog,
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
export async function logout() {
  try {
    await request("logout", {});
    store.authenticated = false;
    store.state = null;
    generation++;
    clearTimeout(retry);
    clearInterval(watchdog);
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
