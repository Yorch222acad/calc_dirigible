# Documentación Técnica Consolidada: Dirigible Híbrido de Aire Caliente y Rotores Eléctricos

**Contexto operativo:** Condiciones de altura de La Paz (`3,350 m s.n.m.`, $P_1 = 67.12\text{ kPa}$, $\rho_1 = 0.811\text{ kg/m}^3$, viento frontal sostenido $v_v = 6.0\text{ m/s}$).  
**Base matemática auditada (`v2`):** Sistema acoplado de **170 variables y 108 ecuaciones**, aislamiento celular en Mylar aluminizado, ciclo térmico dual (**calentador eléctrico en tierra con recirculación** + **calentador aéreo monotubo de etanol**) y puente CAD 3D en SolidWorks ([`CIERRE_AUDITORIAS.md`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/CIERRE_AUDITORIAS.md), auditorías V1–V10 cerradas).

---

## Resumen Ejecutivo e Indicadores Clave

| Indicador principal | Diseño Definitivo (`def`, manta real `12 µm / 17 g/m²`) | Referencia `6 µm / 8.4 g/m²` (`T2 ≤ 95 °C`) |
| :--- | :--- | :--- |
| **Configuración seleccionada** | **`1 / 1` capa simétrica**, $L = 8.083\text{ m}$, $D = 2.275\text{ m}$, $V = 21.90\text{ m}^3$, $T_2 = 114.8\,^\circ\text{C}$, $d_m = 540\text{ m}$ (`2 × 270 m`), $m_{carga} = 1.10\text{ kg}$ | `2 / 1` capas asimétricas, $L = 7.66\text{ m}$, $V = 21.92\text{ m}^3$, $T_2 = 95.0\,^\circ\text{C}$, $d_m = 840\text{ m}$ (`3 × 280 m`), $m_{carga} = 1.00\text{ kg}$ |
| **Reducción de pérdidas térmicas ($Q_p$)** | **−69.5 %** (`21,154.9 W → 6,454.6 W`, $U = 1.379\text{ W/(m}^2\cdot\text{K)}$) | **−79.3 %** (`16,325.7 W → 3,376.2 W`) |
| **Ahorro de batería LiPo ($m_{bat}$)** | **494.2 g** vs. `873.9 g` de dron puro (**−43.5 %**; dron además excede `640 W` y `22 N`) | **637.5 g** vs. `2,130.3 g` de dron puro (**−70.1 %**) |
| **Inercia térmica pasiva ($t_c$ para −20 K)** | **`44.7 s`** con `1/1` capa (`~3.6×` más margen que `12.5 s` en `0/0`) | `96.5 s` en `2/1` (`158.0 s` en base `3/2`) |
| **Costo operativo total ($C_{op}$)** | **`2.553 Bs` / misión** (`1.276 Bs/viaje`, `0.477 Bs` tierra eléc. + `2.036 Bs` etanol + `0.040 Bs` elec. vuelo) | `2.047 Bs` / misión (`0.40 Bs` tierra + `1.59 Bs` etanol + `0.06 Bs` elec.) |
| **Ventaja recarga rápida (`Hot-Swap`)** | **156.4× menor capital:** llenar etanol (`131.7 g`): **`2.37 Bs`** vs. LiPo repuesto (`494.2 g`): **`370.63 Bs`** | Repuesto LiPo ~`298×` más costoso que tanque etanol |

### Estructura del documento (6 ejes técnicos)
1. **Fundamentación metodológica y cierre pre-prototipo:** por qué modelar 108 ecuaciones antes de fabricar y consolidación de las auditorías V1–V10.
2. **Física crítica y comparación frente a dron puro:** arquitectura `C1–C13`, top 5 factores sensibles y justificación en altura.
3. **Caracterización real de la manta térmica y análisis por capas (`1/1` vs. multicapa):** uniones con cinta de poliéster térmico + Kapton y por qué con la manta comercial (`59 g`, `12 µm`, `17 g/m²`) no conviene usar más de una capa celular.
4. **Calentador eléctrico en tierra con recirculación y economía operativa:** precalentamiento eléctrico limpio (`~4.5–6.5 kW`, `5–8 min`) con `0 g` a bordo y ventaja *Hot-Swap*.
5. **Calentador aéreo con etanol (Monotubo Simplificado):** ventilador externo lateral, bandeja-depósito con esponja cerámica antiderrame (`25.7 mL/min`), control `SG90` + `NTC <= 150 °C` y difusor cónico con plato deflector (`fcal = 1.275`, `ncal = 0.75`).
6. **Plataforma de software y puente CAD 3D definitivo:** motor dual CAS/float, 7 gráficas (`G4` multicapa `0/0 → 4/4`), optimizador, histórico y macros VBA en SolidWorks del dirigible y ambos calentadores.

