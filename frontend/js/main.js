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
  postAnalizarDiseno,
  fetchHistorico,
  postGuardarHistorico,
  deleteHistorico,
  postImportarHistorico,
  postReevaluarHistorico,
} from "./api.js?v=21";
import { store } from "./state.js?v=21";
import {
  renderizarSidebarCategorias,
  renderizarSidebarGraficas,
} from "./components/sidebar.js?v=21";
import {
  renderizarPanelEcuaciones,
  desplazarDentroContenedor,
  resaltarYEncuadrarEcuacion,
} from "./components/equations.js?v=21";
import { renderizarMapaFlujoGlobal } from "./components/flowchart.js?v=21";
import { renderizarPanelDiseno } from "./components/designStudio.js?v=21";
import { renderizarPanelGraficas } from "./components/charts.js?v=21";
import {
  inicializarEntradaTeclado,
  renderizarCatalogoVariables,
  renderizarDetalleVariable,
} from "./components/varInput.js?v=21";

// Referencias a elementos del DOM
const appShell = document.getElementById("app-shell");
const alertBanner = document.getElementById("alert-banner");
const countFixedEl = document.getElementById("count-fixed");
const countCalcEl = document.getElementById("count-calc");
const legendPenalizedEl = document.getElementById("legend-penalized");
const btnOpenDesign = document.getElementById("btn-open-design");
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

const flowView = document.getElementById("flow-view");
const flowHeader = document.getElementById("flow-header");
const flowContent = document.getElementById("flow-content");

const designView = document.getElementById("design-view");
const designHeader = document.getElementById("design-header");
const designContent = document.getElementById("design-content");

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

function restaurarScrollRaiz() {
  if (document.documentElement.scrollTop) document.documentElement.scrollTop = 0;
  if (document.body.scrollTop) document.body.scrollTop = 0;
  if (appShell && appShell.scrollTop) appShell.scrollTop = 0;
}

