/**
 * equations.js — Componente de visualización de ecuaciones en filas de arriba hacia abajo.
 *
 * Cada fila de ecuación se divide en 3 columnas:
 *   1. Izquierda: Ecuación general en gris con unidades entre paréntesis.
 *   2. Centro:    Ecuación con variables reemplazadas por datos en notación de ingeniería
 *                 y coloreadas (Amarillo = fija, Verde = calculada, Rojo = sustentación penalizada).
 *   3. Derecha:   Explicación de cada variable involucrada y el nombre completo de su unidad.
 */

import { renderizarFormulaKaTeX } from "../katex_helper.js?v=10";
import { renderizarFlujoCategoria } from "./flowchart.js?v=11";

let localFlashTimeout = null;

function claseColorVariable(color) {
  if (color === "red") return "text-penalized";
  if (color === "yellow") return "text-fixed";
  return "text-calc";
}

/**
 * Crea un nodo DOM con la estructura de 3 columnas para una ecuación individual.
 */
export function crearFilaEcuacion(
  eqData,
  variableSeleccionadaNombre,
  alClickVariable,
  mostrarCategoria = false,
  alClickIrAEcuacion = null
) {
  const card = document.createElement("article");
  card.className = `equation-row-card ${eqData.tiene_penalizada ? "equation-penalized" : ""}`;
  card.setAttribute("data-eq-nombre", eqData.nombre);

  // Cabecera con el título de la ecuación (y enlaces a categorías en detalle o en ecuaciones compartidas)
  const header = document.createElement("div");
  header.className = "equation-row-header";

  const prefijo = eqData.categorias_codigo_str || eqData.categoria_codigo;
  const listaCats =
    eqData.categorias && eqData.categorias.length > 0
      ? eqData.categorias
      : eqData.categoria
      ? [
          {
            id: eqData.categoria_id ?? 0,
            codigo: eqData.categoria_codigo || "",
            nombre: eqData.categoria,
          },
        ]
      : [];

  const title = document.createElement("h3");
  title.className = "equation-row-title";
  title.textContent = prefijo ? `${prefijo} - ${eqData.nombre}` : eqData.nombre;
  if (mostrarCategoria && alClickIrAEcuacion && listaCats.length > 0) {
    const primeraCat = listaCats[0];
    title.classList.add("equation-title-clickable");
    title.title = `Ir a ${primeraCat.codigo ? `${primeraCat.codigo}. ` : ""}${primeraCat.nombre} y resaltar esta ecuación`;
    title.addEventListener("click", () => alClickIrAEcuacion(eqData, primeraCat.id));
  }
  header.appendChild(title);

  if (mostrarCategoria && listaCats.length > 0) {
    const group = document.createElement("div");
    group.className = "equation-goto-cats-group";

    listaCats.forEach((cat) => {
      const catCodigo = cat.codigo ? `${cat.codigo}.` : "";
      if (alClickIrAEcuacion) {
        const gotoBtn = document.createElement("button");
        gotoBtn.type = "button";
        gotoBtn.className = "equation-goto-cat-btn";
        gotoBtn.title = `Ir a la categoría "${cat.nombre}" y ubicar esta ecuación`;
        gotoBtn.innerHTML = `
          ${catCodigo ? `<span class="equation-goto-cat-code">${escaparHtml(catCodigo)}</span>` : ""}
          <span>${escaparHtml(cat.nombre)}</span>
          <span class="equation-goto-arrow">↗</span>
        `;
        gotoBtn.addEventListener("click", () => alClickIrAEcuacion(eqData, cat.id));
        group.appendChild(gotoBtn);
      } else {
        const catTag = document.createElement("span");
        catTag.className = "equation-row-category-tag";
        catTag.textContent = `(${catCodigo ? `${catCodigo} ` : ""}${cat.nombre})`;
        group.appendChild(catTag);
      }
    });

    header.appendChild(group);
  } else if (!mostrarCategoria && eqData.es_compartida && listaCats.length > 1) {
    const otras = listaCats.filter((c) => c.id !== eqData.categoria_id);
    if (otras.length > 0) {
      const sharedDiv = document.createElement("div");
      sharedDiv.className = "equation-shared-links";
      const lbl = document.createElement("span");
      lbl.className = "equation-shared-label";
      lbl.textContent = "También en:";
      sharedDiv.appendChild(lbl);

      otras.forEach((cat) => {
        const chip = document.createElement("button");
        chip.type = "button";
        chip.className = "equation-shared-chip";
        chip.title = `Ver esta ecuación en ${cat.codigo}. ${cat.nombre}`;
        chip.textContent = `${cat.codigo} ↗`;
        chip.addEventListener("click", () => {
          if (alClickIrAEcuacion) alClickIrAEcuacion(eqData, cat.id);
        });
        sharedDiv.appendChild(chip);
      });

      header.appendChild(sharedDiv);
    }
  }

  card.appendChild(header);

  // Cuerpo de 3 columnas: Izquierda (General) | Centro (Reemplazada) | Derecha (Variables)
  const grid = document.createElement("div");
  grid.className = "equation-three-cols";

  // 1. Columna izquierda: Ecuación general simbólica con unidades (en gris)
  const colGen = document.createElement("div");
  colGen.className = "eq-col eq-col-general";
  const mathGen = document.createElement("div");
  mathGen.className = "eq-math-box";
  colGen.appendChild(mathGen);
  renderizarFormulaKaTeX(mathGen, eqData.latex_general);

  // 2. Columna central: Ecuación con datos reemplazados en notación de ingeniería y colores
  const colSust = document.createElement("div");
  colSust.className = "eq-col eq-col-substituted";
  const mathSust = document.createElement("div");
  mathSust.className = "eq-math-box";
  colSust.appendChild(mathSust);
  renderizarFormulaKaTeX(mathSust, eqData.latex_sustitucion);

  // 3. Columna derecha: Explicación de cada variable y nombre completo de su unidad
  const colVars = document.createElement("div");
  colVars.className = "eq-col eq-col-variables";
  const varsList = document.createElement("div");
  varsList.className = "eq-vars-list";

  eqData.variables.forEach((v) => {
    const varBtn = document.createElement("button");
    varBtn.type = "button";
    const esActiva = variableSeleccionadaNombre === v.nombre;
    varBtn.className = `eq-var-item ${esActiva ? "active-var" : ""}`;
    varBtn.title = `Click para ver detalle o modificar '${v.nombre}' (${v.valor_ing})`;

    const codeSpan = document.createElement("span");
    codeSpan.className = `eq-var-code ${claseColorVariable(v.color)}`;
    codeSpan.textContent = v.nombre;

    const descSpan = document.createElement("span");
    descSpan.className = "eq-var-desc";
    descSpan.innerHTML = `${escaparHtml(v.descripcion)} <span class="eq-var-unit-full">(${escaparHtml(v.unidad_nombre)})</span>`;

    varBtn.appendChild(codeSpan);
    varBtn.appendChild(descSpan);

    varBtn.addEventListener("click", () => {
      if (alClickVariable) alClickVariable(v.nombre);
    });

    varsList.appendChild(varBtn);
  });

  colVars.appendChild(varsList);

  grid.appendChild(colGen);
  grid.appendChild(colSust);
  grid.appendChild(colVars);
  card.appendChild(grid);

  if (!mostrarCategoria && eqData.nota_fisica) {
    const notaBox = document.createElement("div");
    notaBox.className = "equation-physical-note";
    notaBox.innerHTML = `<span class="eq-note-icon" title="Interpretación física">ⓘ</span><span class="eq-note-text"></span>`;
    notaBox.querySelector(".eq-note-text").textContent = eqData.nota_fisica;
    card.appendChild(notaBox);
  }

  return card;
}