---

## 1. Fundamentación Metodológica: ¿Por Qué Modelar 108 Ecuaciones Antes de Fabricar?

### El desafío de operar en La Paz con hardware acotado
* **Atmósfera exigente:** $P_1 = 67.12\text{ kPa}$ y $\rho_1 = 0.811\text{ kg/m}^3$ (**~34 % menos densidad del aire** que a nivel del mar) frente a viento frontal sostenido de $v_v = 6.0\text{ m/s}$.
* **Hardware real fijo:** 4 rotores Brushless **A2212 (1000KV)** con hélices de `10"` (`254 mm`), limitados a **640 W eléctricos continuos**, **22 N** de empuje total máximo y batería LiPo **$\le 1\text{ kg}$** (`1,000 g`).
* **Efecto bola de nieve:** cada `+100 g` extra en película o estructura eleva la carga residual `mres`, dispara la potencia inducida ($\propto T^{3/2}$), exige mayor batería y vuelve a aumentar el volumen del casco y su arrastre aerodinámico.

### Lazos cerrados acoplados (`170` variables / `108` ecuaciones)
1. **Envolvente + Batería:** $m_c + m_{bat} \rightarrow$ definen masa total $m_{tot}$ y carga residual $m_{res} = m_{tot} - m_{flot}$.
2. **Dinámica vectorial A2212:** $m_{res}$, fuerza de arrastre $F_D$ e inercia aparente del gas + casco $m_{ap} = f_{ap}(m_{tot} + m)$ $\rightarrow$ determinan $T_{tot}$, ángulos $\theta / \theta_{cruc}$ y potencias $P_{elec} / P_{cruc}$.
3. **Fases de misión:** pico de maniobra ($t_{man} = \min(t_m, n_v \cdot t_a)$ con $t_a = 18\text{ s}$) + crucero estacionario $\rightarrow$ energía integrada $E_{req}$.
4. **Criterio dual de batería:** $m_{bat} = \max(m_{be}\text{ [energía]},\; m_{bp}\text{ [potencia pico]}) \circlearrowleft$ realimentado hacia el paso 1.

### Evolución hasta el diseño definitivo (`Base → Auditorías V1–V10 → Definitivo`)

| Etapa | Configuración clave | Parámetros resultantes y diagnóstico |
| :--- | :--- | :--- |
| **1 · Base Inicial (Inviable)** | $\lambda = 2.3$, $T_2 = 85\,^\circ\text{C}$, $v = 8.5\text{ m/s}$, capas `3/2` ($e = 14\text{ mm}$), `6 µm / 8.4 g/m²`, $V = 20.77\text{ m}^3$ | **4 límites violados:** $P_{elec} = 1,403.8\text{ W}\ (> 640\text{ W})$, $m_{bat} = 1,051.5\text{ g}\ (> 1,000\text{ g})$, $T_{tot} = 23.47\text{ N}\ (> 22.0\text{ N})$, $F_{exc} < 0$. |
| **2 · Auditoría Matemática V1–V10 (`v2`)** | Revisión integral de física, evaluador numérico, optimizador, histórico y Playwright E2E | Corrección área prolada exacta ($+\pi R^2$), piel exterior en $S_c$, celdas sin singularidad (`0/0`..`4/4`), enfriamiento logarítmico e Hipótesis B regional (`tc = 158.0 s` en base), separación maniobra/crucero (`θ` y `θcruc`), límites de hardware sincronizados y tolerancia económica (`c_recambio`, sub-métrica). Residuo máx. `4.64 × 10⁻¹³`. |
| **3 · Diseño Definitivo (`def`, manta real `59 g`)** | `ep = 12 µm`, `σ = 17.0 g/m²`, `ε = 0.08`, `mad = 1.30 kg` (cintas incluidas), `mcarga = 1.10 kg`, `λ = 3.55`, `T2 = 114.8 °C`, **`1/1` capa** (`e = 29.1 mm`), `v = 7.64 m/s`, `dm = 540 m` | **100 % factible (0 alertas):** $P_{elec} = 637.0\text{ W}\ (\le 640\text{ W})$, $P_{cruc} = 449.8\text{ W}$, $m_{bat} = 494.2\text{ g}$, $T_{tot} = 12.91\text{ N}$ ($T_{cruc} = 9.94\text{ N}$), $\theta = 59.2^\circ / 55.2^\circ$, $F_{exc} = +13.32\text{ N}$, carga admisible fija `[0.7427 – 1.1000] kg`. |

