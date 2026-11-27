/**
 * charts.js — Componente del panel central para la vista de Gráficas Comparativas.
 *
 * Renderiza gráficas vectoriales interactivas (SVG de alta precisión con doble eje Y,
 * cursor interactivo con lectura en vivo, marcadores del punto de operación actual ★,
 * barras comparativas y silueta geométrica a escala L × D del dirigible).
 */

const SVG_NS = "http://www.w3.org/2000/svg";

function crearSvgEl(tag, attrs = {}) {
  const el = document.createElementNS(SVG_NS, tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (v !== undefined && v !== null) {
      el.setAttribute(k, String(v));
    }
  }
  return el;
}

function claseColorVariable(color) {
  if (color === "red") return "text-penalized";
  if (color === "yellow") return "text-fixed";
  return "text-calc";
}

function formatearNumero(val) {
  if (val === undefined || val === null || Number.isNaN(val)) return "—";
  const abs = Math.abs(val);
  if (abs >= 1000) return val.toFixed(1);
  if (abs >= 100) return val.toFixed(2);
  if (abs >= 10) return val.toFixed(2);
  if (abs >= 1) return val.toFixed(3);
  return val.toFixed(4);
}

/**
 * Renderiza un panel de curvas paramétricas con doble eje Y (y1 izquierdo, y2 derecho),
 * línea vertical en el punto de operación actual y cursor interactivo.
 */
