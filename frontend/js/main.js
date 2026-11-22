/**
 * main.js — Punto de entrada de la aplicación frontend modular.
 * Conecta el almacén de estado (`state.js`), el cliente de la API (`api.js`)
 * y los componentes visuales (`sidebar.js`, `equations.js`, `varInput.js`, `balancer.js`).
 */

import {
  fetchEstado,
  fetchDetalleVariable,
  postModificar,
  postReiniciar,
} from "./api.js?v=4";
import { store } from "./state.js?v=4";
import {
  renderizarSidebarCategorias,
  renderizarSidebarGraficas,
} from "./components/sidebar.js?v=4";
import { renderizarPanelEcuaciones } from "./components/equations.js?v=4";
import { renderizarPanelGraficas } from "./components/charts.js?v=4";
import {
  inicializarEntradaTeclado,
  renderizarCatalogoVariables,
  renderizarDetalleVariable,
} from "./components/varInput.js?v=4";

// Referencias a elementos del DOM
const appShell = document.getElementById("app-shell");
const alertBanner = document.getElementById("alert-banner");
const countFixedEl = document.getElementById("count-fixed");
const countCalcEl = document.getElementById("count-calc");
const legendPenalizedEl = document.getElementById("legend-penalized");
const btnReset = document.getElementById("btn-reset");

const sidebarCount = document.getElementById("sidebar-count");
const categoryList = document.getElementById("category-list");
const sidebarChartsCount = document.getElementById("sidebar-charts-count");
const chartsNavList = document.getElementById("charts-nav-list");

const equationsView = document.getElementById("equations-view");
const equationsHeader = document.getElementById("equations-header");
const equationsList = document.getElementById("equations-list");

const chartsView = document.getElementById("charts-view");
const chartsHeader = document.getElementById("charts-header");
const chartsList = document.getElementById("charts-list");

const bottomPanel = document.getElementById("bottom-panel");
const bottomResizer = document.getElementById("bottom-resizer");
const varQuickForm = document.getElementById("var-quick-form");
const varKeyboardInput = document.getElementById("var-keyboard-input");
const varAutocomplete = document.getElementById("var-autocomplete");
const btnToggleCatalog = document.getElementById("btn-toggle-catalog");
const btnClearSelection = document.getElementById("btn-clear-selection");
const btnToggleBottomSize = document.getElementById("btn-toggle-bottom-size");
const bottomFeedback = document.getElementById("bottom-feedback");
const catalogContainer = document.getElementById("catalog-container");
const variableDetailContainer = document.getElementById("variable-detail-container");

let feedbackTimeout = null;
let flashTimeout = null;

function irACategoriaYEcuacion(eqData) {
  if (!eqData || !store.sistema) return;

  let catId = eqData.categoria_id;
  if (catId === undefined || catId === null) {
    const encontrada = store.sistema.categorias.find(
      (c) => c.nombre === eqData.categoria
    );
    catId = encontrada ? encontrada.id : 0;
  }

  store.seleccionarCategoria(catId);

  requestAnimationFrame(() => {
    const activeCatBtn = categoryList?.querySelector(".category-btn.active");
    if (activeCatBtn) {
      activeCatBtn.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }

    const cards = equationsList.querySelectorAll(".equation-row-card");
    const targetCard = Array.from(cards).find(
      (el) => el.getAttribute("data-eq-nombre") === eqData.nombre
    );
    if (targetCard) {
      targetCard.scrollIntoView({ behavior: "smooth", block: "center" });
      cards.forEach((c) => c.classList.remove("equation-flash-highlight"));
      targetCard.classList.add("equation-flash-highlight");
      if (flashTimeout) clearTimeout(flashTimeout);
      flashTimeout = setTimeout(() => {
        targetCard.classList.remove("equation-flash-highlight");
      }, 2400);
    }
  });
}

function inicializarRedimensionPanelInferior() {
  if (!bottomPanel || !bottomResizer) return;
  let isDragging = false;

  bottomResizer.addEventListener("mousedown", (e) => {
    if (e.button !== 0) return;
    e.preventDefault();
    isDragging = true;
    bottomPanel.classList.add("is-resizing");
    document.body.style.cursor = "ns-resize";
    document.body.style.userSelect = "none";
  });

  window.addEventListener("mousemove", (e) => {
    if (!isDragging) return;
    const minAltura = 64;
    const maxAltura = Math.max(
      minAltura + 40,
      Math.min(window.innerHeight * 0.80, window.innerHeight - 150)
    );
    const nuevaAltura = window.innerHeight - e.clientY;
    const alturaSegura = Math.max(minAltura, Math.min(maxAltura, nuevaAltura));

    bottomPanel.style.height = `${alturaSegura}px`;
    bottomPanel.style.maxHeight = `${alturaSegura}px`;

    const esExpandido = alturaSegura > window.innerHeight * 0.55;
    bottomPanel.classList.toggle("bottom-expanded", esExpandido);
    btnToggleBottomSize.textContent = esExpandido
      ? "⇕ Reducir panel"
      : "⇕ Expandir panel";
  });

  window.addEventListener("mouseup", () => {
    if (!isDragging) return;
    isDragging = false;
    bottomPanel.classList.remove("is-resizing");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
  });
}

function mostrarMensaje(texto, tipo = "error") {
  if (!bottomFeedback) return;
  if (feedbackTimeout) clearTimeout(feedbackTimeout);

  bottomFeedback.className = `bottom-feedback ${
    tipo === "success" ? "feedback-success" : "feedback-error"
  }`;
  bottomFeedback.innerHTML = `
    <span>${tipo === "success" ? "✔" : "⚠"} ${texto}</span>
    <button type="button" class="btn btn-ghost" style="padding:2px 6px;font-size:11px;">✕</button>
  `;
  bottomFeedback.querySelector("button").addEventListener("click", () => {
    bottomFeedback.classList.add("hidden");
  });
  bottomFeedback.classList.remove("hidden");

  feedbackTimeout = setTimeout(() => {
    bottomFeedback.classList.add("hidden");
  }, 6000);
}