---

## 2. Arquitectura Física y Comparación Frente a Dron Puro

### Los 4 bloques físicos acoplados (`C1 → C13`)
* **C1–C3 · Aerostática y Casco:** gases ideales ($P_1, P_2, T_1, T_2$), densidad media en celdas ($\rho_{cel}$), casco bi-semielipsoidal prolado con $V = V_{nuc} + V_{cel}$, área curva exacta $S = S_f + S_r$ y masa de película Mylar $m_c = S_c \cdot \sigma$.
* **C4–C7 · Térmica y Quemador:** convección externa forzada ($Nu_e \propto Re^{4/5}$) + radiación exterior ($h_{rade}$), celdas cerradas con correlación de Hollands ($Nu_c$) y radiación interna ($h_{rad} \rightarrow U_{sup}, U_{inf}$), enfriamiento logarítmico regional $t_c$, precalentamiento eléctrico en tierra $E_{pre}$ y consumo de etanol aéreo $m_{gm}$.
* **C8 · Viento y Arrastre:** velocidad neta $v_g = v - v_v$, misión multi-viaje $d_m = n_v \cdot d_1$, correlación volumétrica de Hoerner $C_{DVc}(\lambda)$, factor parásito $k_p = 1.45$ y trabajo aéreo $E_D$.
* **C9–C13 · Propulsión y Batería:** reparto híbrido $m_{res} = m_{tot} - m_{flot}$, inercia añadida $m_{ap} = f_{ap}(m_{tot} + m)$, empuje pico vs. crucero y lazo dual $m_{bat} = \max(m_{be}, m_{bp})$.

### Los 5 fenómenos físicos más influyentes
1. **Superficie real $S$ y gramaje de película ($\sigma \cdot S_c$):** en el prototipo real, pasar de película ideal `8.4 g/m²` a la manta medida `17.0 g/m²` eleva $m_c$ a `1,826.7 g` (`36.2 %` de `mtot`) aun usando solo `1/1` capa.
2. **Viento frontal de `6.0 m/s` (`FD ∝ v²`):** domina el arrastre (`8.16 N`), la inclinación (`59.2° / 55.2°`) y reduce la velocidad útil al suelo a $v_g = 1.64\text{ m/s}$.
3. **Separación de maniobra ($t_{man}$) vs. crucero + inercia del gas:** el crucero opera a `449.8 W` frente al pico de `637.0 W` en rampa ($18\text{ s}$), evitando sobredimensionar `mbe` (`426.1 g`).
4. **Reparto híbrido ($m_{flot} = 88.5\text{ \%}\,m_{tot}$):** sostener `4.46 kg` por aire caliente reduce $m_{res}$ a apenas `0.581 kg`, manteniendo la potencia motriz dentro del rango A2212.
5. **Volumen de celdas ($V_{cel} = 1.25\text{ m}^3$):** el aire periférico a $T_m = 64.9\,^\circ\text{C}$ aporta menos flotación que el núcleo a `114.8 °C`, poniendo techo rentable a espesores extremos ($e \approx 29.1\text{ mm}$).

### Justificación en altura (`3,350 m s.n.m.`): Dirigible Híbrido Definitivo vs. Dron Puro Equivalente

| Magnitud (misma carga útil `1.10 kg`, misión `540 m`, `vv = 6.0 m/s`, 4× A2212) | Dron Puro Equivalente (`est. 0.65 kg`, `CD·A = 0.06 m²`) | Dirigible Híbrido Definitivo (`88.5 %` aire caliente) |
| :--- | :--- | :--- |
| **Carga sostenida por rotores** | 100 % rotores (`mtot = 2.81 kg`, `27.5 N` verticales) | $m_{flot} = 4.460\text{ kg}$ aerostáticos; rotores solo cargan $m_{res} = 0.581\text{ kg}$ + avance |
| **Empuje vectorial (`Tmax = 22.0 N`)** | **27.67 N** pico / **27.52 N** crucero (**INVIABLE**, excede `22 N`) | **12.91 N** pico / **9.94 N** crucero (**VIABLE**) |
| **Potencia eléctrica (`Pmax = 640 W`)** | **1,029.1 W** pico / **1,009.9 W** crucero (**INVIABLE**, `1.6×` tope) | **637.0 W** pico / **449.8 W** crucero (**VIABLE**) |
| **Energía y batería LiPo requerida** | `96.5 Wh` $\rightarrow$ **`873.9 g`** | `47.04 Wh` $\rightarrow$ **`494.2 g`** (**−43.5 % batería**) |