function crearPanelLineasDobleEje(panel) {
  const card = document.createElement("div");
  card.className = "chart-subpanel-card";

  const titleBar = document.createElement("div");
  titleBar.className = "chart-subpanel-header";
  titleBar.innerHTML = `<h4 class="chart-subpanel-title">${panel.titulo}</h4>`;

  let escalaUnica = Boolean(panel.escala_unica_inicial);
  const axisTags = [];

  if (panel.permitir_escala_unica) {
    const scaleBtn = document.createElement("button");
    scaleBtn.type = "button";
    scaleBtn.className = `chart-scale-toggle-btn ${escalaUnica ? "active" : ""}`;
    const actualizarTextoEscala = () => {
      scaleBtn.textContent = escalaUnica
        ? "⇄ Escala detallada (Izq./Der.)"
        : "⇄ Misma escala (comparar magnitudes)";
      scaleBtn.title = escalaUnica
        ? "Volver a ejes separados (Izq./Der.) para ver mejor la forma de las curvas menores"
        : "Mostrar todas las energías en un único eje Y desde 0 kJ para comparar magnitudes reales";
      axisTags.forEach((tag) => tag.classList.toggle("hidden", escalaUnica));
    };
    actualizarTextoEscala();
    scaleBtn.addEventListener("click", () => {
      escalaUnica = !escalaUnica;
      scaleBtn.classList.toggle("active", escalaUnica);
      actualizarTextoEscala();
      dibujarSvg();
    });
    titleBar.appendChild(scaleBtn);
  }

  card.appendChild(titleBar);

  // Leyenda interactiva + barra de lectura en vivo al pasar el ratón
  const legendBar = document.createElement("div");
  legendBar.className = "chart-legend-bar";

  const seriesVisibles = panel.series.map(() => true);

  const svgWrapper = document.createElement("div");
  svgWrapper.className = "chart-svg-wrapper";

  const readoutBar = document.createElement("div");
  readoutBar.className = "chart-readout-bar";
  readoutBar.textContent = "Pasa el cursor sobre la gráfica para inspeccionar valores exactos en cada punto.";

  function dibujarSvg() {
    svgWrapper.innerHTML = "";

    const seriesY1 = escalaUnica
      ? panel.series.filter((_, idx) => seriesVisibles[idx])
      : panel.series.filter((s, idx) => s.eje === "y1" && seriesVisibles[idx]);
    const seriesY2 = escalaUnica
      ? []
      : panel.series.filter((s, idx) => s.eje === "y2" && seriesVisibles[idx]);

    const W = 820;
    const H = 370;
    const padL = 68;
    const padR = !escalaUnica && seriesY2.length > 0 ? 68 : 28;
    const padT = 26;
    const padB = 50;
    const plotW = W - padL - padR;
    const plotH = H - padT - padB;

    const svg = crearSvgEl("svg", {
      viewBox: `0 0 ${W} ${H}`,
      class: "chart-svg",
      preserveAspectRatio: "xMidYMid meet",
    });

    const xs = panel.xs || [];
    if (xs.length < 2) {
      svgWrapper.appendChild(svg);
      return;
    }

    const xMin = Math.min(...xs);
    const xMax = Math.max(...xs);
    const xSpan = Math.max(1e-9, xMax - xMin);
    const toX = (x) => padL + ((x - xMin) / xSpan) * plotW;

    const esValidoNum = (v) => typeof v === "number" && Number.isFinite(v);

    function rangoEje(listaSeries, forzarCero = false) {
      if (!listaSeries.length) return [0, 1];
      let minV = Infinity;
      let maxV = -Infinity;
      for (const s of listaSeries) {
        for (const v of s.valores) {
          if (esValidoNum(v)) {
            if (v < minV) minV = v;
            if (v > maxV) maxV = v;
          }
        }
      }
      if (!Number.isFinite(minV) || !Number.isFinite(maxV)) return [0, 1];
      if (forzarCero && minV > 0) {
        minV = 0;
      }
      if (Math.abs(maxV - minV) < 1e-9) {
        const delta = Math.max(1, Math.abs(maxV) * 0.1);
        return [minV - delta, maxV + delta];
      }
      const pad = (maxV - minV) * 0.08;
      return [forzarCero && minV === 0 ? 0 : minV - pad * 0.5, maxV + pad];
    }

    const [y1Min, y1Max] = rangoEje(seriesY1, escalaUnica);
    const [y2Min, y2Max] = rangoEje(seriesY2, false);

    const toY1 = (v) => padT + plotH - ((v - y1Min) / Math.max(1e-9, y1Max - y1Min)) * plotH;
    const toY2 = (v) => padT + plotH - ((v - y2Min) / Math.max(1e-9, y2Max - y2Min)) * plotH;

    // Fondo del área de trazado
    svg.appendChild(
      crearSvgEl("rect", {
        x: padL,
        y: padT,
        width: plotW,
        height: plotH,
        fill: "#0b1120",
        stroke: "#1e293b",
        "stroke-width": 1,
        rx: 4,
      })
    );

    // Cuadrícula horizontal y etiquetas de ejes Y1 / Y2
    const numTicksY = 5;
    for (let i = 0; i <= numTicksY; i++) {
      const frac = i / numTicksY;
      const yPos = padT + plotH - frac * plotH;

      svg.appendChild(
        crearSvgEl("line", {
          x1: padL,
          y1: yPos,
          x2: padL + plotW,
          y2: yPos,
          stroke: "#1e293b",
          "stroke-dasharray": i === 0 ? "" : "3,3",
          "stroke-width": 1,
        })
      );

      if (seriesY1.length > 0) {
        const val1 = y1Min + frac * (y1Max - y1Min);
        const txt1 = crearSvgEl("text", {
          x: padL - 8,
          y: yPos + 4,
          "text-anchor": "end",
          fill: escalaUnica ? "#cbd5e1" : seriesY1[0].color || "#cbd5e1",
          "font-size": "11",
          "font-family": "monospace",
        });
        txt1.textContent = formatearNumero(val1);
        svg.appendChild(txt1);
      }

      if (seriesY2.length > 0) {
        const val2 = y2Min + frac * (y2Max - y2Min);
        const txt2 = crearSvgEl("text", {
          x: padL + plotW + 8,
          y: yPos + 4,
          "text-anchor": "start",
          fill: seriesY2[0].color || "#cbd5e1",
          "font-size": "11",
          "font-family": "monospace",
        });
        txt2.textContent = formatearNumero(val2);
        svg.appendChild(txt2);
      }
    }

    // Cuadrícula vertical y etiquetas de eje X
    const numTicksX = 6;
    for (let i = 0; i <= numTicksX; i++) {
      const frac = i / numTicksX;
      const xVal = xMin + frac * xSpan;
      const xPos = padL + frac * plotW;

      svg.appendChild(
        crearSvgEl("line", {
          x1: xPos,
          y1: padT,
          x2: xPos,
          y2: padT + plotH,
          stroke: "#1e293b",
          "stroke-dasharray": "3,3",
          "stroke-width": 1,
        })
      );

      const txtX = crearSvgEl("text", {
        x: xPos,
        y: padT + plotH + 18,
        "text-anchor": "middle",
        fill: "#94a3b8",
        "font-size": "11",
        "font-family": "monospace",
      });
      txtX.textContent = formatearNumero(xVal);
      svg.appendChild(txtX);
    }

    // Títulos de ejes
    const lblX = crearSvgEl("text", {
      x: padL + plotW / 2,
      y: H - 8,
      "text-anchor": "middle",
      fill: "#e2e8f0",
      "font-size": "12",
      "font-weight": "600",
    });
    lblX.textContent = panel.x_label || "";
    svg.appendChild(lblX);

    const y1Titulo = escalaUnica && panel.y_unica_label ? panel.y_unica_label : panel.y1_label;
    if (y1Titulo) {
      const lblY1 = crearSvgEl("text", {
        x: 15,
        y: padT + plotH / 2,
        "text-anchor": "middle",
        fill: escalaUnica ? "#e2e8f0" : seriesY1[0]?.color || "#38bdf8",
        "font-size": "11.5",
        "font-weight": "600",
        transform: `rotate(-90, 15, ${padT + plotH / 2})`,
      });
      lblY1.textContent = escalaUnica ? y1Titulo : `◀ ${y1Titulo}`;
      svg.appendChild(lblY1);
    }

    if (!escalaUnica && panel.y2_label && seriesY2.length > 0) {
      const lblY2 = crearSvgEl("text", {
        x: W - 12,
        y: padT + plotH / 2,
        "text-anchor": "middle",
        fill: seriesY2[0]?.color || "#facc15",
        "font-size": "11.5",
        "font-weight": "600",
        transform: `rotate(90, ${W - 12}, ${padT + plotH / 2})`,
      });
      lblY2.textContent = `${panel.y2_label} ▶`;
      svg.appendChild(lblY2);
    }

    // Línea vertical de referencia / óptimo (si existe)
    if (
      panel.x_optimo !== undefined &&
      panel.x_optimo !== null &&
      panel.x_optimo >= xMin &&
      panel.x_optimo <= xMax
    ) {
      const xOptPos = toX(panel.x_optimo);
      svg.appendChild(
        crearSvgEl("line", {
          x1: xOptPos,
          y1: padT,
          x2: xOptPos,
          y2: padT + plotH,
          stroke: "#a78bfa",
          "stroke-width": 1.5,
          "stroke-dasharray": "5,4",
        })
      );
      if (panel.x_optimo_label) {
        const txtOpt = crearSvgEl("text", {
          x: Math.min(padL + plotW - 6, Math.max(padL + 6, xOptPos + 5)),
          y: padT + 14,
          "text-anchor": xOptPos > padL + plotW * 0.72 ? "end" : "start",
          fill: "#c4b5fd",
          "font-size": "10.5",
          "font-weight": "700",
        });
        txtOpt.textContent = `◆ ${panel.x_optimo_label}`;
        svg.appendChild(txtOpt);
      }
    }

    // Línea vertical del valor actual de operación (★ Punto actual)
    let idxActual = -1;
    if (
      panel.x_actual !== undefined &&
      panel.x_actual !== null &&
      panel.x_actual >= xMin &&
      panel.x_actual <= xMax
    ) {
      const xActPos = toX(panel.x_actual);
      svg.appendChild(
        crearSvgEl("line", {
          x1: xActPos,
          y1: padT,
          x2: xActPos,
          y2: padT + plotH,
          stroke: "#facc15",
          "stroke-width": 2,
          "stroke-dasharray": "4,3",
        })
      );
      const badgeAct = crearSvgEl("text", {
        x: Math.min(padL + plotW - 6, Math.max(padL + 6, xActPos)),
        y: padT - 7,
        "text-anchor": "middle",
        fill: "#fde047",
        "font-size": "11",
        "font-weight": "700",
      });
      badgeAct.textContent = `★ Actual (${formatearNumero(panel.x_actual)})`;
      svg.appendChild(badgeAct);

      // Índice más cercano a x_actual
      let mejorDist = Infinity;
      xs.forEach((xVal, i) => {
        const d = Math.abs(xVal - panel.x_actual);
        if (d < mejorDist) {
          mejorDist = d;
          idxActual = i;
        }
      });
    }

    // Trazado de cada serie de curvas (dividido en segmentos contiguos válidos; nunca convierte null en 0)
    panel.series.forEach((serie, sIdx) => {
      if (!seriesVisibles[sIdx]) return;
      const toY = !escalaUnica && serie.eje === "y2" ? toY2 : toY1;

      const segmentos = [];
      let segActual = [];
      serie.valores.forEach((val, i) => {
        if (esValidoNum(val)) {
          segActual.push(`${toX(xs[i]).toFixed(1)},${toY(val).toFixed(1)}`);
        } else if (segActual.length > 0) {
          segmentos.push(segActual);
          segActual = [];
        }
      });
      if (segActual.length > 0) segmentos.push(segActual);

      segmentos.forEach((seg) => {
        if (seg.length >= 2) {
          svg.appendChild(
            crearSvgEl("polyline", {
              fill: "none",
              stroke: serie.color || "#38bdf8",
              "stroke-width": 2.6,
              "stroke-dasharray": serie.dashed ? "6,4" : "",
              "stroke-linejoin": "round",
              "stroke-linecap": "round",
              points: seg.join(" "),
            })
          );
        } else if (seg.length === 1) {
          const [px, py] = seg[0].split(",");
          svg.appendChild(
            crearSvgEl("circle", {
              cx: px,
              cy: py,
              r: 3.5,
              fill: serie.color || "#38bdf8",
            })
          );
        }
      });

      // Punto destacado sobre la curva en el estado actual
      if (idxActual >= 0 && esValidoNum(serie.valores[idxActual])) {
        const cx = toX(xs[idxActual]);
        const cy = toY(serie.valores[idxActual]);
        svg.appendChild(
          crearSvgEl("circle", {
            cx,
            cy,
            r: 5,
            fill: serie.color || "#38bdf8",
            stroke: "#0f172a",
            "stroke-width": 2,
          })
        );
      }
    });

    // Elementos de cursor interactivo (crosshair)
    const hoverLine = crearSvgEl("line", {
      x1: padL,
      y1: padT,
      x2: padL,
      y2: padT + plotH,
      stroke: "#e2e8f0",
      "stroke-width": 1,
      "stroke-dasharray": "2,2",
      visibility: "hidden",
    });
    svg.appendChild(hoverLine);

    const hoverDots = panel.series.map((serie) => {
      const dot = crearSvgEl("circle", {
        cx: 0,
        cy: 0,
        r: 4.5,
        fill: serie.color || "#38bdf8",
        stroke: "#ffffff",
        "stroke-width": 1.5,
        visibility: "hidden",
      });
      svg.appendChild(dot);
      return dot;
    });

    // Rectángulo transparente para capturar eventos del ratón
    const overlay = crearSvgEl("rect", {
      x: padL,
      y: padT,
      width: plotW,
      height: plotH,
      fill: "transparent",
      style: "cursor: crosshair;",
    });

    overlay.addEventListener("mousemove", (ev) => {
      const rect = svg.getBoundingClientRect();
      const relX = ((ev.clientX - rect.left) / rect.width) * W;
      const xValCursor = xMin + ((relX - padL) / plotW) * xSpan;

      // Buscar el índice más cercano en xs
      let bestI = 0;
      let minDist = Infinity;
      for (let i = 0; i < xs.length; i++) {
        const d = Math.abs(xs[i] - xValCursor);
        if (d < minDist) {
          minDist = d;
          bestI = i;
        }
      }

      const snapX = toX(xs[bestI]);
      hoverLine.setAttribute("x1", String(snapX));
      hoverLine.setAttribute("x2", String(snapX));
      hoverLine.setAttribute("visibility", "visible");

      const partes = [
        `<strong style="color:#fde047;">X = ${formatearNumero(xs[bestI])}</strong>`,
      ];

      panel.series.forEach((serie, sIdx) => {
        if (!seriesVisibles[sIdx]) {
          hoverDots[sIdx].setAttribute("visibility", "hidden");
          return;
        }
        const val = serie.valores[bestI];
        const estadoPt = Array.isArray(serie.estados) ? serie.estados[bestI] : null;
        if (!esValidoNum(val)) {
          hoverDots[sIdx].setAttribute("visibility", "hidden");
          const msgSinSol = estadoPt || "Sin solución";
          partes.push(
            `<span style="color:${serie.color};font-weight:600;">● ${serie.nombre}: ${msgSinSol}</span>`
          );
          return;
        }
        const toY = !escalaUnica && serie.eje === "y2" ? toY2 : toY1;
        hoverDots[sIdx].setAttribute("cx", String(snapX));
        hoverDots[sIdx].setAttribute("cy", String(toY(val)));
        hoverDots[sIdx].setAttribute("visibility", "visible");
        const sufijoEstado = estadoPt ? ` [${estadoPt}]` : "";
        partes.push(
          `<span style="color:${serie.color};font-weight:600;">● ${serie.nombre}: ${formatearNumero(val)} ${serie.unidad}${sufijoEstado}</span>`
        );
      });

      readoutBar.innerHTML = partes.join(" &nbsp;│&nbsp; ");
    });

    overlay.addEventListener("mouseleave", () => {
      hoverLine.setAttribute("visibility", "hidden");
      hoverDots.forEach((d) => d.setAttribute("visibility", "hidden"));
    });

    svg.appendChild(overlay);
    svgWrapper.appendChild(svg);
  }

  // Construir botones de leyenda para activar/desactivar series
  panel.series.forEach((serie, idx) => {
    const pill = document.createElement("button");
    pill.type = "button";
    pill.className = "chart-legend-pill active";
    pill.innerHTML = `
      <span class="chart-legend-swatch" style="background:${serie.color};"></span>
      <span>${serie.nombre} (${serie.unidad})</span>
      <span class="chart-legend-axis-tag">${serie.eje === "y2" ? "Eje Der." : "Eje Izq."}</span>
    `;
    const tagEl = pill.querySelector(".chart-legend-axis-tag");
    if (tagEl) {
      tagEl.classList.toggle("hidden", escalaUnica);
      axisTags.push(tagEl);
    }
    pill.addEventListener("click", () => {
      seriesVisibles[idx] = !seriesVisibles[idx];
      pill.classList.toggle("active", seriesVisibles[idx]);
      pill.classList.toggle("muted", !seriesVisibles[idx]);
      dibujarSvg();
    });
    legendBar.appendChild(pill);
  });

  card.appendChild(legendBar);
  card.appendChild(svgWrapper);
  card.appendChild(readoutBar);

  dibujarSvg();
  return card;
}

