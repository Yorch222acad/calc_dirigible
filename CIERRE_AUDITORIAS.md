# Cierre del Ciclo de Auditorías (V1–V10) — Dirigible Híbrido v2

**Fecha:** 27 de noviembre de 2026  
**Estado:** Cerrado y verificado sobre el modelo `v2` (`AUDITORIA_MATEMATICA.md` hasta `AUDITORIA_MATEMATICA_V9.md` implementadas y validadas; hallazgos sintéticos de borde de `AUDITORIA_MATEMATICA_V10.md` evaluados y aceptados sin cambios).

---

## 1. Decisión de cierre

Se da por concluido formalmente el ciclo de auditorías matemáticas y funcionales del proyecto sobre la versión **v2** del modelo. Todas las correcciones desde la primera auditoría ([AUDITORIA_MATEMATICA.md](AUDITORIA_MATEMATICA.md)) hasta la novena ([AUDITORIA_MATEMATICA_V9.md](AUDITORIA_MATEMATICA_V9.md)) han sido implementadas, contrastadas numéricamente frente al modelo simbólico en SymPy y cubiertas por pruebas automáticas de regresión tanto en backend ([auditar_modelo.py](auditar_modelo.py)) como en navegador real Chromium ([auditar_frontend.py](auditar_frontend.py)).

Los dos puntos reportados en [AUDITORIA_MATEMATICA_V10.md](AUDITORIA_MATEMATICA_V10.md) no representan fallos físicos ni regresiones de rondas previas, sino casos de borde altamente sintéticos con impacto nulo en el diseño e ingeniería real del dirigible. Por criterio de ingeniería, el código se estabiliza en este punto para evitar complejidad innecesaria sobre esquinas artificiales.

---

## 2. Evolución de la relevancia de los hallazgos (V1–V10)

A lo largo de diez revisiones sucesivas, la naturaleza de los hallazgos siguió una curva clara de rendimientos decrecientes: desde correcciones estructurales indispensables para fabricar el prototipo hasta pruebas de frontera artificiales (*fuzzing*).

### Bloque I · V1–V6: Impacto físico, arquitectónico y operativo alto
Las seis primeras auditorías detectaron y corrigieron errores de fondo que afectaban directamente la validez física del modelo, la factibilidad del hardware y la integridad de los datos publicados:

1. **Geometría prolada y masa real de película (`V1–V2`):** incorporación del área superficial exacta del casco prolado (`Sf + Sr` sin omitir términos geométricos), integración de la piel exterior dentro de `Sc` y soporte sin singularidades numéricas para `0/0`, `1/0` y `0/1` capas celulares.
2. **Modelo térmico regional e Hipótesis B (`V2`, `V6`):** cálculo de energía interna `Q`, precalentamiento `Epre` y capacidad térmica de enfriamiento `Qc`/`tc` distinguiendo el volumen del núcleo (`Vnuc`) y el volumen periférico celular (`Vcel`).
3. **Separación de fases maniobra vs. crucero (`V2`):** evaluación explícita de `Pcruc`, `Tcruc` y `thcruc` además del pico de maniobra en el optimizador, en el evaluador de rango útil y en la comparativa del dron de referencia.
4. **Límites de hardware y cotas mín./máx. exactas (`V3–V6`):** bloqueo del sentido físico de las restricciones de hardware, separación de cotas mínimas y máximas por variable (`mtot`, `Pelec`, `Cop`, `Etot`), búsqueda 1D de fronteras (`brent_1d`) con distinción de estado (`factible`, `vacio`, `inconclusa`) y verificación post-redondeo en intervalos estrechos.
5. **Integridad de histórico, interfaz y E2E (`V3–V6`):** conservación intacta de registros `v1` importados con reevaluación trazable hacia `v2`, bloqueo de botones de guardado a los `pesos` y `cbat_kg` del análisis aprobado, limpieza de `base_overrides` obsoletos, renderizado seguro de `null` en SVG y verificación end-to-end en Chromium con Playwright.

### Bloque II · V7–V9: Refinamientos acotados de consistencia
Estas rondas no descubrieron fallos de física fundamental, sino ajustes de dominio, margen térmico de materiales y coherencia entre rutas de cálculo:

* **V7 (Margen Mylar + Kapton/PET y autonomía):** ajuste del límite editable por defecto a `T2 <= 130 °C` y techo de búsqueda del optimizador a `140 °C`, inclusión de `dm_aut` en el cálculo del intervalo de carga útil, etiqueta explícita de criterios en G7 y exposición dinámica de `dTc` en ficha técnica y documentación.
* **V8 (Presupuesto económico, submétrica y dominio de `e`):** inclusión de `c_recambio` al redimensionar batería en el rango de carga útil, eliminación del recorte mínimo de `1.0 m` para distancias `< 1 m` y rechazo explícito de espesores `e <= 0` (`ValueError` / HTTP `400`).
* **V9 (`Fexc` instalado y bajas velocidades):** cálculo de la reserva vertical `Fexc` con el empuje instalado `N·Tmax1` aunque exista un tope operativo menor sobre `Ttot`, conservación exacta de velocidades `v` pequeñas y rechazo explícito de avance neto `vg = v - vv <= 0` (HTTP `400`).