---

## 3. Caracterización de la Manta Real y Por Qué Se Usa Solo 1 Capa Celular (`1/1`)

### Parámetros reales medidos y método de unión
* **Material conseguido:** Manta térmica de emergencia **FIRSTIME bicolor dorado/plateado de `160 × 210 cm` (`3.36 m²`)**, película BoPET/PET metalizado comercial (`90 %` reflectividad IR declarada).
* **Peso real medido en balanza:** **`59 g`** $\rightarrow$ gramaje puro `59 / 3.36 = 17.56 g/m²` (espesor real $\approx 12.5\text{ µm}$, confirmando `ep = 12 µm`). En el cálculo definitivo se adoptó **`σ = 17.0 g/m²`** y **`ε = 0.08`** orientando la **cara plateada hacia el interior** de la celda para maximizar reflexión infrarroja (`~37 mantas` con merma de corte del `15 %`).
* **Método de unión oficial y límite térmico:** se emplea una **combinación de cinta de poliéster térmico (`180–200 °C`) y cinta Kapton (`220–260 °C`)**, contabilizando el peso de las cintas aparte dentro de `mad = 1.30 kg`. Esto elimina la falla temprana de adhesivos convencionales y fija el límite operativo seguro en **`T2 <= 115 °C`** (alcanzado en `114.8 °C`), protegiendo la película de encogimiento térmico.

### Análisis por número de capas (`G4`: `0/0 → 4/4` capas): por qué `1/1` y no multicapa en este caso

Con una película de `17.0 g/m²` (más del doble del Mylar ultraligero de `6 µm / 8.4 g/m²`), cada capa adicional añade una masa considerable que rompe el balance peso-potencia:

#### A. Barrido manteniendo el casco definitivo (`V = 21.90 m³`, `mflot = 4.46 kg`)

| Capas (`ncapS/ncapI`) | `Qp` (W) | Ahorro `fais` | Etanol `mgm` (g) | Masa film `mc` (g) | `Pelec` (W) | `mbat` (g) | Diagnóstico hardware |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`0 / 0`** (sin celdas) | `20,819.8` | `0.0 %` | `364.9` | `784.4` | `575.7` | `449.8` | Exceso de flotación (`mflot` calibrado para más peso) |
| **`1 / 0`** (solo sup.) | `14,231.6` | `32.2 %` | `249.4` | `1,301.3` | `562.9` | `440.5` | `θ = 89.9° > 75°` (`mres` casi nulo) |
| **`1 / 1` (Definitivo)** | **`6,454.6`** | **`69.5 %`** | **`113.1`** | **`1,826.7`** | **`637.0`** | **`494.2`** | **Equipo OK (única banda óptima factible)** |
| **`2 / 1`** | `4,869.8` | `77.2 %` | `85.3` | `2,360.1` (`+533 g`) | `815.1` | `623.2` | **Excede `Pelec > 640 W`** |
| **`2 / 2`** | `3,897.2` | `81.9 %` | `68.3` | `2,902.1` | `1,103.3` | `832.1` | **Excede `Pelec > 640 W` y `Ttot = 23.5 N > 22 N`** |
| **`3 / 2` → `4 / 4`** | `3,170 → 2,168` | `85.4 → 90.2 %` | `55.6 → 38.0` | `3,452 → 5,150` | `1,509 → 4,025` | `1,126 → 3,159` | **Inviable** (`Pelec`, `Ttot`, `mbat`, `Fexc` fuera de rango) |

#### B. Re-optimizando todo el dirigible (`λ, v, mflot, e, T2, mp`) para cada configuración con `17.0 g/m²`