/**
 * Renderiza un panel de barras comparativas (ej. Aire Caliente vs. Motores, o Energías Con/Sin Aislante).
 */
function crearPanelBarrasComparativas(panel, alSeleccionarVariable) {
  const card = document.createElement("div");
  card.className = "chart-subpanel-card";

  const titleBar = document.createElement("div");
  titleBar.className = "chart-subpanel-header";
  titleBar.innerHTML = `<h4 class="chart-subpanel-title">${panel.titulo}</h4>`;
  card.appendChild(titleBar);

  const groupsContainer = document.createElement("div");
  groupsContainer.className = "chart-bars-groups";

  (panel.grupos || []).forEach((grupo) => {
    const groupBox = document.createElement("div");
    groupBox.className = "chart-bar-group-box";

    const sub = document.createElement("div");
    sub.className = "chart-bar-group-title";
    sub.textContent = grupo.subtitulo;
    groupBox.appendChild(sub);

    const maxVal = Math.max(
      1e-9,
      ...grupo.barras.map((b) => Math.abs(b.valor || 0))
    );

    grupo.barras.forEach((b) => {
      const row = document.createElement("div");
      row.className = "chart-bar-row";

      const topRow = document.createElement("div");
      topRow.className = "chart-bar-row-top";

      const labelBtn = document.createElement("button");
      labelBtn.type = "button";
      labelBtn.className = "chart-bar-var-btn";
      labelBtn.innerHTML = `
        <span class="chart-bar-dot" style="background:${b.color};"></span>
        <span class="chart-bar-label-text">${b.etiqueta}</span>
      `;
      if (b.codigo && alSeleccionarVariable) {
        labelBtn.title = `Hacer clic para abrir '${b.codigo}' en el panel inferior`;
        labelBtn.addEventListener("click", () => alSeleccionarVariable(b.codigo));
      }

      const valGroup = document.createElement("div");
      valGroup.className = "chart-bar-val-group";
      valGroup.innerHTML = `
        <strong class="chart-bar-value" style="color:${b.color};">${formatearNumero(b.valor)} ${grupo.unidad}</strong>
        <span class="chart-bar-detail">${b.detalle || ""}</span>
      `;

      topRow.appendChild(labelBtn);
      topRow.appendChild(valGroup);

      const track = document.createElement("div");
      track.className = "chart-bar-track";

      const fill = document.createElement("div");
      fill.className = "chart-bar-fill";
      const pct = Math.min(100, Math.max(2, (Math.abs(b.valor) / maxVal) * 100));
      fill.style.width = `${pct.toFixed(1)}%`;
      fill.style.background = b.color;
      track.appendChild(fill);

      row.appendChild(topRow);
      row.appendChild(track);
      groupBox.appendChild(row);
    });

    groupsContainer.appendChild(groupBox);
  });

  card.appendChild(groupsContainer);
  return card;
}

