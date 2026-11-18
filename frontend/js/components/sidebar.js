/**
 * sidebar.js — Componente del panel izquierdo dividido en dos secciones con scroll propio:
 *   1. Arriba: Categorías de ecuaciones
 *   2. Abajo: Gráficas comparativas de las variables de interés
 */

export function renderizarSidebarCategorias(
  contenedorLista,
  contadorHeader,
  estadoApp,
  alSeleccionarCategoria
) {
  if (!estadoApp.sistema) return;

  const { categorias, resumen } = estadoApp.sistema;
  if (contadorHeader) {
    contadorHeader.textContent = `${resumen.total_categorias} bloques · ${resumen.total_ecuaciones} ec.`;
  }

  contenedorLista.innerHTML = "";
  const esVistaEcuaciones = estadoApp.vistaActiva === "ecuaciones";

  // Botón para cada una de las categorías
  categorias.forEach((cat) => {
    const activo = esVistaEcuaciones && estadoApp.categoriaActivaId === cat.id;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `category-btn ${activo ? "active" : ""}`;

    const labelDiv = document.createElement("div");
    labelDiv.className = "category-btn-label";

    const idxSpan = document.createElement("span");
    idxSpan.className = "category-index";
    idxSpan.textContent = `C${cat.id + 1}.`;

    const nameSpan = document.createElement("span");
    nameSpan.className = "category-name";
    nameSpan.textContent = cat.nombre;

    labelDiv.appendChild(idxSpan);
    labelDiv.appendChild(nameSpan);

    const metaDiv = document.createElement("div");
    metaDiv.className = "category-meta";

    if (cat.tiene_penalizada) {
      const alertDot = document.createElement("span");
      alertDot.className = "category-alert-dot";
      alertDot.title = "Contiene variables de sustentación penalizadas en negativo";
      metaDiv.appendChild(alertDot);
    }

    const countPill = document.createElement("span");
    countPill.className = "category-count-pill";
    countPill.textContent = `${cat.num_ecuaciones}`;
    countPill.title = `${cat.num_ecuaciones} ecuaciones`;
    metaDiv.appendChild(countPill);

    btn.appendChild(labelDiv);
    btn.appendChild(metaDiv);

    btn.addEventListener("click", () => alSeleccionarCategoria(cat.id));
    contenedorLista.appendChild(btn);
  });

  // Separador y opción para ver todas las categorías juntas
  const sep = document.createElement("hr");
  sep.style.border = "none";
  sep.style.borderTop = "1px solid var(--border-subtle)";
  sep.style.margin = "4px 0";
  contenedorLista.appendChild(sep);

  const activoTodas = esVistaEcuaciones && estadoApp.categoriaActivaId === "all";
  const btnAll = document.createElement("button");
  btnAll.type = "button";
  btnAll.className = `category-btn ${activoTodas ? "active" : ""}`;
  btnAll.innerHTML = `
    <div class="category-btn-label">
      <span class="category-index">★</span>
      <span class="category-name">Ver todas las categorías</span>
    </div>
    <div class="category-meta">
      <span class="category-count-pill">${resumen.total_ecuaciones}</span>
    </div>
  `;
  btnAll.addEventListener("click", () => alSeleccionarCategoria("all"));
  contenedorLista.appendChild(btnAll);
}

export function renderizarSidebarGraficas(
  contenedorLista,
  contadorHeader,
  estadoApp,
  alSeleccionarGrafica
) {
  if (!estadoApp.sistema || !estadoApp.sistema.graficas) return;

  const graficas = estadoApp.sistema.graficas;
  if (contadorHeader) {
    contadorHeader.textContent = `${graficas.length} comparativas`;
  }

  contenedorLista.innerHTML = "";
  const esVistaGraficas = estadoApp.vistaActiva === "graficas";

  graficas.forEach((graf) => {
    const activo = esVistaGraficas && estadoApp.graficaActivaId === graf.id;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `category-btn chart-nav-btn ${activo ? "active chart-active" : ""}`;
    btn.title = graf.titulo;

    const labelDiv = document.createElement("div");
    labelDiv.className = "category-btn-label";

    const idxSpan = document.createElement("span");
    idxSpan.className = "category-index";
    idxSpan.textContent = `G${graf.indice}.`;

    const nameSpan = document.createElement("span");
    nameSpan.className = "category-name";
    nameSpan.textContent = graf.titulo_corto || graf.titulo;

    labelDiv.appendChild(idxSpan);
    labelDiv.appendChild(nameSpan);

    const metaDiv = document.createElement("div");
    metaDiv.className = "category-meta";

    const countPill = document.createElement("span");
    countPill.className = "category-count-pill";
    countPill.textContent = `${graf.variables.length}v`;
    countPill.title = `${graf.variables.length} variables comparadas`;
    metaDiv.appendChild(countPill);

    btn.appendChild(labelDiv);
    btn.appendChild(metaDiv);

    btn.addEventListener("click", () => alSeleccionarGrafica(graf.id));
    contenedorLista.appendChild(btn);
  });

  // Separador y opción para ver todas las gráficas juntas
  const sep = document.createElement("hr");
  sep.style.border = "none";
  sep.style.borderTop = "1px solid var(--border-subtle)";
  sep.style.margin = "4px 0";
  contenedorLista.appendChild(sep);

  const activoTodas = esVistaGraficas && estadoApp.graficaActivaId === "all";
  const btnAll = document.createElement("button");
  btnAll.type = "button";
  btnAll.className = `category-btn chart-nav-btn ${activoTodas ? "active chart-active" : ""}`;
  btnAll.innerHTML = `
    <div class="category-btn-label">
      <span class="category-index">★</span>
      <span class="category-name">Ver todas las gráficas</span>
    </div>
    <div class="category-meta">
      <span class="category-count-pill">${graficas.length}</span>
    </div>
  `;
  btnAll.addEventListener("click", () => alSeleccionarGrafica("all"));
  contenedorLista.appendChild(btnAll);
}