| Capas forzadas | Score | `L` × `D` (`V`) | Masa film `mc` | `Qp` / `tc` (`−20 K`) | `Pelec` / `mbat` | Costo `Cop` | Conclusión |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **`0 / 0`** | `38.61` | `7.48 × 2.07 m` (`16.70 m³`) | `669.1 g` | `18.04 kW` / `12.5 s` | `604.5 W` / `470.6 g` | `4.863 Bs` | Pérdidas extremas (`~316 g` etanol en vuelo) e inercia crítica (`12.5 s`). |
| **`1 / 0`** | `39.85` | `8.10 × 2.16 m` (`19.86 m³`) | `1,175.3 g` | `13.44 kW` / `19.9 s` | `611.6 W` / `475.8 g` | `4.104 Bs` | La mitad inferior sin celdas sigue fugando demasiado calor. |
| **`1 / 1` (Óptimo)** | **`42.01`** | `8.08 × 2.28 m` (`21.90 m³`) | `1,826.7 g` | **`6.45 kW` / `44.7 s`** | `637.0 W` / `494.2 g` | **`2.553 Bs`** | **Mejor balance global:** captura el `69.5 %` de ahorro sin sobredimensionar `V`. |
| **`2 / 1`** | `40.38` | `8.22 × 2.36 m` (`23.98 m³`) | `2,254.7 g` | `6.35 kW` / `50.3 s` | `634.1 W` / `492.1 g` | `2.821 Bs` | Para cargar `+428 g` de Mylar debe inflar el casco y acortar `e`, perdiendo casi todo el ahorro en `Qp` (`−1.6 %`) y subiendo costo/precalentamiento. |
| **`2 / 2`** | `37.17` | `8.84 × 2.51 m` (`29.20 m³`) | `3,118.7 g` | `5.54 kW` / `69.9 s` | `638.7 W` / `573.2 g` | `3.267 Bs` | Casco desproporcionado (`mtot = 6.42 kg`, `3.12 kg` solo de plástico) con peor desempeño neto. |
| **`3 / 2` y sup.** | — | — | — | — | — | — | **Sin solución factible** dentro de `640 W / 22 N / 1 kg`. |

**Conclusión física:** la **primera capa cerrada (`0/0 → 1/1`) aporta el gran salto de eficiencia térmica (`−69.5 %`)** al crear un colchón de aire confinado y dos superficies reflectantes (`ε = 0.08`). Con película de `17 g/m²`, intentar agregar más capas obliga a agrandar el casco para cargar el propio plástico, aumentando `S` y neutralizando el aislamiento extra. Usar `2/1` o `3/2` capas solo vuelve a ser óptimo si en una iteración futura se consigue película ultraligera de `6–8 µm` (`8.4–11 g/m²`).

---

## 4. Calentador Eléctrico en Tierra (Recirculación) y Economía Operativa

La arquitectura térmica divide el problema en **inflar y precalentar eléctricamente en tierra** (equipo externo `0 g` a bordo, **100 % aire limpio sin combustión**) y **mantener temperatura en vuelo** con un quemador ligero de etanol.

