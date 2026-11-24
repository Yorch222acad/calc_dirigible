/**
 * state.js — Almacén de estado centralizado y reactivo del frontend.
 */

export const store = {
  sistema: null,              // Respuesta completa de /api/estado
  vistaActiva: "ecuaciones",  // "ecuaciones" | "graficas" | "flujo" | "simulacion"
  categoriaActivaId: 0,       // Índice de categoría seleccionada (o "all" para ver todas)
  graficaActivaId: "esbeltez",// ID de la gráfica seleccionada (o "all" para ver todas)
  variableDetalle: null,      // Respuesta de /api/variable/{nombre}
  resultadoOptimizacion: null,// Último resultado de POST /api/optimizar
  catalogoAbierto: false,     // Si el catálogo de variables está visible
  filtroCatalogo: "all",      // "all" | "fixed" | "calc"
  listeners: new Set(),

  suscribir(fn) {
    this.listeners.add(fn);
    return () => this.listeners.delete(fn);
  },

  notificar() {
    for (const fn of this.listeners) {
      fn(this);
    }
  },

  actualizarSistema(nuevoSistema) {
    this.sistema = nuevoSistema;
    this.resultadoOptimizacion = null;
    this.notificar();
  },

  seleccionarCategoria(catId) {
    this.vistaActiva = "ecuaciones";
    this.categoriaActivaId = catId;
    this.notificar();
  },

  seleccionarGrafica(graficaId) {
    this.vistaActiva = "graficas";
    this.graficaActivaId = graficaId;
    this.notificar();
  },

  seleccionarMapaFlujo() {
    this.vistaActiva = "flujo";
    this.notificar();
  },

  seleccionarSimulacion() {
    this.vistaActiva = "simulacion";
    this.notificar();
  },

  establecerResultadoOptimizacion(res) {
    this.resultadoOptimizacion = res;
    this.notificar();
  },

  establecerDetalleVariable(detalle) {
    this.variableDetalle = detalle;
    this.notificar();
  },

  alternarCatalogo(forzar = null) {
    this.catalogoAbierto = forzar !== null ? forzar : !this.catalogoAbierto;
    this.notificar();
  },
};
