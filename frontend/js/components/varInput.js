/**
 * varInput.js — Componente del Panel Inferior:
 * 1. Campo de entrada directa por teclado (escribir nombre de variable + Enter) con autocompletado.
 * 2. Catálogo desplegable a 2 columnas de las 102 variables del sistema (Amarillo = Fija, Verde = Calculada).
 * 3. Vista de Detalle de la Variable seleccionada:
 *    - Estado, valor SI y valor en notación de ingeniería.
 *    - Controles de modificación y Asistente de Equilibrio Matemático (`balancer.js`).
 *    - Todas las ecuaciones donde interviene la variable en formato de 3 columnas (`equations.js`).
 */

import { crearFilaEcuacion } from "./equations.js";
import { renderizarAsistenteModificacion } from "./balancer.js";

export function inicializarEntradaTeclado(
  formEl,
  inputEl,
  autocompleteEl,
  obtenerVariablesSistema,
  alSeleccionarVariable,
  mostrarMensaje
) {
  let indiceSugerencia = -1;
  let sugerenciasActuales = [];

  function cerrarAutocomplete() {
    autocompleteEl.classList.add("hidden");
    autocompleteEl.innerHTML = "";
    indiceSugerencia = -1;
    sugerenciasActuales = [];
  }

  function renderSugerencias(query) {
    const vars = obtenerVariablesSistema();
    if (!vars || !query) {
      cerrarAutocomplete();
      return;
    }

    const q = query.toLowerCase();
    // Priorizar coincidencia por nombre exacto/prefijo y luego por descripción
    const porNombre = vars.filter((v) => v.nombre.toLowerCase().startsWith(q));
    const porSubcadena = vars.filter(
      (v) =>
        !v.nombre.toLowerCase().startsWith(q) &&
        (v.nombre.toLowerCase().includes(q) || v.descripcion.toLowerCase().includes(q))
    );
    sugerenciasActuales = [...porNombre, ...porSubcadena].slice(0, 10);

    if (sugerenciasActuales.length === 0) {
      cerrarAutocomplete();
      return;
    }

    autocompleteEl.innerHTML = "";
    indiceSugerencia = -1;

    sugerenciasActuales.forEach((v, idx) => {
      const item = document.createElement("button");
      item.type = "button";
      item.className = "autocomplete-item";
      const colorCls = v.color === "red" ? "text-penalized" : v.fija ? "text-fixed" : "text-calc";

      item.innerHTML = `
        <div class="autocomplete-left">
          <span class="autocomplete-code ${colorCls}">${v.nombre}</span>
          <span class="autocomplete-desc">${v.descripcion}</span>
        </div>
        <span class="autocomplete-val">${v.valor_vista_ing}</span>
      `;

      item.addEventListener("mousedown", (e) => {
        e.preventDefault(); // evitar blur antes del click
        inputEl.value = v.nombre;
        cerrarAutocomplete();
        alSeleccionarVariable(v.nombre);
      });

      autocompleteEl.appendChild(item);
    });

    autocompleteEl.classList.remove("hidden");
  }

  inputEl.addEventListener("input", () => {
    renderSugerencias(inputEl.value.trim());
  });

  inputEl.addEventListener("keydown", (e) => {
    if (autocompleteEl.classList.contains("hidden") || sugerenciasActuales.length === 0) {
      return;
    }
    const items = autocompleteEl.querySelectorAll(".autocomplete-item");
    if (e.key === "ArrowDown") {
      e.preventDefault();
      indiceSugerencia = (indiceSugerencia + 1) % sugerenciasActuales.length;
      actualizarDestacado(items);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      indiceSugerencia = (indiceSugerencia - 1 + sugerenciasActuales.length) % sugerenciasActuales.length;
      actualizarDestacado(items);
    } else if (e.key === "Escape") {
      cerrarAutocomplete();
    }
  });

  function actualizarDestacado(items) {
    items.forEach((el, i) => {
      el.classList.toggle("selected", i === indiceSugerencia);
      if (i === indiceSugerencia) {
        el.scrollIntoView({ block: "nearest" });
      }
    });
  }

  inputEl.addEventListener("blur", () => {
    setTimeout(cerrarAutocomplete, 150);
  });

  formEl.addEventListener("submit", (e) => {
    e.preventDefault();
    const vars = obtenerVariablesSistema();
    if (!vars) return;

    // Si navegó con flechas sobre una sugerencia
    if (indiceSugerencia >= 0 && sugerenciasActuales[indiceSugerencia]) {
      const elegida = sugerenciasActuales[indiceSugerencia].nombre;
      inputEl.value = elegida;
      cerrarAutocomplete();
      alSeleccionarVariable(elegida);
      return;
    }

    const texto = inputEl.value.trim();
    if (!texto) return;

    // Coincidencia exacta primero, o insensible a mayúsculas/minúsculas
    const exacta = vars.find((v) => v.nombre === texto);
    const insensible = vars.find((v) => v.nombre.toLowerCase() === texto.toLowerCase());
    const objetivo = exacta || insensible;

    if (!objetivo) {
      mostrarMensaje(`Variable desconocida: '${texto}'`, "error");
      return;
    }

    inputEl.value = objetivo.nombre;
    cerrarAutocomplete();
    alSeleccionarVariable(objetivo.nombre);
  });
}

/**
 * Renderiza el catálogo de las 102 variables en 2 columnas (`mostrar_menu_variables` en calc.py).
 */