/**
 * Renderiza la silueta 2D a escala del dirigible (dos semielipsoides cf + cr con diámetro D = 2R)
 * junto con el desglose completo de la Masa Total (mtot).
 */
function crearPanelSiluetaYMasas(panel, alSeleccionarVariable) {
  const card = document.createElement("div");
  card.className = "chart-subpanel-card";

  const titleBar = document.createElement("div");
  titleBar.className = "chart-subpanel-header";
  titleBar.innerHTML = `<h4 class="chart-subpanel-title">${panel.titulo}</h4>`;
  card.appendChild(titleBar);

  const contentBox = document.createElement("div");
  contentBox.className = "silhouette-and-masses-box";

  // 1. Dibujo SVG a escala de la silueta del casco L x D
  const g = panel.geometria;
  const W = 760;
  const H = 205;
  const svg = crearSvgEl("svg", {
    viewBox: `0 0 ${W} ${H}`,
    class: "hull-silhouette-svg",
  });

  const maxDrawW = 540;
  const maxDrawH = 125;
  const scale = Math.min(
    maxDrawW / Math.max(0.1, g.L),
    maxDrawH / Math.max(0.1, g.D)
  );
  const drawL = g.L * scale;
  const drawR = g.R * scale;
  const drawCf = g.cf * scale;
  const drawCr = g.cr * scale;

  const startX = (W - drawL) / 2;
  const centerY = 92;
  const joinX = startX + drawCf;
  const endX = startX + drawL;

  // Path de dos semielipsoides unidos en joinX
  const pathD = [
    `M ${startX.toFixed(1)} ${centerY.toFixed(1)}`,
    `A ${drawCf.toFixed(1)} ${drawR.toFixed(1)} 0 0 1 ${joinX.toFixed(1)} ${(centerY - drawR).toFixed(1)}`,
    `A ${drawCr.toFixed(1)} ${drawR.toFixed(1)} 0 0 1 ${endX.toFixed(1)} ${centerY.toFixed(1)}`,
    `A ${drawCr.toFixed(1)} ${drawR.toFixed(1)} 0 0 1 ${joinX.toFixed(1)} ${(centerY + drawR).toFixed(1)}`,
    `A ${drawCf.toFixed(1)} ${drawR.toFixed(1)} 0 0 1 ${startX.toFixed(1)} ${centerY.toFixed(1)}`,
    "Z",
  ].join(" ");

  svg.appendChild(
    crearSvgEl("path", {
      d: pathD,
      fill: "rgba(56, 189, 248, 0.14)",
      stroke: "#38bdf8",
      "stroke-width": 2.5,
    })
  );

  // Capa interior punteada representando el aislante celular (espesor e)
  const innerR = Math.max(4, drawR - 5);
  const innerCf = Math.max(4, drawCf - 5);
  const innerCr = Math.max(4, drawCr - 5);
  const innerPathD = [
    `M ${(startX + 5).toFixed(1)} ${centerY.toFixed(1)}`,
    `A ${innerCf.toFixed(1)} ${innerR.toFixed(1)} 0 0 1 ${joinX.toFixed(1)} ${(centerY - innerR).toFixed(1)}`,
    `A ${innerCr.toFixed(1)} ${innerR.toFixed(1)} 0 0 1 ${(endX - 5).toFixed(1)} ${centerY.toFixed(1)}`,
    `A ${innerCr.toFixed(1)} ${innerR.toFixed(1)} 0 0 1 ${joinX.toFixed(1)} ${(centerY + innerR).toFixed(1)}`,
    `A ${innerCf.toFixed(1)} ${innerR.toFixed(1)} 0 0 1 ${(startX + 5).toFixed(1)} ${centerY.toFixed(1)}`,
    "Z",
  ].join(" ");
  svg.appendChild(
    crearSvgEl("path", {
      d: innerPathD,
      fill: "rgba(249, 115, 22, 0.08)",
      stroke: "#4ade80",
      "stroke-width": 1.3,
      "stroke-dasharray": "4,3",
    })
  );

  // Eje longitudinal L y línea vertical de diámetro máximo D = 2R
  svg.appendChild(
    crearSvgEl("line", {
      x1: startX,
      y1: centerY,
      x2: endX,
      y2: centerY,
      stroke: "#60a5fa",
      "stroke-width": 1.2,
      "stroke-dasharray": "5,4",
    })
  );
  svg.appendChild(
    crearSvgEl("line", {
      x1: joinX,
      y1: centerY - drawR,
      x2: joinX,
      y2: centerY + drawR,
      stroke: "#a78bfa",
      "stroke-width": 2,
    })
  );

  // Cota inferior de Longitud total L
  const cotaY = centerY + drawR + 24;
  svg.appendChild(
    crearSvgEl("line", {
      x1: startX,
      y1: cotaY,
      x2: endX,
      y2: cotaY,
      stroke: "#38bdf8",
      "stroke-width": 1.5,
    })
  );
  const txtL = crearSvgEl("text", {
    x: (startX + endX) / 2,
    y: cotaY + 16,
    "text-anchor": "middle",
    fill: "#38bdf8",
    "font-size": "12",
    "font-weight": "700",
    "font-family": "monospace",
  });
  txtL.textContent = `Longitud L = ${g.L} m  (cf = ${g.cf} m | cr = ${g.cr} m)  ·  λ = ${g.lam}`;
  svg.appendChild(txtL);

  // Etiqueta de Diámetro máximo D = 2R
  const txtD = crearSvgEl("text", {
    x: joinX + 8,
    y: centerY - 6,
    fill: "#c4b5fd",
    "font-size": "11.5",
    "font-weight": "700",
    "font-family": "monospace",
  });
  txtD.textContent = `D = ${g.D} m (R = ${g.R} m)`;
  svg.appendChild(txtD);

  // Etiqueta de Volumen, Superficie y Aislante
  const txtInfo = crearSvgEl("text", {
    x: W / 2,
    y: 18,
    "text-anchor": "middle",
    fill: "#e2e8f0",
    "font-size": "11.5",
    "font-family": "monospace",
  });
  txtInfo.textContent = `Volumen V = ${g.V} m³  │  Superficie S = ${g.S} m²  │  Aislante celular e = ${g.e_mm} mm`;
  svg.appendChild(txtInfo);

  contentBox.appendChild(svg);

  // 2. Barra apilada y desglose de la Masa Total (mtot)
  const massSection = document.createElement("div");
  massSection.className = "mass-breakdown-section";

  const totalG = Math.max(
    1e-6,
    panel.desglose_masas.reduce((acc, item) => acc + item.valor_g, 0)
  );

  const stackedHeader = document.createElement("div");
  stackedHeader.className = "mass-stacked-header";
  stackedHeader.innerHTML = `
    <span>Composición de la Masa Total <strong>mtot = ${panel.mtot_kg} kg</strong> (${totalG.toFixed(0)} g)</span>
    <span>Sustentación: <strong style="color:#f97316;">Aire caliente ${panel.mflot_kg} kg</strong> + <strong style="color:#38bdf8;">Motores ${panel.mres_kg} kg</strong></span>
  `;
  massSection.appendChild(stackedHeader);

  const stackedBar = document.createElement("div");
  stackedBar.className = "mass-stacked-bar";
  panel.desglose_masas.forEach((item) => {
    const pct = (item.valor_g / totalG) * 100;
    const seg = document.createElement("div");
    seg.className = "mass-stacked-segment";
    seg.style.width = `${Math.max(1.5, pct).toFixed(1)}%`;
    seg.style.background = item.color;
    seg.title = `${item.etiqueta}: ${item.valor_g} g (${pct.toFixed(1)}%)`;
    stackedBar.appendChild(seg);
  });
  massSection.appendChild(stackedBar);

  const massGrid = document.createElement("div");
  massGrid.className = "mass-items-grid";
  panel.desglose_masas.forEach((item) => {
    const pct = (item.valor_g / totalG) * 100;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "mass-item-pill";
    btn.innerHTML = `
      <span class="chart-bar-dot" style="background:${item.color};"></span>
      <span class="mass-item-name">${item.etiqueta}</span>
      <strong class="mass-item-val" style="color:${item.color};">${item.valor_g} g (${pct.toFixed(1)}%)</strong>
    `;
    if (item.codigo && alSeleccionarVariable) {
      btn.addEventListener("click", () => alSeleccionarVariable(item.codigo));
    }
    massGrid.appendChild(btn);
  });
  massSection.appendChild(massGrid);

  contentBox.appendChild(massSection);
  card.appendChild(contentBox);
  return card;
}