### Subsistema de tierra: calentador eléctrico compacto con recirculación cerrada
* **Arquitectura CAD ([`calentador_tierra_solidworks_referencial_v2.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_tierra_solidworks_referencial_v2.bas)):** carcasa portátil de **`420 × 220 × 220 mm`** con ventilador axial interno, **9 resistencias eléctricas**, rejilla difusora, compuerta trasera de admisión de aire fresco, dos mangas conectadas a dos válvulas del casco (impulsión y retorno), sonda de temperatura en salida y panel eléctrico de control.
* **Ciclo operativo en 2 pasos (parte desinflado):**
  1. **Inflado inicial:** con la compuerta trasera abierta, el ventilador succiona aire ambiente fresco, lo calienta en el banco de resistencias y lo impulsa por la válvula de entrada hasta llenar los `21.90 m³` del casco.
  2. **Recirculación en lazo cerrado:** la segunda válvula (retorno) devuelve aire tibio del casco hacia el calentador, donde se mezcla y vuelve a pasar por las resistencias de forma controlada hasta alcanzar `T2 = 114.8 °C` (`Vnuc`) y `64.9 °C` (`Vcel`), evitando sobrecalentar localmente la manta de `12 µm` y reduciendo el desperdicio térmico.
* **Energía, potencia general y tiempo:**
  * Calor sensible regional en el casco: **`Q = 1,291.4 kJ`**
  * Energía eléctrica consumida en tierra (`ηpre = 0.65`): **`Epre = 1,986.8 kJ`** (`~0.55 kWh`)
  * Rango de potencia y duración estimado: con **`~4.5–6.5 kW`** eléctricos instalados, el ciclo de calentamiento se completa en **`~5–8 minutos`**; costo eléctrico **`Cpre = 0.477 Bs`** (`cpre = 0.24 Bs/MJ ≈ 0.85 Bs/kWh`), actuando como una **"batería térmica" inicial con `0 g` de equipo de arranque en vuelo**.

### Desglose económico de misión y ventaja *Hot-Swap* (`540 m` / 2 viajes)
* **Costo operativo total por misión:** **`2.553 Bs`** (`1.276 Bs / viaje` · `4.728 Bs / km`):
  * Precalentamiento eléctrico en tierra ($C_{pre}$): **`0.477 Bs`** (`18.7 %`)
  * Etanol en vuelo ($C_{comb}$): **`2.036 Bs`** (`79.8 %`)
  * Recarga eléctrica LiPo de vuelo ($C_{elec}$): **`0.040 Bs`** (`1.6 %`)
* **Recambio rápido (*Hot-Swap*) entre misiones (`373.00 Bs` total combinado):**
  * Rellenar depósito completo de etanol ($m_p = 131.7\text{ g}$): **`2.37 Bs`** (`0.6 %`)
  * Batería LiPo cargada de repuesto ($494.2\text{ g}$ a `750 Bs/kg`): **`370.63 Bs`** (`99.4 %`)
  * $\rightarrow$ La batería de repuesto exige **`156.4×` más capital** que la recarga térmica completa.
* **Ventaja Etanol 96 % (`18 Bs/kg`) vs. latas GLP/Butano (`100–110 Bs/kg`):** `~6×` menor costo por kg, sin envases metálicos presurizados y con recarga líquida en segundos.

---

## 5. Calentador Aéreo con Etanol (Monotubo Simplificado Elegido)

El desafío en vuelo consiste en reponer continuamente **`Qp = 6,454.6 W`** netos (potencia química bruta $Q_p / \eta_{cal} \approx 8.61\text{ kW}$) dentro de una envolvente de PET comercial de `12 µm` cuyo techo seguro es `115 °C`, evitando intercambiadores cerrados pesados (`400–700 g`).

Frente a una arquitectura compleja de 3 etapas concéntricas (conservada solo como respaldo), se consolidó la solución **Monotubo Simplificado con Ventilador Externo y Difusor** ([`calentador_etanol_simple_solidworks_v2.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas)), manteniendo `ηcal = 0.75` y `fcal = 1.275`:

1. **Monotubo exterior de aluminio (`Ø 212 × 340 mm`) con base cerrada:** cilindro ligero de lámina fina (`0.12–0.15 mm`) cerrado en el fondo para canalizar todo el flujo verticalmente, unido al casco mediante collar ignífugo.
2. **Ventilador lateral externo + cortina de aire frío:** soplador/ventilador montado en ducto lateral exterior debajo de la bandeja (alimentado dentro de `Pad = 45 W`); aporta oxígeno para la combustión y crea una cortina anular periférica (`~29 mm`, caudal total de dilución `~139–166 L/s`) que enfría la pared del tubo y diluye los gases por debajo de **`<= 150 °C`**.
3. **Bandeja-depósito integrada (`Ø 150 mm`) con esponja de fibra cerámica:** almacena directamente en el quemador los **`131.7 g` (`~164–180 mL`)** de etanol 96 % retenidos por capilaridad (antiderrame ante cabeceo, sin tanque remoto, bomba ni mangueras). Tasa de consumo en `def`: **`0.344 g/s = 20.65 g/min ≈ 25.7 mL/min`** (`mgm = 113.12 g` en `328.6 s`).
4. **Control de llama y seguridad:** anillo cortaviento perimetral para proteger la llama del flujo lateral, tapa corrediza accionada por **microservo `SG90`** para modular o apagar en vuelo, **malla apagachispas inox** en la boca del monotubo y **sensor `NTC`** vigilando `<= 150 °C` en salida.
5. **Difusor cónico con plato deflector ranurado (3 anillos):** expande y reparte radialmente la mezcla tibia a baja velocidad hacia el núcleo del casco sin chorros focalizados contra el techo.

---

## 6. Plataforma de Software y Puente CAD 3D Definitivo

