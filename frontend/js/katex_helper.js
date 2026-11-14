/**
 * katex_helper.js — Renderizador seguro de fórmulas matemáticas con KaTeX.
 */

export function renderizarFormulaKaTeX(contenedor, codigoLatex, intento = 0) {
  if (!contenedor) return;

  if (window.katex) {
    try {
      window.katex.render(codigoLatex, contenedor, {
        displayMode: true,
        throwOnError: false,
        strict: false,
        trust: true,
      });
      return;
    } catch (err) {
      console.warn("Error al renderizar KaTeX:", err);
      contenedor.textContent = codigoLatex;
      return;
    }
  }

  if (intento < 25) {
    setTimeout(() => {
      renderizarFormulaKaTeX(contenedor, codigoLatex, intento + 1);
    }, 100);
  } else {
    contenedor.textContent = codigoLatex;
  }
}
