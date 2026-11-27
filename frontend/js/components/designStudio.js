/**
 * designStudio.js — Vista "Óptimo y Casos Tipo" con 3 pestañas:
 *   1. Indicadores y Óptimo: pesos configurables, optimizador multi-criterio, comparación
 *      Hot-Swap (combustible vs. batería repuesto) y ficha técnica de construcción.
 *   2. Histórico Manual: guardado selectivo en JSON local, comparador gráfico SVG e import/export.
 *   3. Casos Tipo vs. Óptimo: tabla comparativa compacta filtrable por familia (sin límites duros).
 */

const SVG_NS = "http://www.w3.org/2000/svg";

const PRESETS_PESOS = {
  equilibrado: {
    nombre: "Equilibrado",
    pesos: { costo_operativo: 25, costo_recambio: 20, consumo_energetico: 15, masa_elevable: 15, autonomia: 15, velocidad: 10 },
  },
  economico: {
    nombre: "Mínimo Costo",
    pesos: { costo_operativo: 40, costo_recambio: 30, consumo_energetico: 15, masa_elevable: 5, autonomia: 5, velocidad: 5 },
  },
  alcance: {
    nombre: "Largo Alcance",
    pesos: { costo_operativo: 15, costo_recambio: 15, consumo_energetico: 25, masa_elevable: 10, autonomia: 30, velocidad: 5 },
  },
  rapido: {
    nombre: "Alta Velocidad",
    pesos: { costo_operativo: 15, costo_recambio: 15, consumo_energetico: 15, masa_elevable: 10, autonomia: 15, velocidad: 30 },
  },
  carga: {
    nombre: "Carga Útil",
    pesos: { costo_operativo: 15, costo_recambio: 15, consumo_energetico: 10, masa_elevable: 40, autonomia: 15, velocidad: 5 },
  },
};

const COLORES_SERIES = ["#38bdf8", "#4ade80", "#facc15", "#f472b6", "#fb923c"];

const CATALOGO_VARS_DEFECTO = {
  lam: { label: "Esbeltez (λ)", unidad: "adim", factor: 1, step: 0.05, min: 1.4, max: 6.0, dec: 2, por_defecto: true },
  v: { label: "Vel. aire (v)", unidad: "m/s", factor: 1, step: 0.1, min: 1.0, max: 15.0, dec: 2, por_defecto: true },
  mflot: { label: "Aire cal. (mflot)", unidad: "kg", factor: 1, step: 0.05, min: 0.2, max: 15.0, dec: 3, por_defecto: true },
  e: { label: "Celda Mylar (e)", unidad: "mm", factor: 1000, step: 0.5, min: 1.0, max: 50.0, dec: 1, por_defecto: true },
  T2: { label: "Temp. gas (T₂)", unidad: "°C", factor: 1, step: 1.0, min: 30.0, max: 130.0, dec: 1, por_defecto: true },
  ncapS: { label: "Capas sup. (ncapS)", unidad: "capas", factor: 1, step: 1, min: 0, max: 6, dec: 0, por_defecto: true },
  ncapI: { label: "Capas inf. (ncapI)", unidad: "capas", factor: 1, step: 1, min: 0, max: 6, dec: 0, por_defecto: true },
  mp: { label: "Combustible a bordo (mp)", unidad: "g", factor: 1000, step: 5, min: 5, max: 1000, dec: 1, por_defecto: true },
};

const designUi = {
  pesos: { ...PRESETS_PESOS.equilibrado.pesos },
  cbat_kg: 750,
  varsVisibles: Object.keys(CATALOGO_VARS_DEFECTO),
  variables: new Set(Object.keys(CATALOGO_VARS_DEFECTO)),
  valoresInputs: {},
  ultimoSistemaRef: null,
  restricciones: null,
  usarOptimoComoBase: true,
  familiaActiva: "all",
  seleccionHistorico: new Set(),
  expandidoHistId: null,
};

function obtenerCatalogoVars(res) {
  return res?.catalogo_vars_constructivas || CATALOGO_VARS_DEFECTO;
}

function obtenerValorSistemaDisplay(estadoApp, varKey, meta) {
  const varObj = estadoApp?.sistema?.variables?.find((v) => v.nombre === varKey);
  if (!varObj || !Number.isFinite(Number(varObj.valor)) || !meta) return null;
  return Number((Number(varObj.valor) * meta.factor).toFixed(meta.dec));
}

function sincronizarInputsConSistema(estadoApp, catalogo = CATALOGO_VARS_DEFECTO, forzar = false) {
  if (!estadoApp?.sistema?.variables) return;
  if (!forzar && designUi.ultimoSistemaRef === estadoApp.sistema) return;
  designUi.ultimoSistemaRef = estadoApp.sistema;
  const nuevo = {};
  for (const key of designUi.varsVisibles) {
    const val = obtenerValorSistemaDisplay(estadoApp, key, catalogo[key]);
    if (val !== null) nuevo[key] = val;
  }
  designUi.valoresInputs = nuevo;
}

function construirBaseOverrides(catalogo = CATALOGO_VARS_DEFECTO) {
  const ov = {};
  for (const key of designUi.varsVisibles) {
    const meta = catalogo[key];
    const vDisp = Number(designUi.valoresInputs[key]);
    if (meta && Number.isFinite(vDisp)) {
      ov[key] = vDisp / meta.factor;
    }
  }
  return ov;
}

function escaparHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function fmtInd(key, val) {
  if (!Number.isFinite(Number(val))) return "—";
  const v = Number(val);
  switch (key) {
    case "costo_operativo":
    case "costo_recambio":
      return `${v.toFixed(2)} Bs`;
    case "consumo_energetico":
      return `${v.toFixed(1)} kJ`;
    case "masa_elevable":
      return `${v.toFixed(2)} kg`;
    case "autonomia":
      return `${Math.round(v)} m`;
    case "velocidad":
      return `${v.toFixed(2)} m/s`;
    default:
      return String(v);
  }
}

function renderizarComparadorSvg(contenedor, registrosSel, metas) {
  const keys = Object.keys(metas);
  const w = 680;
  const h = 250;
  const m = { top: 26, right: 20, bottom: 52, left: 42 };
  const plotW = w - m.left - m.right;
  const plotH = h - m.top - m.bottom;

  const svg = document.createElementNS(SVG_NS, "svg");
  svg.setAttribute("class", "sim-svg");
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);

  for (let g = 0; g <= 4; g++) {
    const val = g * 25;
    const y = m.top + plotH - (val / 100) * plotH;
    const line = document.createElementNS(SVG_NS, "line");
    line.setAttribute("x1", m.left);
    line.setAttribute("y1", y);
    line.setAttribute("x2", m.left + plotW);
    line.setAttribute("y2", y);
    line.setAttribute("stroke", "rgba(71, 85, 105, 0.32)");
    svg.appendChild(line);

    const lbl = document.createElementNS(SVG_NS, "text");
    lbl.setAttribute("x", m.left - 6);
    lbl.setAttribute("y", y + 3.5);
    lbl.setAttribute("text-anchor", "end");
    lbl.setAttribute("fill", "#94a3b8");
    lbl.setAttribute("font-size", "9.5");
    lbl.textContent = String(val);
    svg.appendChild(lbl);
  }

  const categorias = ["score_total", ...keys];
  const etiquetas = ["SCORE", ...keys.map((k) => metas[k].corto || k)];
  const grupoW = plotW / categorias.length;
  const nSer = registrosSel.length;
  const barW = Math.min(20, Math.max(6, (grupoW - 16) / Math.max(1, nSer)));

  categorias.forEach((catKey, cIdx) => {
    const gx = m.left + cIdx * grupoW + grupoW / 2;
    const totalBarsW = nSer * barW + Math.max(0, nSer - 1) * 2;
    const startX = gx - totalBarsW / 2;

    registrosSel.forEach((reg, rIdx) => {
      const val = catKey === "score_total" ? reg.score_total : (reg.scores?.[catKey] ?? 0);
      const bh = Math.max(2, (Math.min(100, Math.max(0, val)) / 100) * plotH);
      const bx = startX + rIdx * (barW + 2);
      const by = m.top + plotH - bh;
      const rect = document.createElementNS(SVG_NS, "rect");
      rect.setAttribute("x", bx.toFixed(1));
      rect.setAttribute("y", by.toFixed(1));
      rect.setAttribute("width", barW.toFixed(1));
      rect.setAttribute("height", bh.toFixed(1));
      rect.setAttribute("rx", "2");
      rect.setAttribute("fill", COLORES_SERIES[rIdx % COLORES_SERIES.length]);

      const tip = document.createElementNS(SVG_NS, "title");
      tip.textContent = `${reg.nombre} — ${etiquetas[cIdx]}: ${Number(val).toFixed(1)}/100`;
      rect.appendChild(tip);
      svg.appendChild(rect);
    });

    const tx = document.createElementNS(SVG_NS, "text");
    tx.setAttribute("x", gx.toFixed(1));
    tx.setAttribute("y", m.top + plotH + 16);
    tx.setAttribute("text-anchor", "middle");
    tx.setAttribute("fill", cIdx === 0 ? "#fde047" : "#cbd5e1");
    tx.setAttribute("font-size", "9.8");
    tx.setAttribute("font-weight", cIdx === 0 ? "700" : "600");
    tx.textContent = etiquetas[cIdx];
    svg.appendChild(tx);
  });

  contenedor.innerHTML = "";
  contenedor.appendChild(svg);
}

