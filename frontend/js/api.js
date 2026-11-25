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

export async function postOptimizar(objetivo, variables) {
  const resp = await fetch("/api/optimizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ objetivo, variables }),
  });
  return parsearRespuesta(resp);
}

export async function postAnalizarDiseno(payload) {
  const resp = await fetch("/api/diseno/analizar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parsearRespuesta(resp);
}

export async function fetchHistorico() {
  const resp = await fetch("/api/historico");
  return parsearRespuesta(resp);
}

export async function postGuardarHistorico(payload) {
  const resp = await fetch("/api/historico", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  return parsearRespuesta(resp);
}

export async function deleteHistorico(id) {
  const resp = await fetch(`/api/historico/${encodeURIComponent(id)}`, {
    method: "DELETE",
  });
  return parsearRespuesta(resp);
}

export async function postImportarHistorico(registros) {
  const resp = await fetch("/api/historico/importar", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ registros }),
  });
  return parsearRespuesta(resp);
}