### Bloque III · V10: Casos sintéticos de borde aceptados sin cambios
La décima auditoría (sin hallazgos de severidad *Alta*) evidenció que el ciclo había entrado en pruebas artificiales alejadas de cualquier escenario operativo real:

1. **Admisión de `nv = 1.5` con banda estrecha de energía (`Etot ∈ [903.78, 905.78] kJ`):** detalle preexistente en la admisión del punto de partida dentro de [diseno.py](diseno.py) cuando el propio usuario introduce manualmente un número fraccionario de viajes (`nv = 1.5`) junto a una ventana de energía de `±1 kJ` calibrada para excluir cualquier entero. En operación real los tramos son enteros (`nv = 1, 2, 3, ...`) y el muestreo del optimizador ya redondea toda variable entera.
2. **Umbral `vg > 0.35 m/s` vs. `0.351 m/s` optimizando solo `dTc`:** condición heurística heredada del optimizador cuando hay variables libres para evitar soluciones degeneradas casi estacionarias, mientras el análisis directo (`ejecutar_optimizador=False`) admite cualquier `vg > 0`. Probar un dirigible de ~6 m recorriendo `0.5 m` a `0.350 m/s` (~`1.26 km/h`) sin viento carece de sentido práctico frente a la envolvente de diseño del prototipo (`vv = 6 m/s`, `v ≈ 8–10 m/s`).

### Criterio de cierre
* **Cero regresiones:** las verificaciones de **V2 a V9** y los **5 recorridos E2E en Chromium** pasan íntegramente tras los últimos cambios.
* **Precisión numérica verificada:** el barrido paramétrico completo contra las 108 ecuaciones simbólicas mantiene un residuo relativo máximo de `4.637e-13` (muy por debajo del umbral `1e-10`).
* **Estabilidad del código:** seguir iterando indefinidamente sobre casos de *fuzzing* sintéticos introduce ramificaciones defensivas sin beneficio para la ingeniería del prototipo.

---

## 3. Estado técnico consolidado al cierre

* **Estructura del modelo (`v2`):** `170` variables, `62` entradas fijas iniciales (`FIJAS_INI`), `108` ecuaciones independientes (`ECUACIONES`), `13` categorías y `7` gráficas paramétricas.
* **Candidato óptimo por defecto (`T2 <= 130 °C`, Mylar + Kapton/PET):**
  * `Score = 48.28` · `T2 = 129.57 °C` · `Pelec = 638.23 W` · `Pcruc = 470.89 W`
  * `Ttot = 12.22 N` · `mbat = 562.7 g` · `Cop = 1.623 Bs` · `Cap. fija = 0.6668–1.0 kg`
* **Referencia histórica calibrada (`T2 <= 95 °C`):**
  * `Score = 43.88` · `Pelec = 639.63 W` · `Pcruc = 450.50 W` · `Ttot = 12.77 N`
  * `θman = 60.26°` · `θcruc = 56.52°` · `mbat = 637.5 g` · `Epre = 1651.0 kJ` · `Cop = 2.047 Bs` · `Cap. fija = 0.6716–1.0 kg`
* **Enfriamiento regional (Hipótesis B en configuración base):**
  * `Qc = 264.77 kJ` y `tc = 158.0 s` para caída admisible `dTc = 20 K` (`72.4 s` para `dTc = 10 K`).
* **Comandos de verificación continua:**
  ```bash
  ./venv_sus_d/bin/python -u auditar_modelo.py
  ./venv_sus_d/bin/python -u auditar_frontend.py
  ```

---

## 4. Consolidación posterior al cierre (diseño definitivo `def`)

Sobre el modelo `v2` estabilizado arriba se cerraron las especificaciones constructivas reales y toda la documentación técnica del proyecto:

* **Diseño definitivo (`def`):** [historico_dirigible_2026-11-27_def.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json) (`1/1` capa, manta comercial medida de `59 g` / `12 µm` / `σ = 17.0 g/m²` / `ε = 0.08`, uniones con cinta de poliéster térmico + Kapton contabilizadas en `mad = 1.30 kg`, `T2 = 114.8 °C`, `Pelec = 637.0 W`, `mbat = 494.2 g`, `Cop = 2.553 Bs`).
* **Macros CAD SolidWorks:** dirigible definitivo ([dirigible_solidworks_referencial_2026-11-27_def.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas)), calentador eléctrico compacto en tierra con recirculación ([calentador_tierra_solidworks_referencial_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_tierra_solidworks_referencial_v2.bas)) y calentador aéreo monotubo simplificado de etanol ([calentador_etanol_simple_solidworks_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas)).
* **Documentación sincronizada:** [README.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/README.md), [texto.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/texto.md), [ESTADO_ACTUAL_Y_CALENTADOR.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/ESTADO_ACTUAL_Y_CALENTADOR.md), [RESUMEN_FINAL_DISENO.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/RESUMEN_FINAL_DISENO.md) y [PRESUPUESTO_Y_PESO_FABRICACION.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/PRESUPUESTO_Y_PESO_FABRICACION.md).
