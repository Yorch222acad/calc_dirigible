/**
 * simulation.js — Vista interactiva para Capa 2 (Simulación temporal por fases y
 * enfriamiento pasivo no lineal) y Capa 3 (Optimizador automático multidimensional).
 */

const SVG_NS = "http://www.w3.org/2000/svg";

// Persiste la elección del usuario entre renders
const optUiState = {
  objetivo: "Etot",
  variables: new Set(["lam", "v", "mflot", "e", "T2"]),
  cargando: false,
};

function crearSvgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) {
      el.setAttribute(k, String(v));
    }
  }
  return el;
}

function escaparHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function rangoConMargen(vals, incluirCero = false) {
  let lo = Math.min(...vals);
  let hi = Math.max(...vals);
  if (incluirCero) lo = Math.min(0, lo);
  if (!Number.isFinite(lo) || !Number.isFinite(hi)) return [0, 1];
  if (Math.abs(hi - lo) < 1e-9) {
    const d = Math.max(1, Math.abs(lo) * 0.2);
    return [incluirCero ? Math.min(0, lo - d) : lo - d, hi + d];
  }
  const pad = (hi - lo) * 0.1;
  return [incluirCero ? Math.max(0, lo - pad * 0.2) : lo - pad, hi + pad];
}

function renderizarGraficaFases(contenedor, perfil, resumen) {
  const w = 620;
  const h = 290;
  const m = { top: 28, right: 56, bottom: 38, left: 56 };
  const plotW = w - m.left - m.right;
  const plotH = h - m.top - m.bottom;

  const ts = perfil.ts || [];
  const xMin = 0;
  const xMax = Math.max(1, ts[ts.length - 1] || resumen.tm || 1);
  const [y1Min, y1Max] = rangoConMargen([...perfil.ptot_w, ...perfil.pelec_w, ...perfil.pad_w], true);
  const [y2Min, y2Max] = rangoConMargen(perfil.ttot_n, true);

  const sx = (t) => m.left + ((t - xMin) / (xMax - xMin)) * plotW;
  const sy1 = (v) => m.top + plotH - ((v - y1Min) / Math.max(1e-9, y1Max - y1Min)) * plotH;
  const sy2 = (v) => m.top + plotH - ((v - y2Min) / Math.max(1e-9, y2Max - y2Min)) * plotH;

  const svg = crearSvgEl("svg", { class: "sim-svg", viewBox: `0 0 ${w} ${h}` });

  // Sombreado Fase 1 (Maniobra)
  const xManEnd = sx(Math.min(xMax, resumen.t_man));
  const wMan = Math.max(6, xManEnd - m.left);
  svg.appendChild(
    crearSvgEl("rect", {
      x: m.left,
      y: m.top,
      width: wMan,
      height: plotH,
      fill: "rgba(249, 115, 22, 0.14)",
    })
  );
  svg.appendChild(
    crearSvgEl("line", {
      x1: xManEnd,
      y1: m.top,
      x2: xManEnd,
      y2: m.top + plotH,
      stroke: "#f97316",
      "stroke-dasharray": "4 3",
      "stroke-width": 1.2,
    })
  );
  const lblMan = crearSvgEl("text", {
    x: m.left + 6,
    y: m.top + 14,
    fill: "#fdba74",
    "font-size": 10,
    "font-weight": 700,
  });
  lblMan.textContent = `Fase 1 (${resumen.t_man}s)`;
  svg.appendChild(lblMan);

  const lblCruc = crearSvgEl("text", {
    x: Math.min(m.left + plotW - 10, xManEnd + 10),
    y: m.top + 14,
    fill: "#7dd3fc",
    "font-size": 10,
    "font-weight": 700,
  });
  lblCruc.textContent = "Fase 2: Crucero estacionario (ax=az=0)";
  svg.appendChild(lblCruc);

  // Grilla y ejes Y
  for (let i = 0; i <= 4; i++) {
    const frac = i / 4;
    const y = m.top + plotH - frac * plotH;
    svg.appendChild(
      crearSvgEl("line", {
        x1: m.left,
        y1: y,
        x2: m.left + plotW,
        y2: y,
        stroke: "rgba(71, 85, 105, 0.3)",
      })
    );
    const tL = crearSvgEl("text", {
      x: m.left - 7,
      y: y + 3.5,
      "text-anchor": "end",
      fill: "#94a3b8",
      "font-size": 9.5,
      "font-family": "var(--font-mono, monospace)",
    });
    tL.textContent = (y1Min + frac * (y1Max - y1Min)).toFixed(0);
    svg.appendChild(tL);

    const tR = crearSvgEl("text", {
      x: m.left + plotW + 7,
      y: y + 3.5,
      "text-anchor": "start",
      fill: "#fdba74",
      "font-size": 9.5,
      "font-family": "var(--font-mono, monospace)",
    });
    tR.textContent = (y2Min + frac * (y2Max - y2Min)).toFixed(1);
    svg.appendChild(tR);
  }

  for (let i = 0; i <= 4; i++) {
    const tVal = xMin + (i / 4) * (xMax - xMin);
    const tx = crearSvgEl("text", {
      x: sx(tVal),
      y: m.top + plotH + 16,
      "text-anchor": "middle",
      fill: "#94a3b8",
      "font-size": 9.5,
      "font-family": "var(--font-mono, monospace)",
    });
    tx.textContent = `${tVal.toFixed(0)}s`;
    svg.appendChild(tx);
  }

  const y1Tit = crearSvgEl("text", { x: 10, y: 16, fill: "#38bdf8", "font-size": 10, "font-weight": 700 });
  y1Tit.textContent = "Potencia (W)";
  svg.appendChild(y1Tit);
  const y2Tit = crearSvgEl("text", { x: w - 10, y: 16, "text-anchor": "end", fill: "#f97316", "font-size": 10, "font-weight": 700 });
  y2Tit.textContent = "Empuje Ttot (N)";
  svg.appendChild(y2Tit);

  const trazar = (vals, syFn, color, dash = null, width = 2.0) => {
    const pts = ts.map((t, idx) => `${sx(t).toFixed(1)},${syFn(vals[idx]).toFixed(1)}`).join(" ");
    svg.appendChild(
      crearSvgEl("polyline", {
        points: pts,
        fill: "none",
        stroke: color,
        "stroke-width": width,
        "stroke-dasharray": dash,
      })
    );
  };

  trazar(perfil.ptot_w, sy1, "#38bdf8", null, 2.3);
  trazar(perfil.pelec_w, sy1, "#4ade80", null, 1.9);
  trazar(perfil.pad_w, sy1, "#facc15", "5 4", 1.5);
  trazar(perfil.ttot_n, sy2, "#f97316", "3 3", 1.8);

  contenedor.appendChild(svg);
}