/**
 * Construye una tarjeta completa de una Gráfica (con su barra de variables clicables y sus 2 subpaneles).
 */
function crearTarjetaGrafica(grafica, estadoApp, alSeleccionarVariable) {
  const wrapper = document.createElement("section");
  wrapper.className = "chart-full-card";

  // Barra de descripción y variables involucradas (clicables para editar en el panel inferior)
  const metaBox = document.createElement("div");
  metaBox.className = "chart-meta-box";

  const subText = document.createElement("p");
  subText.className = "chart-subtitle-text";
  subText.textContent = grafica.subtitulo;
  metaBox.appendChild(subText);

  const varsRow = document.createElement("div");
  varsRow.className = "chart-vars-row";

  const varsLabel = document.createElement("span");
  varsLabel.className = "chart-vars-label";
  varsLabel.textContent = "Variables comparadas (clic para modificar abajo):";
  varsRow.appendChild(varsLabel);

  const varActivaNombre = estadoApp.variableDetalle
    ? estadoApp.variableDetalle.variable.nombre
    : null;

  (grafica.variables || []).forEach((v) => {
    const chip = document.createElement("button");
    chip.type = "button";
    chip.className = `chart-var-chip ${
      varActivaNombre === v.nombre ? "active-var" : ""
    }`;
    chip.title = `${v.descripcion} (${v.fija ? "Fija / Entrada" : "Calculada / Despejada"})`;
    chip.innerHTML = `
      <span class="chart-var-chip-code ${claseColorVariable(v.color)}">${v.nombre}</span>
      <span class="chart-var-chip-val">${v.valor_ing}</span>
    `;
    chip.addEventListener("click", () => alSeleccionarVariable(v.nombre));
    varsRow.appendChild(chip);
  });

  metaBox.appendChild(varsRow);
  wrapper.appendChild(metaBox);

  // Cuadrícula de 2 paneles de visualización por gráfica
  const panelsGrid = document.createElement("div");
  panelsGrid.className = "chart-panels-grid";

  (grafica.paneles || []).forEach((panel) => {
    if (panel.tipo === "lineas_doble_eje") {
      panelsGrid.appendChild(crearPanelLineasDobleEje(panel));
    } else if (panel.tipo === "barras_comparativas") {
      panelsGrid.appendChild(
        crearPanelBarrasComparativas(panel, alSeleccionarVariable)
      );
    } else if (panel.tipo === "silueta_y_masas") {
      panelsGrid.appendChild(
        crearPanelSiluetaYMasas(panel, alSeleccionarVariable)
      );
    }
  });

  wrapper.appendChild(panelsGrid);
  return wrapper;
}

