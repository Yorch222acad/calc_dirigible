/**
 * state.js — Almacén de estado centralizado y reactivo del frontend.
 */

export const store = {
  sistema: null,              // Respuesta completa de /api/estado
  categoriaActivaId: 0,       // Índice de categoría seleccionada (o "all" para ver todas)
  variableDetalle: null,      // Respuesta de /api/variable/{nombre}
  catalogoAbierto: false,     // Si el catálogo de 102 variables está visible
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
    this.notificar();
  },

  seleccionarCategoria(catId) {
    this.categoriaActivaId = catId;
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
