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
} from "./api.js";
import { store } from "./state.js";
import { renderizarSidebarCategorias } from "./components/sidebar.js";
import { renderizarPanelEcuaciones } from "./components/equations.js";
import {
  inicializarEntradaTeclado,
  renderizarCatalogoVariables,
  renderizarDetalleVariable,
} from "./components/varInput.js";

// Referencias a elementos del DOM
const appShell = document.getElementById("app-shell");
const alertBanner = document.getElementById("alert-banner");
const countFixedEl = document.getElementById("count-fixed");
const countCalcEl = document.getElementById("count-calc");
const legendPenalizedEl = document.getElementById("legend-penalized");
const btnReset = document.getElementById("btn-reset");

const sidebarCount = document.getElementById("sidebar-count");
const categoryList = document.getElementById("category-list");
const equationsHeader = document.getElementById("equations-header");
const equationsList = document.getElementById("equations-list");

const bottomPanel = document.getElementById("bottom-panel");
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

  renderizarPanelEcuaciones(
    equationsHeader,
    equationsList,
    estadoApp,
    (nomVar) => seleccionarVariable(nomVar)
  );

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
    mostrarMensaje
  );
}

async function iniciarApp() {
  store.suscribir(renderizarTodo);

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