function renderizarPestanaOptimo(root, res, estadoApp, callbacks) {
  const { alAnalizar, alAplicar, alGuardarHistorico } = callbacks;
  const metas = res.indicadores_meta || {};
  const varsRestrMeta = res.variables_restriccion || {};
  const catalogoVars = obtenerCatalogoVars(res);
  const cargando = Boolean(estadoApp?.cargandoDiseno);

  const varsDisponiblesAgregar = Object.entries(catalogoVars).filter(
    ([vk]) => !designUi.varsVisibles.includes(vk)
  );

  if (Array.isArray(res.restricciones)) {
    if (designUi.restricciones === null) {
      designUi.restricciones = res.restricciones.map((r) => ({ ...r }));
    } else {
      const porId = new Map(res.restricciones.map((r) => [r.id, r]));
      designUi.restricciones = designUi.restricciones.map((prev) => {
        const srv = porId.get(prev.id);
        if (srv && prev.grupo === "hardware") {
          return {
            ...prev,
            valor: srv.valor,
            usar_equipo: srv.usar_equipo ?? prev.usar_equipo ?? prev.activa,
            tope_manual: prev.tope_manual ?? null,
          };
        }
        return prev;
      });
    }
  }
  const restricciones = designUi.restricciones || [];
  const hayHwActivo = restricciones.some((r) => r.grupo === "hardware" && r.activa);

  const sumaPesos = Object.values(designUi.pesos).reduce((a, b) => a + b, 0) || 1;
  const actual = res.actual;
  const optimo = res.optimo;
  const encontrado = Boolean(res.encontrado && optimo);
  const ref = optimo || actual;
  const esp = ref.especificaciones || {};

  // 1. Controles de pesos ponderados + variables constructivas editables + restricciones
  const secCtrl = document.createElement("section");
  secCtrl.className = "sim-section";
  secCtrl.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">1. Criterios e Indicadores Ponderados para Especificaciones Óptimas</h3>
        <p class="sim-section-desc">
          Ajusta el peso relativo de cada indicador, edita o fija las variables constructivas y configura límites máximos o mínimos. El optimizador evalúa cientos de diseños en milisegundos (sin SymPy).
        </p>
      </div>
      <div class="design-presets-row">
        ${Object.entries(PRESETS_PESOS)
          .map(
            ([pid, pr]) =>
              `<button type="button" class="btn btn-outline design-preset-btn" data-preset="${pid}">${escaparHtml(pr.nombre)}</button>`
          )
          .join("")}
      </div>
    </div>

    <div class="design-weights-grid">
      ${Object.entries(metas)
        .map(([key, meta]) => {
          const val = designUi.pesos[key] ?? 0;
          const pct = ((100 * val) / sumaPesos).toFixed(0);
          return `
            <div class="design-weight-card" title="${escaparHtml(meta.descripcion)}">
              <div class="design-weight-top">
                <span class="design-weight-name">${escaparHtml(meta.nombre)}</span>
                <span class="design-weight-pct" data-pct-for="${key}">${pct}% (${val})</span>
              </div>
              <input type="range" min="0" max="100" step="5" value="${val}" class="design-weight-slider" data-weight-key="${key}" />
              <div class="design-weight-sub">${meta.sentido === "menor" ? "↓ Menor es mejor" : "↑ Mayor es mejor"} · ${escaparHtml(meta.unidad)}</div>
            </div>
          `;
        })
        .join("")}
    </div>

    <div class="design-vars-section">
      <div class="design-vars-head">
        <span class="opt-label">Variables constructivas (marca <b>Libre</b> para optimizar o edita su valor fijo inicial):</span>
        <button id="btn-reset-design-vars" type="button" class="btn btn-ghost design-mini-btn">↺ Restablecer valores del sistema</button>
      </div>
      <div class="design-vars-grid">
        ${designUi.varsVisibles
          .map((varKey) => {
            const meta = catalogoVars[varKey];
            if (!meta) return "";
            const libre = designUi.variables.has(varKey);
            const valSis = obtenerValorSistemaDisplay(estadoApp, varKey, meta);
            const valInput = designUi.valoresInputs[varKey] ?? valSis ?? "";
            const btnQuitar =
              designUi.varsVisibles.length > 1
                ? `<button type="button" class="btn btn-ghost design-mini-btn design-var-del" data-var="${escaparHtml(varKey)}" title="Quitar variable del panel">✕</button>`
                : "";
            return `
            <div class="design-var-card ${libre ? "is-free" : "is-fixed"}">
              <div class="design-var-top">
                <label class="design-var-chk-lbl" title="Si está marcado, el optimizador varía ${escaparHtml(varKey)}; si se desmarca, usa exactamente el valor numérico ingresado abajo.">
                  <input type="checkbox" class="design-var-check" value="${escaparHtml(varKey)}" ${libre ? "checked" : ""} />
                  <span>${escaparHtml(meta.label)}</span>
                </label>
                <div class="design-var-top-actions">
                  <span class="design-var-state">${libre ? "Libre" : "Fija"}</span>
                  ${btnQuitar}
                </div>
              </div>
              <div class="design-var-input-row">
                <input type="number" class="design-var-num" data-var="${escaparHtml(varKey)}" step="${meta.step}" min="${meta.min}" max="${meta.max}" value="${valInput}" />
                <span class="design-var-unit">${escaparHtml(meta.unidad)}</span>
              </div>
              <div class="design-var-sys">Actual sistema: <strong>${valSis !== null ? valSis : "—"} ${escaparHtml(meta.unidad)}</strong></div>
            </div>
          `;
          })
          .join("")}
      </div>
      ${
        varsDisponiblesAgregar.length > 0
          ? `<div class="design-add-var-row">
              <span class="opt-label">+ Agregar variable constructiva:</span>
              <select id="design-new-var-sel" class="design-lim-var-sel">
                ${varsDisponiblesAgregar
                  .map(([vk, vm]) => `<option value="${escaparHtml(vk)}">${escaparHtml(vm.label)} (${escaparHtml(vm.unidad)})</option>`)
                  .join("")}
              </select>
              <button id="btn-add-design-var" type="button" class="btn btn-outline design-mini-btn">+ Añadir</button>
            </div>`
          : ""
      }
    </div>

    <div class="design-limits-panel">
      <div class="design-limits-head">
        <span class="opt-label">Restricciones y Límites Activos del Diseño:</span>
        <label class="opt-check-pill" title="Activa o desactiva en bloque las 5 cotas físicas de tu hardware actual (batería 1 kg y motores A2212). Puedes editar sus valores numéricos debajo.">
          <input id="design-limits-toggle" type="checkbox" ${hayHwActivo ? "checked" : ""} />
          <span>Activar hardware actual (1 kg / A2212)</span>
        </label>
      </div>

      <div class="design-limits-list">
        ${restricciones
          .map((r, idx) => {
            const meta = varsRestrMeta[r.variable] || { nombre: r.variable, unidad: "", paso: 1 };
            const esHw = r.grupo === "hardware";
            const opMostrar = esHw ? (r.variable === "Fexc" ? ">=" : "<=") : r.op;
            const tieneTope = esHw && r.tope_manual !== null && r.tope_manual !== undefined;
            const valDisplay = tieneTope ? r.tope_manual : r.valor;
            const eqTag = esHw
              ? `<span class="design-var-unit" title="Calculado automáticamente según N, Pmax1, Tmax1, mbmax y thmax">${tieneTope ? `(eq: ${r.valor})` : "(equipo)"}</span>`
              : "";
            const btnClearTope = tieneTope
              ? `<button type="button" class="btn btn-ghost design-mini-btn design-lim-clear-tope" data-idx="${idx}" title="Quitar tope manual y usar solo límite del equipo">↺ eq</button>`
              : "";
            const opTitle = esHw
              ? "El sentido físico del equipo no puede invertirse; agrega una regla personalizada si deseas una cota opuesta."
              : "Operador de comparación";
            return `
              <div class="design-limit-row ${r.activa ? "is-active" : "is-inactive"}">
                <label class="design-limit-chk">
                  <input type="checkbox" class="design-lim-active" data-idx="${idx}" ${r.activa ? "checked" : ""} />
                  <span>${escaparHtml(meta.nombre)}</span>
                </label>
                <select class="design-lim-op" data-idx="${idx}" ${esHw ? "disabled" : ""} title="${opTitle}">
                  <option value="<=" ${opMostrar === "<=" ? "selected" : ""}>≤</option>
                  <option value=">=" ${opMostrar === ">=" ? "selected" : ""}>≥</option>
                </select>
                <input type="number" class="design-lim-val" data-idx="${idx}" step="${meta.paso || 0.5}" value="${valDisplay}" />
                <span class="design-var-unit">${escaparHtml(meta.unidad)}</span>
                ${eqTag}
                ${btnClearTope}
                <button type="button" class="btn btn-ghost design-mini-btn design-lim-del" data-idx="${idx}" title="Quitar restricción">✕</button>
              </div>
            `;
          })
          .join("")}
      </div>

      <div class="design-add-limit-row">
        <span class="opt-label">+ Agregar límite:</span>
        <select id="design-new-lim-var" class="design-lim-var-sel">
          ${Object.entries(varsRestrMeta)
            .map(([vk, vm]) => `<option value="${escaparHtml(vk)}">${escaparHtml(vm.nombre)} (${escaparHtml(vm.unidad)})</option>`)
            .join("")}
        </select>
        <select id="design-new-lim-op" class="design-lim-op">
          <option value="<=">≤</option>
          <option value=">=">≥</option>
        </select>
        <input id="design-new-lim-val" type="number" class="design-lim-val" step="0.5" value="${(varsRestrMeta[Object.keys(varsRestrMeta)[0]] || { valor_def: 95 }).valor_def}" />
        <span id="design-new-lim-unit" class="design-var-unit">${escaparHtml((varsRestrMeta[Object.keys(varsRestrMeta)[0]] || { unidad: "°C" }).unidad)}</span>
        <button id="btn-add-design-limit" type="button" class="btn btn-outline design-mini-btn">+ Añadir</button>
      </div>
    </div>

    <div class="opt-controls-bar">
      <div class="opt-control-group">
        <label class="opt-label" for="design-cbat-input">Batería repuesto (Bs/kg):</label>
        <input id="design-cbat-input" type="number" min="0" step="50" value="${designUi.cbat_kg}" class="design-small-num" />
      </div>
      <div class="opt-control-group">
        <button id="btn-run-design-opt" type="button" class="btn btn-primary" ${cargando ? "disabled" : ""}>
          ${cargando ? "⏳ Calculando..." : "⚡ Calcular Especificaciones Óptimas"}
        </button>
      </div>
    </div>
  `;

  secCtrl.querySelectorAll(".design-preset-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const pr = PRESETS_PESOS[btn.dataset.preset];
      if (!pr) return;
      designUi.pesos = { ...pr.pesos };
      alAnalizar(true);
    });
  });

  secCtrl.querySelectorAll(".design-weight-slider").forEach((sl) => {
    sl.addEventListener("input", () => {
      const k = sl.dataset.weightKey;
      designUi.pesos[k] = Number(sl.value);
      const tot = Object.values(designUi.pesos).reduce((a, b) => a + b, 0) || 1;
      secCtrl.querySelectorAll(".design-weight-pct").forEach((lbl) => {
        const lk = lbl.dataset.pctFor;
        const lv = designUi.pesos[lk] ?? 0;
        lbl.textContent = `${((100 * lv) / tot).toFixed(0)}% (${lv})`;
      });
    });
  });

  secCtrl.querySelectorAll(".design-var-check").forEach((chk) => {
    chk.addEventListener("change", () => {
      if (chk.checked) designUi.variables.add(chk.value);
      else designUi.variables.delete(chk.value);
      const card = chk.closest(".design-var-card");
      if (card) {
        card.classList.toggle("is-free", chk.checked);
        card.classList.toggle("is-fixed", !chk.checked);
        const st = card.querySelector(".design-var-state");
        if (st) st.textContent = chk.checked ? "Libre" : "Fija";
      }
    });
  });

  secCtrl.querySelectorAll(".design-var-num").forEach((inp) => {
    inp.addEventListener("input", () => {
      const val = Number(inp.value);
      if (Number.isFinite(val)) designUi.valoresInputs[inp.dataset.var] = val;
    });
  });

  secCtrl.querySelector("#btn-reset-design-vars")?.addEventListener("click", () => {
    sincronizarInputsConSistema(estadoApp, catalogoVars, true);
    alAnalizar(true);
  });

  const repintarLocal = () => {
    const parent = root.parentElement;
    if (parent) {
      root.innerHTML = "";
      renderizarPestanaOptimo(root, res, estadoApp, callbacks);
    }
  };

  secCtrl.querySelector("#btn-add-design-var")?.addEventListener("click", () => {
    const vk = secCtrl.querySelector("#design-new-var-sel")?.value;
    if (!vk || !catalogoVars[vk] || designUi.varsVisibles.includes(vk)) return;
    designUi.varsVisibles.push(vk);
    designUi.variables.add(vk);
    const valSis = obtenerValorSistemaDisplay(estadoApp, vk, catalogoVars[vk]);
    if (valSis !== null) designUi.valoresInputs[vk] = valSis;
    repintarLocal();
  });

  secCtrl.querySelectorAll(".design-var-del").forEach((btn) => {
    btn.addEventListener("click", () => {
      const vk = btn.dataset.var;
      if (designUi.varsVisibles.length <= 1) return;
      designUi.varsVisibles = designUi.varsVisibles.filter((k) => k !== vk);
      designUi.variables.delete(vk);
      delete designUi.valoresInputs[vk];
      repintarLocal();
    });
  });

  secCtrl.querySelector("#design-limits-toggle")?.addEventListener("change", (e) => {
    const act = Boolean(e.target.checked);
    designUi.restricciones = (designUi.restricciones || []).map((r) =>
      r.grupo === "hardware" ? { ...r, activa: act, usar_equipo: act } : r
    );
    repintarLocal();
  });

  secCtrl.querySelectorAll(".design-lim-active").forEach((chk) => {
    chk.addEventListener("change", () => {
      const idx = Number(chk.dataset.idx);
      if (designUi.restricciones?.[idx]) {
        const act = Boolean(chk.checked);
        designUi.restricciones[idx].activa = act;
        if (designUi.restricciones[idx].grupo === "hardware") {
          designUi.restricciones[idx].usar_equipo = act;
        }
        repintarLocal();
      }
    });
  });

  secCtrl.querySelectorAll(".design-lim-op").forEach((sel) => {
    sel.addEventListener("change", () => {
      const idx = Number(sel.dataset.idx);
      if (designUi.restricciones?.[idx] && designUi.restricciones[idx].grupo !== "hardware") {
        designUi.restricciones[idx].op = sel.value;
      }
    });
  });

  secCtrl.querySelectorAll(".design-lim-val").forEach((inp) => {
    inp.addEventListener("input", () => {
      const idx = Number(inp.dataset.idx);
      const val = Number(inp.value);
      const rObj = designUi.restricciones?.[idx];
      if (rObj && Number.isFinite(val)) {
        if (rObj.grupo === "hardware") {
          rObj.tope_manual = val;
        } else {
          rObj.valor = val;
        }
      }
    });
  });

  secCtrl.querySelectorAll(".design-lim-clear-tope").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.idx);
      if (designUi.restricciones?.[idx]) {
        designUi.restricciones[idx].tope_manual = null;
        repintarLocal();
      }
    });
  });

  secCtrl.querySelectorAll(".design-lim-del").forEach((btn) => {
    btn.addEventListener("click", () => {
      const idx = Number(btn.dataset.idx);
      if (Array.isArray(designUi.restricciones)) {
        designUi.restricciones.splice(idx, 1);
        repintarLocal();
      }
    });
  });

  const selNewVar = secCtrl.querySelector("#design-new-lim-var");
  const selNewOp = secCtrl.querySelector("#design-new-lim-op");
  const inpNewVal = secCtrl.querySelector("#design-new-lim-val");
  const spnNewUnit = secCtrl.querySelector("#design-new-lim-unit");

  selNewVar?.addEventListener("change", () => {
    const meta = varsRestrMeta[selNewVar.value];
    if (!meta) return;
    if (selNewOp) selNewOp.value = meta.op_def;
    if (inpNewVal) {
      inpNewVal.value = meta.valor_def;
      inpNewVal.step = meta.paso || 0.5;
    }
    if (spnNewUnit) spnNewUnit.textContent = meta.unidad;
  });

  secCtrl.querySelector("#btn-add-design-limit")?.addEventListener("click", () => {
    const vNom = selNewVar?.value;
    if (!vNom || !varsRestrMeta[vNom]) return;
    const meta = varsRestrMeta[vNom];
    const op = selNewOp?.value || meta.op_def;
    const val = Number(inpNewVal?.value);
    if (!Number.isFinite(val)) return;
    if (!Array.isArray(designUi.restricciones)) designUi.restricciones = [];
    designUi.restricciones.push({
      id: `custom_${Date.now()}_${vNom}`,
      variable: vNom,
      op,
      valor: val,
      activa: true,
      grupo: "custom",
    });
    repintarLocal();
  });

  const inpCbat = secCtrl.querySelector("#design-cbat-input");
  const syncCbat = () => {
    const val = Number(inpCbat?.value);
    if (Number.isFinite(val) && val >= 0) designUi.cbat_kg = val;
  };
  inpCbat?.addEventListener("input", syncCbat);
  inpCbat?.addEventListener("change", syncCbat);

  secCtrl.querySelector("#btn-run-design-opt")?.addEventListener("click", () => {
    alAnalizar(true);
  });

  root.appendChild(secCtrl);

  // 2. Comparativa de puntuaciones + Costo Operativo (sin Hot-Swap) + Hot-Swap
  const secComp = document.createElement("section");
  secComp.className = "sim-section";
  const avisosOpt = (ref.avisos || [])
    .map((a) => `<span class="design-warn-pill">${escaparHtml(a)}</span>`)
    .join("");
  const deltaBadge =
    !encontrado
      ? `<span class="design-delta-neg">Sin solución</span>`
      : res.mejora_score >= 0
        ? `<span class="opt-mejora-badge">+${res.mejora_score.toFixed(2)} pts</span>`
        : `<span class="design-delta-neg">${res.mejora_score.toFixed(2)} pts</span>`;

  const actActivas = restricciones.filter((r) => r.activa).map((r) => `${r.variable} ${r.op} ${r.valor}`).join(", ");
  const alertaSinSol = !encontrado
    ? `<div class="design-empty-warn">
        ⚠ ${escaparHtml(res.mensaje_error || "Ninguna combinación cumplió todas las restricciones activas.")}
        ${actActivas ? `<div style="margin-top:4px;font-size:11.2px;">Restricciones activas: <code>${escaparHtml(actActivas)}</code>. Desactiva o flexibiliza alguna para hallar un diseño óptimo.</div>` : ""}
      </div>`
    : "";

  secComp.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">2. Puntuación Global, Costo Operativo y Recambio Rápido (Hot-Swap)</h3>
        <p class="sim-section-desc">
          Calculado en <strong>${res.tiempo_opt_ms} ms</strong> (${res.evaluaciones} evaluaciones, ${res.evaluaciones_validas} diseños válidos). Restricciones hardware: <strong>${hayHwActivo ? "Activas" : "Libres (informativas)"}</strong>.
        </p>
      </div>
      <div class="design-score-banner">
        <div class="design-score-box">
          <span class="design-score-lbl">Base / Actual</span>
          <strong class="design-score-num">${actual.score_total.toFixed(1)}</strong>
        </div>
        <span class="design-score-arrow">→</span>
        <div class="design-score-box design-score-best">
          <span class="design-score-lbl">Óptimo</span>
          <strong class="design-score-num text-calc">${encontrado ? optimo.score_total.toFixed(1) : "—"}</strong>
        </div>
        ${deltaBadge}
      </div>
    </div>

    ${alertaSinSol}
    ${avisosOpt ? `<div class="design-avisos-row"><span class="design-avisos-lbl">Notas de dimensionamiento respecto al hardware estándar:</span>${avisosOpt}</div>` : ""}

    <div class="design-ind-grid">
      ${Object.entries(metas)
        .map(([key, meta]) => {
          const valAct = actual.indicadores[key];
          const valOpt = ref.indicadores[key];
          const scAct = actual.scores[key];
          const scOpt = ref.scores[key];
          const pNorm = ((100 * (res.pesos?.[key] ?? 0)) / sumaPesos).toFixed(0);
          return `
            <div class="design-ind-card">
              <div class="design-ind-head">
                <span class="design-ind-title">${escaparHtml(meta.corto)} <small>(peso ${pNorm}%)</small></span>
                <span class="design-ind-scores">${scAct.toFixed(0)} → <strong class="text-calc">${encontrado ? scOpt.toFixed(0) : "—"}</strong>/100</span>
              </div>
              <div class="design-ind-vals">
                <span>Actual: <strong>${fmtInd(key, valAct)}</strong></span>
                <span>Óptimo: <strong class="text-cyan">${encontrado ? fmtInd(key, valOpt) : "—"}</strong></span>
              </div>
              <div class="design-ind-bar-bg">
                <div class="design-ind-bar-opt" style="width:${Math.min(100, encontrado ? scOpt : scAct)}%;"></div>
                <div class="design-ind-bar-act" style="width:${Math.min(100, scAct)}%;"></div>
              </div>
            </div>
          `;
        })
        .join("")}
    </div>

    <div class="design-cost-cards-stack">
      <div class="design-cost-card design-opcost-card">
        <div class="design-cost-header">
          <div class="design-cost-title">💵 Costo Operativo por Misión (sin Hot-Swap)</div>
          <div class="design-cost-total-pill is-opcost">
            Total: <strong>${esp.Cop} Bs</strong> · ${esp.cop_por_viaje} Bs/viaje · ${esp.cop_por_km} Bs/km
          </div>
        </div>
        <p class="design-cost-sub">
          Lo que cuesta operar el dirigible en una misión de <strong>${esp.dm} m</strong> (${esp.nv} viajes), sumando el precalentamiento inicial en tierra, el combustible quemado en vuelo y la recarga eléctrica de la batería.
        </p>
        <div class="design-cost-metrics-3">
          <div class="design-cost-metric">
            <span class="design-cost-metric-lbl"><i style="background:#38bdf8;"></i> Precalentamiento en tierra</span>
            <strong class="design-cost-metric-val">${esp.Cpre} Bs <small>(${esp.pct_cpre}%)</small></strong>
            <span class="design-cost-metric-extra">Energía tierra: ${esp.Epre_kj} kJ</span>
          </div>
          <div class="design-cost-metric">
            <span class="design-cost-metric-lbl"><i style="background:#fb923c;"></i> Combustible térmico en vuelo</span>
            <strong class="design-cost-metric-val">${esp.Ccomb} Bs <small>(${esp.pct_ccomb}%)</small></strong>
            <span class="design-cost-metric-extra">Consumo: ${esp.mgm_g} g</span>
          </div>
          <div class="design-cost-metric">
            <span class="design-cost-metric-lbl"><i style="background:#4ade80;"></i> Electricidad de recarga</span>
            <strong class="design-cost-metric-val">${esp.Celec} Bs <small>(${esp.pct_celec}%)</small></strong>
            <span class="design-cost-metric-extra">Batería: ${esp.Ereq_wh} Wh</span>
          </div>
        </div>
        <div class="design-hs-bar">
          <div class="design-hs-cpre" style="width:${Math.max(2, esp.pct_cpre)}%;" title="Precalentamiento: ${esp.Cpre} Bs (${esp.pct_cpre}%)"></div>
          <div class="design-hs-ccomb" style="width:${Math.max(2, esp.pct_ccomb)}%;" title="Combustible vuelo: ${esp.Ccomb} Bs (${esp.pct_ccomb}%)"></div>
          <div class="design-hs-celec" style="width:${Math.max(2, esp.pct_celec)}%;" title="Electricidad: ${esp.Celec} Bs (${esp.pct_celec}%)"></div>
        </div>
      </div>

      <div class="design-cost-card design-hotswap-card">
        <div class="design-cost-header">
          <div class="design-cost-title is-hotswap">⚡ Costo de Recambio Rápido ("Hot-Swap")</div>
          <div class="design-cost-total-pill is-hotswap">
            Total: <strong>${esp.c_recambio} Bs</strong> · Batería = ${esp.pct_bateria_recambio}% (${esp.ratio_bat_comb}×)
          </div>
        </div>
        <p class="design-cost-sub">
          Costo inmediato para volver a despegar al instante sin esperar a recargar la batería: rellenar el depósito de combustible líquido frente al costo de mantener otra batería LiPo de repuesto ya cargada.
        </p>
        <div class="design-cost-metrics-2">
          <div class="design-cost-metric">
            <span class="design-cost-metric-lbl"><i style="background:#fb923c;"></i> Reposición de combustible líquido</span>
            <strong class="design-cost-metric-val">${esp.c_rec_comb} Bs <small>(${(100 - esp.pct_bateria_recambio).toFixed(1)}%)</small></strong>
            <span class="design-cost-metric-extra">Depósito completo: ${esp.mp_g} g</span>
          </div>
          <div class="design-cost-metric">
            <span class="design-cost-metric-lbl"><i style="background:#facc15;"></i> Batería LiPo cargada de repuesto</span>
            <strong class="design-cost-metric-val">${esp.c_bat_rep} Bs <small>(${esp.pct_bateria_recambio}%)</small></strong>
            <span class="design-cost-metric-extra">Batería: ${esp.mbat_g} g</span>
          </div>
        </div>
        <div class="design-hs-bar">
          <div class="design-hs-comb" style="width:${Math.max(3, 100 - esp.pct_bateria_recambio)}%;" title="Combustible: ${esp.c_rec_comb} Bs"></div>
          <div class="design-hs-bat" style="width:${Math.max(3, esp.pct_bateria_recambio)}%;" title="Batería repuesto: ${esp.c_bat_rep} Bs"></div>
        </div>
      </div>
    </div>
  `;
  root.appendChild(secComp);

  // 3. Ficha Técnica de Especificaciones de Construcción
  const secSpec = document.createElement("section");
  secSpec.className = "sim-section";
  secSpec.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">3. Ficha Técnica de Especificaciones ${encontrado ? "Óptimas de Construcción" : "(Base Actual — Sin Óptimo Factible)"}</h3>
        <p class="sim-section-desc">
          Parámetros geométricos, térmicos, de aislamiento y propulsivos listos para dimensionar el dirigible físico o aplicarlos a toda la calculadora.
        </p>
      </div>
      <div class="opt-control-group">
        <button id="btn-save-opt-hist" type="button" class="btn btn-outline" ${!encontrado ? "disabled" : ""}>💾 Guardar en histórico</button>
        <button id="btn-apply-design-opt" type="button" class="btn btn-success" ${!res.entradas_optimo ? "disabled" : ""}>✔ Aplicar óptimo al sistema</button>
      </div>
    </div>

    <div class="design-spec-grid">
      <div class="design-spec-box">
        <div class="design-spec-title">📐 Geometría del Casco</div>
        <div class="design-spec-rows">
          <div><span>Longitud × Diámetro</span><strong>${esp.L} m × ${esp.D} m</strong></div>
          <div><span>Esbeltez (λ)</span><strong>${esp.lam}</strong></div>
          <div><span>Nariz / Cola (cf / cr)</span><strong>${esp.cf} m / ${esp.cr} m</strong></div>
          <div><span>Volumen total (V)</span><strong>${esp.V} m³</strong></div>
          <div><span>Área exterior (S)</span><strong>${esp.S} m²</strong></div>
        </div>
      </div>

      <div class="design-spec-box">
        <div class="design-spec-title">🛡 Aislamiento Mylar Asimétrico</div>
        <div class="design-spec-rows">
          <div><span>Capas (Sup / Inf)</span><strong>${esp.ncapS} / ${esp.ncapI}</strong></div>
          <div><span>Espesor celda / paso</span><strong>${esp.e_mm} mm / ${esp.W_cm} cm</strong></div>
          <div><span>Película (ep / ε / σ)</span><strong>${esp.ep_um} µm · ε=${esp.eps} · ${esp.sigma_gm2} g/m²</strong></div>
          <div><span>Película total (Sc / mc)</span><strong>${esp.Sc} m² / ${esp.mc_g} g</strong></div>
          <div><span>Ahorro térmico (fais)</span><strong>${esp.fais_pct}% (U = ${esp.U})</strong></div>
        </div>
      </div>

      <div class="design-spec-box">
        <div class="design-spec-title">🔥 Térmica y Combustible</div>
        <div class="design-spec-rows">
          <div><span>Temperatura (T₁ → T₂)</span><strong>${esp.T1} °C → ${esp.T2} °C</strong></div>
          <div><span>Pérdida térmica (Qp)</span><strong>${esp.Qp_w} W</strong></div>
          <div><span>Precalentamiento tierra</span><strong>${esp.Epre_kj} kJ (${esp.Cpre} Bs)</strong></div>
          <div><span>Combustible a bordo (mp)</span><strong>${esp.mp_g} g</strong></div>
          <div><span>Combustible vuelo (mgm)</span><strong>${esp.mgm_g} g (${esp.Ccomb} Bs)</strong></div>
          <div><span>Enfriamiento ${esp.dTc ?? 20} K (tc)</span><strong>${esp.tc_s} s</strong></div>
        </div>
      </div>

      <div class="design-spec-box">
        <div class="design-spec-title">⚡ Masas, Propulsión y Autonomía</div>
        <div class="design-spec-rows">
          <div><span>Aire caliente / Residual</span><strong>${esp.mflot} kg (${esp.frac_aire_pct}%) / ${esp.mres} kg</strong></div>
          <div><span>Carga útil / Masa total</span><strong>${esp.mcarga} kg (bat. fija: ${esp.mcarga_min_kg ?? 0}–${esp.capacidad_util_kg} kg; redim.: ${esp.capacidad_redim_kg ?? esp.capacidad_util_kg} kg) / ${esp.mtot} kg</strong></div>
          <div><span>Empuje / Ángulo / Pot.</span><strong>${esp.Ttot} N (cruc. ${esp.Tcruc} N) · θ ${esp.theta}°/${esp.thcruc ?? esp.theta}° · ${esp.Pelec} W (cruc. ${esp.Pcruc ?? esp.Pelec} W)</strong></div>
          <div><span>Batería / Velocidad vg</span><strong>${esp.mbat_g} g · ${esp.vg} m/s (aire ${esp.v}) · lim. ${esp.fase_limitante || "—"} (${esp.componente_limitante || "—"})</strong></div>
          <div><span>Autonomía máx.</span><strong>${esp.dm_aut} m (${esp.nv_aut} v., lim. ${esp.limitante_aut})</strong></div>
        </div>
      </div>
    </div>
  `;

  secSpec.querySelector("#btn-apply-design-opt")?.addEventListener("click", () => {
    if (res.entradas_optimo && alAplicar) alAplicar(res.entradas_optimo);
  });

  secSpec.querySelector("#btn-save-opt-hist")?.addEventListener("click", () => {
    if (!res.entradas_optimo || !alGuardarHistorico) return;
    const restrSave = Array.isArray(res?.restricciones)
      ? res.restricciones.map((r) => ({ ...r }))
      : (Array.isArray(designUi.restricciones) ? designUi.restricciones.map((r) => ({ ...r })) : null);
    const hwSave = restrSave
      ? restrSave.some((r) => r.grupo === "hardware" && r.activa)
      : Boolean(res?.respetar_limites ?? true);
    const pesosSave = res?.pesos ? { ...res.pesos } : { ...designUi.pesos };
    const cbatSave = Number.isFinite(Number(res?.cbat_kg)) ? Number(res.cbat_kg) : designUi.cbat_kg;
    const nombreDef = `Óptimo (${ref.score_total.toFixed(1)} pts · λ=${esp.lam}, T₂=${esp.T2}°C)`;
    alGuardarHistorico({
      nombre: nombreDef,
      nota: `Cop=${esp.Cop} Bs, Recambio=${esp.c_recambio} Bs, Aut=${esp.dm_aut} m`,
      origen: "optimo",
      entradas: res.entradas_optimo,
      pesos: pesosSave,
      cbat_kg: cbatSave,
      respetar_limites: hwSave,
      restricciones: restrSave,
    });
  });

  root.appendChild(secSpec);
}

function renderizarPestanaHistorico(root, res, historico, callbacks) {
  const {
    alGuardarHistorico,
    alEliminarHistorico,
    alImportarHistorico,
    alReevaluarHistorico,
    alAplicar,
    alMensaje,
  } = callbacks;
  const metas = res?.indicadores_meta || {};

  const secSave = document.createElement("section");
  secSave.className = "sim-section";
  secSave.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">Histórico Manual de Puntuaciones y Configuraciones</h3>
        <p class="sim-section-desc">
          Guarda manualmente solo las configuraciones relevantes para compararlas con sus parámetros constructivos sin saturar la memoria. Persiste en archivo JSON local.
        </p>
      </div>
      <div class="opt-control-group">
        <button id="btn-export-hist" type="button" class="btn btn-outline" ${historico.length === 0 ? "disabled" : ""}>⬇ Exportar JSON</button>
        <label class="btn btn-outline" style="cursor:pointer;">
          ⬆ Importar JSON
          <input id="input-import-hist" type="file" accept=".json,application/json" style="display:none;" />
        </label>
      </div>
    </div>

    <div class="design-save-form">
      <input id="hist-name-input" type="text" class="quick-input" placeholder="Nombre del caso (ej. Prototipo v1 etanol 3/2)" maxlength="80" />
      <input id="hist-note-input" type="text" class="quick-input" placeholder="Nota opcional (observaciones constructivas...)" maxlength="200" />
      <button id="btn-hist-save-actual" type="button" class="btn btn-primary">💾 Guardar estado actual</button>
      <button id="btn-hist-save-optimo" type="button" class="btn btn-success" ${!res?.entradas_optimo ? "disabled" : ""}>💾 Guardar último óptimo</button>
    </div>
  `;

  secSave.querySelector("#btn-hist-save-actual")?.addEventListener("click", () => {
    const nom = secSave.querySelector("#hist-name-input")?.value.trim() || `Estado actual (${new Date().toLocaleTimeString()})`;
    const nota = secSave.querySelector("#hist-note-input")?.value.trim() || "";
    const restrSave = Array.isArray(res?.restricciones)
      ? res.restricciones.map((r) => ({ ...r }))
      : (Array.isArray(designUi.restricciones) ? designUi.restricciones.map((r) => ({ ...r })) : null);
    const hwSave = restrSave
      ? restrSave.some((r) => r.grupo === "hardware" && r.activa)
      : Boolean(res?.respetar_limites ?? true);
    const pesosSave = res?.pesos ? { ...res.pesos } : { ...designUi.pesos };
    const cbatSave = Number.isFinite(Number(res?.cbat_kg)) ? Number(res.cbat_kg) : designUi.cbat_kg;
    alGuardarHistorico({
      nombre: nom,
      nota,
      origen: "actual",
      entradas: null,
      pesos: pesosSave,
      cbat_kg: cbatSave,
      respetar_limites: hwSave,
      restricciones: restrSave,
    });
  });

  secSave.querySelector("#btn-hist-save-optimo")?.addEventListener("click", () => {
    if (!res?.entradas_optimo) return;
    const esp = res.optimo?.especificaciones || {};
    const nom = secSave.querySelector("#hist-name-input")?.value.trim() || `Óptimo (${res.optimo?.score_total?.toFixed(1)} pts · λ=${esp.lam})`;
    const nota = secSave.querySelector("#hist-note-input")?.value.trim() || `Cop=${esp.Cop} Bs, mbat=${esp.mbat_g} g`;
    const restrSave = Array.isArray(res?.restricciones)
      ? res.restricciones.map((r) => ({ ...r }))
      : (Array.isArray(designUi.restricciones) ? designUi.restricciones.map((r) => ({ ...r })) : null);
    const hwSave = restrSave
      ? restrSave.some((r) => r.grupo === "hardware" && r.activa)
      : Boolean(res?.respetar_limites ?? true);
    const pesosSave = res?.pesos ? { ...res.pesos } : { ...designUi.pesos };
    const cbatSave = Number.isFinite(Number(res?.cbat_kg)) ? Number(res.cbat_kg) : designUi.cbat_kg;
    alGuardarHistorico({
      nombre: nom,
      nota,
      origen: "optimo",
      entradas: res.entradas_optimo,
      pesos: pesosSave,
      cbat_kg: cbatSave,
      respetar_limites: hwSave,
      restricciones: restrSave,
    });
  });

  secSave.querySelector("#btn-export-hist")?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(historico, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `historico_dirigible_${new Date().toISOString().slice(0, 10)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  });

  secSave.querySelector("#input-import-hist")?.addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      try {
        const parsed = JSON.parse(String(reader.result || "[]"));
        const lista = Array.isArray(parsed) ? parsed : parsed.registros;
        if (!Array.isArray(lista)) throw new Error("El JSON debe contener una lista de registros.");
        alImportarHistorico(lista);
      } catch (err) {
        if (alMensaje) alMensaje(`JSON inválido: ${err.message}`, "error");
      }
    };
    reader.readAsText(file);
  });

  root.appendChild(secSave);

  // Gráfica comparativa SVG cuando hay 2..5 seleccionados
  const seleccionados = historico.filter((r) => designUi.seleccionHistorico.has(r.id)).slice(0, 5);
  if (seleccionados.length >= 2 && Object.keys(metas).length > 0) {
    const secChart = document.createElement("section");
    secChart.className = "sim-section";
    secChart.innerHTML = `
      <div class="sim-section-header">
        <h3 class="sim-section-title">Comparativa Visual de Puntuaciones (${seleccionados.length} seleccionados)</h3>
        <div class="design-chart-legend">
          ${seleccionados
            .map(
              (r, i) =>
                `<span><i style="background:${COLORES_SERIES[i % COLORES_SERIES.length]};"></i> ${escaparHtml(r.nombre)} (${r.score_total.toFixed(1)})</span>`
            )
            .join("")}
        </div>
      </div>
      <div class="sim-chart-box" id="hist-compare-svg-box"></div>
    `;
    renderizarComparadorSvg(secChart.querySelector("#hist-compare-svg-box"), seleccionados, metas);
    root.appendChild(secChart);
  }

  // Tabla de histórico
  const secList = document.createElement("section");
  secList.className = "sim-section";
  if (historico.length === 0) {
    secList.innerHTML = `
      <div class="flow-rel-empty">
        Todavía no hay configuraciones guardadas en el histórico manual. Usa los botones de arriba o el botón 💾 en "Indicadores y Óptimo" o "Casos Tipo".
      </div>
    `;
    root.appendChild(secList);
    return;
  }

  secList.innerHTML = `
    <div class="sim-section-header">
      <h3 class="sim-section-title">Configuraciones Guardadas (${historico.length}) — Marca 2 a 5 para comparar en gráfica</h3>
    </div>
    <div class="sim-table-wrap">
      <table class="sim-table design-cases-table">
        <thead>
          <tr>
            <th>Comp.</th>
            <th>Fecha / Nombre</th>
            <th>Score</th>
            <th>Cop</th>
            <th>Recambio (Comb/Bat)</th>
            <th>Energía / mgm</th>
            <th>Aire / Total (Útil)</th>
            <th>Auton. / vg</th>
            <th>Casco / Bat</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${historico
            .map((reg) => {
              const esp = reg.especificaciones || {};
              const checked = designUi.seleccionHistorico.has(reg.id) ? "checked" : "";
              const expandido = designUi.expandidoHistId === reg.id;
              const verModelo = reg.modelo_version || "v1";
              return `
                <tr>
                  <td><input type="checkbox" class="hist-sel-chk" data-id="${escaparHtml(reg.id)}" ${checked} /></td>
                  <td>
                    <div class="design-case-name">${escaparHtml(reg.nombre)} <small class="design-var-unit">[${escaparHtml(verModelo)}]</small></div>
                    <div class="design-case-sub">${escaparHtml(reg.fecha)} · ${escaparHtml(reg.origen)}${reg.nota ? ` · ${escaparHtml(reg.nota)}` : ""}</div>
                  </td>
                  <td><strong class="text-calc">${Number(reg.score_total).toFixed(1)}</strong></td>
                  <td>${esp.Cop} Bs</td>
                  <td>${esp.c_recambio} Bs <small>(${esp.c_rec_comb}/${esp.c_bat_rep})</small></td>
                  <td>${esp.Etot_kj} kJ <small>(${esp.mgm_g} g)</small></td>
                  <td>${esp.mflot}/${esp.mtot} kg <small>(u:${esp.capacidad_util_kg})</small></td>
                  <td>${esp.dm_aut} m <small>(${esp.vg} m/s)</small></td>
                  <td>${esp.L}×${esp.D} m <small>(${esp.mbat_g} g)</small></td>
                  <td class="design-actions-cell">
                    <button type="button" class="btn btn-ghost design-mini-btn hist-det-btn" data-id="${escaparHtml(reg.id)}" title="Ver parámetros completos">${expandido ? "▲" : "▼"}</button>
                    <button type="button" class="btn btn-outline design-mini-btn hist-reeval-btn" data-id="${escaparHtml(reg.id)}" title="Reevaluar en motor v2 como registro nuevo (mantiene el original intacto)">↻ v2</button>
                    <button type="button" class="btn btn-outline design-mini-btn hist-load-btn" data-id="${escaparHtml(reg.id)}" title="Aplicar esta configuración al sistema">↩</button>
                    <button type="button" class="btn btn-ghost design-mini-btn hist-del-btn" data-id="${escaparHtml(reg.id)}" title="Eliminar del histórico">🗑</button>
                  </td>
                </tr>
                ${
                  expandido
                    ? `<tr class="hist-detail-row"><td colspan="10">
                        <div class="hist-detail-grid">
                          <span><strong>λ:</strong> ${esp.lam}</span>
                          <span><strong>Capas:</strong> ${esp.ncapS}/${esp.ncapI} (e=${esp.e_mm} mm, ep=${esp.ep_um} µm)</span>
                          <span><strong>T₂:</strong> ${esp.T2} °C</span>
                          <span><strong>Qp:</strong> ${esp.Qp_w} W (fais ${esp.fais_pct}%)</span>
                          <span><strong>v / vv:</strong> ${esp.v} / ${esp.vv} m/s</span>
                          <span><strong>dm:</strong> ${esp.dm} m (${esp.nv} viajes)</span>
                          <span><strong>Pelec / θ (man/cruc):</strong> ${esp.Pelec} W / ${esp.theta}° / ${esp.thcruc ?? esp.theta}°</span>
                          <span><strong>Carga bat. fija:</strong> ${esp.mcarga_min_kg ?? 0}–${esp.capacidad_util_kg} kg</span>
                          ${(() => {
                            const customAct = (reg.restricciones || []).filter((r) => r.activa && r.grupo !== "hardware");
                            return customAct.length > 0
                              ? `<span><strong>Reglas activas:</strong> ${customAct.map((r) => `${escaparHtml(r.variable)} ${escaparHtml(r.op)} ${escaparHtml(r.tope_manual ?? r.valor)}`).join(", ")}</span>`
                              : "";
                          })()}
                          ${reg.origen_id ? `<span><strong>Origen:</strong> ${escaparHtml(reg.origen_version || "v1")} (${escaparHtml(reg.origen_id)})</span>` : ""}
                          <span><strong>Avisos:</strong> ${(reg.avisos || []).join(", ") || "Ninguno"}</span>
                        </div>
                      </td></tr>`
                    : ""
                }
              `;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;

  secList.querySelectorAll(".hist-sel-chk").forEach((chk) => {
    chk.addEventListener("change", () => {
      const id = chk.dataset.id;
      if (chk.checked) {
        if (designUi.seleccionHistorico.size >= 5) {
          chk.checked = false;
          if (alMensaje) alMensaje("Máximo 5 registros simultáneos en la gráfica comparativa.", "error");
          return;
        }
        designUi.seleccionHistorico.add(id);
      } else {
        designUi.seleccionHistorico.delete(id);
      }
      renderizarSoloVista();
    });
  });

  secList.querySelectorAll(".hist-det-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const id = btn.dataset.id;
      designUi.expandidoHistId = designUi.expandidoHistId === id ? null : id;
      renderizarSoloVista();
    });
  });

  secList.querySelectorAll(".hist-reeval-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      if (alReevaluarHistorico) alReevaluarHistorico(btn.dataset.id);
    });
  });

  secList.querySelectorAll(".hist-load-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const reg = historico.find((r) => r.id === btn.dataset.id);
      if (reg?.entradas && alAplicar) alAplicar(reg.entradas);
    });
  });

  secList.querySelectorAll(".hist-del-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      designUi.seleccionHistorico.delete(btn.dataset.id);
      alEliminarHistorico(btn.dataset.id);
    });
  });

  function renderizarSoloVista() {
    const parent = root.parentElement;
    if (parent) {
      root.innerHTML = "";
      renderizarPestanaHistorico(root, res, historico, callbacks);
    }
  }

  root.appendChild(secList);
}