### Núcleo simbólico-numérico, equilibrio inverso y gráficas
* **Motor dual CAS + float (`< 1 ms`):** 108 ecuaciones simbólicas en [`modelo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py) compiladas por descomposición *tearing* en [`evaluador.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py) (`0` SymPy en tiempo de optimización o barridos).
* **Equilibrio inverso BLT (`C1 → C13`):** grafo bipartito + descomposición Tarjan para intercambiar cualquier variable fija por una calculada (`dm ↔ nv`, `T2 ↔ ρ2`, `V ↔ mflot`, `U ↔ e`), interfaz KaTeX en tiempo real y mapa de flujo interactivo.
* **7 gráficas comparativas (`G1–G7`):** incluyendo la **comparativa multicapa `0/0 → 4/4` en `G4` (Paneles C y D)** que expone gráficamente la caída térmica frente al peso de película y saturación de `Pelec / Pmax`, además de `G7` frente al dron puro equivalente.
* **Optimizador multi-criterio (`< 80 ms`) y 14 familias de Casos Tipo:** invariante al orden de variables, histórico persistente JSON y suite de regresión automatizada ([`auditar_modelo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/auditar_modelo.py) + [`auditar_frontend.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/auditar_frontend.py) en Chromium).

### Puente CAD 3D en SolidWorks (Macros Disponibles)
* **Dirigible definitivo ([`dirigible_solidworks_referencial_2026-11-27_def.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas), generado desde [`historico_dirigible_2026-11-27_def.json`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json)):** casco `L = 8.083 m × D = 2.274 m` con piel exterior, `1` capa aislante completa `360°` (`e = 29.1 mm`) y anillos separadores; góndola `600 × 300 × 250 mm` centrada bajo `X_CB = 3.738 m` (`gap = 135 mm`); bastidor en `"H"` triangulado + 4 motores A2212 con hélices `dp = 254 mm` (`±Z = 550 mm`, `X = [3318, 4158] mm`, holguras **`278.9 mm`** al casco y **`273.0 mm`** lateral a góndola).
* **Calentador eléctrico en tierra ([`calentador_tierra_solidworks_referencial_v2.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_tierra_solidworks_referencial_v2.bas)):** caja portátil `420 × 220 × 220 mm` con ventilador interno, 9 resistencias, compuerta trasera de aire fresco, 2 bocas/mangas/válvulas (retorno + impulsión), sonda y panel frontal.
* **Calentador aéreo monotubo de etanol ([`calentador_etanol_simple_solidworks_v2.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas)):** monotubo aluminio, ventilador externo, bandeja con esponja cerámica, servo `SG90`, apagachispas, `NTC` y difusor cónico con plato deflector *(versión de 3 etapas en [`calentador_etanol_solidworks_referencial.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_solidworks_referencial.bas) como respaldo)*.

---

## 7. Conclusiones y Próxima Fase Experimental

1. **Viabilidad cerrada con material comercial real:** aun duplicando el gramaje de película al usar la manta real **FIRSTIME de `59 g` (`12 µm`, `17 g/m²`)**, el dirigible híbrido cumple todas las restricciones reales (`Pelec = 637.0 W ≤ 640 W`, `Ttot = 12.91 N ≤ 22 N`, `mbat = 494.2 g ≤ 1 kg`, `θ = 59.2° ≤ 75°`, `mcarga = 1.10 kg`) donde un dron puro equivalente (`1,029 W / 27.7 N`) resulta físicamente inviable.
2. **Justificación de diseño monocapa (`1/1`):** el análisis acoplado y las curvas `G4` demostraron que a `17 g/m²` usar `2` o más capas dispara el tamaño y el arrastre del casco sin beneficio neto; `1/1` optimiza simultáneamente masa, costo (`2.553 Bs`) e inercia de seguridad (`44.7 s`).
3. **Banco de pruebas experimental inmediato:** validar en banco estático el quemador monotubo de etanol (`165 mL`, llama estable con ventilador externo, `NTC <= 150 °C` y apagado `SG90`), ensayar la resistencia a `115 °C` de las uniones con cinta de poliéster térmico + Kapton, y comprobar el ciclo del calentador eléctrico en tierra (`~4.5–6.5 kW`, `5–8 min`) con ambas válvulas antes del ensamblaje final.

---

## 8. Síntesis Hablada de Referencia (10 Minutos)

