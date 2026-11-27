# Defensa Técnica y Académica: Dirigible Híbrido de Aire Caliente y Rotores Eléctricos

**Contexto operativo:** Condiciones de altura de La Paz (3,350 m s.n.m., $P_1 = 67.1\text{ kPa}$, $\rho_1 = 0.811\text{ kg/m}^3$, viento frontal $v_v = 6\text{ m/s}$, misión multi-viaje de $d_m = 840\text{ m}$ en $n_v = 3$ tramos).  
**Base matemática:** Sistema acoplado de **170 variables y 108 ecuaciones**, aislamiento celular asimétrico en Mylar, quemador capilar de etanol y optimización pre-prototipo (auditado v2).

---

## Resumen Ejecutivo e Indicadores Clave

| Indicador principal | Valor logrado | Referencia / Comparativa |
| :--- | :--- | :--- |
| **Motor matemático** | **170 variables / 108 ecuaciones** | Compilado sin SymPy en tiempo de ejecución (`< 1 ms` por evaluación) |
| **Reducción de pérdidas térmicas ($Q_p$)** | **−79.3 %** (`16,325.7 W → 3,376.2 W`) | Capa celular asimétrica de Mylar `2/1` frente a casco sin aislar `0/0` (hasta **−84.0 %** con `3/2`) |
| **Ahorro de batería LiPo ($m_{bat}$)** | **−70.1 %** (`637.5 g` vs. `2,130.3 g`) | Frente a un dron multirrotor puro equivalente de igual carga útil ($1.0\text{ kg}$), misión y propulsión |
| **Inercia térmica pasiva ($t_c$ para −20 K)** | **4.8× más margen** (`20.0 s → 96.5 s`) | Hasta `163.8 s` en configuración `3/2` para descenso seguro |
| **Costo operativo total ($C_{op}$)** | **2.05 Bs / misión** (`0.68 Bs/viaje`) | `0.40 Bs` precalentamiento + `1.59 Bs` etanol + `0.06 Bs` electricidad (`2.44 Bs/km`) |
| **Ventaja de recarga rápida (`Hot-Swap`)** | **298× menor costo de capital** | Rellenar etanol (`89.2 g`): `1.60 Bs` vs. batería LiPo de repuesto (`637.5 g`): `478.12 Bs` |

### Estructura de la Defensa (10 minutos — 6 ejes)
1. **Fundamentación metodológica y resultados pre-prototipo:** por qué modelar 107 ecuaciones antes de construir y cómo transformó un diseño inviable en factible.
2. **Física crítica y comparación con dron puro:** arquitectura en 4 bloques acoplados, análisis de sensibilidad (top 5 factores) y ventaja en altura.
3. **Capa celular asimétrica de Mylar:** mecanismos físicos (convección Hollands + escudo IR + asimetría) e impacto cuantificado frente a casco sin aislar.
4. **Ciclo térmico y economía operativa:** precalentamiento en tierra como *"batería térmica"*, mantenimiento en vuelo, costos y recarga *Hot-Swap*.
5. **Calentador capilar de etanol propuesto:** diseño en 3 etapas con cámara de dilución segura (`120–150 °C`) y difusor ancho (`fcal = 1.275`, `ncal = 0.75`).
6. **Plataforma completa de software y puente CAD 3D:** motor dual CAS/float, equilibrio inverso BLT, interfaz KaTeX, 7 gráficas, optimizador multi-criterio, 14 Casos Tipo y macro VBA en SolidWorks.

---

## 1. Fundamentación Metodológica: ¿Por Qué Modelar 108 Ecuaciones Antes de Fabricar?

### El desafío de operar en La Paz con hardware acotado
* **Atmósfera exigente:** $P_1 = 67.1\text{ kPa}$ y $\rho_1 = 0.811\text{ kg/m}^3$ (**~34 % menos densidad del aire** que a nivel del mar) frente a viento frontal sostenido de $v_v = 6\text{ m/s}$.
* **Hardware real fijo:** 4 rotores Brushless **A2212** limitados a **640 W eléctricos continuos**, **22 N** de empuje total máximo y batería LiPo **$\le 1\text{ kg}$** ($1,000\text{ g}$).
* **Fallas de fórmulas sueltas:** modificar el grosor de Mylar o la esbeltez ($\lambda$) altera simultáneamente el área térmica, la flotabilidad, el arrastre aerodinámico y la masa de batería requerida.
* **Efecto bola de nieve:** cada $+100\text{ g}$ extra de estructura eleva la carga residual, dispara el empuje inducido ($\propto T^{3/2}$), exige mayor batería y vuelve a incrementar el peso total del vehículo.