function renderizarGraficaEnfriamiento(contenedor, enf) {
  const w = 620;
  const h = 290;
  const m = { top: 28, right: 24, bottom: 38, left: 54 };
  const plotW = w - m.left - m.right;
  const plotH = h - m.top - m.bottom;

  const ts = enf.ts || [];
  const xMax = Math.max(1, ts[ts.length - 1] || 1);
  const [yMin, yMax] = rangoConMargen([...enf.T2_nolineal, ...enf.T2_lineal, enf.T2_objetivo], false);

  const sx = (t) => m.left + (t / xMax) * plotW;
  const sy = (val) => m.top + plotH - ((val - yMin) / Math.max(1e-9, yMax - yMin)) * plotH;

  const svg = crearSvgEl("svg", { class: "sim-svg", viewBox: `0 0 ${w} ${h}` });

  for (let i = 0; i <= 4; i++) {
    const frac = i / 4;
    const y = m.top + plotH - frac * plotH;
    svg.appendChild(
      crearSvgEl("line", {
        x1: m.left,
        y1: y,
        x2: m.left + plotW,
        y2: y,
        stroke: "rgba(71, 85, 105, 0.3)",
      })
    );
    const lbl = crearSvgEl("text", {
      x: m.left - 7,
      y: y + 3.5,
      "text-anchor": "end",
      fill: "#94a3b8",
      "font-size": 9.5,
      "font-family": "var(--font-mono, monospace)",
    });
    lbl.textContent = `${(yMin + frac * (yMax - yMin)).toFixed(0)}°`;
    svg.appendChild(lbl);
  }

  for (let i = 0; i <= 4; i++) {
    const tVal = (i / 4) * xMax;
    const tx = crearSvgEl("text", {
      x: sx(tVal),
      y: m.top + plotH + 16,
      "text-anchor": "middle",
      fill: "#94a3b8",
      "font-size": 9.5,
      "font-family": "var(--font-mono, monospace)",
    });
    tx.textContent = `${tVal.toFixed(0)}s`;
    svg.appendChild(tx);
  }

  // Línea objetivo T2 - dTc
  const yObj = sy(enf.T2_objetivo);
  svg.appendChild(
    crearSvgEl("line", {
      x1: m.left,
      y1: yObj,
      x2: m.left + plotW,
      y2: yObj,
      stroke: "#f87171",
      "stroke-dasharray": "5 4",
      "stroke-width": 1.3,
    })
  );
  const lblObj = crearSvgEl("text", {
    x: m.left + plotW - 4,
    y: yObj - 5,
    "text-anchor": "end",
    fill: "#fca5a5",
    "font-size": 9.5,
  });
  lblObj.textContent = `Límite T2 - dTc = ${enf.T2_objetivo}°C`;
  svg.appendChild(lblObj);

  const trazar = (vals, color, dash = null, width = 2.1) => {
    const pts = ts.map((t, idx) => `${sx(t).toFixed(1)},${sy(vals[idx]).toFixed(1)}`).join(" ");
    svg.appendChild(
      crearSvgEl("polyline", {
        points: pts,
        fill: "none",
        stroke: color,
        "stroke-width": width,
        "stroke-dasharray": dash,
      })
    );
  };

  trazar(enf.T2_lineal, "#94a3b8", "5 4", 1.7);
  trazar(enf.T2_nolineal, "#fb923c", null, 2.4);

  // Marcadores de cruce tc
  [
    { t: enf.tc_lineal, color: "#94a3b8", label: `tc lin: ${enf.tc_lineal}s`, dy: 14 },
    { t: enf.tc_nolineal, color: "#fb923c", label: `tc real: ${enf.tc_nolineal}s`, dy: -7 },
  ].forEach((mkr) => {
    if (mkr.t <= xMax) {
      const cx = sx(mkr.t);
      svg.appendChild(crearSvgEl("circle", { cx, cy: yObj, r: 4, fill: mkr.color }));
      const txt = crearSvgEl("text", {
        x: Math.min(m.left + plotW - 10, Math.max(m.left + 10, cx)),
        y: yObj + mkr.dy,
        "text-anchor": "middle",
        fill: mkr.color,
        "font-size": 9.5,
        "font-weight": 700,
      });
      txt.textContent = mkr.label;
      svg.appendChild(txt);
    }
  });

  const tit = crearSvgEl("text", { x: 10, y: 16, fill: "#fb923c", "font-size": 10, "font-weight": 700 });
  tit.textContent = "Temperatura interna T2 (°C) sin quemador";
  svg.appendChild(tit);

  contenedor.appendChild(svg);
}

