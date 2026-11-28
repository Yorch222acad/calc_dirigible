# Resumen Final del Diseño: Dirigible Híbrido y Calentador de Etanol

Documento de cierre que consolida la configuración definitiva del **dirigible híbrido de aire caliente (`def`)**, la arquitectura final elegida para el **calentador aéreo de etanol**, las **macros 3D de SolidWorks** disponibles y las verificaciones físicas recomendadas antes de construir y volar.

---

## 1. Configuración Definitiva del Dirigible (`def`)

Calibrado sobre el modelo físico-matemático auditado **`v2`** ([modelo.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py), [evaluador.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py)) para las condiciones de **La Paz (`P1 = 67,120 Pa`, `T1 = 15.0 °C`)**, usando los datos reales medidos de la manta térmica **FIRSTIME (`160 × 210 cm = 3.36 m²`, `59 g` medidas $\rightarrow$ `17.0–17.56 g/m²`, espesor `12 µm`)**, con la cara plateada hacia el interior (`eps = 0.08`) y uniones con cinta de poliéster térmico / Kapton (`T2 <= 115 °C`).

Fuente exacta: [historico_dirigible_2026-11-27_def.json](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json) (`id = f53b37f3b5`, **Score `42.01`**, **`0` alertas**).

| Área | Parámetro | Valor definitivo (`def`) |
|---|---|---|
| **Geometría del casco** | Longitud × Diámetro (`L × D`) | **`8.083 m × 2.275 m`** (`cf = 2.829 m`, `cr = 5.254 m`, `λ = 3.55`) |
| | Volumen total (`V` = `Vnuc` + `Vcel`) | **`21.90 m³`** (`20.64 m³` núcleo + `1.25 m³` celdas) |
| | Superficie casco / Película total (`S` / `Sc`) | **`46.91 m²` / `107.45 m²`** |
| **Aislamiento celular** | Capas simétricas (`ncapS / ncapI`) | **`1 / 1` capa** (`e = 29.1 mm`, `W = 20 cm`) |
| | Película Mylar (`ep`, `σ`, `mc`) | `12 µm` · `17.0 g/m²` · **`1,826.7 g`** |
| **Térmica** | Temperatura interna (`T2`) | **`114.8 °C`** (límite seguro `115 °C`) |
| | Pérdida térmica (`Qp`) y ahorro (`fais`) | **`6,454.6 W`** (`U = 1.379 W/(m²·K)`, `69.5 %` de ahorro frente a casco sin celdas) |
| | Enfriamiento pasivo (`dTc = 20 K`) | **`tc = 44.7 s`** |
| **Masas y carga** | Flotabilidad / Residual / Total (`mflot` / `mres` / `mtot`) | **`4.460 kg`** (`88.5 %`) / `0.581 kg` / **`5.041 kg`** |
| | Carga útil instalada (`mcarga`) | **`1.10 kg`** (margen estructural adicional hasta `1.1135 kg`) |
| **Masa adicional (`mad`) / Batería (`mbat`) / Etanol (`mp`)** | `1.30 kg` *(incluye cintas)* / `494.2 g` / `131.7 g` |
| **Propulsión y vuelo** | Motores (`4 × A2212 1000KV`, hélice `1045`) | `Pelec = 637.0 W` (pico) / `Pcruc = 449.8 W` (`Ttot = 12.91 N`, `θ = 59.2°`) |
| | Velocidad aire / suelo (`v` / `vg`, con viento `vv = 6 m/s`) | **`7.64 m/s`** / **`1.64 m/s`** |
| | Misión objetivo (`2 × 270 m = 540 m`) | Duración **`328.6 s` (`~5.5 min`)** · Autonomía máxima **`626 m`** (`2.3` viajes) |
| **Energía y costos** | Precalentamiento en tierra (`Epre`) | `1,986.8 kJ` (`0.477 Bs`) |
| | Etanol consumido en vuelo (`mgm`) / Batería (`Ereq`) | `113.12 g` (`2.036 Bs`) / `47.04 Wh` (`0.040 Bs`) |
| | Costo operativo total (`Cop`) | **`2.553 Bs` por misión** (recambio batería: `370.63 Bs`) |

---

## 2. Arquitectura Final del Calentador Aéreo con Etanol

### Requerimiento térmico base (`def`)
- Potencia útil a reponer en vuelo: **`Qp = 6,454.6 W`**.
- Con rendimiento térmico de combustión `ncal = 0.75`, la potencia química requerida es **`~8,606.1 W`**.
- Consumo de etanol 96 %: **`0.344 g/s` (`20.65 g/min` / `25.66 mL/min`)**, totalizando **`113.1 g` (`~140.5 mL`)** quemados en los `328.6 s` de misión y **`131.7 g` (`~163.6 mL`)** cargados a bordo con reserva.
- Para evitar chorros a alta temperatura sobre el Mylar (`12 µm`), se inyecta aire frío de dilución (`~139–166 L/s`) para entregar la mezcla a **`<= 150 °C`**.

### Solución final adoptada: **Monotubo Simplificado con Ventilador Externo y Difusor**
Se descartó la versión compleja de 3 etapas concéntricas (tanque remoto + tubería + válvula + doble pared + aletas internas) como diseño principal, quedándonos con una arquitectura mucho más ligera, simple de construir y fácil de mantener:

1. **Monotubo de aluminio con base cerrada (`Base_Inferior_Tubo` + `Tubo_Unico_Aluminio`):**
   - Un solo cilindro de lámina de aluminio fina (`0.12–0.15 mm`), cerrado en el fondo para obligar a que todo el aire impulsado suba por el tubo.