### Lazos cerrados acoplados imposibles de resolver a mano
1. **Envolvente Mylar + Batería:** $m_c + m_{bat} \rightarrow$ definen masa total $m_{tot}$ y carga residual $m_{res}$.
2. **Dinámica vectorial A2212:** $m_{res}$, fuerza de arrastre $F_D$ e inercia del gas $m_{ap} \rightarrow$ determinan $T_{tot}$, ángulo $\theta$ y potencia eléctrica $P_{elec}$.
3. **Fases de misión ($840\text{ m}$):** pico de maniobra ($t_{man}$) + crucero estacionario ($P_{cruc}$) $\rightarrow$ energía integrada $E_{req}$.
4. **Criterio dual de batería:** $m_{bat} = \max(m_{be}\text{ [energía]},\; m_{bp}\text{ [potencia pico]}) \circlearrowleft$ retroalimentado hacia el paso 1.

### Qué se logró antes de pruebas en prototipos (Base Inviable vs. Auditoría vs. Óptimo)

| Etapa | Configuración clave | Parámetros resultantes y diagnóstico |
| :--- | :--- | :--- |
| **1 · Base Inicial (Inviable)** | $\lambda = 2.3$, $T_2 = 85\,^\circ\text{C}$, $v = 8.5\text{ m/s}$, capas Mylar `3/2` ($e = 14\text{ mm}$), $V = 20.77\text{ m}^3$, $m_{flot} = 3.20\text{ kg}$ | **4 límites violados:** $P_{elec} = 1,403.8\text{ W}\ (> 640\text{ W})$, $m_{bat} = 1,051.5\text{ g}\ (> 1,000\text{ g})$, $T_{tot} = 23.47\text{ N}\ (> 22.0\text{ N})$, excedente $F_{exc} = -1.05\text{ N}\ (< 0)$. |
| **2 · Auditoría Matemática (v1 y v2)** | Revisión independiente completa sobre el modelo, evaluador y optimizador | • Corrección del área prolada faltante ($+\pi R^2$): **+35 %** de superficie real $S$ detectado antes de cortar material.<br>• Piel exterior integrada en $S_c$ (**+330–390 g** reales incluidos) y soporte sin singularidades en `0/0`, `1/0`, `0/1`.<br>• Descuento térmico regional ($V_{nuc}/V_{cel}$ y $Q$ por regiones) + sensibilidad `-10 K` consistente.<br>• Separación maniobra ($t_a = 18\text{ s}$) vs. crucero ($P_{cruc}$, $\theta_{cruc}$) y tope de inclinación en ambas fases.<br>• Límites de hardware sincronizados (`N·Pmax1`), capacidad útil real por misión y eliminación de mamparos ($< 2\text{ \%}$ ahorro). |
| **3 · Óptimo Factible (0 alertas)** | $\lambda = 3.76$, $T_2 = 95.0\,^\circ\text{C}$, $v = 7.71\text{ m/s}$, capas Mylar `2/1` ($e = 31.9\text{ mm}$), $V = 21.92\text{ m}^3$ (**87.0 %** aire caliente) | **100 % factible (0 alertas):** $P_{elec}$ pico $= 639.6\text{ W}\ (\le 640\text{ W})$, crucero $P_{cruc} = 450.5\text{ W}$, $m_{bat} = 637.5\text{ g}\ (\le 1,000\text{ g})$, $T_{tot} = 12.77\text{ N}$ ($T_{cruc} = 9.78\text{ N}$), $\theta = 60.3^\circ / 56.5^\circ$, $F_{exc} = +13.60\text{ N}$, carga admisible fija `[0.6716 – 1.0000] kg`. |

*Conclusión metodológica:* cero hardware desperdiciado; los errores de escala y las sobreestimaciones de área/masa se detectaron y resolvieron en simulación antes de fabricar el primer prototipo.

---

## 2. Arquitectura Física y Aspectos con Mayor Impacto en el Cálculo

### Los 4 bloques físicos acoplados (`C1 → C13`)
* **C1–C3 · Aerostática y Casco:** gases ideales ($P_1, P_2, T_1, T_2$), densidad media en celdas ($\rho_{cel}$), casco bi-semielipsoidal prolado con $V = V_{nuc} + V_{cel}$, área curva exacta $S = S_f + S_r$ y masa de película Mylar $m_c = S_c \cdot \sigma$.
* **C4–C7 · Térmica y Quemador:** convección externa forzada ($Nu_e \propto Re^{4/5}$) + radiación exterior ($h_{rade}$), celdas de Mylar con correlación de Hollands ($Nu_c$) y radiación interna ($h_{rad} \rightarrow U_{sup}, U_{inf}$), enfriamiento logarítmico $t_c$, precalentamiento $E_{pre}$ y consumo de etanol $m_{gm}$.
* **C8 · Viento y Arrastre:** velocidad neta respecto al suelo $v_g = v - v_v$, misión multi-viaje $d_m = n_v \cdot d_1$ ($840\text{ m}$ en 3 tramos), correlación volumétrica de Hoerner $C_{DVc}(\lambda)$, factor parásito $k_p = 1.45$ y trabajo aéreo $E_D$.
* **C9–C13 · Propulsión y Batería:** reparto híbrido $m_{res} = m_{tot} - m_{flot}$, inercia añadida del gas $m_{ap} = f_{ap}(m_{tot} + m)$, empuje vectorial pico ($T_{tot}, \theta$) vs. crucero ($T_{cruc}, P_{cruc}$), integración energética por fases ($t_{man}$) y lazo dual de batería $m_{bat} = \max(m_{be}, m_{bp})$.

