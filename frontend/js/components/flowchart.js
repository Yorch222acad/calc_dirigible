// =============================================================
// flowchart.js — Diagrama interactivo vertical de flujo por categoría
// y Mapa de Flujo Global (C1 -> C13) con trazado ortogonal tipo
// esquema eléctrico y etiquetas en píldora sin superposición.
// =============================================================

const SVG_NS = "http://www.w3.org/2000/svg";

function crearSvgEl(tag, attrs = {}, textContent = null) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== null && v !== undefined) {
      el.setAttribute(k, String(v));
    }
  }
  if (textContent !== null) {
    el.textContent = textContent;
  }
  return el;
}

function escaparHtml(str) {
  return String(str ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function envolverTexto(texto, maxCaracteres = 24, maxLineas = 2) {
  const palabras = String(texto || "").trim().split(/\s+/);
  const lineas = [];
  let actual = "";
  for (const p of palabras) {
    if (!actual) {
      actual = p;
    } else if ((actual + " " + p).length <= maxCaracteres) {
      actual += " " + p;
    } else {
      lineas.push(actual);
      actual = p;
      if (lineas.length === maxLineas - 1) break;
    }
  }
  if (actual && lineas.length < maxLineas) {
    lineas.push(actual);
  }
  if (lineas.length > maxLineas) {
    lineas.length = maxLineas;
  }
  const ultimo = lineas.length - 1;
  if (ultimo >= 0 && lineas[ultimo].length > maxCaracteres) {
    lineas[ultimo] = lineas[ultimo].slice(0, maxCaracteres - 1) + "…";
  }
  return lineas;
}

function truncarTexto(texto, maxChars) {
  const s = String(texto || "");
  return s.length > maxChars ? s.slice(0, maxChars - 1) + "…" : s;
}

function agregarMarcadores(defs) {
  const marcadores = [
    { id: "arrow-normal", color: "#38bdf8" },
    { id: "arrow-loop", color: "#fb923c" },
    { id: "arrow-ext", color: "#64748b" },
    { id: "arrow-hi", color: "#fde047" },
    { id: "arrow-cat-cyan", color: "#38bdf8" },
    { id: "arrow-cat-orange", color: "#fb923c" },
    { id: "arrow-cat-purple", color: "#a78bfa" },
    { id: "arrow-cat-green", color: "#4ade80" },
  ];
  for (const m of marcadores) {
    const marker = crearSvgEl("marker", {
      id: m.id,
      viewBox: "0 0 10 10",
      refX: "8.5",
      refY: "5",
      markerWidth: "6",
      markerHeight: "6",
      orient: "auto-start-reverse",
    });
    marker.appendChild(
      crearSvgEl("path", {
        d: "M 0 1.4 L 9.5 5 L 0 8.6 z",
        fill: m.color,
      })
    );
    defs.appendChild(marker);
  }
}

function coloresEstadoVar(infoVar, colorGrupo) {
  if (!infoVar) {
    return { stroke: colorGrupo || "#38bdf8", fill: "#0f172a", badge: "#94a3b8" };
  }
  if (infoVar.penalizada) {
    return { stroke: "#f87171", fill: "#28131a", badge: "#fca5a5" };
  }
  if (infoVar.fija ?? infoVar.es_fija) {
    return { stroke: "#facc15", fill: "#241a08", badge: "#fef08a" };
  }
  return { stroke: "#4ade80", fill: "#0e211b", badge: "#86efac" };
}

/**
 * Convierte una polilínea ortogonal `puntos` [{x, y}, ...] en path SVG `d`
 * con esquinas redondeadas mediante curvas cuadráticas Q (estilo esquemático CAD).
 */
function trazarRutaOrtogonal(puntos, radio = 8) {
  const limpios = [];
  for (const p of puntos) {
    const prev = limpios[limpios.length - 1];
    if (prev && Math.hypot(p.x - prev.x, p.y - prev.y) < 0.5) continue;
    limpios.push({ x: Number(p.x.toFixed(1)), y: Number(p.y.toFixed(1)) });
  }
  if (limpios.length === 0) return "";
  if (limpios.length === 1) return `M ${limpios[0].x} ${limpios[0].y}`;
  if (limpios.length === 2) {
    return `M ${limpios[0].x} ${limpios[0].y} L ${limpios[1].x} ${limpios[1].y}`;
  }

  const simples = [limpios[0]];
  for (let i = 1; i < limpios.length - 1; i++) {
    const a = simples[simples.length - 1];
    const b = limpios[i];
    const c = limpios[i + 1];
    const colinealX = Math.abs(a.x - b.x) < 0.5 && Math.abs(b.x - c.x) < 0.5;
    const colinealY = Math.abs(a.y - b.y) < 0.5 && Math.abs(b.y - c.y) < 0.5;
    if (!colinealX && !colinealY) {
      simples.push(b);
    }
  }
  simples.push(limpios[limpios.length - 1]);

  if (simples.length === 2) {
    return `M ${simples[0].x} ${simples[0].y} L ${simples[1].x} ${simples[1].y}`;
  }

  const partes = [`M ${simples[0].x} ${simples[0].y}`];
  for (let i = 1; i < simples.length - 1; i++) {
    const a = simples[i - 1];
    const b = simples[i];
    const c = simples[i + 1];
    const dx1 = b.x - a.x;
    const dy1 = b.y - a.y;
    const dx2 = c.x - b.x;
    const dy2 = c.y - b.y;
    const len1 = Math.hypot(dx1, dy1);
    const len2 = Math.hypot(dx2, dy2);
    const r = Math.min(radio, len1 * 0.45, len2 * 0.45);
    if (r < 1.2 || len1 < 0.5 || len2 < 0.5) {
      partes.push(`L ${b.x} ${b.y}`);
      continue;
    }
    const pEnt = { x: b.x - (dx1 / len1) * r, y: b.y - (dy1 / len1) * r };
    const pSal = { x: b.x + (dx2 / len2) * r, y: b.y + (dy2 / len2) * r };
    partes.push(`L ${pEnt.x.toFixed(1)} ${pEnt.y.toFixed(1)}`);
    partes.push(`Q ${b.x.toFixed(1)} ${b.y.toFixed(1)} ${pSal.x.toFixed(1)} ${pSal.y.toFixed(1)}`);
  }
  const ult = simples[simples.length - 1];
  partes.push(`L ${ult.x} ${ult.y}`);
  return partes.join(" ");
}

function rectSeSolapa(r, caja, margen = 4) {
  return !(
    r.x2 + margen <= caja.x1 ||
    r.x1 - margen >= caja.x2 ||
    r.y2 + margen <= caja.y1 ||
    r.y1 - margen >= caja.y2
  );
}

/**
 * Busca la mejor posición sin colisiones para una etiqueta píldora en SVG.
 */
function ubicarEtiquetaSinColision(candidatos, texto, cajasNodos, cajasLabels, minX = 8, maxX = 1360) {
  const pw = Math.max(40, texto.length * 6.8 + 16);
  const ph = 19;

  const desplazamientos = [
    { dx: 0, dy: 0 },
    { dx: 0, dy: -20 },
    { dx: 0, dy: 20 },
    { dx: -32, dy: 0 },
    { dx: 32, dy: 0 },
    { dx: 0, dy: -38 },
    { dx: 0, dy: 38 },
    { dx: -52, dy: -14 },
    { dx: 52, dy: 14 },
    { dx: 0, dy: -56 },
    { dx: 0, dy: 56 },
  ];

  let mejorFallback = null;
  let menorPenalidad = Infinity;

  for (const base of candidatos) {
    for (const off of desplazamientos) {
      let cx = base.x + off.dx;
      const cy = base.y + off.dy;
      cx = Math.max(minX + pw / 2, Math.min(maxX - pw / 2, cx));
      const rect = {
        x1: cx - pw / 2,
        y1: cy - ph / 2,
        x2: cx + pw / 2,
        y2: cy + ph / 2,
      };

      const chocaNodo = cajasNodos.some((n) => rectSeSolapa(rect, n, 4));
      const chocaLabel = cajasLabels.some((l) => rectSeSolapa(rect, l, 3));

      if (!chocaNodo && !chocaLabel) {
        cajasLabels.push(rect);
        return { x: cx, y: cy, w: pw, h: ph };
      }

      const pen = (chocaNodo ? 100 : 0) + (chocaLabel ? 10 : 0) + Math.hypot(off.dx, off.dy) * 0.01;
      if (pen < menorPenalidad) {
        menorPenalidad = pen;
        mejorFallback = { x: cx, y: cy, w: pw, h: ph, rect };
      }
    }
  }

  if (mejorFallback) {
    cajasLabels.push(mejorFallback.rect);
    return mejorFallback;
  }
  return { x: candidatos[0]?.x || 0, y: candidatos[0]?.y || 0, w: pw, h: ph };
}

/**
 * Crea un badge/píldora oscuro legible con borde sutil para rotular aristas.
 */
function crearEtiquetaPildora(x, y, texto, colorTexto = "#cbd5e1", colorBorde = "#334155") {
  const pw = Math.max(40, texto.length * 6.8 + 16);
  const ph = 19;
  const g = crearSvgEl("g", {
    class: "flow-edge-label",
    "pointer-events": "none",
  });
  g.appendChild(
    crearSvgEl("rect", {
      x: x - pw / 2,
      y: y - ph / 2,
      width: pw,
      height: ph,
      rx: 5,
      fill: "#070e1c",
      "fill-opacity": "0.95",
      stroke: colorBorde,
      "stroke-width": "0.95",
    })
  );
  const t = crearSvgEl(
    "text",
    {
      x,
      y: y + 3.8,
      "text-anchor": "middle",
      fill: colorTexto,
      "font-size": "10.5",
      "font-family": "var(--font-mono), monospace",
      "font-weight": "600",
    },
    texto
  );
  g.appendChild(t);
  return g;
}

function asignarPuertos(listaIds, centroMin, centroMax) {
  const mapa = new Map();
  const n = listaIds.length;
  if (n === 0) return mapa;
  const mid = (centroMin + centroMax) / 2;
  if (n === 1) {
    mapa.set(listaIds[0], mid);
    return mapa;
  }
  const rango = centroMax - centroMin;
  const paso = rango / (n - 1);
  listaIds.forEach((id, idx) => {
    mapa.set(id, centroMin + idx * paso);
  });
  return mapa;
}

/**
 * Renderiza el bloque completo de Flujo de Ecuaciones debajo de las tarjetas de
 * ecuaciones dentro de la vista de categoría seleccionada, extendido verticalmente.
 */
export function renderizarFlujoCategoria(contenedor, catActiva, estadoApp, callbacks = {}) {
  const { alClickCategoria, alClickEcuacion, alClickVariable, alAbrirMapaGlobal } = callbacks;
  const flujo = catActiva?.flujo;
  if (!flujo) {
    contenedor.querySelector("#cat-flow-section")?.remove();
    return;
  }

  const sistema = estadoApp?.sistema || estadoApp;
  const varsRaw = sistema?.variables || [];
  const varsMap = Array.isArray(varsRaw)
    ? Object.fromEntries(varsRaw.map((v) => [v.nombre, v]))
    : varsRaw;
  const catCodigo = flujo.categoria_codigo || catActiva.codigo || `C${(catActiva.id ?? 0) + 1}`;

  const nodos = flujo.nodos || [];
  const aristas = flujo.aristas_internas || [];
  const entradas = flujo.entradas_externas || [];
  const salidas = flujo.salidas_externas || [];
  const grupo = flujo.grupo || { nombre: "", color: "#38bdf8" };

  const section = document.createElement("section");
  section.id = "cat-flow-section";
  section.className = "cat-flow-section";

  // Cabecera del panel de flujo
  const header = document.createElement("div");
  header.className = "cat-flow-header";
  header.innerHTML = `
    <div class="cat-flow-title-wrap">
      <h3 class="cat-flow-title">◈ Flujo de Ecuaciones y Relaciones — ${escaparHtml(catCodigo)}. ${escaparHtml(catActiva.nombre)}</h3>
      <span class="flow-group-pill" style="--grp-color: ${grupo.color};">
        ${escaparHtml(grupo.nombre)}
      </span>
    </div>
  `;

  const btnGlobal = document.createElement("button");
  btnGlobal.type = "button";
  btnGlobal.className = "btn btn-secondary flow-open-global-btn";
  btnGlobal.textContent = "◈ Mapa de Flujo Global (C1 → C13) ↗";
  btnGlobal.addEventListener("click", () => {
    if (alAbrirMapaGlobal) alAbrirMapaGlobal();
  });
  header.appendChild(btnGlobal);
  section.appendChild(header);

  // Tarjetas de explicación física de la categoría y flujo interno
  const narrativa = document.createElement("div");
  narrativa.className = "flow-expl-grid";
  narrativa.innerHTML = `
    <div class="flow-expl-card">
      <div class="flow-expl-label">1. Propósito físico de la categoría</div>
      <p class="flow-expl-text">${escaparHtml(flujo.resumen)}</p>
    </div>
    <div class="flow-expl-card">
      <div class="flow-expl-label">2. Encadenamiento de ecuaciones e iteraciones internas</div>
      <p class="flow-expl-text">${escaparHtml(flujo.flujo_interno)}</p>
    </div>
  `;
  section.appendChild(narrativa);

  // =========================================================================
  // DIAGRAMADOR SVG VERTICAL (ARRIBA → ABAJO) ESTILO ESQUEMA ELÉCTRICO
  // =========================================================================
  const diagramWrap = document.createElement("div");
  diagramWrap.className = "flow-svg-wrapper";

  // Agrupación por capas verticales (capa 0 arriba .. maxCapa abajo)
  const capas = new Map();
  let maxCapa = 0;
  for (const n of nodos) {
    const c = Number(n.capa || 0);
    if (c > maxCapa) maxCapa = c;
    if (!capas.has(c)) capas.set(c, []);
    capas.get(c).push(n);
  }
  const numCapas = maxCapa + 1;
  const maxNodosPorCapa = Math.max(1, ...Array.from(capas.values()).map((arr) => arr.length));

  const nodoTmp = new Map();
  for (const [c, lista] of capas.entries()) {
    lista.forEach((n, idx) => {
      nodoTmp.set(n.var, { capa: c, col: idx, totalCapa: lista.length });
    });
  }

  // Constantes geométricas holgadas y tipografía grande legible
  const padX = 20;
  const padY = 20;
  const bandGapY = 56;
  const titleBandH = 38;
  const topInnerPad = 46;
  const bottomInnerPad = 46;

  const nodeW = 218;
  const nodeH = 74;
  const colGap = 64;
  const rowGap = 86;

  const extW = 212;
  const extH = 74;
  const extGapX = 18;
  const extGapY = 44;
  const extMaxPerRow = 4;

  // Planificar filas de ENTRADAS y SALIDAS (máx 4 por fila)
  const inRowsCount = entradas.length > 0 ? Math.ceil(entradas.length / extMaxPerRow) : 0;
  const outRowsCount = salidas.length > 0 ? Math.ceil(salidas.length / extMaxPerRow) : 0;

  const extOutRowMap = new Map();
  salidas.forEach((_, i) => extOutRowMap.set(i, Math.floor(i / extMaxPerRow)));
  const extInRowMap = new Map();
  entradas.forEach((_, i) => extInRowMap.set(i, Math.floor(i / extMaxPerRow)));

  // Clasificar aristas internas: directas vs buses laterales izquierdo/derecho
  const aristasDirectas = [];
  const aristasLeftBus = [];
  const aristasRightBus = [];

  let leftLoopsSoFar = 0;
  let rightLoopsSoFar = 0;

  aristas.forEach((a, idx) => {
    const o = nodoTmp.get(a.origen);
    const d = nodoTmp.get(a.destino);
    if (!o || !d) return;

    const requiereBus = Boolean(a.lazo) || d.capa < o.capa || d.capa - o.capa > 1;
    if (!requiereBus) {
      aristasDirectas.push({ arista: a, idx });
      return;
    }

    // Elegir lado izquierdo o derecho según posición horizontal o alternancia para múltiples lazos
    const oRel = (o.col + 0.5) / Math.max(1, o.totalCapa);
    const dRel = (d.col + 0.5) / Math.max(1, d.totalCapa);
    const promRel = (oRel + dRel) / 2;

    let side;
    if (a.lazo && leftLoopsSoFar !== rightLoopsSoFar) {
      side = leftLoopsSoFar < rightLoopsSoFar ? "left" : "right";
    } else if (Math.abs(promRel - 0.5) < 0.08) {
      side = leftLoopsSoFar <= rightLoopsSoFar ? "left" : "right";
    } else {
      side = promRel < 0.5 ? "left" : "right";
    }

    if (side === "left") {
      leftLoopsSoFar += 1;
      aristasLeftBus.push({ arista: a, idx, side });
    } else {
      rightLoopsSoFar += 1;
      aristasRightBus.push({ arista: a, idx, side });
    }
  });

  // Planificar conexiones externas profundas vs directas
  const extEdgesPlan = [];
  let leftExtCount = 0;
  let rightExtCount = 0;

  entradas.forEach((ext, extIdx) => {
    const inRow = extInRowMap.get(extIdx) ?? 0;
    const rowLen = Math.min(extMaxPerRow, entradas.length - inRow * extMaxPerRow);
    const colInRow = extIdx % extMaxPerRow;
    const extRel = (colInRow + 0.5) / Math.max(1, rowLen);

    (ext.nodos_conectados || []).forEach((vDst) => {
      const d = nodoTmp.get(vDst);
      if (!d) return;
      const necesitaBus = d.capa > 0 || (inRowsCount > 1 && inRow === 0);
      if (!necesitaBus) {
        extEdgesPlan.push({ dir: "in", ext, extIdx, extRow: inRow, vNode: vDst, direct: true, side: null });
      } else {
        const dRel = (d.col + 0.5) / Math.max(1, d.totalCapa);
        const side = (dRel + extRel) / 2 < 0.5 ? "left" : "right";
        if (side === "left") leftExtCount += 1;
        else rightExtCount += 1;
        extEdgesPlan.push({ dir: "in", ext, extIdx, extRow: inRow, vNode: vDst, direct: false, side });
      }
    });
  });

  salidas.forEach((ext, extIdx) => {
    const outRow = extOutRowMap.get(extIdx) ?? 0;
    const rowLen = Math.min(extMaxPerRow, salidas.length - outRow * extMaxPerRow);
    const colInRow = extIdx % extMaxPerRow;
    const extRel = (colInRow + 0.5) / Math.max(1, rowLen);

    (ext.nodos_conectados || []).forEach((vSrc) => {
      const s = nodoTmp.get(vSrc);
      if (!s) return;
      const necesitaBus = s.capa < maxCapa;
      if (!necesitaBus) {
        extEdgesPlan.push({ dir: "out", ext, extIdx, extRow: outRow, vNode: vSrc, direct: true, side: extRel < 0.5 ? "left" : "right" });
      } else {
        const sRel = (s.col + 0.5) / Math.max(1, s.totalCapa);
        const side = (sRel + extRel) / 2 < 0.5 ? "left" : "right";
        if (side === "left") leftExtCount += 1;
        else rightExtCount += 1;
        extEdgesPlan.push({ dir: "out", ext, extIdx, extRow: outRow, vNode: vSrc, direct: false, side });
      }
    });
  });

  // Cálculo de anchos de carriles laterales y ancho total compacto
  const intTrackStep = 26;
  const extTrackStep = 9;
  const leftBusW = Math.max(54, aristasLeftBus.length * intTrackStep + leftExtCount * extTrackStep + 22);
  const rightBusW = Math.max(54, aristasRightBus.length * intTrackStep + rightExtCount * extTrackStep + 22);

  const gridW = maxNodosPorCapa * nodeW + Math.max(0, maxNodosPorCapa - 1) * colGap;
  const extMaxCols = Math.min(extMaxPerRow, Math.max(entradas.length, salidas.length));
  const extMaxRowW = extMaxCols > 0 ? extMaxCols * extW + (extMaxCols - 1) * extGapX : 0;

  const innerW = Math.max(gridW + leftBusW + rightBusW, extMaxRowW + 116, 860);
  const innerX = padX;
  const totalW = innerW + padX * 2;

  // Cálculo de alturas verticales (ENTRADAS arriba → FLUJO INTERNO centro → SALIDAS abajo)
  const extBandTopPad = 34;
  const extBandBotPad = 14;

  const inBandH =
    inRowsCount > 0 ? extBandTopPad + inRowsCount * extH + Math.max(0, inRowsCount - 1) * extGapY + extBandBotPad : 0;
  const outBandH =
    outRowsCount > 0 ? extBandTopPad + outRowsCount * extH + Math.max(0, outRowsCount - 1) * extGapY + extBandBotPad : 0;

  const nodesGridH = numCapas * nodeH + Math.max(0, numCapas - 1) * rowGap;
  const innerBoxH = titleBandH + topInnerPad + nodesGridH + bottomInnerPad;

  const inBandY = padY;
  const innerBoxY = padY + (inRowsCount > 0 ? inBandH + bandGapY : 0);
  const outBandY = innerBoxY + innerBoxH + (outRowsCount > 0 ? bandGapY : 0);
  const totalH = (outRowsCount > 0 ? outBandY + outBandH : innerBoxY + innerBoxH) + padY;

  const gridStartY = innerBoxY + titleBandH + topInnerPad;
  const gridAreaLeft = innerX + leftBusW;
  const gridAreaW = innerW - leftBusW - rightBusW;

  const svg = crearSvgEl("svg", {
    viewBox: `0 0 ${totalW} ${totalH}`,
    class: "flow-svg",
    role: "img",
    "aria-label": `Diagrama de flujo vertical para ${catCodigo}. ${catActiva.nombre}`,
  });
  svg.style.minWidth = `${Math.round(totalW * 0.82)}px`;
  svg.style.maxWidth = `${Math.round(totalW * 1.08)}px`;
  svg.style.margin = "0 auto";

  const defs = crearSvgEl("defs");
  agregarMarcadores(defs);
  svg.appendChild(defs);

  // Fondos de bandas verticales
  const bgLayer = crearSvgEl("g");
  if (inRowsCount > 0) {
    bgLayer.appendChild(
      crearSvgEl("rect", {
        x: innerX,
        y: inBandY,
        width: innerW,
        height: inBandH,
        rx: 10,
        fill: "#0f172a",
        stroke: "#1e293b",
        "stroke-dasharray": "4 4",
      })
    );
    bgLayer.appendChild(
      crearSvgEl(
        "text",
        {
          x: innerX + 16,
          y: inBandY + 21,
          fill: "#94a3b8",
          "font-size": "11",
          "font-weight": "700",
          "letter-spacing": "0.08em",
        },
        `ENTRADAS (${entradas.length})`
      )
    );
  }

  bgLayer.appendChild(
    crearSvgEl("rect", {
      x: innerX,
      y: innerBoxY,
      width: innerW,
      height: innerBoxH,
      rx: 12,
      fill: "#0a1120",
      stroke: "#1e3a5f",
      "stroke-width": "1.2",
    })
  );
  bgLayer.appendChild(
    crearSvgEl(
      "text",
      {
        x: innerX + 16,
        y: innerBoxY + 23,
        fill: "#38bdf8",
        "font-size": "11.5",
        "font-weight": "700",
        "letter-spacing": "0.05em",
      },
      `FLUJO INTERNO (${catCodigo}) — CLIC EN UN NODO PARA UBICAR LA ECUACIÓN`
    )
  );

  if (outRowsCount > 0) {
    bgLayer.appendChild(
      crearSvgEl("rect", {
        x: innerX,
        y: outBandY,
        width: innerW,
        height: outBandH,
        rx: 10,
        fill: "#0f172a",
        stroke: "#1e293b",
        "stroke-dasharray": "4 4",
      })
    );
    bgLayer.appendChild(
      crearSvgEl(
        "text",
        {
          x: innerX + 16,
          y: outBandY + 21,
          fill: "#94a3b8",
          "font-size": "11",
          "font-weight": "700",
          "letter-spacing": "0.08em",
        },
        `SALIDAS (${salidas.length})`
      )
    );
  }
  svg.appendChild(bgLayer);

  // Calcular posiciones de los nodos internos centrados por fila en gridArea
  const nodePos = new Map();
  const layerYs = [];
  for (let c = 0; c < numCapas; c++) {
    const ny = gridStartY + c * (nodeH + rowGap);
    layerYs.push(ny);
    const lista = capas.get(c) || [];
    const rowW = lista.length * nodeW + Math.max(0, lista.length - 1) * colGap;
    const startX = gridAreaLeft + (gridAreaW - rowW) / 2;
    lista.forEach((n, idx) => {
      const nx = startX + idx * (nodeW + colGap);
      nodePos.set(n.var, { ...n, capa: c, col: idx, totalCapa: lista.length, x: nx, y: ny, w: nodeW, h: nodeH });
    });
  }

  // Centros de pasillos horizontales entre filas (aisleAbove(c), aisleBelow(c))
  const aisleMidY = (c) => gridStartY + c * (nodeH + rowGap) + nodeH + rowGap / 2;

  // Posiciones de cajas externas centradas horizontalmente dentro de [innerX + 56, innerX + innerW - 56]
  const extAreaLeft = innerX + 56;
  const extAreaW = innerW - 112;

  function layoutExtBoxes(lista, bandY) {
    const res = [];
    const rows = lista.length > 0 ? Math.ceil(lista.length / extMaxPerRow) : 0;
    for (let r = 0; r < rows; r++) {
      const slice = lista.slice(r * extMaxPerRow, (r + 1) * extMaxPerRow);
      const rowW = slice.length * extW + Math.max(0, slice.length - 1) * extGapX;
      const startX = extAreaLeft + (extAreaW - rowW) / 2;
      const by = bandY + extBandTopPad + r * (extH + extGapY);
      slice.forEach((ext, k) => {
        res.push({
          ...ext,
          row: r,
          col: k,
          x: startX + k * (extW + extGapX),
          y: by,
          w: extW,
          h: extH,
        });
      });
    }
    return res;
  }

  const extInBoxes = layoutExtBoxes(entradas, inBandY);
  const extOutBoxes = layoutExtBoxes(salidas, outBandY);

  // Coordenadas X reales de los carriles verticales laterales (fuera de toda caja de nodo)
  const leftIntXs = [];
  for (let i = 0; i < aristasLeftBus.length; i++) {
    leftIntXs.push(gridAreaLeft - 24 - i * intTrackStep);
  }
  const leftExtBaseX = gridAreaLeft - 24 - aristasLeftBus.length * intTrackStep;
  const rightIntXs = [];
  for (let i = 0; i < aristasRightBus.length; i++) {
    rightIntXs.push(gridAreaLeft + gridAreaW + 24 + i * intTrackStep);
  }
  const rightExtBaseX = gridAreaLeft + gridAreaW + 24 + aristasRightBus.length * intTrackStep;

  let leftExtCursor = 0;
  let rightExtCursor = 0;
  function nextExtBusX(side) {
    if (side === "left") {
      const x = Math.max(innerX + 14, leftExtBaseX - leftExtCursor * extTrackStep);
      leftExtCursor += 1;
      return x;
    }
    const x = Math.min(innerX + innerW - 14, rightExtBaseX + rightExtCursor * extTrackStep);
    rightExtCursor += 1;
    return x;
  }

  // Asignación de puertos horizontales X en borde superior (entradas) e inferior (salidas) de cada nodo
  const topPortsIn = new Map();
  const botPortsOut = new Map();
  for (const n of nodePos.values()) {
    topPortsIn.set(n.var, []);
    botPortsOut.set(n.var, []);
  }

  aristasDirectas.forEach(({ arista, idx }) => {
    const s = nodePos.get(arista.origen);
    const d = nodePos.get(arista.destino);
    if (!s || !d || s.capa === d.capa) return;
    botPortsOut.get(s.var).push({ key: `int-out-${idx}`, sortX: d.x + d.w / 2 });
    topPortsIn.get(d.var).push({ key: `int-in-${idx}`, sortX: s.x + s.w / 2 });
  });

  aristasLeftBus.forEach(({ arista, idx }) => {
    const s = nodePos.get(arista.origen);
    const d = nodePos.get(arista.destino);
    if (!s || !d) return;
    botPortsOut.get(s.var).push({ key: `int-out-${idx}`, sortX: -10000 - idx });
    topPortsIn.get(d.var).push({ key: `int-in-${idx}`, sortX: -10000 - idx });
  });

  aristasRightBus.forEach(({ arista, idx }) => {
    const s = nodePos.get(arista.origen);
    const d = nodePos.get(arista.destino);
    if (!s || !d) return;
    botPortsOut.get(s.var).push({ key: `int-out-${idx}`, sortX: 100000 + idx });
    topPortsIn.get(d.var).push({ key: `int-in-${idx}`, sortX: 100000 + idx });
  });

  extEdgesPlan.forEach((item, idx) => {
    if (item.dir === "in") {
      const box = extInBoxes[item.extIdx];
      const sortX = item.direct ? (box?.x || 0) + (box?.w || 0) / 2 : item.side === "left" ? -5000 + idx : 50000 + idx;
      topPortsIn.get(item.vNode)?.push({ key: `ext-in-${idx}`, sortX });
    } else {
      const box = extOutBoxes[item.extIdx];
      const sortX = item.direct ? (box?.x || 0) + (box?.w || 0) / 2 : item.side === "left" ? -5000 + idx : 50000 + idx;
      botPortsOut.get(item.vNode)?.push({ key: `ext-out-${idx}`, sortX });
    }
  });

  const nodePortX = new Map();
  for (const n of nodePos.values()) {
    const ins = topPortsIn.get(n.var).sort((a, b) => a.sortX - b.sortX);
    const outs = botPortsOut.get(n.var).sort((a, b) => a.sortX - b.sortX);
    const inMap = asignarPuertos(ins.map((x) => x.key), n.x + 24, n.x + n.w - 24);
    const outMap = asignarPuertos(outs.map((x) => x.key), n.x + 24, n.x + n.w - 24);
    for (const [k, v] of inMap.entries()) nodePortX.set(k, v);
    for (const [k, v] of outMap.entries()) nodePortX.set(k, v);
  }

  // Puertos X en cajas externas (borde inferior de ENTRADAS y superior de SALIDAS)
  const extInOutPortsX = new Map();
  extInBoxes.forEach((box, extIdx) => {
    const items = extEdgesPlan
      .map((it, idx) => ({ it, idx }))
      .filter(({ it }) => it.dir === "in" && it.extIdx === extIdx)
      .sort((a, b) => (nodePos.get(a.it.vNode)?.x || 0) - (nodePos.get(b.it.vNode)?.x || 0));
    const mapX = asignarPuertos(items.map((x) => x.idx), box.x + 28, box.x + box.w - 28);
    for (const [k, v] of mapX.entries()) extInOutPortsX.set(k, v);
  });

  const extOutInPortsX = new Map();
  extOutBoxes.forEach((box, extIdx) => {
    const items = extEdgesPlan
      .map((it, idx) => ({ it, idx }))
      .filter(({ it }) => it.dir === "out" && it.extIdx === extIdx)
      .sort((a, b) => (nodePos.get(a.it.vNode)?.x || 0) - (nodePos.get(b.it.vNode)?.x || 0));
    const mapX = asignarPuertos(items.map((x) => x.idx), box.x + 28, box.x + box.w - 28);
    for (const [k, v] of mapX.entries()) extOutInPortsX.set(k, v);
  });

  const cajasNodos = [
    ...Array.from(nodePos.values()).map((n) => ({ x1: n.x, y1: n.y, x2: n.x + n.w, y2: n.y + n.h })),
    ...extInBoxes.map((b) => ({ x1: b.x, y1: b.y, x2: b.x + b.w, y2: b.y + b.h })),
    ...extOutBoxes.map((b) => ({ x1: b.x, y1: b.y, x2: b.x + b.w, y2: b.y + b.h })),
  ];
  const cajasLabels = [];

  const edgesLayer = crearSvgEl("g", { class: "flow-edges-layer" });
  const nodesLayer = crearSvgEl("g", { class: "flow-nodes-layer" });
  const labelsLayer = crearSvgEl("g", { class: "flow-labels-layer" });
  svg.appendChild(edgesLayer);
  svg.appendChild(nodesLayer);
  svg.appendChild(labelsLayer);

  const edgeRefs = [];

  // Contadores de sub-carriles horizontales por brecha entre filas (para evitar superposición de trazos horizontales)
  const directAisleCounter = new Map();
  function nextDirectAisleY(capa) {
    const k = directAisleCounter.get(capa) || 0;
    directAisleCounter.set(capa, k + 1);
    const seq = [0, -10, 10, -20, 20];
    return aisleMidY(capa) + (seq[k % seq.length] ?? 0);
  }

  const depBandCounter = new Map();
  function depBandY(capa) {
    const k = depBandCounter.get(capa) || 0;
    depBandCounter.set(capa, k + 1);
    const base = layerYs[capa] + nodeH + 14;
    return base + (k % 3) * 7;
  }

  const arrBandCounter = new Map();
  function arrBandY(capa) {
    const k = arrBandCounter.get(capa) || 0;
    arrBandCounter.set(capa, k + 1);
    const base = layerYs[capa] - 14;
    return base - (k % 3) * 7;
  }

  let topBandGapIdx = 0;
  function nextTopBandGapY() {
    const mid = inBandY + inBandH + bandGapY / 2;
    const seq = [0, -10, 10, -19, 19];
    const y = mid + (seq[topBandGapIdx % seq.length] ?? 0);
    topBandGapIdx += 1;
    return y;
  }

  let botBandGapIdx = 0;
  function nextBotBandGapY() {
    const mid = innerBoxY + innerBoxH + bandGapY / 2;
    const seq = [0, -10, 10, -19, 19, -24, 24];
    const y = mid + (seq[botBandGapIdx % seq.length] ?? 0);
    botBandGapIdx += 1;
    return y;
  }

  let rowGapInIdx = 0;
  let rowGapOutIdx = 0;
  let leftOuterRow1Cursor = 0;
  let rightOuterRow1Cursor = 0;

  // 1) CONEXIONES EXTERNAS (ENTRADAS -> FLUJO INTERNO, FLUJO INTERNO -> SALIDAS)
  extEdgesPlan.forEach((item, idx) => {
    const n = nodePos.get(item.vNode);
    if (!n) return;
    const isLazo = Boolean(item.ext.es_lazo);
    const strokeCol = isLazo ? "#fb923c" : "#64748b";
    const markerEnd = isLazo ? "url(#arrow-loop)" : "url(#arrow-ext)";

    let puntos = [];
    if (item.dir === "in") {
      const box = extInBoxes[item.extIdx];
      const x1 = extInOutPortsX.get(idx) ?? box.x + box.w / 2;
      const y1 = box.y + box.h;
      const x2 = nodePortX.get(`ext-in-${idx}`) ?? n.x + n.w / 2;
      const y2 = n.y;
      const yGap = nextTopBandGapY();

      if (item.direct) {
        puntos = [
          { x: x1, y: y1 },
          { x: x1, y: yGap },
          { x: x2, y: yGap },
          { x: x2, y: y2 - 4 },
        ];
      } else if (inRowsCount > 1 && box.row === 0) {
        const gX =
          item.side === "left"
            ? innerX + 18 + (leftOuterRow1Cursor++ % 3) * 9
            : innerX + innerW - 18 - (rightOuterRow1Cursor++ % 3) * 9;
        const yBetween = box.y + box.h + 18 + (rowGapInIdx++ % 3) * 7;
        const busX = n.capa > 0 ? nextExtBusX(item.side) : gX;
        const yArr = arrBandY(n.capa);
        puntos = [
          { x: x1, y: y1 },
          { x: x1, y: yBetween },
          { x: gX, y: yBetween },
          { x: gX, y: yGap },
          { x: busX, y: yGap },
          { x: busX, y: yArr },
          { x: x2, y: yArr },
          { x: x2, y: y2 - 4 },
        ];
      } else {
        const busX = nextExtBusX(item.side);
        const yArr = arrBandY(n.capa);
        puntos = [
          { x: x1, y: y1 },
          { x: x1, y: yGap },
          { x: busX, y: yGap },
          { x: busX, y: yArr },
          { x: x2, y: yArr },
          { x: x2, y: y2 - 4 },
        ];
      }
    } else {
      const box = extOutBoxes[item.extIdx];
      const x1 = nodePortX.get(`ext-out-${idx}`) ?? n.x + n.w / 2;
      const y1 = n.y + n.h;
      const x2 = extOutInPortsX.get(idx) ?? box.x + box.w / 2;
      const y2 = box.y;
      const yGap = nextBotBandGapY();

      // Parte A: desde el nodo hasta el borde de salida hacia bandGapY
      const ptsA = [{ x: x1, y: y1 }];
      if (!item.direct) {
        const busX = nextExtBusX(item.side);
        const yDep = depBandY(n.capa);
        ptsA.push({ x: x1, y: yDep }, { x: busX, y: yDep }, { x: busX, y: yGap });
      } else {
        ptsA.push({ x: x1, y: yGap });
      }

      // Parte B: desde yGap hasta la caja de SALIDAS (directo si fila 0, o borde exterior si fila 1)
      if (box.row === 0) {
        puntos = [...ptsA, { x: x2, y: yGap }, { x: x2, y: y2 - 4 }];
      } else {
        const gX =
          item.side === "left"
            ? innerX + 18 + (leftOuterRow1Cursor++ % 3) * 9
            : innerX + innerW - 18 - (rightOuterRow1Cursor++ % 3) * 9;
        const yBetween = outBandY + extBandTopPad + extH + 14 + (rowGapOutIdx++ % 4) * 6;
        puntos = [...ptsA, { x: gX, y: yGap }, { x: gX, y: yBetween }, { x: x2, y: yBetween }, { x: x2, y: y2 - 4 }];
      }
    }

    const path = crearSvgEl("path", {
      d: trazarRutaOrtogonal(puntos, 8),
      fill: "none",
      stroke: strokeCol,
      "stroke-width": isLazo ? "1.8" : "1.45",
      "stroke-dasharray": "5 4",
      "marker-end": markerEnd,
      opacity: "0.75",
    });
    edgesLayer.appendChild(path);
    edgeRefs.push({
      pathEl: path,
      labelEl: null,
      vars: [item.vNode],
      baseColor: strokeCol,
      baseWidth: isLazo ? "1.8" : "1.45",
      baseMarker: markerEnd,
      isExt: true,
    });
  });

  // 2) ARISTAS INTERNAS: directas + buses laterales
  const todasInternasPlan = [];

  for (const { arista, idx } of aristasDirectas) {
    const s = nodePos.get(arista.origen);
    const d = nodePos.get(arista.destino);
    if (!s || !d) continue;

    let puntos = [];
    let candidatosLabel = [];

    if (s.capa === d.capa) {
      if (Math.abs(s.col - d.col) === 1) {
        const dirRight = d.col > s.col;
        const x1 = dirRight ? s.x + s.w : s.x;
        const x2 = dirRight ? d.x - 4 : d.x + d.w + 4;
        const yMid = s.y + s.h / 2;
        const midX = (x1 + x2) / 2;
        puntos = [
          { x: x1, y: yMid },
          { x: x2, y: yMid },
        ];
        candidatosLabel = [
          { x: midX, y: yMid - 14 },
          { x: midX, y: s.y - 16 },
          { x: midX, y: s.y + s.h + 16 },
        ];
      } else {
        const x1 = s.x + s.w / 2;
        const x2 = d.x + d.w / 2;
        const yAisle = depBandY(s.capa);
        puntos = [
          { x: x1, y: s.y + s.h },
          { x: x1, y: yAisle },
          { x: x2, y: yAisle },
          { x: x2, y: d.y + d.h + 4 },
        ];
        candidatosLabel = [{ x: (x1 + x2) / 2, y: yAisle }];
      }
    } else {
      const x1 = nodePortX.get(`int-out-${idx}`) ?? s.x + s.w / 2;
      const y1 = s.y + s.h;
      const x2 = nodePortX.get(`int-in-${idx}`) ?? d.x + d.w / 2;
      const y2 = d.y;

      if (Math.abs(x1 - x2) < 1.5) {
        puntos = [
          { x: x1, y: y1 },
          { x: x2, y: y2 - 4 },
        ];
        const ym = (y1 + y2) / 2;
        candidatosLabel = [
          { x: x1, y: ym },
          { x: x1 + 48, y: ym },
          { x: x1 - 48, y: ym },
        ];
      } else {
        const yAisle = nextDirectAisleY(s.capa);
        puntos = [
          { x: x1, y: y1 },
          { x: x1, y: yAisle },
          { x: x2, y: yAisle },
          { x: x2, y: y2 - 4 },
        ];
        candidatosLabel = [
          { x: (x1 + x2) / 2, y: yAisle },
          { x: x1, y: (y1 + yAisle) / 2 },
          { x: x2, y: (yAisle + y2) / 2 },
        ];
      }
    }

    todasInternasPlan.push({ arista, idx, s, d, puntos, candidatosLabel });
  }

  function planificarAristaBusLateral(item, trackIdx) {
    const { arista, idx, side } = item;
    const s = nodePos.get(arista.origen);
    const d = nodePos.get(arista.destino);
    if (!s || !d) return;

    const busX = side === "left" ? leftIntXs[trackIdx] : rightIntXs[trackIdx];
    const x1 = nodePortX.get(`int-out-${idx}`) ?? s.x + s.w / 2;
    const y1 = s.y + s.h;
    const x2 = nodePortX.get(`int-in-${idx}`) ?? d.x + d.w / 2;
    const y2 = d.y;

    const yDep = depBandY(s.capa);
    const yArr = arrBandY(d.capa);

    const puntos = [
      { x: x1, y: y1 },
      { x: x1, y: yDep },
      { x: busX, y: yDep },
      { x: busX, y: yArr },
      { x: x2, y: yArr },
      { x: x2, y: y2 - 4 },
    ];

    const yVertMid = (yDep + yArr) / 2;
    const arrMidX = (busX + x2) / 2;
    todasInternasPlan.push({
      arista,
      idx,
      s,
      d,
      puntos,
      candidatosLabel: [
        { x: arrMidX, y: yArr },
        { x: busX, y: yVertMid },
        { x: (x1 + busX) / 2, y: yDep },
      ],
    });
  }

  aristasLeftBus.forEach((it, i) => planificarAristaBusLateral(it, i));
  aristasRightBus.forEach((it, i) => planificarAristaBusLateral(it, i));

  // Pintar las aristas internas y ubicar píldoras en labelsLayer
  for (const plan of todasInternasPlan) {
    const { arista, puntos, candidatosLabel } = plan;
    const esLazo = Boolean(arista.lazo);
    const color = esLazo ? "#fb923c" : "#38bdf8";
    const marker = esLazo ? "url(#arrow-loop)" : "url(#arrow-normal)";

    const path = crearSvgEl("path", {
      d: trazarRutaOrtogonal(puntos, 8),
      fill: "none",
      stroke: color,
      "stroke-width": esLazo ? "2.2" : "1.9",
      "stroke-dasharray": esLazo ? "6 4" : null,
      "marker-end": marker,
      opacity: "0.80",
    });
    edgesLayer.appendChild(path);

    let labelEl = null;
    if (arista.etiqueta) {
      const posLbl = ubicarEtiquetaSinColision(
        candidatosLabel,
        arista.etiqueta,
        cajasNodos,
        cajasLabels,
        innerX + 10,
        innerX + innerW - 10
      );
      labelEl = crearEtiquetaPildora(
        posLbl.x,
        posLbl.y,
        arista.etiqueta,
        esLazo ? "#fdba74" : "#bae6fd",
        esLazo ? "rgba(251, 146, 60, 0.45)" : "rgba(56, 189, 248, 0.34)"
      );
      labelsLayer.appendChild(labelEl);
    }

    edgeRefs.push({
      pathEl: path,
      labelEl,
      vars: [arista.origen, arista.destino],
      baseColor: color,
      baseWidth: esLazo ? "2.2" : "1.9",
      baseMarker: marker,
      isExt: false,
    });
  }

  // 3) Cajas externas (ENTRADAS arriba y SALIDAS abajo)
  function renderCajaExterna(box, esEntrada) {
    const g = crearSvgEl("g", {
      class: "flow-svg-ext-node",
      style: "cursor: pointer;",
    });
    g.appendChild(
      crearSvgEl("rect", {
        x: box.x,
        y: box.y,
        width: box.w,
        height: box.h,
        rx: 8,
        fill: "#111c33",
        stroke: box.color || "#64748b",
        "stroke-width": "1.6",
      })
    );

    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: box.x + 11,
          y: box.y + 18,
          fill: box.color || "#38bdf8",
          "font-size": "11.5",
          "font-family": "var(--font-mono), monospace",
          "font-weight": "700",
        },
        box.categoria_codigo
      )
    );
    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: box.x + box.w - 10,
          y: box.y + 18,
          "text-anchor": "end",
          fill: box.es_lazo ? "#fb923c" : "#64748b",
          "font-size": "10",
          "font-weight": box.es_lazo ? "700" : "400",
        },
        box.es_lazo ? "↺ Lazo cerrado ↗" : "Abrir ↗"
      )
    );

    const nomLineas = envolverTexto(box.categoria_corto, 24, 2);
    nomLineas.forEach((ln, idx) => {
      g.appendChild(
        crearSvgEl(
          "text",
          {
            x: box.x + 11,
            y: box.y + 34 + idx * 13,
            fill: "#e2e8f0",
            "font-size": "11.8",
            "font-weight": "700",
          },
          ln
        )
      );
    });

    const pref = esEntrada ? "← " : "→ ";
    const varsTxt = truncarTexto(pref + (box.variables || []).join(", "), 27);
    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: box.x + 11,
          y: box.y + box.h - 9,
          fill: "#94a3b8",
          "font-size": "10.5",
          "font-family": "var(--font-mono), monospace",
        },
        varsTxt
      )
    );

    g.addEventListener("click", () => {
      if (alClickCategoria) alClickCategoria(box.categoria_id);
    });
    const titleTip = document.createElementNS(SVG_NS, "title");
    titleTip.textContent = `${box.categoria_codigo}. ${box.categoria_nombre}\n${box.explicacion}\nClic para ir a ${box.categoria_codigo}`;
    g.appendChild(titleTip);
    nodesLayer.appendChild(g);
  }

  extInBoxes.forEach((b) => renderCajaExterna(b, true));
  extOutBoxes.forEach((b) => renderCajaExterna(b, false));

  // 4) Nodos internos con tipografía grande legible
  const nodeEls = new Map();
  for (const n of nodePos.values()) {
    const infoVar = varsMap[n.var];
    const cols = coloresEstadoVar(infoVar, grupo.color);
    const g = crearSvgEl("g", {
      class: "flow-svg-node",
      style: "cursor: pointer;",
    });

    const rect = crearSvgEl("rect", {
      x: n.x,
      y: n.y,
      width: n.w,
      height: n.h,
      rx: 8,
      fill: cols.fill,
      stroke: cols.stroke,
      "stroke-width": n.es_compartida ? "2" : "1.7",
      "stroke-dasharray": n.es_compartida ? "5 3" : null,
    });
    g.appendChild(rect);

    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: n.x + 12,
          y: n.y + 21,
          fill: cols.badge,
          "font-size": "13.5",
          "font-weight": "700",
          "font-family": "var(--font-mono), monospace",
        },
        n.var
      )
    );

    const valStr = infoVar?.valor_vista_ing || infoVar?.valor_ing || "";
    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: n.x + n.w - 11,
          y: n.y + 21,
          "text-anchor": "end",
          fill: "#cbd5e1",
          "font-size": "11",
          "font-family": "var(--font-mono), monospace",
        },
        truncarTexto(valStr, 19)
      )
    );

    const lineas = envolverTexto(n.etiqueta, 26, 2);
    lineas.forEach((ln, idx) => {
      g.appendChild(
        crearSvgEl(
          "text",
          {
            x: n.x + 12,
            y: n.y + 40 + idx * 13,
            fill: "#e2e8f0",
            "font-size": "11.5",
          },
          ln
        )
      );
    });

    if (n.es_compartida) {
      g.appendChild(
        crearSvgEl(
          "text",
          {
            x: n.x + n.w - 10,
            y: n.y + n.h - 7,
            "text-anchor": "end",
            fill: "#38bdf8",
            "font-size": "9.8",
            "font-weight": "700",
          },
          `⇄ ${n.categorias_codigo_str}`
        )
      );
    }

    const tip = document.createElementNS(SVG_NS, "title");
    tip.textContent = `${n.eq}\nVariable salida típica: ${n.var} = ${valStr}\nClic: localizar ecuación e inspeccionar '${n.var}'`;
    g.appendChild(tip);

    g.addEventListener("mouseenter", () => {
      for (const ref of edgeRefs) {
        const activa = ref.vars.includes(n.var);
        ref.pathEl.setAttribute("opacity", activa ? "1" : "0.14");
        if (activa) {
          ref.pathEl.setAttribute("stroke", "#fde047");
          ref.pathEl.setAttribute("stroke-width", "2.6");
          ref.pathEl.setAttribute("marker-end", "url(#arrow-hi)");
        }
        if (ref.labelEl) {
          ref.labelEl.setAttribute("opacity", activa ? "1" : "0.18");
        }
      }
      for (const [k, otherRect] of nodeEls.entries()) {
        otherRect.setAttribute("opacity", k === n.var ? "1" : "0.52");
      }
      rect.setAttribute("opacity", "1");
    });

    g.addEventListener("mouseleave", () => {
      for (const ref of edgeRefs) {
        ref.pathEl.setAttribute("opacity", ref.isExt ? "0.75" : "0.80");
        ref.pathEl.setAttribute("stroke", ref.baseColor);
        ref.pathEl.setAttribute("stroke-width", ref.baseWidth);
        ref.pathEl.setAttribute("marker-end", ref.baseMarker);
        if (ref.labelEl) {
          ref.labelEl.setAttribute("opacity", "1");
        }
      }
      for (const otherRect of nodeEls.values()) {
        otherRect.setAttribute("opacity", "1");
      }
    });

    g.addEventListener("click", () => {
      if (alClickEcuacion) alClickEcuacion(n.eq);
      if (alClickVariable) alClickVariable(n.var);
    });

    nodeEls.set(n.var, rect);
    nodesLayer.appendChild(g);
  }

  diagramWrap.appendChild(svg);
  section.appendChild(diagramWrap);

  // Leyenda visual debajo del diagrama
  const legend = document.createElement("div");
  legend.className = "flow-legend";
  legend.innerHTML = `
    <span class="flow-legend-item"><span class="flow-legend-box flow-box-fixed"></span> Variable fijada</span>
    <span class="flow-legend-item"><span class="flow-legend-box flow-box-calc"></span> Variable calculada</span>
    <span class="flow-legend-item"><span class="flow-legend-box flow-box-shared"></span> Ecuación compartida (varias categorías)</span>
    <span class="flow-legend-item"><span class="flow-legend-line flow-line-direct"></span> Flujo directo</span>
    <span class="flow-legend-item"><span class="flow-legend-line flow-line-loop"></span> Lazo acoplado / iteración</span>
  `;
  section.appendChild(legend);

  // Tarjetas de detalle Entradas y Salidas debajo del diagrama
  const ioGrid = document.createElement("div");
  ioGrid.className = "flow-relations-grid";

  const colEnt = document.createElement("div");
  colEnt.className = "flow-rel-col";
  colEnt.innerHTML = `<h4 class="flow-rel-col-title">← Entradas desde otras categorías (${entradas.length})</h4>`;
  if (entradas.length === 0) {
    colEnt.innerHTML += `<div class="flow-rel-empty">Categoría raíz: toma únicamente parámetros independientes configurados en variables.</div>`;
  } else {
    entradas.forEach((con) => colEnt.appendChild(crearTarjetaConexion(con, "desde", alClickCategoria, alClickVariable)));
  }

  const colSal = document.createElement("div");
  colSal.className = "flow-rel-col";
  colSal.innerHTML = `<h4 class="flow-rel-col-title">→ Salidas hacia otras categorías (${salidas.length})</h4>`;
  if (salidas.length === 0) {
    colSal.innerHTML += `<div class="flow-rel-empty">Categoría terminal del flujo.</div>`;
  } else {
    salidas.forEach((con) => colSal.appendChild(crearTarjetaConexion(con, "hacia", alClickCategoria, alClickVariable)));
  }

  ioGrid.appendChild(colEnt);
  ioGrid.appendChild(colSal);
  section.appendChild(ioGrid);

  // Conservar las tarjetas de ecuaciones arriba: solo reemplazar el bloque de flujo si existía
  contenedor.querySelector("#cat-flow-section")?.remove();
  contenedor.appendChild(section);
}