function renderizarPestanaCasos(root, res, callbacks) {
  const { alAnalizar, alAplicar, alGuardarHistorico } = callbacks;
  const familias = res.familias || [];
  const casos = res.casos_tipo || [];
  const filtrados =
    designUi.familiaActiva === "all"
      ? casos
      : casos.filter((c) => c.es_referencia || c.familia === designUi.familiaActiva);

  const secCasos = document.createElement("section");
  secCasos.className = "sim-section";
  secCasos.innerHTML = `
    <div class="sim-section-header">
      <div>
        <h3 class="sim-section-title">Casos Tipo respecto al Punto Óptimo (Evaluación sin límites de 1 kg / A2212)</h3>
        <p class="sim-section-desc">
          Cada fila modifica parámetros clave respecto al punto de referencia (Score base: <strong>${res.referencia_score.toFixed(1)}</strong> · Capas ${res.referencia_capas}) mostrando solo los datos relevantes de desempeño, costo, recambio rápido y dimensionamiento.
        </p>
      </div>
      <div class="opt-control-group">
        <label class="opt-check-pill">
          <input id="chk-casos-sobre-opt" type="checkbox" ${designUi.usarOptimoComoBase ? "checked" : ""} />
          <span>Partir del Óptimo (vs. Estado actual)</span>
        </label>
        <button id="btn-recalc-casos" type="button" class="btn btn-outline">↻ Recalcular casos</button>
      </div>
    </div>

    <div class="design-filter-bar">
      <button type="button" class="btn btn-outline design-fam-btn ${designUi.familiaActiva === "all" ? "active" : ""}" data-fam="all">Todas (${casos.length})</button>
      ${familias
        .filter((f) => f.id !== "referencia")
        .map(
          (f) =>
            `<button type="button" class="btn btn-outline design-fam-btn ${designUi.familiaActiva === f.id ? "active" : ""}" data-fam="${escaparHtml(f.id)}">${escaparHtml(f.titulo)}</button>`
        )
        .join("")}
    </div>

    <div class="sim-table-wrap">
      <table class="sim-table design-cases-table">
        <thead>
          <tr>
            <th>Caso / Variante</th>
            <th>Score (Δ)</th>
            <th>Cop (Bs)</th>
            <th>Recambio (Comb/Bat)</th>
            <th>Etot / mgm</th>
            <th>Aire / Total (mcarga)</th>
            <th>Autonomía / vg</th>
            <th>Casco / Bat</th>
            <th>Estado / Avisos</th>
            <th>Acciones</th>
          </tr>
        </thead>
        <tbody>
          ${filtrados
            .map((c) => {
              const esp = c.especificaciones || {};
              const dCls = c.delta_score > 0.05 ? "text-calc" : c.delta_score < -0.05 ? "text-penalized" : "text-fixed";
              const dTxt = c.es_referencia ? "REF" : `${c.delta_score >= 0 ? "+" : ""}${c.delta_score.toFixed(1)}`;
              const avisosHtml =
                c.avisos && c.avisos.length > 0
                  ? c.avisos.map((a) => `<span class="design-warn-pill">${escaparHtml(a)}</span>`).join("")
                  : `<span class="design-ok-pill">OK A2212</span>`;
              return `
                <tr class="${c.es_referencia ? "design-row-ref" : ""}">
                  <td>
                    <div class="design-case-name">${escaparHtml(c.nombre)}</div>
                    <div class="design-case-sub">${escaparHtml(c.familia_titulo)} · ${escaparHtml(c.cambios_txt)}</div>
                  </td>
                  <td><strong>${c.score_total.toFixed(1)}</strong> <span class="${dCls}">(${dTxt})</span></td>
                  <td><strong>${esp.Cop}</strong> <small>(t:${esp.Cpre}+v:${esp.Ccomb})</small></td>
                  <td>${esp.c_recambio} <small>(${esp.c_rec_comb} / ${esp.c_bat_rep})</small></td>
                  <td>${esp.Etot_kj} kJ <small>(${esp.mgm_g} g)</small></td>
                  <td>${esp.mflot}/${esp.mtot} kg <small>(${esp.frac_aire_pct}%, u:${esp.mcarga})</small></td>
                  <td>${esp.dm_aut} m <small>(${esp.nv_aut}v · ${esp.vg} m/s)</small></td>
                  <td>${esp.L}×${esp.D} m <small>(${esp.mbat_g} g)</small></td>
                  <td>${avisosHtml}</td>
                  <td class="design-actions-cell">
                    <button type="button" class="btn btn-outline design-mini-btn caso-load-btn" data-id="${escaparHtml(c.id)}" title="Aplicar este caso a la calculadora principal">↩</button>
                    <button type="button" class="btn btn-ghost design-mini-btn caso-save-btn" data-id="${escaparHtml(c.id)}" title="Guardar este caso en el histórico manual">💾</button>
                  </td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;

  secCasos.querySelector("#chk-casos-sobre-opt")?.addEventListener("change", (e) => {
    designUi.usarOptimoComoBase = Boolean(e.target.checked);
    alAnalizar(true);
  });

  secCasos.querySelector("#btn-recalc-casos")?.addEventListener("click", () => {
    alAnalizar(true);
  });

  secCasos.querySelectorAll(".design-fam-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      designUi.familiaActiva = btn.dataset.fam;
      const parent = root.parentElement;
      if (parent) {
        root.innerHTML = "";
        renderizarPestanaCasos(root, res, callbacks);
      }
    });
  });

  secCasos.querySelectorAll(".caso-load-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const caso = casos.find((c) => c.id === btn.dataset.id);
      if (caso?.entradas && alAplicar) alAplicar(caso.entradas);
    });
  });

  secCasos.querySelectorAll(".caso-save-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const caso = casos.find((c) => c.id === btn.dataset.id);
      if (!caso?.entradas || !alGuardarHistorico) return;
      const pesosSave = res?.pesos ? { ...res.pesos } : { ...designUi.pesos };
      const cbatSave = Number.isFinite(Number(res?.cbat_kg)) ? Number(res.cbat_kg) : designUi.cbat_kg;
      alGuardarHistorico({
        nombre: caso.nombre,
        nota: `${caso.familia_titulo}: ${caso.cambios_txt}`,
        origen: "caso_tipo",
        entradas: caso.entradas,
        pesos: pesosSave,
        cbat_kg: cbatSave,
      });
    });
  });

  root.appendChild(secCasos);
}