### Los 5 fenómenos físicos más influyentes (ordenados por impacto)
1. **Superficie real $S$ + piel exterior $S_c$ (`+26–35 % área`):** multiplica directamente las pérdidas térmicas $Q_p$, la masa de Mylar $m_c$ ($1.16\text{ kg}$) y el consumo de combustible $m_{gm}$.
2. **Viento frontal de $6\text{ m/s}$ y velocidad aerodinámica $v$ (`FD ∝ v²`):** frena el avance neto respecto al suelo ($v_g = v - v_v$), alarga el tiempo de misión $t_m$ y degrada la eficiencia propulsiva de las hélices $\eta_{prop}(v)$.
3. **Separación de maniobra ($t_{man}$) vs. crucero + inercia del gas (`−21 a −38 % batería`):** separar la rampa de arranque ($t_a = 18\text{ s}$) del crucero estacionario e incluir la masa de aire contenido $m$ ($\approx 14\text{ kg}$) evita sobredimensionar la batería frente a asumir aceleración continua.
4. **Reparto híbrido ($m_{flot} = 87\text{ \%}\,m_{tot}$, `> 3× menos batería`):** al incrementar la sustentación aerostática cae $m_{res}$ y se reduce drásticamente la potencia inducida ($\propto T_{tot}^{3/2}$), liberando a los motores.
5. **Volumen ocupado por las celdas ($V_{cel}$, `9–17 % de V`):** el aire atrapado en las celdas está a temperatura media $T_m < T_2$ (más denso que el núcleo), lo que frena la ganancia neta al aumentar espesores por encima de $e > 30\text{ mm}$ ($V = 21.92\text{ m}^3$: $V_{nuc} = 19.86\text{ m}^3$, $V_{cel} = 2.06\text{ m}^3$).

### Justificación en altura ($3,350\text{ m}$): Dirigible Híbrido vs. Dron Puro (igual carga útil $1.0\text{ kg}$ y misión $840\text{ m}$)

| Magnitud (misma carga útil $1.0\text{ kg}$, misión $840\text{ m}$, $v_v = 6\text{ m/s}$, 4× A2212) | Dron Puro Equivalente (0 % aire caliente, est. `0.65 kg`, $C_D A = 0.06\text{ m}^2$) | Dirigible Híbrido Óptimo (87 % aire caliente) |
| :--- | :--- | :--- |
| **Carga sostenida por rotores** | 100 % rotores ($39.0\text{ N}$ con `mtot = 3.97 kg`, $\rho_1 = 0.811\text{ kg/m}^3$) | $m_{flot} = 3.71\text{ kg}$ compensados a $95\,^\circ\text{C}$; rotores cargan $m_{res} = 0.55\text{ kg}$ + avance |
| **Potencia eléctrica requerida** | **1,751.3 W** pico / **1,722.2 W** crucero (`2.7×` sobre límite `640 W`) | **639.6 W** pico / **450.5 W** crucero (viable) |
| **Energía eléctrica integrada ($491\text{ s}$)** | **235.2 Wh** | **70.4 Wh** |
| **Batería LiPo requerida ($m_{bat}$)** | **2,130.3 g** (**INVIABLE**, $> 1,000\text{ g}$) | **637.5 g** (**VIABLE**, **−70.1 %** de masa de batería) |

---

## 3. La Capa Celular Asimétrica de Mylar: Funcionamiento e Impacto

### Cómo funciona (3 mecanismos combinados)
1. **Atrapamiento convectivo (correlación de Hollands):** celdas cuadradas de aire cerradas (espesor $e = 32\text{ mm}$ en el óptimo, ancho $W = 20\text{ cm}$) mantienen el número de Rayleigh cercano o inferior al crítico ($Ra_c = 1,708$), frenando la convección natural interna.
2. **Escudo infrarrojo multicapa ($\varepsilon = 0.04$):** el Mylar aluminizado presenta emisividad efectiva $\varepsilon_{ef} \approx 0.020$ entre caras enfrentadas, suprimiendo **~40×** la transferencia de calor por radiación respecto a un plástico opaco convencional.
3. **Asimetría estructural ($n_{capS} > n_{capI}$):** en la mitad superior (donde el aire caliente asciende por flotabilidad) se colocan más capas (`2` en el óptimo `2/1`, `3` en el caso `3/2`); en la mitad inferior el aire frío tiende a estratificarse de forma estable ($Nu = 1$), lo que permite reducir capas sin degradar el aislamiento y ahorrar peso de película.