2. **Ventilador externo lateral (`Ducto_Ventilador_Externo`, `Motor_Ventilador_Externo`, `Helice_Ventilador_Externo`):**
   - Ubicado en el costado exterior debajo de la bandeja; inyecta aire ambiente fresco que alimenta la combustión de la llama y asciende por el anillo perimetral (`~29 mm`) formando una cortina de aire frío que protege la pared del tubo y el collar del casco.
3. **Bandeja-depósito integrada con esponja refractaria (`Bandeja_Deposito_Etanol` + `Esponja_Fibra_Ceramica`):**
   - La propia bandeja del quemador almacena los `~164–180 mL` de etanol retenidos por capilaridad en una **esponja de manta de fibra cerámica** (o tejido limpio de fibra de vidrio *sin resina ni aglutinante* como alternativa temporal), evitando derrames al cabecear y eliminando tanque externo, mangueras y válvulas.
4. **Control de llama y seguridad (`Anillo_Cortaviento_Llama`, `Tapa_Apagado_Llama`, `Microservo_SG90_Apagado`, `Malla_Apagachispas_Inox`, `Sensor_NTC_Salida`):**
   - Cortaviento perimetral para que el aire del ventilador no apague la llama.
   - Tapa corrediza accionada por microservo `SG90` para modular o ahogar la llama en vuelo.
   - Malla apagachispas de acero inoxidable en la boca del tubo, collar ignífugo en la interfaz con la tela del casco y sonda `NTC` en la salida para vigilar el límite de `<= 150 °C`.
5. **Difusor cónico con plato deflector (`Difusor_Conico_Salida` + `Plato_Deflector_Difusor`):**
   - Cono superior con plato ranurado de 3 anillos concéntricos que expande, mezcla y reparte radialmente el aire tibio a baja velocidad dentro del casco.

*(La versión anterior de 3 etapas concéntricas se mantiene en el repositorio únicamente como respaldo de referencia en caso de requerir aislamiento por doble camisa física.)*

---

## 3. Macros de SolidWorks Disponibles y Cómo Abrirlas

| Modelo | Generador Python | Macro VBA lista (`.bas`) | Nombre del módulo en VBA |
|---|---|---|---|
| **Dirigible completo (`def`)** | [generar_cad_solidworks.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_solidworks.py) | [dirigible_solidworks_referencial_2026-11-27_def.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas) | `DirigibleReferencial` |
| **Calentador eléctrico en tierra (recirculación)** | *(macro directa)* | [calentador_tierra_solidworks_referencial_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_tierra_solidworks_referencial_v2.bas) | `CalentadorTierraRef` |
| **Calentador aéreo simplificado (elegido)** | [generar_cad_calentador_simple_solidworks.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_calentador_simple_solidworks.py) | [calentador_etanol_simple_solidworks_v2.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_simple_solidworks_v2.bas) | `CalentadorEtanolSimple` |
| **Calentador de 3 etapas (respaldo)** | [generar_cad_calentador_solidworks.py](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_calentador_solidworks.py) | [calentador_etanol_solidworks_referencial.bas](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/calentador_etanol_solidworks_referencial.bas) | `CalentadorEtanol3Etapas` |

### Flujo validado para ejecutar cualquier `.bas` en SolidWorks
1. Abre una **Pieza nueva vacía** en SolidWorks.
2. Ve a **Herramientas → Macro → Nuevo** (guárdala con un nombre temporal `.swp`).
3. En el editor VBA: **Archivo → Importar archivo...** y selecciona el archivo `.bas`.
4. En el explorador izquierdo entra en **Módulos**, abre el módulo correspondiente (`DirigibleReferencial`, `CalentadorTierraRef`, `CalentadorEtanolSimple` o `CalentadorEtanol3Etapas`), haz clic dentro de `Sub main()` y pulsa **`F5`**.
5. En las macros del calentador aéreo, `CORTE_EXPOSITIVO = True` muestra un corte de `270°` para ver el interior; para generar la pieza cerrada a `360°`, cambia esa constante a `False` o ejecuta el generador con `--completo`. En la macro del calentador eléctrico en tierra, oculta `1_Pared_Lateral_Visor` para inspeccionar las 9 resistencias y el recorrido de recirculación.

---

## 4. Próximos Pasos Prácticos Antes de Volar

1. **Control real de peso (`mad <= 1,300 g`):** pesar en balanza gramera el calentador monotubo terminado, la cinta de poliéster térmico + Kapton empleada en la envolvente, el bastidor en H, la góndola, el cableado y la aviónica antes de ensamblar (referencia detallada de compra y pesos en [PRESUPUESTO_Y_PESO_FABRICACION.md](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/PRESUPUESTO_Y_PESO_FABRICACION.md)).
2. **Prueba estática del calentador en banco (sin casco):**
   - Cargar `165 mL` de etanol 96 % en la esponja cerámica, encender y verificar tiempo de quemado (`~5.5–6 min`).
   - Comprobar con el ventilador externo en marcha que la llama sea estable (sin apagarse por exceso de aire) y que la lectura del `NTC` sobre el difusor no supere **`150 °C`**.
   - Probar el cierre remoto completo de la llama con el microservo `SG90`.
3. **Precalentamiento eléctrico en tierra (recirculación cerrada):** usar el calentador eléctrico compacto con resistencias internas (`~4.5–6.5 kW`, rango estimado **`5–8 min`**), conectando las mangas a la válvula de entrada y a la válvula de retorno para inflar y llevar el casco con aire `100 %` limpio hasta `T2 ≈ 114.8 °C` (`Epre ≈ 1.99 MJ`) antes de encender el quemador de a bordo y soltar amarras.