export function renderizarCatalogoVariables(
  contenedorCatalogo,
  estadoApp,
  alSeleccionarVariable,
  alCambiarFiltro
) {
  if (!estadoApp.sistema || !estadoApp.catalogoAbierto) {
    contenedorCatalogo.classList.add("hidden");
    contenedorCatalogo.innerHTML = "";
    return;
  }

  contenedorCatalogo.classList.remove("hidden");
  contenedorCatalogo.innerHTML = "";

  const { variables, resumen } = estadoApp.sistema;
  const filtro = estadoApp.filtroCatalogo || "all";

  const header = document.createElement("div");
  header.className = "catalog-header";
  header.innerHTML = `
    <div class="catalog-title">
      Variables del Sistema (<span class="text-fixed">Amarillo = Fija</span>, <span class="text-calc">Verde = Calculada</span>)
    </div>
    <div class="catalog-filter-group">
      <button type="button" data-f="all" class="btn btn-outline ${filtro === "all" ? "active" : ""}">
        Todas (${resumen.total_variables})
      </button>
      <button type="button" data-f="fixed" class="btn btn-outline ${filtro === "fixed" ? "active" : ""}">
        Fijas (${resumen.total_fijas})
      </button>
      <button type="button" data-f="calc" class="btn btn-outline ${filtro === "calc" ? "active" : ""}">
        Calculadas (${resumen.total_calculadas})
      </button>
    </div>
  `;

  header.querySelectorAll("button[data-f]").forEach((btn) => {
    btn.addEventListener("click", () => alCambiarFiltro(btn.getAttribute("data-f")));
  });

  contenedorCatalogo.appendChild(header);

  const filtradas = variables.filter((v) => {
    if (filtro === "fixed") return v.fija;
    if (filtro === "calc") return !v.fija;
    return true;
  });

  const grid = document.createElement("div");
  grid.className = "catalog-grid";

  filtradas.forEach((v) => {
    const rowBtn = document.createElement("button");
    rowBtn.type = "button";
    rowBtn.className = "catalog-row-btn";
    const colorCls = v.color === "red" ? "text-penalized" : v.fija ? "text-fixed" : "text-calc";
    rowBtn.innerHTML = `
      <span class="catalog-row-code ${colorCls}">${v.nombre}</span>
      <span class="catalog-row-desc">${v.descripcion}</span>
      <span class="catalog-row-val">${v.valor_vista_ing}</span>
    `;
    rowBtn.addEventListener("click", () => alSeleccionarVariable(v.nombre));
    grid.appendChild(rowBtn);
  });

  contenedorCatalogo.appendChild(grid);
}

/**
 * Renderiza el panel de Detalle de Variable (`_mostrar_detalle_variable` en calc.py).
 */
export function renderizarDetalleVariable(
  contenedorDetalle,
  estadoApp,
  alSeleccionarVariable,
  alAplicarModificacion,
  mostrarMensaje
) {
  const detalle = estadoApp.variableDetalle;
  if (!detalle || !estadoApp.sistema) {
    contenedorDetalle.innerHTML = "";
    return;
  }

  const { variable, ecuaciones } = detalle;
  contenedorDetalle.innerHTML = "";

  const card = document.createElement("div");
  card.className = "detail-panel-card";

  // 1. Cabecera con nombre, descripción, estado (FIJA / CALCULADA) y valor actual SI + Ingeniería
  const headerBar = document.createElement("div");
  headerBar.className = "detail-header-bar";

  const badgeClass = variable.fija ? "badge-fixed" : "badge-calc";
  const badgeText = variable.fija ? "FIJA (amarilla)" : "CALCULADA (verde)";
  const valColorCls = variable.penalizada
    ? "text-penalized"
    : variable.fija
    ? "text-fixed"
    : "text-calc";

  headerBar.innerHTML = `
    <div class="detail-var-summary">
      <span class="detail-var-name">${variable.nombre}</span>
      <span class="detail-var-desc">— ${variable.descripcion} <span style="color: var(--text-muted);">(${variable.unidad_nombre})</span></span>
      <span class="detail-state-badge ${badgeClass}">Estado: ${badgeText}</span>
    </div>
    <div class="detail-values-pill">
      Actual: <strong class="${valColorCls}">${Number(variable.valor_vista.toPrecision(6))} ${variable.unidad}</strong>
      <span style="color: var(--text-muted);">(${variable.valor_vista_ing})</span>
    </div>
  `;
  card.appendChild(headerBar);

  // 2. Contenedor de modificación / intercambio y Asistente de Equilibrio Matemático
  const balancerContainer = document.createElement("div");
  card.appendChild(balancerContainer);
  renderizarAsistenteModificacion(
    balancerContainer,
    detalle,
    estadoApp.sistema,
    alAplicarModificacion,
    mostrarMensaje
  );

  // 3. Ecuaciones donde interviene la variable (con valores reemplazados en formato de 3 columnas)
  const eqSection = document.createElement("div");
  eqSection.className = "detail-equations-section";

  const eqSubtitle = document.createElement("div");
  eqSubtitle.className = "detail-section-subtitle";
  eqSubtitle.textContent = `Ecuaciones donde interviene '${variable.nombre}' (${ecuaciones.length} ecuación(es) con valores reemplazados):`;
  eqSection.appendChild(eqSubtitle);

  ecuaciones.forEach((eq) => {
    eqSection.appendChild(
      crearFilaEcuacion(eq, variable.nombre, alSeleccionarVariable, true)
    );
  });

  card.appendChild(eqSection);
  contenedorDetalle.appendChild(card);
}