*Papel en el proyecto:* sustituye los mamparos interiores y concentra **> 70 %** de la resistencia térmica total en la pared de la envolvente.

### Efecto cuantificado: Con vs. Sin Capa Celular (misma envolvente óptima, $T_2 = 95\,^\circ\text{C}$, $v = 7.71\text{ m/s}$, $840\text{ m}$)

| Magnitud evaluada | Sin aislante (`0 / 0`) | Con capa celular (`2 / 1`) | Efecto real obtenido |
| :--- | :--- | :--- | :--- |
| **Transmitancia global $U$** | `4.279 W/(m²·K)` | `0.885 W/(m²·K)` | **−79.3 %** fuga térmica |
| **Pérdida calorífica $Q_p$** | `16,325.7 W` | `3,376.2 W` | Evita necesitar quemador de `16.3 kW` |
| **Enfriamiento pasivo (−20 K, $t_c$)** | `20.0 s` | `96.5 s` | **4.8×** margen de seguridad |
| **Etanol requerido en vuelo ($m_{gm}$)** | `427.3 g` | `88.4 g` | **−79.3 %** combustible |
| **Costo operativo total ($C_{op}$)** | `8.15 Bs` | `2.05 Bs` | **−74.9 %** costo por misión |
| **Autonomía con $m_p = 89.2\text{ g}$ a bordo** | `175 m` (`0.6 viajes`) | `840 m` (`3.0 viajes`) | Habilita completar los 3 viajes |

Sin aislamiento celular, la masa adicional del quemador y del etanol junto a un enfriamiento en apenas `20 s` vuelven impracticable el dirigible.

---

## 4. Ciclo Térmico (Calentar y Mantener) y Economía Operativa

### Estrategia térmica en 4 fases
La estrategia clave consiste en utilizar el aire precalentado en tierra como una **"batería térmica" barata (`0.40 Bs`)** para no cargar peso de arranque en vuelo, y usar combustible líquido únicamente para sostener el equilibrio térmico contra las pérdidas $Q_p$:

1. **① En tierra · Precalentamiento:** un soplador externo calienta los $21.92\text{ m}^3$ ($V_{nuc} = 19.86\text{ m}^3$ a $95\,^\circ\text{C}$ y $V_{cel} = 2.06\text{ m}^3$ a $T_m = 55\,^\circ\text{C}$) desde $15\,^\circ\text{C}$ antes del despegue.
   * $Q = 1,073.1\text{ kJ}$, $E_{pre} = 1,651.0\text{ kJ}$ ($\eta_{pre} = 0.65$), costo $C_{pre} = 0.396\text{ Bs}$ (**~0.40 Bs**), **cero peso** de equipo de arranque en vuelo.
2. **② Despegue · Maniobra pico:** rampa suave ($t_a = 18\text{ s}$) hacia crucero; el aire ya parte caliente al 100 % de flotación.
   * Tiempo acumulado de maniobra $t_{man} = 54\text{ s}$, $P_{elec} = 639.6\text{ W}$ ($\le 640\text{ W}$), $T_{tot} = 12.77\text{ N}$ ($\le 22\text{ N}$), $\theta = 60.3^\circ$ (crucero $56.5^\circ$).
3. **③ En vuelo · Mantenimiento de $Q_p$:** el quemador de etanol solo repone las fugas térmicas a través de la pared sin recalentar desde cero.
   * Consume $m_{gm} = 88.36\text{ g}$ en $491\text{ s}$ ($E_{prop} = 2,209\text{ kJ}$, $C_{comb} = 1.591\text{ Bs}$); costo eléctrico $C_{elec} = 0.060\text{ Bs}$.
4. **④ Seguridad · Inercia térmica:** si el quemador se apaga o raciona la llama, la capa de Mylar conserva el calor útil.
   * Enfriamiento logarítmico $t_c = 96.5\text{ s}$ para caer $20\text{ K}$ en `2/1` (y `163.8 s` en configuración `3/2`), garantizando tiempo suficiente para aterrizar con control.

### Desglose económico y ventaja *Hot-Swap* (`840 m` / 3 viajes)
* **Costo operativo total por misión:** **2.05 Bs** (`0.68 Bs / viaje` · `2.44 Bs / km`):
  * Precalentamiento en tierra ($C_{pre}$): **0.40 Bs** (**19.4 %**)
  * Etanol en vuelo ($C_{comb}$): **1.59 Bs** (**77.7 %**)
  * Recarga eléctrica LiPo ($C_{elec}$): **0.06 Bs** (**2.9 %**)