/**
 * Renderiza el panel central completo para la categoría seleccionada (o todas),
 * incluyendo al pie de cada categoría su diagrama de flujo y explicaciones.
 */
export function renderizarPanelEcuaciones(
  contenedorHeader,
  contenedorLista,
  estadoApp,
  alClickVariable,
  alClickIrAEcuacion = null,
  alClickCategoria = null,
  alAbrirMapaGlobal = null
) {
  if (!estadoApp.sistema) return;

  const { categorias, resumen } = estadoApp.sistema;
  const varActiva = estadoApp.variableDetalle ? estadoApp.variableDetalle.variable.nombre : null;

  contenedorHeader.innerHTML = "";
  contenedorLista.innerHTML = "";

  if (estadoApp.categoriaActivaId === "all") {
    contenedorHeader.innerHTML = `
      <div class="cat-banner-title">▌ TODAS LAS CATEGORÍAS DEL SISTEMA</div>
      <div class="cat-banner-actions">
        <div class="cat-banner-stats">${resumen.total_categorias} categorías · ${resumen.total_ecuaciones} ecuaciones únicas</div>
        <button id="btn-open-global-flow" type="button" class="btn btn-outline cat-banner-btn">◈ Mapa de Flujo Global</button>
      </div>
    `;
    contenedorHeader
      .querySelector("#btn-open-global-flow")
      ?.addEventListener("click", () => {
        if (alAbrirMapaGlobal) alAbrirMapaGlobal();
      });

    categorias.forEach((cat) => {
      const divider = document.createElement("div");
      divider.className = "category-section-divider";
      divider.textContent = `C${cat.id + 1}. ${cat.nombre} (${cat.num_ecuaciones} ec.)`;
      contenedorLista.appendChild(divider);

      cat.ecuaciones.forEach((eq) => {
        contenedorLista.appendChild(
          crearFilaEcuacion(eq, varActiva, alClickVariable, false, alClickIrAEcuacion)
        );
      });
    });
    return;
  }

  const catActiva = categorias.find((c) => c.id === estadoApp.categoriaActivaId) || categorias[0];
  if (!catActiva) return;

  const compTxt = catActiva.num_compartidas ? ` (${catActiva.num_compartidas} compartida(s))` : "";
  contenedorHeader.innerHTML = `
    <div class="cat-banner-title">▌ C${catActiva.id + 1}. ${escaparHtml(catActiva.nombre.toUpperCase())}</div>
    <div class="cat-banner-actions">
      <div class="cat-banner-stats">
        ${catActiva.num_ecuaciones} ecuación(es)${compTxt} · ${catActiva.num_fijas} fija(s) · ${catActiva.num_calculadas} calculada(s)
      </div>
      <button id="btn-jump-cat-flow" type="button" class="btn btn-outline cat-banner-btn" title="Ir al diagrama de flujo y explicaciones de esta categoría">
        ↓ Flujo y relaciones
      </button>
    </div>
  `;
  contenedorHeader
    .querySelector("#btn-jump-cat-flow")
    ?.addEventListener("click", () => {
      const flowSec = contenedorLista.querySelector("#cat-flow-section");
      if (flowSec) {
        flowSec.scrollIntoView({ behavior: "smooth", block: "start" });
      }
    });

  catActiva.ecuaciones.forEach((eq) => {
    contenedorLista.appendChild(
      crearFilaEcuacion(eq, varActiva, alClickVariable, false, alClickIrAEcuacion)
    );
  });

  renderizarFlujoCategoria(contenedorLista, catActiva, estadoApp, {
    alClickCategoria,
    alClickVariable,
    alAbrirMapaGlobal,
    alClickEcuacion: (nombreEq) => {
      const cards = contenedorLista.querySelectorAll(".equation-row-card");
      const targetCard = Array.from(cards).find(
        (el) => el.getAttribute("data-eq-nombre") === nombreEq
      );
      if (targetCard) {
        targetCard.scrollIntoView({ behavior: "smooth", block: "center" });
        cards.forEach((c) => c.classList.remove("equation-flash-highlight"));
        targetCard.classList.add("equation-flash-highlight");
        if (localFlashTimeout) clearTimeout(localFlashTimeout);
        localFlashTimeout = setTimeout(() => {
          targetCard.classList.remove("equation-flash-highlight");
        }, 2400);
      }
    },
  });
}

function escaparHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