function crearTarjetaConexion(con, direccion, alClickCategoria, alClickVariable) {
  const card = document.createElement("div");
  card.className = `flow-rel-card ${con.es_lazo ? "flow-rel-loop" : ""}`;
  card.style.setProperty("--grp-color", con.color || "#38bdf8");
  card.innerHTML = `
    <div class="flow-rel-card-top">
      <button type="button" class="flow-rel-cat-btn" style="--grp-color: ${con.color || "#38bdf8"};">
        <span class="flow-rel-arrow">${direccion === "desde" ? "←" : "→"}</span>
        <span class="flow-rel-code">${escaparHtml(con.categoria_codigo)}</span>
        <span>${escaparHtml(con.categoria_corto)}</span>
      </button>
      ${con.es_lazo ? '<span class="flow-loop-badge">↺ Lazo acoplado</span>' : ""}
    </div>
    <div class="flow-rel-vars">
      <span class="flow-rel-vars-label">Variables:</span>
      ${(con.variables || []).map((v) => `<button type="button" class="flow-var-chip" data-var="${escaparHtml(v)}">${escaparHtml(v)}</button>`).join("")}
    </div>
    <p class="flow-rel-desc">${escaparHtml(con.explicacion)}</p>
  `;
  card.querySelector(".flow-rel-cat-btn")?.addEventListener("click", () => {
    if (alClickCategoria) alClickCategoria(con.categoria_id);
  });
  card.querySelectorAll(".flow-var-chip").forEach((chip) => {
    chip.addEventListener("click", () => {
      if (alClickVariable) alClickVariable(chip.dataset.var);
    });
  });
  return card;
}