* **Recambio rápido (*Hot-Swap*) entre vuelos sin esperar carga eléctrica (`479.72 Bs` total combinado):**
  * Rellenar depósito de etanol ($m_p = 89.2\text{ g}$): **1.60 Bs** (**0.3 %**)
  * Batería LiPo cargada de repuesto ($637.5\text{ g}$): **478.12 Bs** (**99.7 %**)
  * $\rightarrow$ La batería de repuesto exige **298× más capital** que la recarga térmica completa.
* **Ventaja Etanol 96 % (`18 Bs/kg`) vs. latas GLP/Butano (`100–110 Bs/kg`):** **~6× menor costo por kg**, sin envase metálico presurizado y con recarga líquida en segundos.
* *Tarifas de referencia del modelo:* electricidad `0.85 Bs/kWh`, gas en tierra `0.24 Bs/MJ`, etanol `18 Bs/kg`, batería LiPo `750 Bs/kg`.

---

## 5. Calentador Capilar de Etanol Propuesto

El desafío térmico consiste en inyectar entre $2$ y $3\text{ kW}$ de potencia calorífica dentro de un casco cuya lámina de Mylar pierde integridad estructural por encima de **110–140 °C**, sin penalizar la carga útil con un intercambiador metálico pesado. Se propone un subsistema vertical en **3 etapas**:

1. **Quemador capilar blindado (base):**
   * Fieltro de fibra cerámica embebido en etanol líquido (consumo aproximado de **~5.6–10 mL/min** según régimen).
   * Retiene el combustible por capilaridad evitando derrames al cabecear o inclinarse el dirigible.
   * Alojado dentro de una camisa cortaviento de doble pared perforada más malla apagachispas de acero inoxidable.
2. **Cámara / chimenea de dilución térmica (etapa media):**
   * Los gases de combustión salen a **600–800 °C** con caudal reducido (**~2–3 L/s**) hacia una chimenea ligera de aluminio.
   * Un micro-ventilador de **5–10 W** (potencia contemplada dentro de $P_{ad} = 45\text{ W}$ auxiliares) recircula **30–60 L/s** de aire más frío tomado del fondo del propio casco para mezclarlo con los gases.
   * La mezcla diluye la temperatura de salida a unos seguros **120–150 °C**, protegiendo el Mylar superior.
3. **Difusor cónico ancho y justificación de $f_{cal} = 1.275$ / $\eta_{cal} = 0.75$:**
   * Un difusor cónico superior perforado descarga el flujo templado a baja velocidad (**$< 1\text{ m/s}$**), evitando chorros calientes focalizados hacia el techo.
   * Esta transferencia directa con dilución justifica el factor de exceso/pérdida del calentador $f_{cal} = 1.275$ y rendimiento $\eta_{cal} = 0.75$; por contraste, un intercambiador de calor cerrado aleteado añadiría **400–700 g** de masa muerta y reduciría $\eta_{cal}$ a **0.50–0.65**.
   * El alivio inferior (~2 L/s) en la zona más fría del casco minimiza las pérdidas energéticas de purga; con aislamiento Mylar, variar $f_{cal}$ apenas desplaza el costo operativo $C_{op}$ en $\pm 1\text{ \%}$.

---

## 6. Muestra de la Plataforma de Software y Puente CAD 3D

### Núcleo simbólico-numérico, equilibrio inverso e interfaz (`calc.py` + FastAPI)
* **Motor dual CAS + float (`< 1 ms`):** las 108 ecuaciones residen simbólicamente en SymPy (`modelo.py`) para trazabilidad total, y se compilan por descomposición *tearing* en `evaluador.py` en aritmética float pura (**cero SymPy en barridos y optimización**).
* **Equilibrio e intercambio inverso:** grafo bipartito (**Hopcroft/DFS + descomposición BLT de Tarjan**) que permite intercambiar cualquier variable fija por una calculada ($d_m \leftrightarrow n_v$, $T_2 \leftrightarrow \rho_2$, $V \leftrightarrow m_{flot}$, $U \leftrightarrow e$) verificando la consistencia del balance.
* **Ecuaciones KaTeX + alertas reales:** aplicación web FastAPI con 13 categorías, sustitución numérica en tiempo real, cajas explicativas de coeficientes y alertas físicas reales sin ocultar ni alterar signos físicos.
* **Mapa de flujo global (`C1 → C13`):** diagramas interactivos por categoría y mapa global completo con resaltado de lazos cerrados (batería$\leftrightarrow$masa y celdas$\leftrightarrow$volumen) y navegación directa a cada ecuación.