* **[0:00 – 0:30] Apertura:** Presento el proyecto de dirigible híbrido de aire caliente y rotores eléctricos optimizado para operar en altura en La Paz (`3,350 m s.n.m.`, `6 m/s` de viento frontal). Mostraré cómo un modelo acoplado de 170 variables y 108 ecuaciones, calibrado con la manta térmica comercial medida en balanza, permitió cerrar un diseño viable y generar los modelos 3D en SolidWorks.
* **[0:30 – 1:30] Por qué 108 ecuaciones y cierre de auditoría:** Con `34 %` menos densidad del aire y cuatro motores A2212 limitados a `640 W`, `22 N` y `1 kg` de batería, el peso de la envolvente y el empuje forman un lazo muy sensible. Tras 10 rondas de auditoría matemática y pruebas automatizadas en navegador, corregimos superficie prolada exacta, piel exterior, enfriamiento regional, separación de maniobra/crucero y márgenes reales hasta lograr un residuo menor a `5 × 10⁻¹³`.
* **[1:30 – 2:40] Física crítica y ventaja frente a dron puro:** Comparando contra un dron puro equivalente levantando `1.1 kg` durante `540 m` contra `6 m/s` de viento, el multirrotor exige `1,029 W` y `27.7 N`, completamente fuera del equipo. Al delegar `88.5 %` del peso (`4.46 kg`) al aire caliente a `114.8 °C`, nuestros rotores bajan a `637 W` pico, `450 W` en crucero, `12.9 N` de empuje y `494 g` de batería (`−43.5 %`).
* **[2:40 – 4:30] Manta real de `59 g` y por qué usamos solo `1/1` capa:** Medimos nuestra manta comercial de `160 × 210 cm` en `59 g` (`12 µm`, `17 g/m²`) y la unimos con cinta de poliéster térmico y Kapton (contabilizada en `mad = 1.30 kg`) para operar hasta `115 °C`. Al reoptimizar con ese gramaje real, vimos en la gráfica multicapa `G4` algo crucial: la primera capa `1/1` ya reduce `69.5 %` las pérdidas térmicas (`21.1 kW` a `6.45 kW`), pero añadir `2/1` o `2/2` suma tantos cientos de gramos que dispara el volumen a `24–29 m³` o excede los `640 W`. Por eso `1/1` es el óptimo real con este material.
* **[4:30 – 6:15] Calentador eléctrico en tierra y economía *Hot-Swap*:** Dividimos la energía térmica en dos sistemas. En tierra, un calentador eléctrico compacto con 9 resistencias (`~4.5–6.5 kW`) y lazo de recirculación mediante dos válvulas en el casco infla el dirigible con aire limpio y lo lleva a `114.8 °C` en unos `5 a 8 minutos` (`0.48 Bs`) actuando como batería térmica de cero gramos a bordo. La misión completa cuesta `2.55 Bs`, y en recarga rápida rellenar `132 g` de etanol cuesta `2.37 Bs` frente a `371 Bs` por una batería LiPo de repuesto (`156×` más barata la energía térmica).
* **[6:15 – 7:50] Calentador aéreo monotubo de etanol:** Para reponer `6.45 kW` en vuelo sin dañar la manta de `12 µm` ni añadir peso innecesario, consolidamos un monotubo de aluminio con bandeja-depósito integrada y esponja cerámica antiderrame (`~25.7 mL/min`), alimentado por un ventilador lateral externo que crea una cortina fría y diluye la mezcla bajo `150 °C`, vigilado por sensor `NTC`, apagado remoto con microservo `SG90` y difusor cónico con plato deflector.
* **[7:50 – 9:20] Software y puente CAD SolidWorks:** Todo vive en una plataforma web FastAPI + SymPy/float (`< 1 ms`), con equilibrio inverso BLT, 7 gráficas paramétricas, optimizador multi-criterio e histórico JSON. Desde allí generamos automáticamente las macros VBA en SolidWorks del dirigible definitivo (`8.08 × 2.27 m`, capa `1/1`, bastidor en H con `279 mm` de holgura en hélices), del calentador eléctrico terrestre con recirculación y del calentador aéreo monotubo de etanol.
* **[9:20 – 10:00] Cierre:** Con el diseño definitivo, el presupuesto ajustado y los tres CAD cerrados, el siguiente paso pasa directo al banco experimental para validar el quemador monotubo, las costuras a `115 °C` y el precalentamiento eléctrico en recirculación antes del ensamblaje final. Gracias.