/**
 * Renderiza la vista completa "Mapa de Flujo Global (C1 -> C13)" con trazado ortogonal en pasillos vacíos.
 */
export function renderizarMapaFlujoGlobal(contenedorHeader, contenedorBody, estadoApp, callbacks = {}) {
  const { alClickCategoria } = callbacks;
  const sistema = estadoApp?.sistema || estadoApp;
  const mapa = sistema?.mapa_flujo || sistema?.mapa_flujo_global;
  const cats = sistema?.categorias || [];
  if (!mapa) return;

  if (contenedorHeader) {
    contenedorHeader.innerHTML = `
      <div class="cat-banner-title">◈ Mapa de Flujo Global del Dirigible (C1 → C13)</div>
      <div class="cat-banner-stats">${cats.length} categorías en 4 bloques temáticos — trazado limpio sin cruce por nodos</div>
    `;
  }

  const nodos = mapa.nodos || [];
  const aristas = mapa.aristas || [];
  const grupos = mapa.grupos || [];

  const root = document.createElement("div");
  root.className = "flow-global-root";

  const inspector = document.createElement("div");
  inspector.className = "flow-global-inspector";
  const textoBaseInspector = `<span class="flow-inspector-hint">Pasa el cursor sobre cualquier bloque C1–C13 para resaltar sus conexiones de entrada y salida; haz clic para abrir su categoría.</span>`;
  inspector.innerHTML = textoBaseInspector;
  root.appendChild(inspector);

  const diagCard = document.createElement("div");
  diagCard.className = "flow-svg-wrapper flow-global-svg-wrapper";

  const svgW = 1380;
  const svgH = 740;
  const svg = crearSvgEl("svg", {
    viewBox: `0 0 ${svgW} ${svgH}`,
    class: "flow-svg",
    role: "img",
    "aria-label": "Mapa de flujo global de categorías C1 a C13",
  });
  svg.style.minWidth = "1080px";
  svg.style.margin = "0 auto";

  const defs = crearSvgEl("defs");
  agregarMarcadores(defs);
  svg.appendChild(defs);

  const leftCols = 204;
  const boxW = 170;
  const boxH = 84;
  const gapCol = 66;
  const bandH = 122;
  const bandYs = [24, 200, 376, 552];
  const rowBoxOffset = 19;

  const corridorYs = [
    12,
    bandYs[0] + rowBoxOffset + boxH + (bandYs[1] + rowBoxOffset - (bandYs[0] + rowBoxOffset + boxH)) / 2,
    bandYs[1] + rowBoxOffset + boxH + (bandYs[2] + rowBoxOffset - (bandYs[1] + rowBoxOffset + boxH)) / 2,
    bandYs[2] + rowBoxOffset + boxH + (bandYs[3] + rowBoxOffset - (bandYs[2] + rowBoxOffset + boxH)) / 2,
    bandYs[3] + rowBoxOffset + boxH + 42,
  ];

  const colX = (c) => leftCols + c * (boxW + gapCol);
  const gutterXs = [
    leftCols - 22,
    colX(0) + boxW + gapCol / 2,
    colX(1) + boxW + gapCol / 2,
    colX(2) + boxW + gapCol / 2,
    colX(3) + boxW + gapCol / 2,
    colX(4) + boxW + 20,
  ];

  const bandsLayer = crearSvgEl("g");
  grupos.forEach((g, idx) => {
    const y = bandYs[idx];
    const h = idx === 3 ? bandH + 56 : bandH;
    bandsLayer.appendChild(
      crearSvgEl("rect", {
        x: 12,
        y,
        width: svgW - 24,
        height: h,
        rx: 12,
        fill: `${g.color}0a`,
        stroke: `${g.color}33`,
        "stroke-width": "1.2",
      })
    );
    bandsLayer.appendChild(
      crearSvgEl("rect", {
        x: 12,
        y,
        width: 7,
        height: bandH,
        rx: 3.5,
        fill: g.color,
      })
    );
    const labelLineas = envolverTexto(g.nombre, 20, 3);
    labelLineas.forEach((ln, li) => {
      bandsLayer.appendChild(
        crearSvgEl(
          "text",
          {
            x: 30,
            y: y + 48 + li * 16,
            fill: g.color,
            "font-size": "12",
            "font-weight": "700",
          },
          ln
        )
      );
    });
  });

  bandsLayer.appendChild(
    crearSvgEl("rect", {
      x: leftCols - 10,
      y: bandYs[3] + 10,
      width: 5 * boxW + 4 * gapCol + 20,
      height: 158,
      rx: 10,
      fill: "none",
      stroke: "#fb923c66",
      "stroke-dasharray": "6 5",
      "stroke-width": "1.4",
    })
  );
  svg.appendChild(bandsLayer);

  const posGlobalMap = new Map();
  const occupiedCells = new Set();
  for (const n of nodos) {
    const fila = n.pos_global?.fila ?? 0;
    const col = n.pos_global?.col ?? 0;
    occupiedCells.add(`${fila}:${col}`);
    const x = colX(col);
    const y = bandYs[fila] + rowBoxOffset;
    posGlobalMap.set(n.id, { ...n, fila, col, x, y, w: boxW, h: boxH });
  }

  function columnaDespejadaEntre(filaA, filaB, col) {
    const fMin = Math.min(filaA, filaB);
    const fMax = Math.max(filaA, filaB);
    for (let f = fMin + 1; f < fMax; f++) {
      if (occupiedCells.has(`${f}:${col}`)) return false;
    }
    return true;
  }

  const cajasNodosGlobal = Array.from(posGlobalMap.values()).map((n) => ({
    x1: n.x,
    y1: n.y,
    x2: n.x + n.w,
    y2: n.y + n.h,
  }));
  const cajasLabelsGlobal = [];

  const edgesLayer = crearSvgEl("g");
  const nodesLayer = crearSvgEl("g");
  const labelsLayer = crearSvgEl("g");
  svg.appendChild(edgesLayer);
  svg.appendChild(nodesLayer);
  svg.appendChild(labelsLayer);

  const globalEdges = [];

  const corridorUsed = new Map();
  const gutterUsed = new Map();
  function offsetCorridorY(cIdx) {
    const k = corridorUsed.get(cIdx) || 0;
    corridorUsed.set(cIdx, k + 1);
    const seq = [0, -10, 10, -20, 20, -30, 30];
    return corridorYs[cIdx] + (seq[k % seq.length] ?? 0);
  }
  function offsetGutterX(gIdx) {
    const k = gutterUsed.get(gIdx) || 0;
    gutterUsed.set(gIdx, k + 1);
    const seq = [0, -8, 8, -14];
    return gutterXs[gIdx] + (seq[k % seq.length] ?? 0);
  }

  aristas.forEach((ar, idx) => {
    const o = posGlobalMap.get(ar.origen_id);
    const d = posGlobalMap.get(ar.destino_id);
    if (!o || !d) return;

    const esLazo = Boolean(ar.es_lazo);
    const strokeCol = esLazo ? "#fb923c" : o.color || "#38bdf8";
    const markerMap = {
      "#38bdf8": "url(#arrow-cat-cyan)",
      "#fb923c": "url(#arrow-cat-orange)",
      "#a78bfa": "url(#arrow-cat-purple)",
      "#4ade80": "url(#arrow-cat-green)",
    };
    const marker = esLazo ? "url(#arrow-loop)" : markerMap[strokeCol] || "url(#arrow-normal)";

    let puntos = [];
    let candidatosLabel = [];
    const etiquetaVars =
      (ar.variables || []).length > 2
        ? `${ar.variables.slice(0, 2).join(",")}…`
        : (ar.variables || []).join(",");

    const srcOffset = ((idx % 5) - 2) * 14;
    const dstOffset = (((idx + 2) % 5) - 2) * 14;

    if (esLazo) {
      const yTrack = bandYs[3] + 148;
      const x1 = o.x + o.w * 0.5;
      const y1 = o.y + o.h;
      const x2 = d.x + d.w * 0.5;
      const y2 = d.y + d.h;
      puntos = [
        { x: x1, y: y1 },
        { x: x1, y: yTrack },
        { x: x2, y: yTrack },
        { x: x2, y: y2 + 4 },
      ];
      candidatosLabel = [{ x: (x1 + x2) / 2, y: yTrack }];
    } else if (o.fila === d.fila && d.col - o.col === 1) {
      const x1 = o.x + o.w;
      const y1 = o.y + o.h / 2;
      const x2 = d.x;
      const y2 = d.y + d.h / 2;
      puntos = [
        { x: x1, y: y1 },
        { x: x2 - 4, y: y2 },
      ];
      candidatosLabel = [
        { x: (x1 + x2) / 2, y: y1 - 15 },
        { x: (x1 + x2) / 2, y: y1 + 15 },
      ];
    } else if (o.fila === d.fila) {
      const irPorArriba = o.fila === 3;
      const cIdx = irPorArriba ? 3 : o.fila + 1;
      const yBus = offsetCorridorY(cIdx);
      const x1 = o.x + o.w / 2 + srcOffset;
      const y1 = irPorArriba ? o.y : o.y + o.h;
      const x2 = d.x + d.w / 2 + dstOffset;
      const y2 = irPorArriba ? d.y - 4 : d.y + d.h + 4;
      puntos = [
        { x: x1, y: y1 },
        { x: x1, y: yBus },
        { x: x2, y: yBus },
        { x: x2, y: y2 },
      ];
      candidatosLabel = [{ x: (x1 + x2) / 2, y: yBus }];
    } else if (o.col === d.col && columnaDespejadaEntre(o.fila, d.fila, o.col)) {
      const dirDown = d.fila > o.fila;
      const xVert = o.x + o.w * 0.5 + srcOffset * 0.6;
      const y1 = dirDown ? o.y + o.h : o.y;
      const y2 = dirDown ? d.y - 4 : d.y + d.h + 4;
      puntos = [
        { x: xVert, y: y1 },
        { x: xVert, y: y2 },
      ];
      candidatosLabel = [{ x: xVert, y: (y1 + y2) / 2 }];
    } else if (Math.abs(d.fila - o.fila) === 1) {
      const dirDown = d.fila > o.fila;
      const corrIdx = dirDown ? d.fila : o.fila;
      const yBus = offsetCorridorY(corrIdx);
      const x1 = o.x + o.w / 2 + srcOffset;
      const y1 = dirDown ? o.y + o.h : o.y;
      const x2 = d.x + d.w / 2 + dstOffset;
      const y2 = dirDown ? d.y - 4 : d.y + d.h + 4;
      puntos = [
        { x: x1, y: y1 },
        { x: x1, y: yBus },
        { x: x2, y: yBus },
        { x: x2, y: y2 },
      ];
      candidatosLabel = [
        { x: (x1 + x2) / 2, y: yBus },
        { x: x1, y: (y1 + yBus) / 2 },
        { x: x2, y: (yBus + y2) / 2 },
      ];
    } else {
      const dirDown = d.fila > o.fila;
      const corrExitIdx = dirDown ? o.fila + 1 : o.fila;
      const corrEnterIdx = dirDown ? d.fila : o.fila - 1;
      const yBusExit = offsetCorridorY(corrExitIdx);
      const yBusEnter = offsetCorridorY(corrEnterIdx);

      let gutterChoice = o.col <= d.col ? Math.min(5, o.col + 1) : o.col;
      if (o.col === 0 && d.col === 0) {
        gutterChoice = 0;
      }
      const xGutter = offsetGutterX(gutterChoice);

      const x1 = o.x + o.w / 2 + srcOffset * 0.5;
      const y1 = dirDown ? o.y + o.h : o.y;
      const x2 = d.x + d.w / 2 + dstOffset * 0.5;
      const y2 = dirDown ? d.y - 4 : d.y + d.h + 4;

      if (gutterChoice === 0 && o.col === 0) {
        const yLeft = o.y + o.h * 0.65;
        puntos = [
          { x: o.x, y: yLeft },
          { x: xGutter, y: yLeft },
          { x: xGutter, y: yBusEnter },
          { x: x2, y: yBusEnter },
          { x: x2, y: y2 },
        ];
        candidatosLabel = [
          { x: xGutter, y: (yLeft + yBusEnter) / 2 },
          { x: (xGutter + x2) / 2, y: yBusEnter },
        ];
      } else {
        puntos = [
          { x: x1, y: y1 },
          { x: x1, y: yBusExit },
          { x: xGutter, y: yBusExit },
          { x: xGutter, y: yBusEnter },
          { x: x2, y: yBusEnter },
          { x: x2, y: y2 },
        ];
        candidatosLabel = [
          { x: xGutter, y: (yBusExit + yBusEnter) / 2 },
          { x: (xGutter + x2) / 2, y: yBusEnter },
        ];
      }
    }

    const path = crearSvgEl("path", {
      d: trazarRutaOrtogonal(puntos, 10),
      fill: "none",
      stroke: strokeCol,
      "stroke-width": esLazo ? "2.4" : "1.9",
      "stroke-dasharray": esLazo ? "7 5" : null,
      "marker-end": marker,
      opacity: "0.72",
    });
    edgesLayer.appendChild(path);

    let labelEl = null;
    if (etiquetaVars) {
      const txtLabel = esLazo ? `↺ ${etiquetaVars}` : etiquetaVars;
      const posLbl = ubicarEtiquetaSinColision(
        candidatosLabel,
        txtLabel,
        cajasNodosGlobal,
        cajasLabelsGlobal,
        leftCols - 28,
        svgW - 18
      );
      labelEl = crearEtiquetaPildora(
        posLbl.x,
        posLbl.y,
        txtLabel,
        esLazo ? "#fdba74" : "#cbd5e1",
        esLazo ? "rgba(251, 146, 60, 0.45)" : `${strokeCol}55`
      );
      labelsLayer.appendChild(labelEl);
    }

    globalEdges.push({
      pathEl: path,
      labelEl,
      origen_id: ar.origen_id,
      destino_id: ar.destino_id,
      baseStroke: strokeCol,
      baseWidth: esLazo ? "2.4" : "1.9",
    });
  });

  const globalBoxMap = new Map();
  nodos.forEach((n) => {
    const pos = posGlobalMap.get(n.id);
    if (!pos) return;
    const g = crearSvgEl("g", {
      class: "flow-global-node",
      style: "cursor: pointer;",
    });

    const rect = crearSvgEl("rect", {
      x: pos.x,
      y: pos.y,
      width: pos.w,
      height: pos.h,
      rx: 9,
      fill: "#0f172a",
      stroke: n.color,
      "stroke-width": "1.9",
    });
    g.appendChild(rect);

    g.appendChild(
      crearSvgEl("rect", {
        x: pos.x + 1,
        y: pos.y + 1,
        width: pos.w - 2,
        height: 22,
        rx: 8,
        fill: `${n.color}22`,
      })
    );
    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: pos.x + 10,
          y: pos.y + 16,
          fill: n.color,
          "font-size": "11.5",
          "font-weight": "700",
          "font-family": "var(--font-mono), monospace",
        },
        n.codigo
      )
    );
    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: pos.x + pos.w - 10,
          y: pos.y + 16,
          "text-anchor": "end",
          fill: "#94a3b8",
          "font-size": "9.5",
          "font-family": "var(--font-mono), monospace",
        },
        `${n.num_ecuaciones} ec.`
      )
    );

    const lineas = envolverTexto(n.titulo_corto, 22, 2);
    lineas.forEach((ln, li) => {
      g.appendChild(
        crearSvgEl(
          "text",
          {
            x: pos.x + 10,
            y: pos.y + 40 + li * 14,
            fill: "#f1f5f9",
            "font-size": "11.2",
            "font-weight": "600",
          },
          ln
        )
      );
    });

    g.appendChild(
      crearSvgEl(
        "text",
        {
          x: pos.x + 10,
          y: pos.y + pos.h - 10,
          fill: "#64748b",
          "font-size": "9.3",
          "font-family": "var(--font-mono), monospace",
        },
        truncarTexto((n.variables_clave || []).slice(0, 4).join(" · "), 25)
      )
    );

    const tip = document.createElementNS(SVG_NS, "title");
    tip.textContent = `${n.codigo}. ${n.nombre}\n${n.resumen}\nEntradas: ${n.entradas_codigos.join(", ") || "Raíz"}\nSalidas: ${n.salidas_codigos.join(", ") || "Terminal"}`;
    g.appendChild(tip);

    g.addEventListener("mouseenter", () => {
      const relacionados = new Set([n.id]);
      for (const ge of globalEdges) {
        const hit = ge.origen_id === n.id || ge.destino_id === n.id;
        if (hit) {
          relacionados.add(ge.origen_id);
          relacionados.add(ge.destino_id);
        }
        ge.pathEl.setAttribute("opacity", hit ? "1" : "0.14");
        ge.pathEl.setAttribute("stroke-width", hit ? "2.8" : ge.baseWidth);
        if (ge.labelEl) {
          ge.labelEl.setAttribute("opacity", hit ? "1" : "0.18");
        }
      }
      for (const [id, r] of globalBoxMap.entries()) {
        r.setAttribute("opacity", relacionados.has(id) ? "1" : "0.38");
      }
      inspector.innerHTML = `
        <strong style="color: ${n.color};">${escaparHtml(n.codigo)}. ${escaparHtml(n.nombre)}</strong>
        <span class="flow-inspector-meta">(${n.num_ecuaciones} eq., ${n.num_compartidas} compartidas)</span>
        <span class="flow-inspector-io">← Entradas: <strong>${escaparHtml(n.entradas_codigos.join(", ") || "Raíz")}</strong> · Salidas → <strong>${escaparHtml(n.salidas_codigos.join(", ") || "Terminal")}</strong></span>
        <span class="flow-inspector-summary">${escaparHtml(n.resumen)}</span>
      `;
    });

    g.addEventListener("mouseleave", () => {
      for (const ge of globalEdges) {
        ge.pathEl.setAttribute("opacity", "0.72");
        ge.pathEl.setAttribute("stroke-width", ge.baseWidth);
        if (ge.labelEl) {
          ge.labelEl.setAttribute("opacity", "1");
        }
      }
      for (const r of globalBoxMap.values()) {
        r.setAttribute("opacity", "1");
      }
      inspector.innerHTML = textoBaseInspector;
    });

    g.addEventListener("click", () => {
      if (alClickCategoria) alClickCategoria(n.id);
    });

    globalBoxMap.set(n.id, rect);
    nodesLayer.appendChild(g);
  });

  diagCard.appendChild(svg);
  root.appendChild(diagCard);

  const headingChains = document.createElement("h3");
  headingChains.className = "flow-section-heading";
  headingChains.textContent = "Resumen de cadenas físicas acopladas";
  root.appendChild(headingChains);

  const cardsGrid = document.createElement("div");
  cardsGrid.className = "flow-chains-grid";
  cardsGrid.innerHTML = `
    <div class="flow-chain-card" style="--grp-color: #38bdf8;">
      <div class="flow-chain-title">1. Cadena Aerostática (C1 → C2 → C3)</div>
      <p class="flow-chain-desc"><strong>ρ₁, ρ₂, ΔT y mflot</strong> definen el empuje <strong>F</strong> y el volumen <strong>V</strong> (C1–C2). Con la esbeltez <strong>λ = L/D</strong> se fijan <strong>R, L, cf, cr</strong> y se calculan las áreas semielipsoidales <strong>Sf, Sr, S</strong> más la película aislante <strong>Sc</strong> y su masa <strong>mc</strong> (C3).</p>
    </div>
    <div class="flow-chain-card" style="--grp-color: #fb923c;">
      <div class="flow-chain-title">2. Cadena Térmica (C4 → C5 → C6 → C7)</div>
      <p class="flow-chain-desc">Usando <strong>L, D, S, m</strong> y el Reynolds de viento <strong>ReL</strong> (C8), se resuelven los lazos de convección interna y externa en casco base <strong>U0</strong> (C4) y con cavidad aislante <strong>U</strong> (C5). De ahí salen las pérdidas <strong>Qp0, Qp</strong>, el ahorro <strong>fais</strong>, el enfriamiento <strong>vT, tc</strong> (C6) y la energía/masa de GLP <strong>Eprop, mgm</strong> (C7).</p>
    </div>
    <div class="flow-chain-card" style="--grp-color: #a78bfa;">
      <div class="flow-chain-title">3. Cadena Aerodinámica (C8)</div>
      <p class="flow-chain-desc">La velocidad aerodinámica <strong>v = vg + vv</strong> (con viento en contra) determina simultáneamente el tiempo de misión <strong>tm = dm/vg</strong> y el arrastre de Hoerner <strong>ReL → Cf → CDVc → CDV → FD</strong> y el trabajo mecánico resistente <strong>ED</strong>.</p>
    </div>
    <div class="flow-chain-card" style="--grp-color: #4ade80;">
      <div class="flow-chain-title">4. Cadena Propulsiva y Lazo de Batería (C9 ↔ C10 ↔ C11 ↔ C12 ↔ C13)</div>
      <p class="flow-chain-desc"><strong>mart = mc + mmot + mbat + …</strong> fija <strong>mtot, map y mres = mtot − mflot</strong> (C9). Eso define el empuje vectorial <strong>Ttot = √(FL² + FX²)</strong> (C10), la potencia motriz <strong>Pelec</strong> (C11), la potencia total a bordo <strong>Ptot = Pelec + Pad</strong> y energía <strong>Ereq</strong> (C12), y la batería exacta <strong>mbat = max(mbe, mbp)</strong> (C13) que vuelve a pesar en <strong>mart</strong> (C9).</p>
    </div>
  `;
  root.appendChild(cardsGrid);

  const indexTitle = document.createElement("h3");
  indexTitle.className = "flow-section-heading";
  indexTitle.textContent = "Índice completo de categorías (clic para abrir ecuaciones y flujo interno)";
  root.appendChild(indexTitle);

  const indexGrid = document.createElement("div");
  indexGrid.className = "flow-cat-index-grid";
  nodos.forEach((n) => {
    const item = document.createElement("div");
    item.className = "flow-cat-index-card";
    item.style.setProperty("--grp-color", n.color);
    item.style.cursor = "pointer";
    item.innerHTML = `
      <div class="flow-cat-index-top">
        <div>
          <span class="flow-cat-index-code">${escaparHtml(n.codigo)}</span>
          <strong class="flow-cat-index-name">${escaparHtml(n.nombre)}</strong>
        </div>
        <span class="flow-cat-index-counts">${n.num_ecuaciones} eq. (${n.num_compartidas} compart.)</span>
      </div>
      <p class="flow-cat-index-summary">${escaparHtml(n.resumen)}</p>
      <div class="flow-cat-index-links">
        <span>← Entradas: <strong>${escaparHtml(n.entradas_codigos.join(", ") || "Raíz")}</strong></span>
        <span>Salidas → <strong>${escaparHtml(n.salidas_codigos.join(", ") || "Terminal")}</strong></span>
      </div>
    `;
    item.addEventListener("click", () => {
      if (alClickCategoria) alClickCategoria(n.id);
    });
    indexGrid.appendChild(item);
  });
  root.appendChild(indexGrid);

  contenedorBody.innerHTML = "";
  contenedorBody.appendChild(root);
}
