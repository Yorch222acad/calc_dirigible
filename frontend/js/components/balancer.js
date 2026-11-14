/**
 * balancer.js — Módulo de modificación de variables y Asistente de Equilibrio Matemático.
 *
 * Exporta al frontend toda la lógica de `modificar()` y `_equilibrar_sistema()` de `calc.py`:
 * - Si la variable seleccionada es FIJA (amarilla): permite cambiar su valor numérico directo,
 *   o liberarla eligiendo qué variable calculada (verde) volver fija (por teclado o clic).
 * - Si la variable seleccionada es CALCULADA (verde): permite asignarle un valor fijo y
 *   elegir qué variable fija (amarilla) liberar (por teclado o clic).
 * - Si el cambio involucra múltiples variables, guía paso a paso mostrando cuántas y cuáles
 *   variables faltan por fijar o liberar según el grafo bipartito (`/api/equilibrio`).
 */

import { postEquilibrio } from "../api.js";

export function renderizarAsistenteModificacion(
  contenedor,
  detalleVar,
  sistemaActual,
  alAplicarModificacion,
  mostrarMensaje
) {
  const { variable, candidatas } = detalleVar;
  const mapaVars = new Map(sistemaActual.variables.map((v) => [v.nombre, v]));

  // Estado local de la transacción de equilibrio (idéntico a nuevas_fijas, entradas, protegidas en calc.py)
  let nuevasFijas = new Set(sistemaActual.fijas);
  let entradas = {};
  sistemaActual.variables.forEach((v) => {
    if (nuevasFijas.has(v.nombre)) {
      entradas[v.nombre] = v.valor;
    }
  });
  let protegidas = new Set([variable.nombre]);
  let enModoEquilibrio = false;
  let esperandoValorParaFijar = null; // nombre de variable calculada pendiente de confirmar valor

  function renderVistaInicial() {
    contenedor.innerHTML = "";
    contenedor.className = "balancer-box";

    if (variable.fija) {
      renderVistaInicialFija();
    } else {
      renderVistaInicialCalculada();
    }
  }

  // -------------------------------------------------------------
  // Caso 1: La variable seleccionada es FIJA (amarilla)
  // -------------------------------------------------------------
  function renderVistaInicialFija() {
    const formRow = document.createElement("form");
    formRow.className = "balancer-action-row";
    formRow.innerHTML = `
      <label class="candidates-section-title">
        Acción para <span class="text-fixed">${variable.nombre}</span> (FIJA):
      </label>
      <div class="balancer-input-group">
        <input
          type="text"
          id="input-accion-fija"
          class="balancer-number-input"
          style="width: 310px;"
          placeholder="Nuevo valor (ej. ${variable.valor}) o variable verde / 'liberar'"
          value="${variable.valor}"
        />
        <button type="submit" class="btn btn-primary">
          Aplicar valor o comando (Enter)
        </button>
        <button type="button" id="btn-liberar-directo" class="btn btn-warning">
          🔓 Liberar '${variable.nombre}' (volverla calculada)
        </button>
      </div>
    `;

    formRow.addEventListener("submit", async (e) => {
      e.preventDefault();
      const raw = formRow.querySelector("#input-accion-fija").value.trim();
      if (!raw) return;

      // ¿Es un número para cambiar directamente el valor de la variable fija?
      const num = Number(raw);
      if (!Number.isNaN(num) && raw !== "") {
        entradas[variable.nombre] = num;
        await alAplicarModificacion(entradas);
        return;
      }

      // El usuario escribió 'liberar' o el nombre de otra variable (igual que en calc.py)
      nuevasFijas.delete(variable.nombre);
      delete entradas[variable.nombre];

      if (raw.toLowerCase() !== "liberar" && raw.toLowerCase() !== "l") {
        if (!mapaVars.has(raw)) {
          mostrarMensaje(`Entrada no válida o variable desconocida: '${raw}'`, "error");
          reiniciarBorrador();
          return;
        }
        if (nuevasFijas.has(raw)) {
          // Liberó una segunda variable fija además de `variable.nombre`
          nuevasFijas.delete(raw);
          delete entradas[raw];
          protegidas.add(raw);
        } else {
          // Eligió una variable calculada para volverla fija: pedir su valor
          esperandoValorParaFijar = raw;
          renderPedirValorFijo(raw);
          return;
        }
      }

      enModoEquilibrio = true;
      await actualizarPasoEquilibrio();
    });

    formRow.querySelector("#btn-liberar-directo").addEventListener("click", async () => {
      nuevasFijas.delete(variable.nombre);
      delete entradas[variable.nombre];
      enModoEquilibrio = true;
      await actualizarPasoEquilibrio();
    });

    contenedor.appendChild(formRow);

    // Tabla de candidatas calculadas (verdes) que se pueden volver fijas si se libera `variable.nombre`
    const candTitle = document.createElement("div");
    candTitle.className = "candidates-section-title";
    candTitle.innerHTML = `
      Variables calculadas (<span class="text-calc">verdes</span>) que se pueden volver fijas si liberas
      <span class="text-fixed">${variable.nombre}</span> (${candidatas.length} disponibles — haz clic en una o escríbela arriba):
    `;
    contenedor.appendChild(candTitle);

    if (candidatas.length > 0) {
      contenedor.appendChild(
        crearRejillaCandidatas(candidatas, "green", (candNombre) => {
          nuevasFijas.delete(variable.nombre);
          delete entradas[variable.nombre];
          esperandoValorParaFijar = candNombre;
          renderPedirValorFijo(candNombre);
        })
      );
    } else {
      const emptyMsg = document.createElement("div");
      emptyMsg.className = "text-penalized";
      emptyMsg.textContent = "Ninguna variable calculada individual permite liberar esta variable directamente (usa el botón Liberar para intercambio múltiple).";
      contenedor.appendChild(emptyMsg);
    }
  }

  // -------------------------------------------------------------
  // Caso 2: La variable seleccionada es CALCULADA (verde)
  // -------------------------------------------------------------
  function renderVistaInicialCalculada() {
    const formRow = document.createElement("form");
    formRow.className = "balancer-action-row";
    formRow.innerHTML = `
      <label class="candidates-section-title">
        Fijar <span class="text-calc">${variable.nombre}</span> (CALCULADA → FIJA) con valor (${variable.unidad}):
      </label>
      <div class="balancer-input-group">
        <input
          type="number"
          step="any"
          id="input-nuevo-fijo-calc"
          class="balancer-number-input"
          value="${variable.valor}"
          required
        />
        <span style="color: var(--text-muted); font-size: 12px;">
          Actual: ${variable.valor_ing}
        </span>
        <button type="submit" class="btn btn-primary">
          Fijar valor y abrir asistente de equilibrio (Enter)
        </button>
      </div>
    `;

    formRow.addEventListener("submit", async (e) => {
      e.preventDefault();
      const valStr = formRow.querySelector("#input-nuevo-fijo-calc").value.trim();
      const num = Number(valStr);
      if (Number.isNaN(num)) {
        mostrarMensaje("Valor numérico inválido.", "error");
        return;
      }
      nuevasFijas.add(variable.nombre);
      entradas[variable.nombre] = num;
      enModoEquilibrio = true;
      await actualizarPasoEquilibrio();
    });

    contenedor.appendChild(formRow);

    const candTitle = document.createElement("div");
    candTitle.className = "candidates-section-title";
    candTitle.innerHTML = `
      Variables fijas (<span class="text-fixed">amarillas</span>) que se pueden liberar (volver calculadas) al fijar
      <span class="text-calc">${variable.nombre}</span> (${candidatas.length} disponibles — haz clic directo para intercambiar):
    `;
    contenedor.appendChild(candTitle);

    if (candidatas.length > 0) {
      contenedor.appendChild(
        crearRejillaCandidatas(candidatas, "yellow", async (fijaALiberar) => {
          const valInput = formRow.querySelector("#input-nuevo-fijo-calc");
          const num = Number(valInput ? valInput.value : variable.valor);
          if (Number.isNaN(num)) {
            mostrarMensaje("Ingresa un valor numérico válido primero.", "error");
            return;
          }
          nuevasFijas.add(variable.nombre);
          entradas[variable.nombre] = num;
          nuevasFijas.delete(fijaALiberar);
          delete entradas[fijaALiberar];
          protegidas.add(fijaALiberar);
          await actualizarPasoEquilibrio();
        })
      );
    } else {
      const emptyMsg = document.createElement("div");
      emptyMsg.className = "text-penalized";
      emptyMsg.textContent = "Ninguna variable fija individual permite despejar esta variable directamente.";
      contenedor.appendChild(emptyMsg);
    }
  }

  // -------------------------------------------------------------
  // Sub-vista: Pedir valor numérico para una variable calculada que pasa a fija
  // (Equivalente a `_pedir_valor_fijo` en `calc.py`)
  // -------------------------------------------------------------
  function renderPedirValorFijo(nomVar) {
    const info = mapaVars.get(nomVar);
    contenedor.innerHTML = "";
    contenedor.className = "balancer-box balancer-pending";

    const form = document.createElement("form");
    form.className = "balancer-action-row";
    form.innerHTML = `
      <div class="candidates-section-title">
        Valor fijo para <span class="text-calc">${info.nombre}</span> (${info.descripcion})
        [actual: <strong>${info.valor} ${info.unidad}</strong> (${info.valor_ing}) | Enter = mantener actual]:
      </div>
      <div class="balancer-input-group">
        <input
          type="number"
          step="any"
          id="input-confirmar-fijo"
          class="balancer-number-input"
          value="${info.valor}"
        />
        <button type="submit" class="btn btn-success">Confirmar valor (Enter)</button>
        <button type="button" id="btn-cancelar-paso" class="btn btn-ghost">Cancelar</button>
      </div>
    `;

    form.addEventListener("submit", async (e) => {
      e.preventDefault();
      const raw = form.querySelector("#input-confirmar-fijo").value.trim();
      const valFinal = raw === "" ? info.valor : Number(raw);
      if (Number.isNaN(valFinal)) {
        mostrarMensaje("Valor numérico inválido.", "error");
        return;
      }
      nuevasFijas.add(nomVar);
      entradas[nomVar] = valFinal;
      protegidas.add(nomVar);
      esperandoValorParaFijar = null;
      await actualizarPasoEquilibrio();
    });

    form.querySelector("#btn-cancelar-paso").addEventListener("click", () => {
      reiniciarBorrador();
    });

    contenedor.appendChild(form);
    const inp = form.querySelector("#input-confirmar-fijo");
    if (inp) {
      inp.focus();
      inp.select();
    }
  }

  // -------------------------------------------------------------
  // Asistente paso a paso de equilibrio matemático (`_equilibrar_sistema`)
  // -------------------------------------------------------------
  async function actualizarPasoEquilibrio() {
    try {
      const eqState = await postEquilibrio(Array.from(nuevasFijas), Array.from(protegidas));

      if (eqState.equilibrado) {
        await alAplicarModificacion(entradas);
        return;
      }

      contenedor.innerHTML = "";
      contenedor.className = "balancer-box balancer-pending";

      // Caso A: Faltan variables calculadas por volver fijas
      if (eqState.faltan_fijar > 0) {
        const plural = eqState.faltan_fijar > 1 ? "s" : "";
        const header = document.createElement("div");
        header.className = "candidates-section-title text-fixed";
        header.textContent = `⚖ Equilibrio Matemático — Falta${eqState.faltan_fijar > 1 ? "n" : ""} ${eqState.faltan_fijar} variable${plural} calculada${plural} (verde${plural}) por volver fija${plural} para lograr el sentido matemático:`;
        contenedor.appendChild(header);

        const form = document.createElement("form");
        form.className = "balancer-action-row";
        form.innerHTML = `
          <div class="balancer-input-group">
            <input
              type="text"
              id="input-paso-eq"
              class="balancer-number-input"
              style="width: 340px;"
              placeholder="Escribe variable calculada a fijar (o fija a liberar)..."
            />
            <button type="submit" class="btn btn-primary">Siguiente paso (Enter)</button>
            <button type="button" id="btn-cancelar-eq" class="btn btn-ghost">Cancelar operación</button>
          </div>
        `;

        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const eleccion = form.querySelector("#input-paso-eq").value.trim();
          if (!eleccion) {
            reiniciarBorrador();
            return;
          }
          await procesarEleccionEquilibrio(eleccion, "fijar");
        });

        form.querySelector("#btn-cancelar-eq").addEventListener("click", reiniciarBorrador);
        contenedor.appendChild(form);

        if (eqState.candidatas_fijar.length > 0) {
          contenedor.appendChild(
            crearRejillaCandidatas(eqState.candidatas_fijar, "green", (candNombre) => {
              procesarEleccionEquilibrio(candNombre, "fijar");
            })
          );
        }

        const inp = form.querySelector("#input-paso-eq");
        if (inp) inp.focus();
        return;
      }

      // Caso B: Faltan variables fijas por liberar (volver calculadas)
      if (eqState.faltan_liberar > 0) {
        const plural = eqState.faltan_liberar > 1 ? "s" : "";
        const header = document.createElement("div");
        header.className = "candidates-section-title text-fixed";
        header.textContent = `⚖ Equilibrio Matemático — Falta${eqState.faltan_liberar > 1 ? "n" : ""} ${eqState.faltan_liberar} variable${plural} fija${plural} (amarilla${plural}) por liberar (volver calculada${plural}) para lograr el sentido matemático:`;
        contenedor.appendChild(header);

        const form = document.createElement("form");
        form.className = "balancer-action-row";
        form.innerHTML = `
          <div class="balancer-input-group">
            <input
              type="text"
              id="input-paso-eq"
              class="balancer-number-input"
              style="width: 340px;"
              placeholder="Escribe variable fija a liberar (o calculada a fijar)..."
            />
            <button type="submit" class="btn btn-primary">Siguiente paso (Enter)</button>
            <button type="button" id="btn-cancelar-eq" class="btn btn-ghost">Cancelar operación</button>
          </div>
        `;

        form.addEventListener("submit", async (e) => {
          e.preventDefault();
          const eleccion = form.querySelector("#input-paso-eq").value.trim();
          if (!eleccion) {
            reiniciarBorrador();
            return;
          }
          await procesarEleccionEquilibrio(eleccion, "liberar");
        });

        form.querySelector("#btn-cancelar-eq").addEventListener("click", reiniciarBorrador);
        contenedor.appendChild(form);

        if (eqState.candidatas_liberar.length > 0) {
          contenedor.appendChild(
            crearRejillaCandidatas(eqState.candidatas_liberar, "yellow", (candNombre) => {
              procesarEleccionEquilibrio(candNombre, "liberar");
            })
          );
        }

        const inp = form.querySelector("#input-paso-eq");
        if (inp) inp.focus();
      }
    } catch (err) {
      mostrarMensaje(err.message, "error");
      reiniciarBorrador();
    }
  }

  async function procesarEleccionEquilibrio(eleccion, modoPrincipal) {
    if (!mapaVars.has(eleccion)) {
      mostrarMensaje(`Variable desconocida: '${eleccion}'`, "error");
      return;
    }
    if (protegidas.has(eleccion)) {
      mostrarMensaje(`'${eleccion}' ya fue modificada en este paso.`, "error");
      return;
    }

    if (modoPrincipal === "fijar") {
      if (nuevasFijas.has(eleccion)) {
        // El usuario decidió liberar una variable fija adicional
        nuevasFijas.delete(eleccion);
        delete entradas[eleccion];
        protegidas.add(eleccion);
        mostrarMensaje(`Se liberó la variable fija '${eleccion}' (pasa a ser calculada).`, "success");
        await actualizarPasoEquilibrio();
      } else {
        renderPedirValorFijo(eleccion);
      }
    } else {
      if (!nuevasFijas.has(eleccion)) {
        // El usuario decidió fijar otra variable calculada adicional
        renderPedirValorFijo(eleccion);
      } else {
        nuevasFijas.delete(eleccion);
        delete entradas[eleccion];
        protegidas.add(eleccion);
        await actualizarPasoEquilibrio();
      }
    }
  }

  function reiniciarBorrador() {
    nuevasFijas = new Set(sistemaActual.fijas);
    entradas = {};
    sistemaActual.variables.forEach((v) => {
      if (nuevasFijas.has(v.nombre)) {
        entradas[v.nombre] = v.valor;
      }
    });
    protegidas = new Set([variable.nombre]);
    enModoEquilibrio = false;
    esperandoValorParaFijar = null;
    renderVistaInicial();
  }

  renderVistaInicial();
}

/**
 * Construye una rejilla a 2 columnas con las variables candidatas (igual que `_tabla_candidatas` en calc.py).
 */
function crearRejillaCandidatas(listaCandidatas, color, alElegir) {
  const grid = document.createElement("div");
  grid.className = "candidates-grid";

  const colorClass = color === "yellow" ? "text-fixed" : "text-calc";

  listaCandidatas.forEach((c) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "candidate-item-btn";
    btn.title = `Seleccionar '${c.nombre}' (${c.descripcion})`;
    btn.innerHTML = `
      <span class="candidate-code ${colorClass}">${c.nombre}</span>
      <span>=</span>
      <span class="candidate-val">${c.valor_ing}</span>
      <span class="candidate-desc">— ${c.descripcion}</span>
    `;
    btn.addEventListener("click", () => alElegir(c.nombre));
    grid.appendChild(btn);
  });

  return grid;
}
