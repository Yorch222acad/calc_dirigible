/**
 * api.js — Módulo cliente HTTP para comunicarse con el backend FastAPI (app.py).
 */

async function parsearRespuesta(resp) {
  const data = await resp.json().catch(() => ({}));
  if (!resp.ok) {
    const detalle = data.detail || `Error HTTP ${resp.status}`;
    throw new Error(detalle);
  }
  return data;
}

export async function fetchEstado() {
  const resp = await fetch("/api/estado");
  return parsearRespuesta(resp);
}

export async function fetchDetalleVariable(nombre) {
  const resp = await fetch(`/api/variable/${encodeURIComponent(nombre)}`);
  return parsearRespuesta(resp);
}

export async function postEquilibrio(fijas, protegidas = []) {
  const resp = await fetch("/api/equilibrio", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ fijas, protegidas }),
  });
  return parsearRespuesta(resp);
}

export async function postModificar(entradas) {
  const resp = await fetch("/api/modificar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ entradas }),
  });
  return parsearRespuesta(resp);
}

export async function postReiniciar() {
  const resp = await fetch("/api/reiniciar", {
    method: "POST",
  });
  return parsearRespuesta(resp);
}
