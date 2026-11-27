# Presupuesto de Fabricación, Desglose de Pesos (`mad`) y Guía de Compra en Bolivia

Documento técnico-económico de referencia para el **Dirigible Híbrido de Aire Caliente + 4 Motores A2212 (1000KV)**, calibrado sobre el modelo consolidado **`v2`** ([modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py), [evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py)) y el último diseño guardado en [historico_disenos.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/historico_disenos.json) (`2026-11-27 12:50`, configuración **`v3`**).

---

## 1. Contexto del Diseño Actual (`v3`) y Estructura de Masas

En la configuración `v3` (`2/2` capas de manta térmica de `12 µm`, `e = 32 mm`, `T2 = 114.9 °C`, `mcarga = 1.20 kg`, `nv = 2` viajes de `280 m` con viento `vv = 6.0 m/s`), las dimensiones y parámetros principales del prototipo son:

| Parámetro | Valor en `v3` | Referencia |
|---|---|---|
| Dimensiones exteriores (`L × D`, `V`) | `7.161 m × 2.279 m` (`19.48 m³`) | [historico_disenos.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/historico_disenos.json) |
| Superficie casco (`S`) / Película total (`Sc`) | `41.98 m²` / `152.80 m²` | Casco + `2/2` capas + tabiques |
| Bastidor en H + Góndola (referencia CAD) | Góndola `600×300×250 mm`, `z_mot ≈ 550 mm`, `dx_mot = 420 mm` | [generar_cad_solidworks.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_solidworks.py) |
| Potencia motriz pico (`Pelec` / tope `Pmax`) | `639.6 W` / `640.0 W` | Al límite exacto del hardware |
| Consumo eléctrico auxiliar supuesto (`Pad`) | `45.0 W` | Sobreestimado; ver Sección 7 |
| Masa adicional agrupada (`mad`) | `1,300 g` (`1.30 kg`) | Objetivo: detallar y reducir |

