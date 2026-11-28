# Presupuesto de Fabricación, Desglose de Pesos (`mad`) y Guía de Compra en Bolivia

Documento técnico-económico consolidado para el **Dirigible Híbrido de Aire Caliente + 4 Motores A2212 (1000KV)**, calibrado íntegramente sobre el diseño definitivo **`def`** ([historico_dirigible_2026-11-27_def.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json), `id = f53b37f3b5`) y el modelo auditado **`v2`** ([modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py), [evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py)).

---

## 1. Contexto del Diseño Definitivo (`def`) y Estructura de Masas

En la configuración definitiva `def` (**`1 / 1` capa simétrica** con manta térmica comercial de `12 µm`, `σ = 17.0 g/m²`, `ε = 0.08`, `e = 29.1 mm`, `T2 = 114.8 °C`, `mcarga = 1.10 kg`, misión `2 × 270 m = 540 m` contra viento `vv = 6.0 m/s`), las dimensiones y parámetros principales del prototipo son:

| Parámetro | Valor en `def` | Referencia |
|---|---|---|
| Dimensiones exteriores (`L × D`, `V`) | **`8.083 m × 2.275 m`** (`21.90 m³`) | [historico_dirigible_2026-11-27_def.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json) |
| Superficie casco (`S`) / Película total (`Sc`) | `46.91 m²` / **`107.45 m²`** | Casco + `1/1` capa + tabiques |
| Flotabilidad aérea (`mflot`) / Residual (`mres`) | `4.460 kg` (`88.5 %`) / `0.581 kg` | Masa total `mtot = 5.041 kg` |
| Bastidor en H + Góndola (referencia CAD) | Envolvente CAD `600×300×250 mm` (caja interna útil `~400×220×180 mm`), `z_mot = 550 mm`, `dx_mot = 420 mm` | [dirigible_solidworks_referencial_2026-11-27_def.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas) |
| Potencia motriz pico (`Pelec` / tope `Pmax`) | **`637.0 W`** / `640.0 W` | Crucero `449.8 W` · Empuje `12.91 N` (`θ = 59.2°`) |
| Consumo eléctrico auxiliar (`Pad`) | **`45.0 W`** | Incluye ventilador externo de dilución + aviónica |
| Masa adicional agrupada (`mad`) | **`1,300 g` (`1.30 kg`)** | Incluye estructura, calentador aéreo, válvulas, electrónica y cintas |

