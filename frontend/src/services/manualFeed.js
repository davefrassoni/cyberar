// Video de referencia para la cabina de control manual, servido por el
// backend propio (ver backend/api/manual_feed.py) en vez de directo desde
// DF Drive: el share público sirve el archivo como adjunto genérico
// (octet-stream) resuelto detrás de un job asincrónico, que <video> no
// reproduce inline, y un fetch directo del navegador choca con CORS/CSP
// cuando esta app no comparte origen con davefrassoni.com. El proxy
// same-origin devuelve Content-Type video/mp4 con soporte de Range, así que
// el navegador puede reproducirlo y buscar (seek) de forma nativa.
const base = import.meta.env.BASE_URL;
export const MANUAL_FEED_URL = `${base}api/manual-feed/`;
