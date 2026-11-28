# Estado Final del Desarrollo — Dirigible Híbrido y Calentador en Tierra

Documento de cierre y síntesis del estado actual del proyecto tras la revisión integral del código/documentación y la definición de la arquitectura final del **calentador en tierra**.

---

## 1. Estado del Núcleo Matemático y Plataforma de Software

* **Modelo consolidado (`v2`):** Sistema simbólico-numérico de **170 variables**, **62 entradas fijas iniciales (`FIJAS_INI`)**, **108 ecuaciones independientes (`ECUACIONES_DEF`)** y **13 categorías (`C1–C13`)** en [modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py), con evaluador rápido en `float` puro en [evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py) y optimizador multi-criterio en [diseno.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/diseno.py).
* **Auditorías cerradas (V1–V10):** El ciclo de auditorías matemáticas y funcionales quedó formalmente cerrado en [CIERRE_AUDITORIAS.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/CIERRE_AUDITORIAS.md), cubierto por las suites [auditar_modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/auditar_modelo.py) y [auditar_frontend.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/auditar_frontend.py).
* **Interfaces activas:** Aplicación web FastAPI ([app.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/app.py) + [frontend/index.html](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/frontend/index.html)) con 7 gráficas (`G1–G7`), diagramas de flujo interactivos y estudio de diseño; además de la consola CLI ([calc.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/calc.py)).

---

## 2. Diseño Definitivo del Dirigible (`def`)

Calibrado para **La Paz (~3,350 m s.n.m., $P_1 = 67.12\text{ kPa}$, viento en contra $v_v = 6.0\text{ m/s}$)** con la manta térmica comercial pesada (`59 g` en `3.36 m²` $\rightarrow$ `ep = 12 µm`, `σ = 17.0 g/m²`, `ε = 0.08`, uniones de poliéster térmico/Kapton):

* **Archivo de configuración:** [historico_dirigible_2026-11-27_def.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json) (`id = f53b37f3b5`, **Score `42.01`**, `0` alertas).
* **Macro CAD 3D (SolidWorks):** [dirigible_solidworks_referencial_2026-11-27_def.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas).
* **Parámetros principales:**
  * **Casco:** `L = 8.083 m × D = 2.275 m` (`V = 21.90 m³`, `λ = 3.55`, `cf = 2.829 m`, `cr = 5.254 m`).
  * **Aislamiento:** **`1/1` capa simétrica** (`e = 29.1 mm`, `Sc = 107.45 m²`, `mc = 1,826.7 g`). No se usan más capas porque con `17.0 g/m²` el peso extra dispara el volumen y excede los `640 W` de los motores.
  * **Térmica:** `T₂ = 114.8 °C`, `Qp = 6,454.6 W` (`69.5 %` de ahorro frente al casco sin celdas), `U = 1.379 W/(m²·K)`, tiempo de enfriamiento pasivo `tc = 44.7 s` (`dTc = 20 K`).
  * **Propulsión y masas (`4 × A2212`, misión `2 × 270 m = 540 m`):** `mflot = 4.460 kg` (`88.5 %` aire caliente), `mres = 0.581 kg`, `mcarga = 1.10 kg`, `mtot = 5.041 kg`, `Pelec = 637.0 W` (`Pcruc = 449.8 W`), `Ttot = 12.91 N` (`Tcruc = 9.94 N`), `θ = 59.2° / 55.2°`, `mbat = 494.2 g`, `Fexc = +13.32 N`.
  * **Energía y costos:** `Q = 1,291.4 kJ` (`Epre = 1,986.8 kJ`), combustible aéreo etanol `mgm = 113.12 g` (`mp = 131.7 g`), costo operativo `Cop = 2.553 Bs`.

---

## 3. Decisión Final sobre el Calentador en Tierra

Respecto al subsistema de precalentamiento previo al despegue, se descartó usar quemadores a GLP o combustión directa en tierra, estableciendo la arquitectura definitiva:

* **Principio de funcionamiento:** **Calentador eléctrico compacto en tierra con recirculación cerrada de aire** (calienta aire únicamente con resistencias eléctricas y aire limpio, sin gases de combustión ni llama).
* **Régimen operativo estimado:** potencia eléctrica de **`~4.5–6.5 kW`** para aportar los `Epre = 1,986.8 kJ` (`~0.55 kWh`, `Q = 1,291.4 kJ` útiles con `ηpre = 0.65`) en un rango aproximado de **`5–8 minutos`**, con un costo eléctrico de `Cpre = 0.477 Bs` (`cpre = 0.24 Bs/MJ ≈ 0.85 Bs/kWh`) y **`0 g`** de peso a bordo.
* **Ciclo de operación con dos válvulas en el dirigible (inicio desinflado):**
  1. **Inflado inicial:** El dirigible parte desinflado. Se abre la **compuerta trasera de aire fresco** del calentador para succionar aire ambiente, pasarlo por el banco de resistencias e inyectarlo por la **válvula de entrada** hasta llenar el casco.
  2. **Recirculación en lazo cerrado:** Para no desperdiciar energía ni enviar aire excesivamente caliente que dañe la manta de `12 µm`, el aire que pierde temperatura en el casco sale por una **segunda válvula (retorno)**, reingresa al calentador, se mezcla y vuelve a pasar por el ventilador y las resistencias eléctricas hasta alcanzar el volumen y la temperatura de despegue (`T₂ ≈ 114.8 °C`).
  3. **Control térmico:** Un sensor de temperatura en la cámara de salida vigila que el aire impulsado se mantenga dentro del rango seguro para el PET aluminizado.
* **Macro CAD 3D Referencial (SolidWorks):** Generada en [calentador_tierra_solidworks_referencial_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_tierra_solidworks_referencial_v2.bas) (`420 × 220 × 220 mm`, modelo multicuerpo donde ocultando `1_Pared_Lateral_Visor` se observa el circuito completo: compuerta trasera de aire fresco, boca/manga/válvula de retorno, ventilador interno con tabique divisor, 9 resistencias eléctricas, rejilla difusora, sensor de temperatura, boca/manga/válvula de impulsión y panel de control).
* **Calentador aéreo con etanol:** Arquitectura **Monotubo Simplificado con Ventilador Externo y Difusor** en [calentador_etanol_simple_solidworks_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas) (`~6.45 kW` netos, bandeja integrada con esponja cerámica).

---

## 4. Próximas Validaciones en Banco Experimental

1. **Verificación de uniones de manta térmica (`12 µm`):**
   * Ensayar la combinación oficial de **cinta de poliéster térmico + cinta Kapton** (contabilizada dentro de `mad = 1.30 kg`) bajo tracción y temperatura hasta `115 °C`.
2. **Pruebas del calentador eléctrico en tierra y válvulas:**
   * Validar caudal, mezcla en retorno cerrado y control de temperatura de impulsión con el prototipo de resistencias (`~4.5–6.5 kW`, ciclo objetivo `5–8 min`) conectado a las dos bocas del casco.
3. **Pruebas del quemador aéreo monotubo de etanol (`6.45 kW` netos):**
   * Contrastar consumo real (`~25.7 mL/min`), estabilidad de llama frente al ventilador externo lateral y temperatura `NTC <= 150 °C` sobre el difusor antes del montaje en casco (guía completa de compras y pesos en [PRESUPUESTO_Y_PESO_FABRICACION.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/PRESUPUESTO_Y_PESO_FABRICACION.md)).