function renderizarBarraSuperiorYAlertas(estadoApp) {
  if (!estadoApp.sistema) return;
  const { alertas, penalizado, resumen } = estadoApp.sistema;

  countFixedEl.textContent = String(resumen.total_fijas);
  countCalcEl.textContent = String(resumen.total_calculadas);
  btnToggleCatalog.textContent = `☰ Catálogo de las ${resumen.total_variables} Variables`;

  appShell.classList.toggle("shell-penalized", penalizado);
  legendPenalizedEl.classList.toggle("hidden", !penalizado);

  if (alertas && alertas.length > 0) {
    alertBanner.innerHTML = alertas
      .map((a) => `<div class="alert-banner-item">⚠ ${a}</div>`)
      .join("");
    alertBanner.classList.remove("hidden");
  } else {
    alertBanner.innerHTML = "";
    alertBanner.classList.add("hidden");
  }
}

async function seleccionarVariable(nombre) {
  try {
    const detalle = await fetchDetalleVariable(nombre);
    varKeyboardInput.value = nombre;
    btnClearSelection.classList.remove("hidden");
    store.establecerDetalleVariable(detalle);
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

async function aplicarModificacion(entradas) {
  try {
    const nuevoEstado = await postModificar(entradas);
    store.sistema = nuevoEstado;

    // Si hay una variable abierta en detalle, refrescar su detalle con los nuevos cálculos
    if (store.variableDetalle) {
      const nomActual = store.variableDetalle.variable.nombre;
      store.variableDetalle = await fetchDetalleVariable(nomActual);
    }

    store.notificar();
    mostrarMensaje("Sistema resuelto y actualizado correctamente.", "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

function renderizarTodo(estadoApp) {
  renderizarBarraSuperiorYAlertas(estadoApp);

  renderizarSidebarCategorias(
    categoryList,
    sidebarCount,
    estadoApp,
    (catId) => {
      store.seleccionarCategoria(catId);
      equationsList.scrollTop = 0;
    }
  );

  renderizarSidebarGraficas(
    chartsNavList,
    sidebarChartsCount,
    estadoApp,
    (graficaId) => {
      store.seleccionarGrafica(graficaId);
      chartsList.scrollTop = 0;
    }
  );

  const esVistaGraficas = estadoApp.vistaActiva === "graficas";
  equationsView.classList.toggle("hidden", esVistaGraficas);
  chartsView.classList.toggle("hidden", !esVistaGraficas);

  if (esVistaGraficas) {
    renderizarPanelGraficas(
      chartsHeader,
      chartsList,
      estadoApp,
      (nomVar) => seleccionarVariable(nomVar),
      (graficaId) => {
        store.seleccionarGrafica(graficaId);
        chartsList.scrollTop = 0;
      }
    );
  } else {
    renderizarPanelEcuaciones(
      equationsHeader,
      equationsList,
      estadoApp,
      (nomVar) => seleccionarVariable(nomVar)
    );
  }

  btnToggleCatalog.classList.toggle("active", estadoApp.catalogoAbierto);

  renderizarCatalogoVariables(
    catalogContainer,
    estadoApp,
    (nomVar) => {
      store.catalogoAbierto = false;
      seleccionarVariable(nomVar);
    },
    (nuevoFiltro) => {
      store.filtroCatalogo = nuevoFiltro;
      store.notificar();
    }
  );

  renderizarDetalleVariable(
    variableDetailContainer,
    estadoApp,
    (nomVar) => seleccionarVariable(nomVar),
    aplicarModificacion,
    mostrarMensaje,
    irACategoriaYEcuacion
  );
}

async function iniciarApp() {
  store.suscribir(renderizarTodo);
  inicializarRedimensionPanelInferior();

  inicializarEntradaTeclado(
    varQuickForm,
    varKeyboardInput,
    varAutocomplete,
    () => (store.sistema ? store.sistema.variables : []),
    (nomVar) => seleccionarVariable(nomVar),
    mostrarMensaje
  );

  btnToggleCatalog.addEventListener("click", () => {
    store.alternarCatalogo();
  });

  btnClearSelection.addEventListener("click", () => {
    varKeyboardInput.value = "";
    btnClearSelection.classList.add("hidden");
    store.establecerDetalleVariable(null);
  });

  btnToggleBottomSize.addEventListener("click", () => {
    bottomPanel.style.height = "";
    bottomPanel.style.maxHeight = "";
    const exp = bottomPanel.classList.toggle("bottom-expanded");
    btnToggleBottomSize.textContent = exp ? "⇕ Reducir panel" : "⇕ Expandir panel";
  });

  btnReset.addEventListener("click", async () => {
    try {
      const estadoInicial = await postReiniciar();
      store.sistema = estadoInicial;
      if (store.variableDetalle) {
        store.variableDetalle = await fetchDetalleVariable(
          store.variableDetalle.variable.nombre
        );
      }
      store.notificar();
      mostrarMensaje("Valores restaurados a la calibración inicial.", "success");
    } catch (err) {
      mostrarMensaje(err.message, "error");
    }
  });

  try {
    const estadoInicial = await fetchEstado();
    store.actualizarSistema(estadoInicial);
  } catch (err) {
    mostrarMensaje(`No se pudo cargar el estado inicial: ${err.message}`, "error");
  }
}

iniciarApp();
