/**
 * equations.js — Componente de visualización de ecuaciones en filas de arriba hacia abajo.
 *
 * Cada fila de ecuación se divide en 3 columnas:
 *   1. Izquierda: Ecuación general en gris con unidades entre paréntesis.
 *   2. Centro:    Ecuación con variables reemplazadas por datos en notación de ingeniería
 *                 y coloreadas (Amarillo = fija, Verde = calculada, Rojo = sustentación penalizada).
 *   3. Derecha:   Explicación de cada variable involucrada y el nombre completo de su unidad.
 */

import { renderizarFormulaKaTeX } from "../katex_helper.js";

function claseColorVariable(color) {
  if (color === "red") return "text-penalized";
  if (color === "yellow") return "text-fixed";
  return "text-calc";
}

/**
 * Crea un nodo DOM con la estructura de 3 columnas para una ecuación individual.
 */
export function crearFilaEcuacion(eqData, variableSeleccionadaNombre, alClickVariable, mostrarCategoria = false) {
  const card = document.createElement("article");
  card.className = `equation-row-card ${eqData.tiene_penalizada ? "equation-penalized" : ""}`;

  // Cabecera con el título de la ecuación (y categoría opcional en el panel de detalle)
  const header = document.createElement("div");
  header.className = "equation-row-header";

  const title = document.createElement("h3");
  title.className = "equation-row-title";
  title.textContent = eqData.nombre;
  header.appendChild(title);

  if (mostrarCategoria && eqData.categoria) {
    const catTag = document.createElement("span");
    catTag.className = "equation-row-category-tag";
    catTag.textContent = `(${eqData.categoria})`;
    header.appendChild(catTag);
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

  return card;
}

/**
 * Renderiza el panel central completo para la categoría seleccionada (o todas).
 */
export function renderizarPanelEcuaciones(
  contenedorHeader,
  contenedorLista,
  estadoApp,
  alClickVariable
) {
  if (!estadoApp.sistema) return;

  const { categorias, resumen } = estadoApp.sistema;
  const varActiva = estadoApp.variableDetalle ? estadoApp.variableDetalle.variable.nombre : null;

  contenedorHeader.innerHTML = "";
  contenedorLista.innerHTML = "";

  if (estadoApp.categoriaActivaId === "all") {
    contenedorHeader.innerHTML = `
      <div class="cat-banner-title">▌ TODAS LAS CATEGORÍAS DEL SISTEMA</div>
      <div class="cat-banner-stats">${resumen.total_categorias} categorías · ${resumen.total_ecuaciones} ecuaciones</div>
    `;

    categorias.forEach((cat) => {
      const divider = document.createElement("div");
      divider.className = "category-section-divider";
      divider.textContent = `${cat.id + 1}. ${cat.nombre}`;
      contenedorLista.appendChild(divider);

      cat.ecuaciones.forEach((eq) => {
        contenedorLista.appendChild(crearFilaEcuacion(eq, varActiva, alClickVariable, false));
      });
    });
    return;
  }

  const catActiva = categorias.find((c) => c.id === estadoApp.categoriaActivaId) || categorias[0];
  if (!catActiva) return;

  contenedorHeader.innerHTML = `
    <div class="cat-banner-title">▌ ${catActiva.id + 1}. ${escaparHtml(catActiva.nombre.toUpperCase())}</div>
    <div class="cat-banner-stats">
      ${catActiva.num_ecuaciones} ecuación(es) · ${catActiva.num_fijas} fija(s) · ${catActiva.num_calculadas} calculada(s)
    </div>
  `;

  catActiva.ecuaciones.forEach((eq) => {
    contenedorLista.appendChild(crearFilaEcuacion(eq, varActiva, alClickVariable, false));
  });
}

function escaparHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