En [modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py#L666-L671), la masa total del artefacto es:

$$\text{mart} = m_c + N \cdot m_{\text{mot}} + m_p + m_{\text{ad}} + m_{\text{bat}}, \qquad m_{\text{tot}} = \text{mart} + m_{\text{carga}}$$

Para evitar duplicaciones ni omisiones, los componentes se dividen en tres bloques:
- **Bloque A (en vuelo, fuera de `mad`):** película del casco (`mc`), los 4 motores A2212 pelados (`N·mmot`), el etanol líquido (`mp`) y la batería LiPo (`mbat`).
- **Bloque B (en vuelo, dentro de `mad`):** todo el resto del hardware, estructura, aviónica, calefactor, válvulas, cableado y extras que hoy se engloban en `mad = 1,300 g`.
- **Bloque C (`0 g` en vuelo):** equipamiento en tierra (emisora, receptor FPV, cargador, precalentador y herramientas de fabricación).

---

## 2. Alerta Prioritaria de Verificación: Manta Térmica (Camping Bag Bolivia)

Datos reales cotizados para la manta térmica de **Camping Bag Bolivia**:
- **Medidas por unidad:** `160 × 210 cm = 3.36 m²`.
- **Precio unitario:** **`30 Bs`** (1 ejemplar ya adquirido para pruebas).
- **Precio al por mayor:** **`18 Bs`** por manta.
- **Cantidad estimada para `Sc = 152.80 m²` (+15 % merma por cortes curvos y tabiques = `~176 m²`):** **`53 mantas`** (`176 / 3.36 ≈ 52.4`).
  - Compra total: 1 ya adquirida (`30 Bs`) + 52 al por mayor (`52 × 18 Bs = 936 Bs`) = **`966 Bs`** *(o `954 Bs` si las 53 entran al precio mayorista)*.

> [!WARNING]
> **Riesgo crítico de peso en `sigma` (`g/m²`) para la manta de `12 µm`:**
> En el registro `v3` se cambió el espesor `ep` de `6 µm` a `12 µm`, **pero el gramaje `sigma` quedó en `8.4 g/m²`** (que corresponde a `6 µm` de PET: $6\;\mu\text{m} \times 1.40\;\text{g/cm}^3 = 8.4\;\text{g/m}^2$).
>
> Una manta comercial de `12 µm` suele pesar **`15–16.8 g/m²`** ($\approx 50\text{–}56\;\text{g}$ por manta entera). Al evaluar `sigma = 16.8 g/m²` directamente en [evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py), `mc` salta de **`1,283 g`** a **`2,567 g`**, elevando `Pelec` a **`1,274 W`** (inviable con `2/2` capas y `N=4`).
>
> **Acción inmediata:** Pesa tu ejemplar entero de `160 × 210 cm` en una balanza gramera y divide por `3.36`:
> $$\sigma\;(\text{g/m}^2) = \frac{\text{Peso de 1 manta (g)}}{3.36}$$
> - Si pesa `~28–30 g` $\rightarrow$ `sigma ≈ 8.4–8.9 g/m²` (los cálculos de `v3` se mantienen válidos).
> - Si pesa `~50–56 g` $\rightarrow$ `sigma ≈ 15–16.8 g/m²` (deberás actualizar `sigma` y re-optimizar capas `ncapS/ncapI`, por ejemplo a `1/1` o `2/1` con menor `e`).

---

## 3. Bloque A · Componentes en Vuelo FUERA de `mad` (Ya Modelados Aparte)

| Componente | Variable | Estado | Peso (g) | Precio en Bolivia (Bs) | Dónde comprar en Bolivia | Notas |
|---|---|---|---:|---:|---|---|
| **Manta térmica `160×210 cm` (~53 uds.)** | `mc` | **1 comprada** + 52 por comprar | `1,283` *(si $\sigma=8.4$)* | **`966 Bs`** (`30 + 52×18`) | **Camping Bag Bolivia** | Pesar el ejemplar disponible para confirmar `sigma`. |
| **4× Motores Brushless A2212 1000KV** | `N·mmot` | **Ya comprados** | `188` (`4 × 47 g`) | **`440 Bs`** (`110 Bs` c/u) | Ya adquiridos | Peso solo del cuerpo motor; hélices, collets y ESCs van en `mad`. |
| **Batería LiPo 3S (11.1 V) o 4S (~4500–5200 mAh)** | `mbat` | Por comprar | `496` *(según modelo)* | **`375 – 500 Bs`** | **Hobby House Men** (SCZ/envíos), **Sawers**, **EPY Electrónica**, grupos RC/FPV | Ref. local: LiPo 3S 2200 mAh 25C ~`315 Bs`, 3S 1800 mAh 75C ~`500 Bs`; el modelo estima `750 Bs/kg` (`~372 Bs`). Conviene tasa $\ge 20\text{C}$ (~`60 A` pico en 3S). |
| **Combustible Etanol 96 % (carga útil de vuelo)** | `mp` | Consumible | `64` | **`18 Bs / L`** (`~1.5 Bs`/vuelo) | Farmacias / distribuidores de alcohol potable | Depósito, quemador y manguera van en `mad`. |
| **Subtotal Bloque A** | | `440 + 30 = 470 Bs` pagados | **~2,031 g** | **`1,781 – 1,908 Bs`** *(pendiente: `1,311 – 1,438 Bs`)* | | |

---

## 4. Bloque B · Desglose Realista de `mad` en Bolivia

A continuación se comparan dos alternativas viables dentro del mercado boliviano:
- **Opción Realista Estándar (Bolivia):** componentes de stock inmediato en tiendas locales de La Paz, Cochabamba y Santa Cruz o ferreterías/librerías, aplicando aligeramiento básico (quitar carcasas plásticas y cables sobrantes).
- **Opción Realista Optimizada (Bolivia):** mismos canales locales más piezas más ligeras de grupos FPV/aeromodelismo o adaptación ingeniosa local (ej. tramos de caña de pescar de carbono en lugar de fibra de vidrio, micro-ESCs/4-en-1, góndola abierta).

### B1. Propulsión complementaria y basculamiento (`θ ≤ 75°`)

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia | Notas clave |
|---|---|---|---:|---:|---:|---|---|
| **4× Hélices `1045` / `1045R` negras (~26 cm)** | **Ya compradas** (`1045` + `1045R`) | Mismas ya compradas | 56 | 56 | **`24 Bs`** *(ya pagado)* | Ya adquiridas (`12 Bs`/par) | Pesar las 4 juntas (~14 g c/u estimado). |
| **4× Adaptadores collet + tornillos M3** | Collet aluminio (con motores) + montaje directo sin cruz metálica | Igual | 28 | 28 | `0 Bs` | Incluidos con A2212 | Evitar la cruz de acero ahorra `~24 g`. |
| **4× Variadores ESC (30–45 A)** | **4× ESC 30A SimonK / XXD** sin funda termoencogible gruesa ni conectores bala, cerca de los motores | **1× ESC 4-en-1 35–45A** (`15 g`) o **4× micro-ESC BLHeli_S 30A** (`24 g`) | 76 | 20 | `320 Bs` *(est.)* / `380 Bs` *(opt.)* | **Ardunel** (`~79–83 Bs`/u), **Sawers**, **EPY Electrónica**, **i2C** / grupos FPV Bolivia | Sin aligerar, 4 ESC 30A pesan `~96–100 g`. |
| **Servos de basculamiento + mecanismo** | **2× MG90S metálicos** (`13.4 g`, `2.2 kg·cm` a `6 V`) moviendo **2 ejes compartidos** (par izq. + par der.) + 4 bujes/rodamientos `688ZZ` + soportes PETG | Igual (alineados al eje del motor para mínimo par) | 62 | 55 | `90 Bs` (`2×30 Bs` + `30 Bs` bujes/soportes) | **Ardunel** (`~24–26 Bs`), **Sawers**, **EPY**, **EC Robotics / i2C** (`~35 Bs`) | **Por qué 2 servos alcanzan:** con eje alineado, el par por empuje (`5.5 N × 0.01 m ≈ 0.56 kg·cm`) es `< 1/3` del torque del MG90S. Mantiene control completo de *pitch*, *roll* (diferencial de acelerador) y *yaw* (inclinación diferencial izq./der.). |
| **Subtotal B1** | | | **222 g** | **159 g** | **`434 Bs`** *(est.)* / **`494 Bs`** *(opt.)* | | **`24 Bs` ya pagados** (hélices). |

---

### B2. Placa de control, cámara FPV, sensores y enlace de datos

> **Por qué no usar ESP32-CAM ni Wi-Fi a 70 m de altura:** El enlace Wi-Fi sufre cortes y latencia severa a `70 m` de altura y `300–600 m` de distancia con viento. El estándar más ligero y confiable disponible en Bolivia es **video analógico 5.8 GHz + radio control `2.4 GHz` (FlySky) + telemetría LoRa `433 MHz`**.

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia | Notas clave |
|---|---|---|---:|---:|---:|---|---|
| **Placa de control + IMU + Barómetro + BEC** | **ESP32 DevKit** (`10 g`) + **MPU6050** (`3 g`) + **BMP280** (`1.5 g`) + **UBEC 5V/6V 5A** (`12 g`, o usar BEC de ESCs + mini step-down `5 g`) | **ESP32-S3 Mini** + **GY-91** (MPU9250+BMP280) + mini BEC/step-down | 27 | 18 | `165 Bs` *(est.)* / `195 Bs` *(opt.)* | **Sawers**, **EPY Electrónica**, **Ardunel**, **Eloy Salmón (LP)** | *Alternativa sin programar PID desde cero:* **APM 2.8 / Pixhawk 2.4.8 sin carcasa** (`~30 g`, `450–900 Bs` en **TecBolivia / Sawers / EPY**). |
| **GPS + Brújula** | **u-blox NEO-M8N / NEO-6M sin carcasa plástica** | Igual sin carcasa ni cable largo | 17 | 14 | `125 Bs` | **Ardunel** (`~115–130 Bs`), **EPY Electrónica**, **Sawers** | Retirar la carcasa plástica ahorra `~15 g`. Necesario para mantener posición contra viento de `6 m/s`. |
| **Sensores de temperatura** | **2× Termistores NTC 100k** cápsula vidrio (`3950K`) + cable fino AWG 28/30 al techo del casco y difusor | Igual | 15 | 13 | `40 Bs` (`2×15 Bs` + cable) | **Sawers**, **EPY Electrónica**, **Ardunel** | Vigila el límite crítico del techo (`115 °C`) y la mezcla en chimenea (`120–150 °C`). |
| **Cámara FPV + VTX 5.8 GHz + Antena** | Cámara FPV CMOS básica (`6 g`) + VTX `TS5828` `600 mW` sin carcasa (`10 g`) + antena dipolo/clover ligera (`6 g`) | Micro cámara FPV + nano VTX `200–400 mW` + dipolo cobre (`~10 g` conjunto) | 22 | 12 | `390 Bs` *(est.)* / `430 Bs` *(opt.)* | Grupos **FPV Bolivia / Aeromodelismo**, **TecBolivia**, **EPY**, Marketplace | Calidad analógica más que suficiente para distinguir edificios, cerros y zona de aterrizaje a `70 m`. |
| **Receptor RC + Telemetría** | Receptor **FlySky FS-iA6B sin carcasa** (`10 g`, viene con emisora) + **LoRa SX1278 / Ra-02 433 MHz** con antena alambre (`7 g`) | Receptor **FlySky FS-X6B / FS-A8S** (`4 g`) + **LoRa SX1278** (`6 g`) | 17 | 10 | `65 Bs` *(est., solo LoRa)* / `165 Bs` *(opt., +RX mini)* | **Sawers**, **EPY**, **Ardunel** (LoRa); grupos RC / **EPY** (FS-A8S) | LoRa envía en tiempo real `T2`, altura barométrica, GPS y voltaje de batería a tierra. |
| **Subtotal B2** | | | **98 g** | **67 g** | **`785 Bs`** *(est.)* / **`915 Bs`** *(opt.)* | | |

---

### B3. Cableado de potencia, señal y conectores *(faltaba en lista original)*

Con las distancias de [generar_cad_solidworks.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_solidworks.py#L148-L156) (`z_mot ≈ 0.55 m`, `dx_mot = 0.42 m`, `~1.0 m` de recorrido desde el centro de la góndola):

| Elemento | Configuración recomendada | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---:|---:|---|
| **Cableado de potencia a motores** | **ESCs junto a los motores/brazos:** 2 hilos DC silicona **AWG 16/18** por costado (`~4 m` totales) + tramos trifásicos cortos (`<15 cm`). *Evita llevar 12 m de cable trifásico desde la góndola (`+40 g`).* | 100 | 85 | `55 Bs` | **Eloy Salmón**, **EPY Electrónica**, **Sawers** |
| **Cables de señal PWM, servos, sensores y bridas** | AWG 28/30 para señal ESC/servos/NTC + conector **XT60** (`7 g`) + cable batería (`15 g`) + termocontraíble/bridas (`13 g`) | 55 | 45 | `35 Bs` | **EPY Electrónica**, **Sawers**, **Eloy Salmón** |
| **Subtotal B3** | | **155 g** | **130 g** | **`90 Bs`** | |

---

### B4. Estructura: Góndola, Bastidor en H y Arnés de suspensión

Tomando las `~6.4 m` de tubería total del diseño CAD (`3.88 m` para brazos transversales + largueros en H, y `2.50 m` para 2 puntales + 4 tirantes diagonales):

| Componente | Opción Realista Estándar (Bolivia) | Opción Realista Optimizada (Bolivia) | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---|---:|---:|---:|---|
| **Bastidor en H (`3.88 m`)** | **Varillas huecas de fibra de vidrio para carpa (`Ø 8 mm`)** sin casquillos de acero (`~52 g/m`) | **Tramos de caña de pescar telescópica de carbono** (secciones gruesas, `~38–42 g/m`) | 202 | 155 | `80 Bs` *(est.)* / `150 Bs` *(opt.)* | **Camping Bag Bolivia**, calle **Uyustus**, **Feria 16 de Julio** (carpas); tiendas de pesca **Uyustus / Eloy Salmón** (cañas) |
| **Puntales + 4 tirantes (`2.50 m`)** | **Varillas fibra de vidrio `5–6 mm`** o varilla bambú/balsa reforzada (`~28 g/m`) | **Puntas de caña de carbono** (`~18 g/m`) | 70 | 45 | `40 Bs` *(est.)* / `50 Bs` *(opt.)* | Tiendas de pesca, **Librería Brasil**, **Fibracenter** |
| **8× Uniones / abrazaderas del bastidor** | Piezas impresas en 3D PETG pared fina o atado con hilo + resina epoxi | Atado directo con hilo carbono/nylon + cianoacrilato/epoxi | 56 | 35 | `30 Bs` | Impresión 3D local / ferretería (Poxipol / epoxi) |
| **Góndola (compactada a `400×220×180 mm`)** | Caja ligera en **Tecnopor alta densidad / XPS `6 mm`** + piso de **madera balsa `3 mm`** | **Esqueleto abierto** de varilla balsa/carbono + base mínima de balsa `3 mm` (`90 g`) | 125 | 90 | `45 Bs` | **Librería Brasil** / zona **Monoblock–Camacho** (`6–12 Bs`/plancha balsa), **Tecnopor Ltda.** |
| **Arnés catenario de suspensión al casco** *(faltaba en lista)* | **Parches catenarios de tela Ripstop / cinta filamento** + **hilo trenzado de pesca PE/Dyneema `0.5 mm`** (reparte los `~3.2 kg` sin rasgar la manta de `12 µm`) | Igual | 55 | 50 | `60 Bs` | Tiendas de pesca (**hilo multifilamento/trenzado**) + mercería/camping (Ripstop) |
| **Subtotal B4** | | | **508 g** | **375 g** | **`255 Bs`** *(est.)* / **`335 Bs`** *(opt.)* | |

---

### B5. Calefactor en Aire (Quemador Capilar de Etanol — [texto.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/texto.md))

Arquitectura vertical de 3 etapas (`2–3 kW`, mezcla con aire frío inferior a `120–150 °C` para proteger la manta térmica):

| Componente | Opción Más Ligera Conseguible en Bolivia | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---:|---:|---|
| **Copa capilar + camisa cortaviento + chimenea + difusor** | Fabricación artesanal en **lámina de aluminio `0.12–0.15 mm`** (aluminio fino de latas de bebida / lámina de repostería o ferretería, `~0.20 m²` totales para Ø11×35 cm + cono Ø25 cm) + alambre/remaches aluminio | 135 | 120 | `30 Bs` | Ferreterías / tiendas de insumos de repostería / reciclaje de latas |
| **Mecha capilar + malla apagachispas + depósito** | Retazo de **manta de fibra cerámica** (`10 g`, retiene el etanol sin derrames al cabecear) + **malla inox fina** de colador (`10 g`) + botella PET `100 mL` y manguera silicona (`22 g`) | 42 | 40 | `47 Bs` | Casas de refractarios/estufas o **Refrak** (fibra cerámica), bazar/ferretería (colador inox), farmacia (manguera) |
| **Ventilador de dilución (`5–8 W`)** | *Estándar:* **Axial 12V `80×80×25 mm`** recortando esquinas del marco (`60 g`). *Optimizada:* **Axial 12V `60×60×15 mm` de alta RPM** o micro-motor brushless + hélice 3" (`35–42 g`). | 60 | 38 | `25 Bs` *(est.)* / `65 Bs` *(opt.)* | **Eloy Salmón**, **Sawers**, **EPY Electrónica** |
| **Apagado / control remoto de llama en vuelo** | **1× Microservo SG90 (`9 g`)** + paleta corrediza de aluminio (`5 g`) para cerrar/regular la boca del quemador en vuelo *(encendido en tierra = `0 g` de ignitor)* | 14 | 14 | `20 Bs` | **Ardunel**, **Sawers**, **EPY Electrónica** (`~15–20 Bs`) |
| **Subtotal B5** | | **251 g** | **212 g** | **`122 Bs`** *(est.)* / **`162 Bs`** *(opt.)* | |

---

### B6. "Válvulas" de Precalentamiento en Tierra y Alivio en Vuelo

Al operar a presión atmosférica (`0–30 Pa` de sobrepresión), **no se requieren válvulas mecánicas rígidas ni pesadas**:

| Elemento | Solución Más Ligera (100 % local) | Peso (g) | Precio aprox. (Bs) | Dónde comprar / fabricar |
|---|---|---:|---:|---|
| **Puerto de precalentamiento en tierra** | **Manga tubular flexible** (`Ø 18 cm × 30 cm`) de tela Ripstop o sobrante de manta térmica en la panza trasera, con **cordón elástico y tensor plástico** para sellar tras retirar el soplador | 20 | `15 Bs` | Mercería / camping (tela + elástico + tensor) |
| **Válvula de purga inferior (`~2 L/s`)** | **Lengüeta pasiva (*flapper valve*)** recortada del propio Mylar + borde con cinta Kapton en la zona más baja y fría | 4 | `0 Bs` | Sobrante de manta térmica |
| **Parche de desinflado rápido en tierra** | Ventana superior pequeña cerrada con **velcro fino + cordón de tiro** (evita arrastre por viento al aterrizar) | 12 | `10 Bs` | Mercería |
| **Subtotal B6** | | **36 g** | **`25 Bs`** | |

---

### B7. Otros Componentes Críticos Omitidos en la Lista Original

| Componente omitido | Por qué es indispensable | Opción Ligera en Bolivia | Peso Estándar (g) | Peso Optim. (g) | Precio aprox. (Bs) | Dónde comprar en Bolivia |
|---|---|---|---:|---:|---:|---|
| **Aletas estabilizadoras de cola (3 o 4)** | Sin empenaje, un casco de `7.16 m` a `7.7 m/s` es direccionalmente inestable y obliga a los motores a corregir todo el tiempo | Marco de **varilla balsa `3 mm` / varilla bambú** forrado con sobrante de manta térmica (*est.: 4 aletas; opt.: 3 aletas en Y invertida*) | 90 | 65 | `30 Bs` | **Librería Brasil**, zona **Monoblock**, tiendas de cometas |
| **Patines / tren de aterrizaje** | Protege el quemador inferior, cámara y hélices al aterrizar con viento | 2 arcos de **varilla fibra `5 mm`** o espuma XPS | 35 | 25 | `20 Bs` | Ferretería / repuesto carpa / librerías |
| **Sujeción carga útil (`1.2 kg`) y batería (`0.5 kg`)** | Fijación segura ante inclinaciones | Correas velcro + bridas + plaquita fina | 25 | 20 | `15 Bs` | Mercería / ferretería |
| **Cinta Kapton `10 mm × 33 m` (uniones parciales)** | **⚠️ Ver nota:** solo para costuras principales y zonas calientes; las celdas deben **termosellarse** | 3 rollos (`~0.68 g/m`, uso ~80 m en zonas críticas) | 55 | 45 | `60 Bs` (`3×20 Bs`) | **Sawers**, **EPY**, **EC Robotics**, **SK Bolivia** (`~15–25 Bs`/rollo) |
| **Subtotal B7** | | | **205 g** | **155 g** | **`125 Bs`** | |

> [!CAUTION]
> **Por qué NO debes pegar toda la cuadrícula con cinta:**
> Una cinta Kapton de `10 mm` pesa `~0.68 g/m`. Unir `152.8 m²` de cuadrícula celular (`W = 20 cm`) con cinta continua consumiría `400–800 m` de cinta = **`270–550 g` de peso muerto extra**. Debes **termosellar** las celdas de la manta térmica (cautín regulado con punta ancha sobre papel teflón/horno) y reservar la cinta Kapton únicamente para refuerzos, vértices, válvulas y proximidad del difusor caliente.

---

## 5. Bloque C · Equipamiento en Tierra y Taller (`0 g` en vuelo)

| Elemento | Función | Precio aprox. en Bolivia (Bs) | Dónde comprar en Bolivia |
|---|---|---:|---|
| **Emisora Radio Control FlySky FS-i6X (10 ch) + RX** | Control de vuelo y basculamiento hasta `>1 km` | `650 – 800 Bs` *(FS-i6 6 ch ~500 Bs)* | **EPY Electrónica**, **Sawers**, **Ardunel**, **Electrónica Cyber** |
| **Receptor FPV 5.8 GHz OTG (celular/laptop)** | Ver video de la cámara en tierra sin monitor pesado | `200 – 260 Bs` *(monitor/gafas ~450 Bs)* | Grupos **FPV Bolivia**, Marketplace, importación |
| **Módulo LoRa SX1278 tierra + adaptador USB/ESP32** | Recibir telemetría de `T2`, altura y batería en laptop | `100 Bs` | **Sawers**, **EPY**, **Ardunel** |
| **Cargador balanceador LiPo iMAX B6 (con fuente)** | Carga segura de batería LiPo 3S/4S | `220 – 280 Bs` | **EPY**, **Sawers**, **Hobby House Men** |
| **Precalentador externo en tierra** | **Soplador eléctrico 400–600 W** (`160–220 Bs`) + **soplete/quemador GLP** para garrafa doméstica + tubo metálico deflector (`100–150 Bs`) | `260 – 370 Bs` | Calle **Uyustus**, **Feria 16 de Julio** (El Alto), ferreterías |
| **Cautín regulado + lámina/cinta teflón** | Termosellado limpio de las celdas de manta térmica | `120 – 160 Bs` | **Eloy Salmón**, **Sawers**, ferreterías |
| **Subtotal Bloque C (0 g en vuelo)** | | **`1,550 – 1,970 Bs`** | *(Se omite lo que ya tengas disponible)* |

---

## 6. Resumen Consolidado de `mad` y Presupuesto Total

### A. Comparativa de `mad` (Peso y Costo en Bolivia)

| Subsistema de `mad` | Peso Estándar (g) | Peso Optimizado (g) | Costo Estándar (Bs) | Costo Optimizado (Bs) |
|---|---:|---:|---:|---:|
| **B1.** Hélices, collets, ESCs y 2 servos basculamiento | 222 | 159 | 434 | 494 |
| **B2.** Placa de control, GPS, NTCs, cámara FPV, VTX y RX/LoRa | 98 | 67 | 785 | 915 |
| **B3.** Cableado de potencia, señal y conectores | 155 | 130 | 90 | 90 |
| **B4.** Estructura (góndola, bastidor H y arnés catenario) | 508 | 375 | 255 | 335 |
| **B5.** Calefactor capilar de etanol en aire + ventilador + obturador | 251 | 212 | 122 | 162 |
| **B6.** Válvulas en vuelo (manga precalent., purga y desinflado) | 36 | 36 | 25 | 25 |
| **B7.** Extras críticos (aletas cola, patines, sujeción, cinta parcial) | 205 | 155 | 125 | 125 |
| **TOTAL `mad` EN VUELO** | **1,475 g** *(1.48 kg)* | **1,134 g** *(1.13 kg)* | **`1,836 Bs`** | **`2,146 Bs`** |

> **Lectura clave:**
> - Con materiales estándar sin cuidado de peso (`1.48 kg`), quedarías **`+175 g` por encima** del `mad = 1.30 kg` asumido en `v3`.
> - Con la **Opción Realista Optimizada en Bolivia (`~1.13 kg`)**, bajas **`-166 g`** respecto al `1.30 kg` actual (y con un ajuste fino adicional en cableado/aletas puedes acercarte a **`~1.05 kg`**).

### B. Presupuesto Global del Proyecto (Bolivia)

| Bloque | Costo Estándar (Bs) | Costo Optimizado (Bs) | Ya pagado (Bs) | Pendiente por gastar (Bs) |
|---|---:|---:|---:|---:|
| **Bloque A:** Manta térmica (`53` uds.), 4× A2212, batería LiPo y etanol | 1,781 – 1,908 | 1,781 – 1,908 | 470 (`440 + 30`) | 1,311 – 1,438 |
| **Bloque B (`mad`):** Subcomponentes de vuelo B1–B7 | 1,836 | 2,146 | 24 (hélices) | 1,812 – 2,122 |
| **Total Hardware de Vuelo (A + B)** | **~3,617 – 3,744 Bs** | **~3,927 – 4,054 Bs** | **494 Bs** | **3,123 – 3,560 Bs** |
| **Bloque C:** Equipo en tierra y taller *(si no se posee)* | 1,550 – 1,970 | 1,550 – 1,970 | 0 | 1,550 – 1,970 |
| **TOTAL GENERAL DEL PROYECTO** | **~5,167 – 5,714 Bs** | **~5,477 – 6,024 Bs** | **494 Bs** | **4,673 – 5,530 Bs** |

---

## 7. Ahorro en Potencia Auxiliar (`Pad`) e Impacto en el Simulador

En `v3` se asumió **`Pad = 45 W`**, pero el consumo real del equipamiento seleccionado es menos de la mitad:

| Carga eléctrica auxiliar | Consumo promedio real |
|---|---:|
| ESP32 + MPU6050 + BMP280 + GPS NEO-M8N + LoRa + RX | `~1.5 – 2.5 W` |
| Cámara FPV + VTX 5.8 GHz (`400–600 mW`) | `~2.5 – 3.5 W` |
| 2× MG90S (basculamiento) + 1× SG90 (quemador) promedio | `~1.5 – 2.5 W` |
| Ventilador de dilución 12V en chimenea del quemador | `~4.0 – 6.0 W` |
| Pérdidas en UBEC / reguladores | `~1.5 – 2.0 W` |
| **Total real (`Pad`)** | **`~11 – 16.5 W`** *(usar **`Pad = 20 W`** con margen)* |

Al introducir estos valores optimizados pero realistas para Bolivia en el evaluador del proyecto ([evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py)), manteniendo `T2 = 114.9 °C`, `mcarga = 1.20 kg` y `vv = 6.0 m/s`:

| Escenario sobre `v3` (`σ = 8.4 g/m²`) | `mtot` | `mres` | `mbat` | `Pelec` pico (límite `640 W`) | `Pcruc` | `Ttot` | `θman` |
|---|---:|---:|---:|---:|---:|---:|---:|
| **Actual `v3`** (`mad = 1.30 kg`, `Pad = 45 W`) | `4.532 kg` | `0.680 kg` | `496 g` | `639.6 W` *(al límite)* | `470.3 W` | `13.08 N` | `55.1°` |
| **Optimizado Bolivia** (`mad = 1.05 kg`, `Pad = 20 W`) | **`4.224 kg`** | `0.372 kg` | **`438 g`** (`-58 g`) | **`584.4 W`** (`55.6 W` libres) | **`419.9 W`** | `11.57 N` | `67.3°` |

*(Al re-optimizar posteriormente `mflot` y el tamaño del casco con `mad ≈ 1.13 kg` y `Pad = 20 W`, ese margen de `55 W` permite encoger el casco o recuperar un ángulo `θ` más bajo).*

---

## 8. Plan de Acción Inmediata (Antes de Comprar al por Mayor)

1. **Pesar tu ejemplar de manta térmica (`160×210 cm`):** calcular $\sigma = \text{peso(g)} / 3.36$. Este dato define si el diseño `v3` se mantiene o si hay que re-optimizar capas `ncapS/ncapI` antes de comprar las `~52` mantas restantes.
2. **Pesar las 4 hélices `1045`/`1045R` y 1 motor A2212 con su collet:** confirmar exactamente cuántos gramos reales corresponden a `N·mmot` y al inicio de `mad`.
3. **Hacer prueba de termosellado en un retazo de la manta:** verificar temperatura de cautín/selladora sobre papel teflón para asegurar costuras resistentes sin usar rollos pesados de cinta continua.
4. **Cotizar por WhatsApp en paralelo** antes de comprar: **Sawers** (`65589882` LP), **EPY Electrónica**, **Ardunel** y **Hobby House Men** (para la LiPo 3S/4S de `~450–500 g`), además de **tiendas de pesca en Uyustus/Eloy Salmón** (tramos de caña de carbono + hilo trenzado).
5. **Actualizar en la calculadora (`app.py` / `diseno.py`)** los valores reales medidos de `sigma`, `mad` (`~1.13 kg`) y `Pad` (`20 W`) y volver a correr el optimizador para congelar las medidas finales antes de cortar la manta térmica.
