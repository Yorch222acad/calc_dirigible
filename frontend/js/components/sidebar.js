/**
 * sidebar.js — Componente del panel izquierdo para navegación por categorías.
 */

export function renderizarSidebarCategorias(contenedorLista, contadorHeader, estadoApp, alSeleccionarCategoria) {
  if (!estadoApp.sistema) return;

  const { categorias, resumen } = estadoApp.sistema;
  if (contadorHeader) {
    contadorHeader.textContent = `${resumen.total_categorias} bloques · ${resumen.total_ecuaciones} ec.`;
  }

  contenedorLista.innerHTML = "";

  // Botón para cada una de las 11 categorías
  categorias.forEach((cat) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = `category-btn ${estadoApp.categoriaActivaId === cat.id ? "active" : ""}`;

    const labelDiv = document.createElement("div");
    labelDiv.className = "category-btn-label";

    const idxSpan = document.createElement("span");
    idxSpan.className = "category-index";
    idxSpan.textContent = `${cat.id + 1}.`;

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

  const btnAll = document.createElement("button");
  btnAll.type = "button";
  btnAll.className = `category-btn ${estadoApp.categoriaActivaId === "all" ? "active" : ""}`;
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