/**
 * Renderiza la vista de Simulación por Fases (Capa 2) y Optimizador Automático (Capa 3).
 */
export function renderizarPanelSimulacion(
  contenedorHeader,
  contenedorBody,
  estadoApp,
  callbacks = {}
) {
  if (!estadoApp.sistema || !estadoApp.sistema.simulacion) return;
  const {
    alEjecutarOptimizacion = null,
    alAplicarOptimo = null,
    alClickVariable = null,
  } = callbacks;

  const { simulacion, resumen } = estadoApp.sistema;
  const res = simulacion.resumen_fases;
  const enf = simulacion.enfriamiento;

  contenedorHeader.innerHTML = `
    <div class="cat-banner-title">▌ SIMULACIÓN TEMPORAL POR FASES (CAPA 2) &amp; OPTIMIZADOR (CAPA 3)</div>
    <div class="cat-banner-stats">
      Maniobra ${res.t_man}s + Crucero ${res.t_cruc}s · Enfriamiento RK2 · ${resumen.total_variables} variables
    </div>
  `;

  contenedorBody.innerHTML = "";

  // =========================================================
  // SECCIÓN 1: CAPA 2 — SIMULACIÓN TEMPORAL POR FASES
  // =========================================================
  const secFases = document.createElement("section");
  secFases.className = "sim-section";
  secFases.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">1. Simulación Realista por Fases (Maniobra vs. Crucero) &amp; Enfriamiento No Lineal</h3>
        <p class="sim-section-desc">
          El modelo algebraico base asume de forma conservadora la aceleración de maniobra durante todo el vuelo.
          Aquí se separa la fase inicial de arranque (<b>0 → ${res.t_man} s</b>) del crucero estacionario (<b>${res.t_man} → ${res.tm} s</b>)
          y se integra paso a paso el enfriamiento pasivo del globo cuando se apaga el quemador.
        </p>
      </div>
    </div>
  `;

  // KPI Grid
  const kpiGrid = document.createElement("div");
  kpiGrid.className = "sim-kpi-grid";
  kpiGrid.innerHTML = `
    <div class="sim-kpi-card">
      <div class="sim-kpi-label">Potencia Total Ptot (Maniobra → Crucero)</div>
      <div class="sim-kpi-val text-cyan">${res.Ptot_man} W → ${res.Ptot_cruc} W</div>
      <div class="sim-kpi-sub">Motores ${res.Pelec_man}→${res.Pelec_cruc} W + Adicional ${res.Pad} W</div>
    </div>
    <div class="sim-kpi-card">
      <div class="sim-kpi-label">Ahorro Eléctrico por Fases</div>
      <div class="sim-kpi-val text-calc">${res.Eelec_fases_kj} kJ (${res.ahorro_elec_pct}% menos)</div>
      <div class="sim-kpi-sub">Frente a ${res.Eelec_cas_kj} kJ del CAS conservador</div>
    </div>
    <div class="sim-kpi-card">
      <div class="sim-kpi-label">Batería Exacta max(mbe, mbp)</div>
      <div class="sim-kpi-val text-fixed">${res.mbat_fases_g} g (CAS: ${res.mbat_cas_g} g)</div>
      <div class="sim-kpi-sub">Energía ${res.mbe_fases_g} g | Potencia pico ${res.mbp_pico_g} g</div>
    </div>
    <div class="sim-kpi-card">
      <div class="sim-kpi-label">Enfriamiento Real T2 - dTc</div>
      <div class="sim-kpi-val" style="color:#fb923c;">${enf.tc_nolineal} s (Lineal: ${enf.tc_lineal} s)</div>
      <div class="sim-kpi-sub">Al bajar ΔT cae Qp(T2) y frena el enfriamiento</div>
    </div>
  `;
  secFases.appendChild(kpiGrid);

  // Gráficas SVG lado a lado
  const chartsGrid = document.createElement("div");
  chartsGrid.className = "sim-charts-grid";

  const card1 = document.createElement("div");
  card1.className = "sim-chart-card";
  card1.innerHTML = `<div class="sim-chart-title">A. Potencia y Empuje durante las Fases de Vuelo</div>`;
  const box1 = document.createElement("div");
  box1.className = "sim-chart-box";
  renderizarGraficaFases(box1, simulacion.perfil_vuelo, res);
  card1.appendChild(box1);
  card1.insertAdjacentHTML(
    "beforeend",
    `<div class="sim-legend">
      <span><i style="background:#38bdf8"></i> Ptot = Pelec + Pad (W)</span>
      <span><i style="background:#4ade80"></i> Pelec motores (W)</span>
      <span><i style="background:#facc15"></i> Pad base (${res.Pad} W)</span>
      <span><i style="background:#f97316"></i> Ttot (N)</span>
    </div>`
  );

  const card2 = document.createElement("div");
  card2.className = "sim-chart-card";
  card2.innerHTML = `<div class="sim-chart-title">B. Enfriamiento Pasivo No Lineal sin Quemador (RK2)</div>`;
  const box2 = document.createElement("div");
  box2.className = "sim-chart-box";
  renderizarGraficaEnfriamiento(box2, enf);
  card2.appendChild(box2);
  card2.insertAdjacentHTML(
    "beforeend",
    `<div class="sim-legend">
      <span><i style="background:#fb923c"></i> Curva real integrada T2(t)</span>
      <span><i style="background:#94a3b8"></i> Aproximación lineal vT cte.</span>
      <span><i style="background:#f87171"></i> Objetivo caída admisible dTc</span>
    </div>`
  );

  chartsGrid.appendChild(card1);
  chartsGrid.appendChild(card2);
  secFases.appendChild(chartsGrid);

  // Tabla comparativa
  const tableWrap = document.createElement("div");
  tableWrap.className = "sim-table-wrap";
  tableWrap.innerHTML = `
    <table class="sim-table">
      <thead>
        <tr>
          <th>Parámetro</th>
          <th>Fase 1 · Maniobra (0 → ${res.t_man}s)</th>
          <th>Fase 2 · Crucero (${res.t_man} → ${res.tm}s)</th>
          <th>Modelo CAS Conservador (todo ${res.tm}s)</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>Empuje total motores (Ttot)</td>
          <td>${res.Ttot_man} N</td>
          <td>${res.Ttot_cruc} N</td>
          <td>${res.Ttot_man} N</td>
        </tr>
        <tr>
          <td>Inclinación motores (theta)</td>
          <td>${res.theta_man}°</td>
          <td>${res.theta_cruc}°</td>
          <td>${res.theta_man}°</td>
        </tr>
        <tr>
          <td>Potencia motores (Pelec)</td>
          <td>${res.Pelec_man} W</td>
          <td>${res.Pelec_cruc} W</td>
          <td>${res.Pelec_man} W</td>
        </tr>
        <tr>
          <td>Potencia total a bordo (Ptot = Pelec + Pad)</td>
          <td><strong>${res.Ptot_man} W</strong></td>
          <td><strong>${res.Ptot_cruc} W</strong></td>
          <td><strong>${res.Ptot_man} W</strong></td>
        </tr>
        <tr>
          <td>Energía eléctrica acumulada / Total Etot</td>
          <td colspan="2">${res.Eelec_fases_kj} kJ eléc. · ${res.Etot_fases_kj} kJ total (ahorro ${res.ahorro_tot_pct}%)</td>
          <td>${res.Eelec_cas_kj} kJ eléc. · ${res.Etot_cas_kj} kJ total</td>
        </tr>
      </tbody>
    </table>
  `;
  secFases.appendChild(tableWrap);
  contenedorBody.appendChild(secFases);

  // =========================================================
  // SECCIÓN 2: CAPA 3 — OPTIMIZADOR AUTOMÁTICO MULTIDIMENSIONAL
  // =========================================================
  const secOpt = document.createElement("section");
  secOpt.className = "sim-section";
  secOpt.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">2. Optimizador Automático de Diseño (Capa 3 — Búsqueda Global + Refinamiento Local)</h3>
        <p class="sim-section-desc">
          Explora cientos de combinaciones válidas sobre el evaluador rápido con tearing en milisegundos, respetando
          simultáneamente todos los límites físicos (<b>mbat ≤ mbmax</b>, <b>theta ≤ thmax</b>, <b>Pelec ≤ Pmax</b>, <b>Ttot ≤ N·Tmax1</b>).
        </p>
      </div>
    </div>
  `;

  const controlsBar = document.createElement("div");
  controlsBar.className = "opt-controls-bar";

  const objGroup = document.createElement("div");
  objGroup.className = "opt-control-group";
  objGroup.innerHTML = `<label for="opt-obj-select" class="opt-label">Objetivo a minimizar:</label>`;
  const selectEl = document.createElement("select");
  selectEl.id = "opt-obj-select";
  selectEl.className = "opt-select";
  [
    ["Etot", "Energía total en misión (Etot)"],
    ["Cop", "Costo operativo total de misión (Cop)"],
    ["mtot", "Masa total del dirigible (mtot)"],
    ["mbat", "Masa de batería requerida (mbat)"],
    ["mgm", "Consumo de combustible térmico (mgm)"],
  ].forEach(([val, txt]) => {
    const o = document.createElement("option");
    o.value = val;
    o.textContent = txt;
    o.selected = optUiState.objetivo === val;
    selectEl.appendChild(o);
  });
  selectEl.addEventListener("change", () => {
    optUiState.objetivo = selectEl.value;
  });
  objGroup.appendChild(selectEl);

  const varsGroup = document.createElement("div");
  varsGroup.className = "opt-control-group";
  varsGroup.innerHTML = `<span class="opt-label">Variables libres:</span>`;
  [
    ["lam", "λ (esbeltez)"],
    ["v", "v (velocidad)"],
    ["mflot", "mflot (aire caliente)"],
    ["e", "e (espesor Mylar)"],
    ["T2", "T2 (temp. interior)"],
  ].forEach(([vCod, vTxt]) => {
    const lbl = document.createElement("label");
    lbl.className = "opt-check-pill";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = optUiState.variables.has(vCod);
    cb.addEventListener("change", () => {
      if (cb.checked) {
        optUiState.variables.add(vCod);
      } else if (optUiState.variables.size > 1) {
        optUiState.variables.delete(vCod);
      } else {
        cb.checked = true;
      }
    });
    lbl.appendChild(cb);
    lbl.appendChild(document.createTextNode(` ${vTxt}`));
    varsGroup.appendChild(lbl);
  });

  const btnRun = document.createElement("button");
  btnRun.type = "button";
  btnRun.className = "btn btn-primary opt-run-btn";
  btnRun.disabled = optUiState.cargando;
  btnRun.textContent = optUiState.cargando ? "⏳ Optimizando..." : "⚡ Ejecutar optimización";
  btnRun.addEventListener("click", async () => {
    if (!alEjecutarOptimizacion || optUiState.cargando) return;
    optUiState.cargando = true;
    btnRun.disabled = true;
    btnRun.textContent = "⏳ Optimizando...";
    try {
      await alEjecutarOptimizacion(optUiState.objetivo, Array.from(optUiState.variables));
    } finally {
      optUiState.cargando = false;
    }
  });

  controlsBar.appendChild(objGroup);
  controlsBar.appendChild(varsGroup);
  controlsBar.appendChild(btnRun);
  secOpt.appendChild(controlsBar);

  // Resultados de optimización
  const optRes = estadoApp.resultadoOptimizacion;
  if (optRes) {
    const resCard = document.createElement("div");
    resCard.className = "opt-results-card";

    if (!optRes.encontrado) {
      resCard.innerHTML = `
        <div class="opt-no-result">
          ⚠ No se encontró ningún punto físicamente válido dentro de los rangos explorados
          (${optRes.evaluaciones} combinaciones evaluadas en ${optRes.tiempo_ms} ms).
          Verifica que parámetros fijos como <b>dm</b>, <b>vv</b>, <b>T2</b> o <b>mcarga</b> permitan vuelo dentro de <b>Pmax</b> y <b>mbmax</b>.
        </div>
      `;
    } else {
      const act = optRes.actual;
      const opt = optRes.optimo;
      const signoMejora = optRes.mejora_pct >= 0 ? "−" : "+";

      resCard.innerHTML = `
        <div class="opt-res-header">
          <div>
            <strong>✔ Óptimo encontrado para ${escaparHtml(optRes.objetivo)}</strong>
            <span class="opt-res-meta">
              ${optRes.evaluaciones_validas} puntos válidos de ${optRes.evaluaciones} evaluados en <b>${optRes.tiempo_ms} ms</b>
            </span>
          </div>
          <span class="opt-mejora-badge">
            ${signoMejora}${Math.abs(optRes.mejora_pct).toFixed(2)}% en ${escaparHtml(optRes.objetivo)}
          </span>
        </div>
        <div class="sim-table-wrap">
          <table class="sim-table">
            <thead>
              <tr>
                <th>Parámetro / Métrica</th>
                <th>Diseño Actual ${act.valido ? "" : "(⚠ Inválido)"}</th>
                <th>Diseño Óptimo Válido</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>Relación de esbeltez (<button type="button" class="flow-var-chip" data-var="lam">lam</button>)</td>
                <td>${act.lam}</td>
                <td><b>${opt.lam}</b></td>
              </tr>
              <tr>
                <td>Velocidad relativa al aire (<button type="button" class="flow-var-chip" data-var="v">v</button>)</td>
                <td>${act.v} m/s</td>
                <td><b>${opt.v} m/s</b></td>
              </tr>
              <tr>
                <td>Carga aire caliente (<button type="button" class="flow-var-chip" data-var="mflot">mflot</button>)</td>
                <td>${act.mflot} kg</td>
                <td><b>${opt.mflot} kg</b></td>
              </tr>
              <tr>
                <td>Espesor capa celular (<button type="button" class="flow-var-chip" data-var="e">e</button>)</td>
                <td>${act.e_mm} mm</td>
                <td><b>${opt.e_mm} mm</b></td>
              </tr>
              <tr>
                <td>Temperatura interior (<button type="button" class="flow-var-chip" data-var="T2">T2</button>)</td>
                <td>${act.T2} °C</td>
                <td><b>${opt.T2} °C</b></td>
              </tr>
              <tr>
                <td>Pérdida térmica (<button type="button" class="flow-var-chip" data-var="Qp">Qp</button>) / Costo (<button type="button" class="flow-var-chip" data-var="Cop">Cop</button>)</td>
                <td>${act.Qp_w} W / ${act.Cop_bs} Bs</td>
                <td><b>${opt.Qp_w} W / ${opt.Cop_bs} Bs</b></td>
              </tr>
              <tr>
                <td>Energía total misión (Etot = Eprop + Eelec)</td>
                <td>${act.Etot_kj} kJ (${act.Eprop_kj} comb. + ${act.Eelec_kj} eléc.)</td>
                <td><b>${opt.Etot_kj} kJ</b> (${opt.Eprop_kj} comb. + ${opt.Eelec_kj} eléc.)</td>
              </tr>
              <tr>
                <td>Masa total (mtot) / Batería (mbat) / Combustible (mgm)</td>
                <td>${act.mtot} kg / ${act.mbat_g} g / ${act.mgm_g} g</td>
                <td><b>${opt.mtot} kg / ${opt.mbat_g} g / ${opt.mgm_g} g</b></td>
              </tr>
              <tr>
                <td>Potencia motores (Pelec) / Total (Ptot) / Ángulo (theta)</td>
                <td>${act.Pelec_w} W / ${act.Ptot_w} W / ${act.theta_deg}°</td>
                <td><b>${opt.Pelec_w} W / ${opt.Ptot_w} W / ${opt.theta_deg}°</b></td>
              </tr>
            </tbody>
          </table>
        </div>
      `;

      resCard.querySelectorAll("button[data-var]").forEach((b) => {
        b.addEventListener("click", () => {
          if (alClickVariable) alClickVariable(b.getAttribute("data-var"));
        });
      });

      const footer = document.createElement("div");
      footer.className = "opt-res-footer";
      if (optRes.requiere_cambio_fijas) {
        const nota = document.createElement("span");
        nota.className = "opt-res-note";
        nota.textContent = `Al aplicar se restablecerán las ${resumen.total_fijas} variables fijas estándar para fijar los parámetros optimizados.`;
        footer.appendChild(nota);
      }
      if (optRes.entradas_optimo && alAplicarOptimo) {
        const btnApply = document.createElement("button");
        btnApply.type = "button";
        btnApply.className = "btn btn-primary";
        btnApply.textContent = "✔ Aplicar diseño óptimo al sistema";
        btnApply.addEventListener("click", () => alAplicarOptimo(optRes.entradas_optimo));
        footer.appendChild(btnApply);
      }
      resCard.appendChild(footer);
    }

    secOpt.appendChild(resCard);
  }

  contenedorBody.appendChild(secOpt);
}