### Exploración paramétrica, optimizador y Casos Tipo
* **7 gráficas interactivas (`G1–G7`):**
  * `G1`: Esbeltez $\lambda$ vs. energías y dimensiones.
  * `G2`: Reparto híbrido $m_{flot} / m_{res}$ y $F / F_L$.
  * `G3`: Distancia, viajes ($n_v$) y viento frontal.
  * `G4`: Espesor de Mylar $e$ vs. ahorro térmico.
  * `G5`: Combustible $m_{gm}$ acumulado en vuelo.
  * `G6`: Silueta 2D a escala y desglose de masas.
  * `G7`: Temperatura $T_2$ óptima ($-10\text{ K}$) y comparación directa vs. dron puro.
* **Optimizador multi-criterio:** 6 indicadores ponderables por perfil (costo operativo, *Hot-Swap*, energía, masa útil, autonomía, velocidad), variables constructivas libres/editables dinámicamente y límites activos de hardware. Opera mediante **muestreo Halton canónico + descenso hacia factibilidad** en **`< 80 ms`**, de forma **invariante al orden** de variables.
* **Auditoría matemática verificada:** residuo máximo de **$4.6 \times 10^{-13}$** y criterio de factibilidad unificado en todas las vistas.
* **14 familias de Casos Tipo e Histórico JSON:** ~40 escenarios comparativos frente al óptimo (nivel del mar, HDPE/Nylon, propano/butano, `0/1/3` capas, vientos fuertes y 1–7 viajes) más histórico manual persistente con comparador SVG multi-diseño, exportación e importación JSON.

### Puente automático hacia geometría CAD 3D en SolidWorks
* **Flujo:** `Histórico JSON → generar_cad_solidworks.py → Macro VBA (.bas)`.
* **Geometría generada automáticamente:**
  * Casco bi-semielipsoidal hueco generado por revolución exacta con piel exterior y capas celulares asimétricas visibles en vista de corte.
  * Anillos separadores internos espaciados según el espesor $e$.
  * Góndola rectangular centrada bajo el centro de flotación ($x_{cb}$) con puntales acortados.
  * Bastidor en H + 4 tirantes diagonales triangulados y 4 motores con discos de hélice ($d_p$) para validar holguras geométricas y empaquetamiento antes de fabricar.

---

## 7. Conclusiones y Hoja de Ruta Experimental

1. **Viabilidad demostrada:** el modelo acoplado confirma que el dirigible híbrido cumple los límites reales de 4 motores A2212 (`639.6 W ≤ 640 W`), ángulo tanto en maniobra como en crucero (`60.3° / 56.5° ≤ 75°`) y batería LiPo `≤ 1 kg` (`637.5 g`) operando a `3,350 m` con `6 m/s` de viento frontal y capacidad útil verificada (`0.67–1.00 kg` con batería instalada fija).
2. **Habilitadores físicos:** la capa celular asimétrica de Mylar (`−79.3 %` pérdidas térmicas) junto al precalentamiento en tierra (`0.40 Bs`) y el quemador capilar de etanol (`1.60 Bs` *Hot-Swap*) resuelven simultáneamente autonomía y costo.
3. **Siguiente fase en banco experimental:** contrastar experimentalmente potencia térmica, mezcla y temperatura de salida del quemador de etanol en cámara cortaviento, medir la masa real de unión de las celdas de Mylar y validar las curvas reales empuje–potencia en altura antes de ensamblar el demostrador completo.

---

## 8. Guion Cronometrado Sugerido para el Video de 10 Minutos