/**
 * Renderiza el panel central de Gráficas (una sola gráfica ocupando todo el espacio
 * central, o todas apiladas si se eligió "Ver todas las gráficas").
 */
export function renderizarPanelGraficas(
  contenedorHeader,
  contenedorLista,
  estadoApp,
  alSeleccionarVariable,
  alSeleccionarGrafica
) {
  if (!estadoApp.sistema || !estadoApp.sistema.graficas) return;

  const graficas = estadoApp.sistema.graficas;
  const activaId = estadoApp.graficaActivaId;
  contenedorLista.innerHTML = "";

  if (activaId === "all") {
    contenedorHeader.innerHTML = `
      <div class="cat-banner-title">
        <span>📊</span>
        <span>VISTA GLOBAL DE GRÁFICAS — ${graficas.length} ANÁLISIS COMPARATIVOS</span>
      </div>
      <div class="cat-banner-stats">
        Haz clic en cualquier variable para editarla en el panel inferior
      </div>
    `;

    graficas.forEach((graf) => {
      const divider = document.createElement("div");
      divider.className = "category-section-divider chart-section-divider";
      divider.textContent = `G${graf.indice}. ${graf.titulo}`;
      contenedorLista.appendChild(divider);
      contenedorLista.appendChild(
        crearTarjetaGrafica(graf, estadoApp, alSeleccionarVariable)
      );
    });
    return;
  }

  const idxActual = Math.max(
    0,
    graficas.findIndex((g) => g.id === activaId)
  );
  const graficaActiva = graficas[idxActual] || graficas[0];
  const prevGraf = graficas[(idxActual - 1 + graficas.length) % graficas.length];
  const nextGraf = graficas[(idxActual + 1) % graficas.length];

  contenedorHeader.innerHTML = `
    <div class="cat-banner-title">
      <span>📊</span>
      <span>G${graficaActiva.indice}. ${graficaActiva.titulo}</span>
    </div>
    <div class="chart-header-nav">
      <button type="button" id="btn-prev-chart" class="btn btn-ghost chart-step-btn" title="Gráfica anterior: ${prevGraf.titulo}">
        ◀ Anterior
      </button>
      <span class="cat-banner-stats">${graficaActiva.indice} / ${graficas.length}</span>
      <button type="button" id="btn-next-chart" class="btn btn-ghost chart-step-btn" title="Siguiente gráfica: ${nextGraf.titulo}">
        Siguiente ▶
      </button>
    </div>
  `;

  const btnPrev = contenedorHeader.querySelector("#btn-prev-chart");
  const btnNext = contenedorHeader.querySelector("#btn-next-chart");
  if (btnPrev && alSeleccionarGrafica) {
    btnPrev.addEventListener("click", () => alSeleccionarGrafica(prevGraf.id));
  }
  if (btnNext && alSeleccionarGrafica) {
    btnNext.addEventListener("click", () => alSeleccionarGrafica(nextGraf.id));
  }

  contenedorLista.appendChild(
    crearTarjetaGrafica(graficaActiva, estadoApp, alSeleccionarVariable)
  );
}