function irACategoriaYEcuacion(eqData, catIdObjetivo = null) {
  if (!eqData || !store.sistema) return;

  let catId =
    catIdObjetivo !== null && catIdObjetivo !== undefined
      ? catIdObjetivo
      : eqData.categorias && eqData.categorias.length > 0
      ? eqData.categorias[0].id
      : eqData.categoria_id;

  if (catId === undefined || catId === null) {
    const encontrada = store.sistema.categorias.find(
      (c) => c.nombre === eqData.categoria
    );
    catId = encontrada ? encontrada.id : 0;
  }

  store.seleccionarCategoria(catId);

  requestAnimationFrame(() => {
    requestAnimationFrame(() => {
      restaurarScrollRaiz();
      const activeCatBtn = categoryList?.querySelector(".category-btn.active");
      if (activeCatBtn) {
        desplazarDentroContenedor(categoryList, activeCatBtn, "nearest");
      }
      resaltarYEncuadrarEcuacion(equationsList, eqData.nombre);
    });
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
    store.resultadoDiseno = null;

    // Si hay una variable abierta en detalle, refrescar su detalle con los nuevos cálculos
    if (store.variableDetalle) {
      const nomActual = store.variableDetalle.variable.nombre;
      store.variableDetalle = await fetchDetalleVariable(nomActual);
    }

    store.notificar();
    const { base_overrides: _descartarBase, ...payloadFresco } = ultimoPayloadDiseno;
    ultimoPayloadDiseno = payloadFresco;
    if (store.vistaActiva === "diseno") {
      analizarDisenoYCargar(payloadFresco);
    }
    mostrarMensaje("Sistema resuelto y actualizado correctamente.", "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

let ultimoPayloadDiseno = {};

async function analizarDisenoYCargar(payload = {}) {
  ultimoPayloadDiseno = { ...payload };
  store.cargandoDiseno = true;
  store.notificar();
  try {
    const res = await postAnalizarDiseno(payload);
    store.cargandoDiseno = false;
    store.establecerResultadoDiseno(res);
  } catch (err) {
    store.cargandoDiseno = false;
    store.notificar();
    mostrarMensaje(err.message, "error");
  }
}

async function cargarHistorico() {
  try {
    const data = await fetchHistorico();
    store.establecerHistorico(data.registros || []);
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

async function guardarEnHistorico(payload) {
  try {
    const data = await postGuardarHistorico(payload);
    store.establecerHistorico(data.registros || []);
    mostrarMensaje(`Configuración "${payload.nombre}" guardada en el histórico.`, "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

async function eliminarDeHistorico(id) {
  try {
    const data = await deleteHistorico(id);
    store.establecerHistorico(data.registros || []);
    mostrarMensaje("Registro eliminado del histórico.", "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

async function importarEnHistorico(registros) {
  try {
    const data = await postImportarHistorico(registros);
    store.establecerHistorico(data.registros || []);
    mostrarMensaje("Histórico importado correctamente.", "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

async function reevaluarEnHistorico(id) {
  try {
    const data = await postReevaluarHistorico(id);
    store.establecerHistorico(data.registros || []);
    mostrarMensaje("Registro reevaluado en motor v2 como nueva entrada del histórico.", "success");
  } catch (err) {
    mostrarMensaje(err.message, "error");
  }
}

function renderizarTodo(estadoApp) {
  restaurarScrollRaiz();
  renderizarBarraSuperiorYAlertas(estadoApp);

  const abrirMapaFlujo = () => {
    store.seleccionarMapaFlujo();
    if (flowContent) flowContent.scrollTop = 0;
  };
  const abrirCategoria = (catId) => {
    store.seleccionarCategoria(catId);
    equationsList.scrollTop = 0;
  };

  renderizarSidebarCategorias(
    categoryList,
    sidebarCount,
    estadoApp,
    abrirCategoria,
    abrirMapaFlujo
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
  const esVistaFlujo = estadoApp.vistaActiva === "flujo";
  const esVistaDiseno = estadoApp.vistaActiva === "diseno";
  const esVistaEcuaciones = !esVistaGraficas && !esVistaFlujo && !esVistaDiseno;

  btnOpenDesign?.classList.toggle("active", esVistaDiseno);

  equationsView.classList.toggle("hidden", !esVistaEcuaciones);
  chartsView.classList.toggle("hidden", !esVistaGraficas);
  flowView?.classList.toggle("hidden", !esVistaFlujo);
  designView?.classList.toggle("hidden", !esVistaDiseno);

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
  } else if (esVistaFlujo) {
    renderizarMapaFlujoGlobal(flowHeader, flowContent, estadoApp, {
      alClickCategoria: abrirCategoria,
      alClickVariable: (nomVar) => seleccionarVariable(nomVar),
    });
  } else if (esVistaDiseno) {
    renderizarPanelDiseno(designHeader, designContent, estadoApp, {
      alAnalizar: analizarDisenoYCargar,
      alAplicar: aplicarModificacion,
      alGuardarHistorico: guardarEnHistorico,
      alEliminarHistorico: eliminarDeHistorico,
      alImportarHistorico: importarEnHistorico,
      alReevaluarHistorico: reevaluarEnHistorico,
      alMensaje: mostrarMensaje,
      alCambiarPestana: (tab) => {
        store.seleccionarDiseno(tab);
        if (designContent) designContent.scrollTop = 0;
      },
    });
  } else {
    renderizarPanelEcuaciones(
      equationsHeader,
      equationsList,
      estadoApp,
      (nomVar) => seleccionarVariable(nomVar),
      irACategoriaYEcuacion,
      abrirCategoria,
      abrirMapaFlujo
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

  btnOpenDesign?.addEventListener("click", () => {
    store.seleccionarDiseno();
    if (designContent) designContent.scrollTop = 0;
    if (!store.resultadoDiseno) {
      analizarDisenoYCargar(ultimoPayloadDiseno);
    }
    cargarHistorico();
  });

  btnReset.addEventListener("click", async () => {
    try {
      const estadoInicial = await postReiniciar();
      store.sistema = estadoInicial;
      store.resultadoDiseno = null;
      if (store.variableDetalle) {
        store.variableDetalle = await fetchDetalleVariable(
          store.variableDetalle.variable.nombre
        );
      }
      store.notificar();
      const { base_overrides: _descartarBase, ...payloadFresco } = ultimoPayloadDiseno;
      ultimoPayloadDiseno = payloadFresco;
      if (store.vistaActiva === "diseno") {
        analizarDisenoYCargar(payloadFresco);
      }
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