* **[0:00 – 0:30] Apertura:** Buenos días. Presento la defensa técnica del proyecto de dirigible híbrido de aire caliente con rotores eléctricos, diseñado específicamente para operar en altura en La Paz (3,350 m s.n.m.) con viento frontal de 6 m/s. En los próximos 10 minutos explicaré por qué fue necesario construir un modelo acoplado de 170 variables y 108 ecuaciones antes de cortar una sola lámina de material, qué fenómenos físicos dominan el rendimiento, cómo funciona la capa celular de Mylar y el quemador de etanol propuesto, y mostraré las capacidades del software desarrollado.
* **[0:30 – 0:55] Mapa de exposición:** La presentación recorre seis bloques en secuencia lógica: primero, la fundamentación matemática y lo logrado antes de fabricar prototipos; segundo, los aspectos físicos con mayor peso en el modelo; tercero, el papel decisivo de la capa celular de Mylar; cuarto, la estrategia térmica de precalentamiento en tierra y sus costos operativos; quinto, la arquitectura del quemador de etanol; y por último, una muestra de todas las herramientas del software.
* **[0:55 – 1:40] Por qué 108 ecuaciones:** ¿Por qué necesitamos 108 ecuaciones y no unas pocas fórmulas de hoja de cálculo? Porque a 3,350 metros de altura la densidad del aire cae un 34 %, mientras debemos vencer 6 m/s de viento en contra con cuatro motores A2212 limitados a 640 W y 1 kg máximo de batería. En estas condiciones el sistema tiene un lazo cerrado muy sensible: si sube la masa de aislante o de batería, sube la carga residual que sostienen los rotores, sube la potencia inducida $T^{3/2}$, se requiere más batería, y esa batería vuelve a aumentar el peso total. Sin resolver ese lazo junto al térmico-geométrico en computadora, cualquier prototipo empírico quedaría fuera de rango.
* **[1:40 – 2:30] Logros pre-prototipo:** Nuestro punto base inicial superaba ampliamente los límites con 1,404 W de potencia y más de 1 kg de batería. Además, una auditoría matemática independiente detectó errores que habrían arruinado las pruebas reales: el término $\pi R^2$ faltante en la superficie de cada semielipsoide, el peso de la piel exterior, el calor sensible regional, el ángulo de los motores durante el crucero y la capacidad útil real de misión. Con el modelo ya auditado, el optimizador halló un punto 100 % factible: esbeltez 3.76, 2/1 capas, 95 °C y crucero a 7.71 m/s, que cumple todos los límites con 640 W pico, 451 W en crucero y solo 638 g de batería.
* **[2:30 – 3:10] Bloques físicos:** Todo el modelo físico se organiza en cuatro grandes bloques acoplados a lo largo de 13 categorías: aerostática y geometría del casco prolado descontando celdas; transferencia térmica combinando convección, radiación infrarroja y Hollands; aerodinámica con viento en contra de 6 m/s y arrastre volumétrico de Hoerner; y finalmente el bloque propulsivo con disco actuador, separación de maniobra y crucero y dimensionamiento dual de la batería.
* **[3:10 – 4:00] Los 5 factores críticos:** De las 108 ecuaciones, cinco fenómenos dominan el comportamiento numérico. Primero, la superficie exterior real y su piel, porque controlan tanto la pérdida térmica como la masa del casco. Segundo, el viento de 6 m/s: cada metro por segundo adicional dispara el arrastre cuadráticamente y castiga el tiempo en vuelo. Tercero, separar la maniobra de aceleración —incluyendo la inercia de unos 14 kg de aire contenido— respecto al crucero estacionario, lo que recorta la batería necesaria entre 21 % y 38 % frente a suponer aceleración continua. Cuarto, el porcentaje de carga cubierto por aire caliente (87 % en el óptimo), y quinto, el volumen periférico de celdas aislantes, que limita físicamente el grosor rentable.
* **[4:00 – 4:35] Híbrido vs. Dron puro:** Esta comparación muestra la razón de ser del vehículo híbrido: si intentamos mover la misma carga útil de 1 kg en un dron multirrotor puro equivalente (con su propia estructura ligera y sin masa de gas) a 3,350 metros y con 6 m/s de viento frontal durante 840 metros, el modelo predice 1,751 W pico y más de 2.1 kg de batería, completamente fuera del límite del hardware. En nuestro dirigible híbrido, al descargar el 87 % del peso en el aire caliente, los cuatro rotores bajan a 451 W en crucero, 640 W en pico de arranque y solo 638 g de batería: un recorte del 70 % que hace viable la misión.
* **[4:35 – 5:20] Capa celular de Mylar:** La pieza habilitadora del proyecto es la capa celular asimétrica de Mylar aluminizado. En vez de una tela simple que perdería calor masivamente hacia el viento de 6 m/s, rodeamos el casco con celdas cuadradas cerradas que combinan tres mecanismos: primero, confinan el aire en espesores finos para suprimir corrientes convectivas según la correlación de Hollands; segundo, al ser láminas reflectantes con emisividad 0.04, bloquean cerca de 40 veces la transferencia por radiación infrarroja respecto a un plástico opaco; y tercero, la configuración es asimétrica: concentra más capas en la mitad superior, donde asciende el aire caliente, mientras abajo la estratificación estable permite usar menos capas y ahorrar peso.
* **[5:20 – 6:00] Impacto cuantificado del Mylar:** En números exactos, pasar de piel simple (0/0) a capa celular asimétrica (2/1) reduce la transmitancia $U$ de 4.28 a 0.89 W/(m²·K), recortando la pérdida térmica de 16.3 kW a 3.38 kW (−79.3 %). Esto tiene cuatro consecuencias directas: el tiempo de enfriamiento sube casi cinco veces (de 20 a 96.5 segundos), el consumo de etanol para 840 metros baja de 427 gramos a solo 88.4 gramos, el costo operativo cae de 8.15 a 2.05 Bs, y la autonomía con 89 gramos a bordo pasa de 175 metros (inviable) a completar los 3 viajes.
* **[6:00 – 6:40] Ciclo térmico en vuelo:** El ciclo térmico se divide en cuatro fases para optimizar peso y costo. Primero, en tierra se calienta el volumen considerando sus dos regiones térmicas antes del despegue: son 1.65 MJ que cuestan apenas 40 centavos de boliviano y actúan como una batería térmica sin cargar ese calentador a bordo. Segundo, durante los despegues y giros (54 segundos acumulados de maniobra) los rotores operan hasta 640 W. Tercero, en crucero el quemador a bordo solo repone las pérdidas continuas a través del Mylar usando 88.4 g de etanol. Cuarto, si fallara la llama, la capa celular garantiza entre 96 y 164 segundos antes de perder 20 K, permitiendo un descenso controlado.
* **[6:40 – 7:25] Costos y Hot-Swap:** En términos económicos, completar los tres viajes cuesta apenas 2.05 bolivianos: 19 % corresponde al precalentamiento en tierra, 78 % al etanol consumido en vuelo y solo 3 % a la electricidad de los motores. Más revelador aún es comparar el recambio rápido o *Hot-Swap* para operar de continuo: rellenar el tanque completo de etanol cuesta 1.60 bolivianos, mientras mantener una batería LiPo cargada de repuesto ronda 478 bolivianos, casi 300 veces más caro. Además, el etanol comercial a 18 Bs/kg resulta seis veces más económico que las latas presurizadas de propano o butano y evita manipular envases a presión.
* **[7:25 – 8:15] Calentador capilar de etanol:** ¿Cómo transferimos entre 2 y 3 kW de calor dentro de un casco de Mylar que se ablanda sobre 110–140 °C sin usar un pesado intercambiador cerrado? Proponemos un quemador capilar en tres etapas verticales. Abajo, un recipiente con fibra cerámica retiene el etanol por capilaridad para evitar derrames si el dirigible cabecea, rodeado por una camisa cortaviento perforada y malla apagachispas. En la etapa media, los escasos litros por segundo de gases a 600–800 °C entran a una chimenea de aluminio donde un micro-ventilador de menos de 10 W mezcla de 30 a 60 L/s de aire tomado del fondo del propio casco, diluyendo la temperatura a unos seguros 120–150 °C. Arriba, un difusor ancho perforado libera el aire a baja velocidad (< 1 m/s), evitando chorros contra el techo y justificando $f_{cal} = 1.275$ y rendimiento térmico $\eta_{cal} = 0.75$ sin añadir los 400 a 700 gramos de un intercambiador aleteado.
* **[8:15 – 8:45] Software (Núcleo e interfaz):** Pasando a lo que ofrece el software desarrollado: combina la trazabilidad exacta de 108 ecuaciones simbólicas en SymPy con un evaluador numérico en float puro por descomposición *tearing* que corre en menos de un milisegundo. Su asistente de equilibrio matemático usa grafos bipartitos y descomposición por bloques de Tarjan para permitir cálculos inversos —por ejemplo fijar un volumen o transmitancia $U$ y despejar $m_{flot}$ o espesor $e$—. Todo se presenta en una interfaz web con ecuaciones KaTeX coloreadas, notas de ingeniería y mapas de flujo interactivos.
* **[8:45 – 9:20] Gráficas, optimizador y casos:** Además del explorador de ecuaciones, la plataforma ofrece tres herramientas clave de ingeniería: siete gráficas paramétricas para analizar sensibilidad térmica, aerodinámica y comparación contra un dron puro; un estudio óptimo multi-criterio con seis indicadores ponderables y restricciones configurables de hardware que encuentra soluciones factibles en menos de 80 milisegundos de forma invariante al orden de variables; y una matriz de 14 familias de casos tipo junto a un histórico JSON exportable para comparar alternativas constructivas.
* **[9:20 – 9:40] Puente CAD 3D:** Finalmente, el archivo JSON exportado desde el histórico alimenta el script `generar_cad_solidworks.py`, que genera automáticamente una macro VBA nativa para construir en SolidWorks un modelo sólido 3D referencial: casco hueco con sus capas asimétricas y anillos separadores visibles en corte, góndola ubicada bajo el centro de flotación, bastidor en H triangulado y los cuatro rotores con su diámetro real de hélice para verificar holguras.
* **[9:40 – 10:00] Cierre:** En conclusión, la modelización previa nos permitió demostrar viabilidad en altura bajo restricciones estrictas de motor y batería, validar la capa celular de Mylar y el ciclo de etanol como ejes habilitadores, y construir una plataforma completa conectada hasta CAD 3D. El siguiente paso inmediato es pasar al banco de pruebas experimental para validar el quemador capilar con difusor, pesar las uniones reales de Mylar y contrastar la curva de empuje-potencia de las hélices antes del montaje final. Muchas gracias.