/**
 * Renderiza la vista completa "📐 Óptimo y Casos Tipo".
 */
export function renderizarPanelDiseno(
  contenedorHeader,
  contenedorBody,
  estadoApp,
  callbacks = {}
) {
  if (!estadoApp.sistema) return;
  const res = estadoApp.resultadoDiseno;
  const catalogoVars = obtenerCatalogoVars(res);
  sincronizarInputsConSistema(estadoApp, catalogoVars);
  const historico = estadoApp.historicoDisenos || [];
  const pestana = estadoApp.pestanaDiseno || "optimo";

  if (contenedorHeader) {
    const nCasos = res?.casos_tipo?.length || 0;
    const tTxt = estadoApp.cargandoDiseno
      ? "Calculando..."
      : res
        ? `Análisis en ${res.tiempo_total_ms} ms (0 SymPy)`
        : "Cargando análisis...";
    contenedorHeader.innerHTML = `
      <div class="cat-banner-title">📐 ESPECIFICACIONES ÓPTIMAS, INDICADORES PONDERADOS Y CASOS TIPO</div>
      <div class="design-header-right">
        <div class="design-tabs-bar">
          <button type="button" class="btn btn-outline design-tab-btn ${pestana === "optimo" ? "active" : ""}" data-tab="optimo">1. Indicadores y Óptimo</button>
          <button type="button" class="btn btn-outline design-tab-btn ${pestana === "historico" ? "active" : ""}" data-tab="historico">2. Histórico Manual (${historico.length})</button>
          <button type="button" class="btn btn-outline design-tab-btn ${pestana === "casos" ? "active" : ""}" data-tab="casos">3. Casos Tipo (${nCasos})</button>
        </div>
        <div class="cat-banner-stats">${tTxt}</div>
      </div>
    `;
    contenedorHeader.querySelectorAll(".design-tab-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        if (callbacks.alCambiarPestana) callbacks.alCambiarPestana(btn.dataset.tab);
      });
    });
  }

  contenedorBody.innerHTML = "";
  if (!res) {
    contenedorBody.innerHTML = `<div class="sim-section"><p class="sim-section-desc">⏳ Calculando indicadores ponderados, especificaciones óptimas y casos tipo...</p></div>`;
    return;
  }

  const bodyRoot = document.createElement("div");
  bodyRoot.className = "design-body-root";
  contenedorBody.appendChild(bodyRoot);

  const wrappedCallbacks = {
    ...callbacks,
    alAnalizar: (ejecutarOpt = true) => {
      if (callbacks.alAnalizar) {
        const restrPayload = Array.isArray(designUi.restricciones)
          ? designUi.restricciones.map((r) => ({ ...r }))
          : null;
        const hwAct = Boolean(restrPayload?.some((r) => r.grupo === "hardware" && r.activa));
        callbacks.alAnalizar({
          pesos: { ...designUi.pesos },
          variables: Array.from(designUi.variables),
          cbat_kg: designUi.cbat_kg,
          respetar_limites: hwAct,
          restricciones: restrPayload,
          base_overrides: construirBaseOverrides(catalogoVars),
          ejecutar_optimizador: ejecutarOpt,
          usar_optimo_como_base: designUi.usarOptimoComoBase,
        });
      }
    },
  };

  if (pestana === "historico") {
    renderizarPestanaHistorico(bodyRoot, res, historico, wrappedCallbacks);
  } else if (pestana === "casos") {
    renderizarPestanaCasos(bodyRoot, res, wrappedCallbacks);
  } else {
    renderizarPestanaOptimo(bodyRoot, res, estadoApp, wrappedCallbacks);
  }
}
