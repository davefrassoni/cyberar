const base = import.meta.env.BASE_URL;
let csrf = "";
export async function request(path, body) {
  const response = await fetch(`${base}api/${path}/`, {
    method: body === undefined ? "GET" : "POST",
    credentials: "same-origin",
    headers:
      body === undefined
        ? {}
        : { "Content-Type": "application/json", "X-CSRFToken": csrf },
    ...(body === undefined ? {} : { body: JSON.stringify(body) }),
  });
  const data = await response
    .json()
    .catch(() => ({ detail: "Respuesta inesperada del servidor" }));
  if (!response.ok) {
    const error = new Error(data.detail || `Error ${response.status}`);
    error.status = response.status;
    throw error;
  }
  if (data.csrf) csrf = data.csrf;
  return data;
}
export function socketURL() {
  return `${location.protocol === "https:" ? "wss:" : "ws:"}//${location.host}${base}ws/mission/`;
}