En [modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py#L666-L671), la masa total del artefacto es:

$$\text{mart} = m_c + N \cdot m_{\text{mot}} + m_p + m_{\text{ad}} + m_{\text{bat}}, \qquad m_{\text{tot}} = \text{mart} + m_{\text{carga}}$$

Para evitar duplicaciones ni omisiones, los componentes se dividen en tres bloques exactos que cierran en **`mtot = 5,041 g`** (`2,641 g` Bloque A + `1,300 g` Bloque B + `1,100 g` carga útil):
- **Bloque A (en vuelo, fuera de `mad`):** película del casco (`mc = 1,827 g`), 4 motores A2212 pelados (`188 g`), etanol líquido (`132 g`) y batería LiPo (`494 g`).
- **Bloque B (en vuelo, dentro de `mad = 1,300 g`):** propulsión auxiliar, electrónica/FPV, cableado, bastidor/góndola, calentador aéreo monotubo de etanol, válvulas de precalentamiento/purga, aletas y **cinta de poliéster térmico + Kapton**.
- **Bloque C (`0 g` en vuelo):** equipamiento en tierra (emisora, receptor FPV, LoRa tierra, cargador y **calentador eléctrico compacto en tierra con recirculación**).

---

## 2. Manta Térmica Caracterizada y Método de Unión (`1/1` Capa)

Datos reales medidos de la manta térmica comercial adquirida (**FIRSTIME / Camping Bag Bolivia**):
- **Medidas por unidad:** `160 × 210 cm = 3.36 m²`.
- **Peso medido real:** **`59 g`** $\rightarrow$ gramaje puro `59 / 3.36 = 17.56 g/m²` (espesor real `12 µm`, modelada como `σ = 17.0 g/m²`, cara plateada orientada al interior con `ε = 0.08`).
- **Cantidad para `Sc = 107.45 m²` (+15 % merma por cortes curvos y tabiques = `~123.6 m²`):** **`37 mantas`** (`123.6 / 3.36 ≈ 36.8`):
  - Compra total: `1` ya adquirida (`30 Bs`) + `36` al por mayor (`36 × 18 Bs = 648 Bs`) = **`678 Bs`** *(o `666 Bs` si las 37 entran al precio mayorista)*.
- **Por qué se construye con `1 / 1` capa celular:** con `17.0 g/m²`, la primera capa `1/1` ya reduce **`69.5 %`** las pérdidas térmicas (`21.15 kW → 6.45 kW`). Al pasar a `2/1` o `2/2`, la película extra suma entre `+533 g` y `+1,292 g`, obligando a agrandar el casco y superando los `640 W` de los 4 motores A2212 (ver Paneles C y D de `G4` en [graficas.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/graficas.py)).
- **Unión oficial de la envolvente:** **combinación de cinta de poliéster térmico (`180–200 °C`) y cinta Kapton (`220–260 °C`)**, que permite trabajar con margen seguro hasta `T2 <= 115 °C`. Su peso se contabiliza aparte dentro del **Bloque B7 (`mad`)**.

---

## 3. Bloque A · Componentes en Vuelo FUERA de `mad` (Modelados en el JSON `def`)

| Componente | Variable | Estado | Peso (g) | Precio en Bolivia (Bs) | Dónde comprar en Bolivia | Notas |
|---|---|---|---:|---:|---|---|
| **Manta térmica `160×210 cm` (`37` uds.)** | `mc` | **1 comprada** + 36 por comprar | `1,827` | **`678 Bs`** (`30 + 36×18`) | **Camping Bag Bolivia** | `107.45 m²` netos (`+15 %` merma $\rightarrow$ 37 mantas). |
| **4× Motores Brushless A2212 1000KV** | `N·mmot` | **Ya comprados** | `188` (`4 × 47 g`) | **`440 Bs`** (`110 Bs` c/u) | Ya adquiridos | Peso solo del cuerpo motor; hélices, collets y ESCs van en `mad`. |
| **Batería LiPo 3S/4S (`mbat = 494.2 g`)** | `mbat` | Por comprar | `494` | **`375 – 500 Bs`** | **Hobby House Men**, **Sawers**, **EPY Electrónica**, grupos RC/FPV | El modelo estima `750 Bs/kg` (`~371 Bs`). Elegir tasa $\ge 20\text{C}$ (~`60 A` pico en 3S / `45 A` en 4S). |
| **Combustible Etanol 96 % (carga a bordo)** | `mp` | Consumible | `132` (`~164 mL`) | **`18 Bs / L`** (`~2.4 Bs`/vuelo) | Farmacias / distribuidores alcohol potable | Se aloja directamente en la esponja cerámica del monotubo. |
| **Subtotal Bloque A** | | `440 + 30 = 470 Bs` pagados | **2,641 g** | **`1,511 – 1,636 Bs`** *(pendiente: `1,041 – 1,166 Bs`)* | | Con `mad = 1,300 g` + `mcarga = 1,100 g` $\rightarrow$ **`5,041 g` (`mtot`)**. |

---

## 4. Bloque B · Desglose Realista de `mad` (`1,300 g`) en Bolivia

Se comparan dos niveles de armado con stock conseguible en Bolivia (**Opción Realista Estándar** vs. **Opción Realista Optimizada**).

### B1. Propulsión complementaria y basculamiento (`θ ≤ 75°`)

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia | Notas clave |
|---|---|---|---:|---:|---:|---|---|
| **4× Hélices `1045` / `1045R`** | **Ya compradas** (`1045` + `1045R`) | Mismas ya compradas | 56 | 56 | **`24 Bs`** *(ya pagado)* | Ya adquiridas (`12 Bs`/par) | Pesar las 4 juntas para verificar valor real. |
| **4× Adaptadores collet + tornillos M3** | Collet aluminio (con motores) + montaje directo sin cruz metálica | Igual | 28 | 28 | `0 Bs` | Incluidos con A2212 | Evitar la cruz de acero ahorra `~24 g`. |
| **4× Variadores ESC (30–45 A)** | **4× ESC 30A SimonK / XXD** sin termoencogible grueso ni conectores bala | **1× ESC 4-en-1 35–45A** o **4× micro-ESC BLHeli_S 30A** | 76 | 20 | `320 Bs` *(est.)* / `380 Bs` *(opt.)* | **Ardunel**, **Sawers**, **EPY Electrónica**, **i2C** / grupos FPV | Instalar cerca de motores acorta cables de fase. |
| **Servos de basculamiento + mecanismo** | **2× MG90S metálicos** moviendo 2 ejes compartidos + 4 bujes/rodamientos `688ZZ` + soportes PETG | Igual (alineados al eje del motor para mínimo par) | 62 | 55 | `90 Bs` | **Ardunel**, **Sawers**, **EPY**, **EC Robotics / i2C** | Mantiene control completo de *pitch*, *roll* y *yaw*. |
| **Subtotal B1** | | | **222 g** | **159 g** | **`434 Bs`** *(est.)* / **`494 Bs`** *(opt.)* | | **`24 Bs` ya pagados** (hélices). |

---

### B2. Placa de control, cámara FPV, sensores y enlace de datos

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia | Notas clave |
|---|---|---|---:|---:|---:|---|---|
| **Placa de control + IMU + Barómetro + BEC** | **ESP32 DevKit** + **MPU6050** + **BMP280** + **UBEC 5V/6V 5A** | **ESP32-S3 Mini** + **GY-91** + mini BEC/step-down | 27 | 18 | `165 Bs` *(est.)* / `195 Bs` *(opt.)* | **Sawers**, **EPY Electrónica**, **Ardunel**, **Eloy Salmón (LP)** | Alternativa con firmware listo: **APM 2.8 / Pixhawk 2.4.8 sin carcasa** (`~30 g`). |
| **GPS + Brújula** | **u-blox NEO-M8N / NEO-6M sin carcasa plástica** | Igual sin carcasa ni cable largo | 17 | 14 | `125 Bs` | **Ardunel**, **EPY Electrónica**, **Sawers** | Indispensable para compensar viento de `6.0 m/s`. |
| **Sensores de temperatura** | **2× Termistores NTC 100k** + cable fino AWG 28/30 al techo y difusor | Igual | 15 | 13 | `40 Bs` | **Sawers**, **EPY**, **Ardunel** | Vigila el techo del casco (`<= 115 °C`) y boca del difusor (`<= 150 °C`). |
| **Cámara FPV + VTX 5.8 GHz + Antena** | Cámara FPV CMOS + VTX `TS5828` sin carcasa + dipolo | Micro cámara FPV + nano VTX `200–400 mW` + dipolo cobre | 22 | 12 | `390 Bs` *(est.)* / `430 Bs` *(opt.)* | Grupos **FPV Bolivia**, **TecBolivia**, **EPY** | Video analógico fiable a distancia (`540 m` de misión). |
| **Receptor RC + Telemetría** | Receptor **FlySky FS-iA6B sin carcasa** + **LoRa SX1278 433 MHz** | Receptor **FlySky FS-A8S / FS-X6B** + **LoRa SX1278** | 17 | 10 | `65 Bs` *(est.)* / `165 Bs` *(opt.)* | **Sawers**, **EPY**, **Ardunel** | Telemetría en vivo de `T2`, altura y voltaje de batería. |
| **Subtotal B2** | | | **98 g** | **67 g** | **`785 Bs`** *(est.)* / **`915 Bs`** *(opt.)* | | |

---

### B3. Cableado de potencia, señal y conectores

Con las distancias del diseño CAD definitivo (`z_mot = 550 mm`, `dx_mot = 420 mm`, motores en `X = [3318, 4158] mm` respecto al casco):

| Elemento | Configuración recomendada | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---:|---:|---|
| **Cableado de potencia a motores** | **ESCs junto a motores/brazos:** 2 hilos DC silicona **AWG 16/18** por costado (`~4 m` totales) + tramos trifásicos cortos (`< 15 cm`) | 100 | 85 | `55 Bs` | **Eloy Salmón**, **EPY Electrónica**, **Sawers** |
| **Cables señal PWM, sensores y XT60** | AWG 28/30 señal/NTC + **XT60** + cable batería + bridas/termocontraíble | 55 | 45 | `35 Bs` | **EPY**, **Sawers**, **Eloy Salmón** |
| **Subtotal B3** | | **155 g** | **130 g** | **`90 Bs`** | |

---

### B4. Estructura: Góndola, Bastidor en H y Arnés de suspensión

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---|---:|---:|---:|---|
| **Bastidor en H (`~3.88 m`)** | **Varillas huecas fibra de vidrio carpa (`Ø 8 mm`)** sin casquillos de acero | **Tramos caña de pescar telescópica de carbono** | 202 | 155 | `80 Bs` *(est.)* / `150 Bs` *(opt.)* | **Camping Bag Bolivia**, calle **Uyustus**, **Feria 16 de Julio** |
| **Puntales + 4 tirantes (`~2.50 m`)** | **Varillas fibra de vidrio `5–6 mm`** | **Puntas de caña de carbono** | 70 | 45 | `40 Bs` *(est.)* / `50 Bs` *(opt.)* | Tiendas de pesca, **Librería Brasil**, **Fibracenter** |
| **8× Uniones / abrazaderas** | Piezas impresas 3D PETG pared fina / epoxi | Atado directo con hilo nylon/carbono + epoxi | 56 | 35 | `30 Bs` | Impresión 3D local / ferretería |
| **Góndola (envolvente CAD `600×300×250 mm`, caja útil `~400×220×180 mm`)** | Caja ligera en **Tecnopor alta densidad / XPS `6 mm`** + base **balsa `3 mm`** | **Esqueleto abierto** varilla balsa/carbono + base mínima balsa `3 mm` | 125 | 90 | `45 Bs` | **Librería Brasil**, **Tecnopor Ltda.** |
| **Arnés catenario de suspensión** | **Parches tela Ripstop** + **hilo trenzado PE/Dyneema `0.5 mm`** (reparte los `4.46 kg` de flotación) | Igual | 55 | 50 | `60 Bs` | Tiendas de pesca + mercería/camping |
| **Subtotal B4** | | | **508 g** | **375 g** | **`255 Bs`** *(est.)* / **`335 Bs`** *(opt.)* | |

---

### B5. Calefactor Aéreo de Etanol (`6.45 kW` netos — Monotubo Simplificado)

Corresponde a la arquitectura definitiva de [calentador_etanol_simple_solidworks_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas): un solo tubo de aluminio con ventilador externo lateral y bandeja-depósito integrada para `~164–180 mL` de etanol (`~25.7 mL/min`).

| Componente | Opción Más Ligera Conseguible en Bolivia | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---:|---:|---|
| **Monotubo `Ø212×340 mm`, base, bandeja `Ø150`, cortaviento, collar y difusor con plato** | Fabricación artesanal en **lámina fina de aluminio `0.12–0.15 mm`** (repostería / latas / ferretería) + remaches aluminio | 145 | 125 | `35 Bs` | Ferreterías / tiendas repostería |
| **Esponja cerámica + malla apagachispas inox** | Retazo de **manta de fibra cerámica** en bandeja (retiene `165 mL` sin derrames; alt. fibra de vidrio sin resina) + **malla inox** fina de colador | 28 | 24 | `35 Bs` | Casas de refractarios / **Refrak**, bazar/ferretería |
| **Ventilador externo lateral de dilución** | *Estándar:* **Axial/soplador 12V alto flujo** (`80×80` o `92×92 mm`, marco aligerado). *Optim.:* **Micro-motor brushless + hélice 3"–4"** en ducto fino (`Ø 96 mm`) para diluir `6.45 kW` por debajo de `150 °C` | 65 | 48 | `65 Bs` *(est.)* / `85 Bs` *(opt.)* | **Eloy Salmón**, **Sawers**, **EPY Electrónica**, FPV |
| **Apagado / control remoto de llama** | **1× Microservo SG90** + tapa corrediza aluminio | 16 | 14 | `20 Bs` | **Ardunel**, **Sawers**, **EPY** |
| **Subtotal B5** | | **254 g** | **211 g** | **`155 Bs`** *(est.)* / **`175 Bs`** *(opt.)* | |

---

### B6. Válvulas de Precalentamiento Eléctrico en Tierra, Purga y Desinflado

Al operar en tierra con **recirculación cerrada** (`2` mangas al casco) y en vuelo a presión atmosférica (`0–30 Pa`):

| Elemento | Solución Ligera (100 % local) | Peso (g) | Precio aprox. (Bs) | Dónde comprar / fabricar |
|---|---|---:|---:|---|
| **2× Válvulas/mangas flexibles (impulsión + retorno)** | Mangas tubulares ligeras (`Ø 11–13 cm`) en Ripstop/manta térmica con cordón elástico y cierre rápido al retirar el calentador | 36 | `25 Bs` | Mercería / camping |
| **Válvula de purga inferior + parche de desinflado rápido** | Lengüeta pasiva (*flapper*) con Kapton en panza baja + ventana superior con velcro fino y cordón de tiro | 16 | `10 Bs` | Mercería + sobrante de manta |
| **Subtotal B6** | | **52 g** | **`35 Bs`** | |

---

### B7. Aletas, Patines y Cintas de Poliéster Térmico + Kapton *(contabilizadas en `mad`)*

| Componente | Descripción | Opción Ligera en Bolivia | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---|---:|---:|---:|---|
| **Aletas estabilizadoras de cola (3 o 4)** | Estabilidad direccional del casco de `8.08 m` a `7.64 m/s` | Varilla **balsa `3 mm` / bambú** forrada con sobrante de manta (*est.: 4 aletas; opt.: 3 en Y invertida*) | 95 | 70 | `35 Bs` | **Librería Brasil**, Monoblock, tiendas cometas |
| **Patines + sujeción carga útil (`1.1 kg`) y LiPo** | Protección en aterrizaje + correas velcro/bridas | Varilla fibra `5 mm` / XPS + correas | 60 | 45 | `30 Bs` | Ferretería / mercería |
| **Cinta de poliéster térmico + cinta Kapton** | **Unión oficial del casco y celdas (`107.45 m²`)**, resistente hasta `180–260 °C` y contabilizada aquí en `mad` | Poliéster térmico PET ancho fino (`~0.5–0.6 g/m`) para paños/tabiques + **Kapton** (`10 mm`) en zonas calientes y refuerzos (`~140–180 m` totales con aplicación discontinua/solape optimizado) | 110 | 85 | `100 Bs` | **Sawers**, **EPY**, **EC Robotics**, ferreterías/serigrafía |
| **Subtotal B7** | | | **265 g** | **200 g** | **`165 Bs`** | |

---

## 5. Bloque C · Equipamiento en Tierra y Taller (`0 g` en vuelo)

| Elemento | Función | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---|
| **Emisora Radio Control FlySky FS-i6X (10 ch) + RX** | Control de vuelo, basculamiento y apagado `SG90` | `650 – 800 Bs` | **EPY Electrónica**, **Sawers**, **Ardunel** |
| **Receptor FPV 5.8 GHz OTG (celular/laptop)** | Visualización en vivo sin monitor pesado | `200 – 260 Bs` | Grupos **FPV Bolivia**, Marketplace |
| **Módulo LoRa SX1278 tierra + USB/ESP32** | Telemetría en tierra (`T2`, altura, batería) | `100 Bs` | **Sawers**, **EPY**, **Ardunel** |
| **Cargador balanceador LiPo iMAX B6** | Carga segura de batería LiPo 3S/4S | `220 – 280 Bs` | **EPY**, **Sawers**, **Hobby House Men** |
| **Calentador eléctrico compacto en tierra (`420×220×220 mm`)** | Caja con **9 resistencias eléctricas (`~4.5–6.5 kW`)**, ventilador axial interno, compuerta de aire fresco, 2 mangas flexibles (impulsión/retorno), sensor térmico y panel eléctrico (`~5–8 min`, `100 %` aire limpio sin GLP) | `350 – 550 Bs` | **Eloy Salmón**, ferreterías/resistencias industriales, **Feria 16 de Julio** |
| **Herramientas de corte y armado** | Tijeras, regla larga, bisturí/cúter y mesa de corte para las 37 mantas | `60 – 100 Bs` | Ferreterías / librerías |
| **Subtotal Bloque C (0 g en vuelo)** | | **`1,580 – 2,090 Bs`** | *(Omitir lo que ya se tenga disponible)* |

---

## 6. Resumen Consolidado de `mad` (`1,300 g`) y Presupuesto Total

### A. Comparativa de `mad` (Peso y Costo en Bolivia)

| Subsistema de `mad` | Peso Estándar (g) | Peso Optimizado (g) | Costo Estándar (Bs) | Costo Optimizado (Bs) |
|---|---:|---:|---:|---:|
| **B1.** Hélices, collets, ESCs y 2 servos basculamiento | 222 | 159 | 434 | 494 |
| **B2.** Controladora, GPS, NTCs, FPV, VTX y RX/LoRa | 98 | 67 | 785 | 915 |
| **B3.** Cableado de potencia, señal y conectores | 155 | 130 | 90 | 90 |
| **B4.** Estructura (góndola, bastidor H y arnés catenario) | 508 | 375 | 255 | 335 |
| **B5.** Calentador aéreo monotubo de etanol (`6.45 kW`) | 254 | 211 | 155 | 175 |
| **B6.** Válvulas/mangas de precalentamiento, purga y desinflado | 52 | 52 | 35 | 35 |
| **B7.** Aletas cola, patines, sujeción y cintas poliéster/Kapton | 265 | 200 | 165 | 165 |
| **TOTAL `mad` EN VUELO** *(meta `def`: `1,300 g`)* | **1,554 g** *(1.55 kg)* | **1,194 g** *(1.19 kg)* | **`1,919 Bs`** | **`2,209 Bs`** |

> **Lectura clave:**
> - Con la **Opción Realista Optimizada (`1,194 g`)**, quedas **`−106 g` por debajo** del presupuesto `mad = 1,300 g` del diseño definitivo `def`, manteniendo un margen constructivo real sin comprometer `637 W / 640 W`.
> - En la **Opción Estándar (`1,554 g`)**, ese exceso de `+254 g` obligaría a recortar `mcarga` (`1.10 → ~0.85 kg`) o incrementar flotación/potencia; por eso conviene cuidar peso especialmente en **B1 (ESC 4-en-1)**, **B4 (carbono + balsa)** y **B7 (aplicación racional de cinta)**.

### B. Presupuesto Global del Proyecto (Bolivia)

| Bloque | Costo Estándar (Bs) | Costo Optimizado (Bs) | Ya pagado (Bs) | Pendiente por gastar (Bs) |
|---|---:|---:|---:|---:|
| **Bloque A:** Manta térmica (`37` uds.), 4× A2212, LiPo y etanol | 1,511 – 1,636 | 1,511 – 1,636 | 470 (`440 + 30`) | 1,041 – 1,166 |
| **Bloque B (`mad`):** Subcomponentes de vuelo B1–B7 | 1,919 | 2,209 | 24 (hélices) | 1,895 – 2,185 |
| **Total Hardware de Vuelo (A + B)** | **~3,430 – 3,555 Bs** | **~3,720 – 3,845 Bs** | **494 Bs** | **2,936 – 3,351 Bs** |
| **Bloque C:** Equipo en tierra y taller *(si no se posee)* | 1,580 – 2,090 | 1,580 – 2,090 | 0 | 1,580 – 2,090 |
| **TOTAL GENERAL DEL PROYECTO** | **~5,010 – 5,645 Bs** | **~5,300 – 5,935 Bs** | **494 Bs** | **4,516 – 5,441 Bs** |

---

## 7. Potencia Auxiliar (`Pad = 45 W`) en el Diseño Definitivo `def`

En `def` se mantiene **`Pad = 45.0 W`** para dar holgura al **ventilador externo de mayor caudal** necesario para diluir `6.45 kW` por debajo de `150 °C`:

| Carga eléctrica auxiliar | Consumo estimado en vuelo (`def`) |
|---|---:|
| ESP32 + IMU + BMP280 + GPS + LoRa + RX | `~2.0 – 3.0 W` |
| Cámara FPV + VTX 5.8 GHz (`400–600 mW`) | `~2.5 – 4.0 W` |
| 2× MG90S (basculamiento) + 1× SG90 (quemador) | `~1.5 – 3.0 W` |
| Ventilador externo lateral de dilución (`~139–166 L/s`) | `~12.0 – 20.0 W` |
| Pérdidas en UBEC / reguladores | `~2.0 – 4.0 W` |
| **Consumo real estimado vs. modelo (`Pad`)** | **`~20 – 34 W`** *(se mantiene **`Pad = 45 W`** en `def` como margen seguro)* |

---

## 8. Plan de Acción Antes de Comprar el Lote Completo

1. **Pesar los tramos de cinta elegidos (`poliéster térmico + Kapton`):** verificar masa por metro (`g/m`) y confirmar que el trazado de costuras para `107.45 m²` de `1/1` capa permanezca bajo `~100 g`.
2. **Pesar las 4 hélices `1045`/`1045R` y 1 motor A2212 con collet:** validar pesos reales de arranque para `N·mmot` y `B1`.
3. **Ensayar en banco el calentador aéreo monotubo (`165 mL` etanol) y el calentador eléctrico en tierra:** validar consumo (`~25.7 mL/min`), estabilidad de llama con ventilador lateral, temperatura en difusor (`<= 150 °C`), y temperatura/tiempo de recirculación (`~5–8 min`) en el calentador eléctrico antes de ensamblar todo el casco de `37` mantas.
4. **Cotizar por WhatsApp antes de comprar:** **Sawers**, **EPY Electrónica**, **Ardunel** y **Hobby House Men** (LiPo `~494 g`), más tiendas de pesca en **Uyustus / Eloy Salmón** (varillas de carbono + hilo trenzado).
