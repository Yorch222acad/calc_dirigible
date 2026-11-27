# Calculadora de Sustentación para Dirigible Híbrido (Aire Caliente + Motores)

Herramienta de ingeniería y modelado físico-económico para el diseño, análisis térmico, aerodinámico, energético y de costos de un **dirigible híbrido no rígido de aire caliente** con propulsión y empuje vectorial mediante rotores eléctricos.

El proyecto cuenta con dos interfaces sobre un mismo núcleo matemático:
- **Interfaz Web (FastAPI + HTML/JS/KaTeX/Canvas)**: panel lateral con **170 variables** agrupadas en **13 categorías**, vista de ecuaciones en tiempo real con resaltado por dependencias, diagramas de flujo interactivos, **7 gráficas** de sensibilidad/escalabilidad y estudio de diseño **📐 Óptimo y Casos Tipo** (`diseno.py`).
- **Interfaz CLI (`calc.py`)**: consola interactiva con `rich` para inspeccionar, modificar y equilibrar variables rápidamente.

---

## ¿Qué cambió y por qué? (Resumen de mejoras y auditoría matemática)

Esta versión incorpora las correcciones de la auditoría matemática y de física térmica sobre el modelo simbólico-numérico:

### 1. Área superficial curva exacta de semielipsoides prolados y piel exterior en `Sc`
- **Qué cambió**: Se corrigió la fórmula de superficie lateral de cada semielipsoide prolado ($c > R$, sin disco ecuatorial) tanto en `modelo.py` como en `evaluador.py`:
  $$S_{\text{mitad}} = \pi R^2 + \pi R c \frac{\arcsin(e)}{e}, \quad e = \sqrt{1 - \left(\frac{R}{c}\right)^2}$$
  lo que garantiza continuidad exacta con el límite hemisférico $2\pi R^2$ cuando $c \to R$ y coincide al $10^{-12}$ con la integración numérica de revolución.
- **Piel exterior**: El área total de película Mylar pasó a $S_c = S \cdot \left[1 + n_{\text{cap}}\left(1 + \frac{2e}{W}\right)\right]$, contabilizando explícitamente la piel exterior junto a las capas y tabiques celulares en coherencia con las $n_{\text{cap}} + 1$ láminas térmicas.

### 2. Flotabilidad por regiones (`Vnuc`, `Vcel`, `rhocel`) y volumen ocupado por celdas
- **Qué cambió**: Se descuenta la menor flotabilidad de la corona periférica de celdas aislantes (a densidad media `rhocel = P2 / (R2 · Tm)`) respecto al núcleo caliente interior `Vnuc` (`Vcel = V - Vnuc`, `m = rho2·Vnuc + rhocel·Vcel`).
- **Por qué**: Evita que el optimizador sobreestime el empuje aerostático al elegir espesores celulares muy grandes ($e > 25\text{ mm}$) o muchas capas.

### 3. Dinámica por fases (maniobra vs. crucero), inercia del gas (`m`) y disipación `ED`
- **Qué cambió**:
  - La masa aparente inercial incluye ahora el gas encerrado junto a la estructura (`map = fap·(mtot + m)`) tanto en avance como en ascenso (`FL = mres·g + map·az`), con un tiempo de rampa de maniobra realista para dirigible (`ta = 18 s`).
  - Se separó el régimen pico de maniobra (`Ttot`, `Pelec`, `Ptot`) del régimen continuo de crucero estacionario (`Tcruc`, `Pcruc`), integrando la energía eléctrica de misión `Ereq` por fases mediante `tman = min(tm, nv·ta)`.
  - El trabajo aerodinámico `ED = FD·v·tm` se refiere al desplazamiento relativo al aire (`v·tm`) en lugar de la distancia sobre el suelo `dm`.

### 4. Enfriamiento pasivo logarítmico (`tc`), aislamiento asimétrico y ramas inversas
- **Qué cambió**: Se reemplazó la aproximación lineal $Q_c / Q_p$ por la integral exponencial exacta a transmitancia $U$ constante y capacidad calorífica efectiva regional $C_{\text{ef}} = Q / \Delta T = c_p(\rho_2 V_{\text{nuc}} + \tfrac{1}{2}\rho_{\text{cel}} V_{\text{cel}})$:
  $$t_c = \frac{Q}{Q_p} \ln\!\left(\frac{\Delta T}{\Delta T - \Delta T_c}\right)$$
  y se validan dominios físicos estrictos (`0 < dTc < dT`, `0 < ncal < 1`, enteros para `N >= 1`, `ncapS >= 0`, `ncapI >= 0`).
- **Correlación de Hollands (`Nuc`) y ramas inversas**: La transmitancia $U(e)$ presenta físicamente dos raíces posibles a ambos lados de `Rac = 1708` (una en conducción pura `Nuc = 1` y otra en régimen convectivo `Nuc > 1`), y el intercambio `xf ↔ 1 - xf` conserva $S$.
- **Aislamiento de `U0`**: La referencia sin aislar `U0` permanece estrictamente independiente de `e`, `W`, `ncapS`, `ncapI`, `Nuc` y `hrad`.

### 5. Factibilidad unificada, signos reales en alertas y optimizador invariante
- **Qué cambió**:
  - Se eliminó la inversión artificial a negativo de las variables de sustentación (`F`, `mflot`, `FL`, `FLmax`, `Fexc`): toda magnitud conserva su signo físico real y las alertas marcan únicamente las variables cuyo límite ha sido excedido (incluyendo `mp < mgm` y `Fexc < 0`).
  - En `diseno.py` y `app.py`, los límites del hardware configurado (`N·Pmax1`, `N·Tmax1`, `mbmax`, `thmax`, `Fexc >= 0`, además de `T2 <= 130 °C` editable para Mylar con uniones Kapton/PET —techo interno de búsqueda `140 °C`— y `mp <= 300 g`; las referencias históricas anteriores conservan `95 °C`) inician activos por defecto, son evaluados incluso en análisis directo (`ejecutar_optimizador=False`) y el optimizador ordena canónicamente las variables libres para que los resultados sean invariantes al orden elegido.

### 6. Validación v2: ángulo en crucero, 0/0 capas, precalentamiento regional y capacidad útil real
- **Qué cambió**:
  - Se incorporó el ángulo de inclinación de los motores en crucero (`thcruc = arctan(FD / (mres·g))`) y el margen conjunto `dth = thmax - max(theta, thcruc)` en todas las comprobaciones de factibilidad y alertas.
  - Se manejaron sin singularidades los cascos `0/0`, `1/0` y `0/1` (`dTcel = 0`, `Rae = 0`, `Nuc = 1`) tanto en el evaluador rápido como en el solver simbólico/BLT (`sp.Piecewise`).
  - El calor sensible de precalentamiento `Q` distingue las dos regiones de temperatura (`Q = cp·[rho2·Vnuc·dT + rhocel·Vcel·(dT/2)]`), coherente con `m = rho2·Vnuc + rhocel·Vcel` y la sensibilidad térmica a casco fijo de `G7`.
  - Se unificaron los topes de equipo (`N·Pmax1`, `N·Tmax1`, `mbmax`, `thmax`) separados de eventuales topes manuales (`tope_manual`), la capacidad útil en ficha se evalúa resolviendo la misión completa con equipo y batería instalada fija (y la referencia de dron puro en `G7` usa masa estructural, arrastre e inercia propios integrados por fases).

---

## Valores base verificados (Condiciones de La Paz, ~3.350 m s.n.m.)

Con los parámetros iniciales en `modelo.py` (`P1 = 67120 Pa`, `T1 = 15 °C`, `T2 = 85 °C`, `lam = 2.3`, `mflot = 3.20 kg`, `v = 8.5 m/s`, `vv = 6.0 m/s`, `d1 = 280 m`, `nv = 3`, `ta = 18.0 s`, `mcarga = 1.0 kg`, `mad = 1.15 kg`, `mp = 0.220 kg`, `N = 4`):

| Magnitud | Símbolo | Valor base |
|---|---|---|
| Diámetro / Longitud / Volumen exterior | `D` / `L` / `V` | `2.584 m` / `5.943 m` / `20.775 m³` (`Vnuc = 19.434`, `Vcel = 1.341 m³`) |
| Área exterior del casco / Película total | `S` / `Sc` | `40.648 m²` / `156.494 m²` |
| Coef. global sin / con aislante | `U0` / `U` | `4.324` / `0.694 W/(m²·K)` (`Usup = 0.587`, `Uinf = 0.801`) |
| Pérdida térmica sin / con aislante | `Qp0` / `Qp` | `12301.9 W` / `1973.7 W` (`fais = 84.0 %`) |
| Enfriamiento logarítmico (20 K) | `tc` | `158.0 s` |
| Masa película Mylar / Masa batería | `mc` / `mbat` | `1314.5 g` / `1051.5 g` |
| Masa residual / Masa total | `mres` / `mtot` | `1.724 kg` / `4.924 kg` |
| Potencia pico / crucero / Empuje / Ángulos | `Pelec` / `Pcruc` / `Ttot` / `theta` / `thcruc` | `1403.8 W` / `1159.5 W` / `23.47 N` (`Tcruc = 20.88 N`) / `40.7°` / `36.2°` |
| Energía precalentamiento / térmica / eléctrica / arrastre | `Epre` / `Eprop` / `Eelec` / `ED` | `1425.7 kJ` (`Q = 926.7 kJ`) / `884.2 kJ` (`mgm = 35.4 g`) / `417.9 kJ` / `35.2 kJ` |
| Energía total en vuelo (`nv = 3`, `dm = 840 m`) | `Etot` | `1302.1 kJ` (`tm = 336.0 s`) |
| Costo operativo total | `Cop` | `1.077 Bs` (`Cpre = 0.342`, `Ccomb = 0.637`, `Celec = 0.099 Bs`) |
| Alertas de diseño activas en punto base | — | `4` alertas (`mbat > 1 kg`, `Pelec > 640 W`, `Ttot > 22 N`, `Fexc < 0`) |

---

## Diseño definitivo de construcción (manta térmica real `12 µm` / `17 g/m²`)

A partir del modelo auditado `v2` ([`CIERRE_AUDITORIAS.md`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/CIERRE_AUDITORIAS.md)), se caracterizó la manta térmica comercial adquirida (**FIRSTIME `160 × 210 cm` = `3.36 m²`**, peso medido **`59 g`** $\rightarrow$ `17.56 g/m²` pura, espesor estándar `ep = 12 µm`) unida con **cinta de poliéster térmico (`180–200 °C`) y cinta Kapton (`220–260 °C`)**, fijando un límite térmico seguro de `T2 <= 115 °C`, orientando la cara plateada al interior (`eps = 0.08`) e incorporando márgenes constructivos realistas (`mad = 1.30 kg`, `mcarga = 1.10 kg`, misión `2 × 270 m = 540 m` contra `vv = 6.0 m/s`).

El diseño definitivo exportado en [`especf_optm_hist/historico_dirigible_2026-11-27_def.json`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/historico_dirigible_2026-11-27_def.json) (`id = f53b37f3b5`, **Score `42.01`**, `0` alertas) y su macro CAD en [`especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas) quedan establecidos en:

| Magnitud del diseño definitivo (`def`) | Símbolo | Valor verificado |
|---|---|---|
| Casco bi-semielipsoidal (`cf = 2.829 m`, `cr = 5.254 m`, `λ = 3.55`) | `L` / `D` / `V` | `8.083 m` / `2.275 m` / `21.90 m³` (`Vnuc = 20.64`, `Vcel = 1.25 m³`) |
| Área exterior / Película total Mylar | `S` / `Sc` | `46.91 m²` / `107.45 m²` |
| Configuración celular simétrica (`e = 29.1 mm`, `W = 20 cm`) | `ncapS` / `ncapI` / `mc` | **`1 / 1` capa** · `1,826.7 g` (`ep = 12 µm`, `σ = 17.0 g/m²`, `ε = 0.08`) |
| Desempeño térmico e inercia (`T2 = 114.8 °C`, `dTc = 20 K`) | `U` / `Qp` / `fais` / `tc` | `1.379 W/(m²·K)` / `6,454.6 W` (`69.5 %` ahorro) / `44.7 s` |
| Reparto de masas (`88.5 %` aire caliente) | `mflot` / `mres` / `mtot` | `4.460 kg` / `0.581 kg` / `5.041 kg` (`capacidad fija: 0.7427–1.1000 kg`) |
| Propulsión (`4 × A2212`, `v = 7.64 m/s`, `vg = 1.64 m/s`) | `Pelec` / `Pcruc` / `Ttot` / `θ` | `637.0 W` / `449.8 W` / `12.91 N` (`Tcruc = 9.94 N`) / `59.2°` (`55.2°`) |
| Excedente vertical y batería LiPo | `Fexc` / `mbat` | `+13.32 N` / `494.2 g` (`Ereq = 47.04 Wh`, autonomía `626 m`) |
| Energías y costos (`dm = 540 m`, `tm = 328.6 s`) | `Epre` / `mgm` / `Cop` | `1,986.8 kJ` (`0.477 Bs`) / `113.12 g` (`2.036 Bs`) / **`2.553 Bs`** (`Recambio: 2.37 vs. 370.63 Bs`) |
| Macro CAD SolidWorks (góndola `600×300×250 mm`, `gap = 135 mm`) | `X_CB` / holguras | `3.738 m` / `278.9 mm` al casco y `273.0 mm` lateral a góndola |

* **Ventaja frente a dron puro equivalente (`mcarga = 1.1 kg`, `540 m`, `3,350 m s.n.m.`, `vv = 6 m/s`):** un multirrotor equivalente sin sustentación aerostática requeriría `1,029.1 W` pico (`1,009.9 W` crucero, excede `640 W`), `27.67 N` de empuje (excede `22 N`) y `873.9 g` de batería, resultando inviable con los `4 × A2212`; el dirigible híbrido recorta `43.5 %` de batería (`494.2 g`) y hace viable el hardware.

### Por qué se usa solo `1` capa celular (`1/1`) y no multicapa en este caso

Con el gramaje real de la manta comercial (`σ = 17.0 g/m²`, más del doble de `8.4 g/m²` del Mylar de `6 µm`), el **Panel C y Panel D de `G4`** muestran que añadir una segunda o tercera capa penaliza la masa más rápido de lo que ahorra térmicamente:

1. **Barrido sobre el mismo casco (`mflot = 4.46 kg`):** pasar de `0/0` a `1/1` recorta `Qp` de `20.82 kW` a `6.45 kW` (**`−69.5 %`**) cumpliendo todos los topes (`Pelec = 637.0 W`). Al subir a `2/1`, `Qp` baja a `4.87 kW`, pero la película sube a `mc = 2,360.1 g` (`+533 g`) y `Pelec` salta a `815.1 W` (`> 640 W`); en `2/2` llega a `1,103.3 W` y `23.5 N` (`> 22 N`), y en `4/4` alcanza `mc = 5,149.9 g` y `4,024.9 W`.
2. **Re-optimizando todo el casco (`λ, v, mflot, e, T2, mp`) para cada par de capas (`σ = 17.0 g/m²`):**
   - `0/0`: `Score = 38.61`, `V = 16.70 m³`, `mc = 669.1 g`, `Qp = 18.04 kW`, `tc = 12.5 s`, `Cop = 4.863 Bs`.
   - `1/0`: `Score = 39.85`, `V = 19.86 m³`, `mc = 1,175.3 g`, `Qp = 13.44 kW`, `tc = 19.9 s`, `Cop = 4.104 Bs`.
   - **`1/1` (óptimo definitivo):** `Score = 42.01`, `V = 21.90 m³`, `mc = 1,826.7 g`, `Qp = 6.45 kW`, `tc = 44.7 s`, `Cop = 2.553 Bs`.
   - `2/1`: `Score = 40.38`, exige crecer a `23.98 m³` (`mc = 2,254.7 g`), apenas reduce `Qp` a `6.35 kW` (porque obliga a reducir `e` y agrandar `S`) y encarece el costo a `2.821 Bs`.
   - `2/2`: `Score = 37.17`, se dispara a `L = 8.84 m`, `V = 29.20 m³`, `mc = 3,118.7 g`, `mtot = 6.42 kg`, `mbat = 573.2 g` y `Cop = 3.267 Bs`.
   - **`3/2` o superior:** **sin solución factible** dentro de `640 W / 22 N / 1 kg`.

En consecuencia, `1/1` captura la mayor parte del beneficio aislante sin provocar la "bola de nieve" volumétrica; pasar a `2/1` o `3/2` capas solo vuelve a ser conveniente si se consigue película ultraligera de `6–8 µm` (`σ ≈ 8.4–11 g/m²`).

### Subsistemas térmicos consolidados: calentador en tierra y calentador aéreo con etanol

* **Calentador en tierra (precalentamiento previo al despegue):** soplador externo de aire caliente a GLP/gas en estación de tierra (`ηpre = 0.65`, `cpre = 0.24 Bs/MJ`) que entrega `Q = 1,291.4 kJ` útiles (`Epre = 1,986.8 kJ`, costo `Cpre = 0.477 Bs`, `~1.5–3.5 min` con equipo de `10–20 kW`). Permite despegar con el núcleo `Vnuc` a `114.8 °C` y las celdas `Vcel` a `64.9 °C` al **100 % de flotabilidad inicial** sin cargar peso de arranque a bordo.
* **Calentador aéreo con etanol (mantenimiento continuo de `Qp`):** quemador capilar vertical en **3 etapas** sin intercambiador metálico cerrado (ahorra `400–700 g` de masa muerta manteniendo `ηcal = 0.75` y `fcal = 1.275`):
  1. **Quemador capilar blindado (base):** matriz multi-mecha / cama ancha de fibra cerámica embebida en etanol 96 % (`PC = 25 MJ/kg`, `18 Bs/kg`, retenido por capilaridad ante cabeceo) dentro de camisa cortaviento perforada y malla apagachispas de acero inoxidable. En el diseño definitivo `1/1` (`Qp = 6.45 kW`, potencia química bruta `~8.6 kW`) consume `20.7 g/min ≈ 26 mL/min` (`mgm = 113.1 g` en `328.6 s`, tanque `mp = 131.7 g`).
  2. **Chimenea / cámara de dilución térmica (etapa media):** mezcla los gases de combustión (`600–800 °C`) con aire recirculado desde el fondo frío del casco mediante un ventilador axial ligero (contemplado en `Pad = 45 W`) para bajar el chorro a **`125–155 °C`**, protegiendo la manta de `12 µm` y sus uniones de poliéster térmico/Kapton (requiere `~110–135 L/s` de dilución para `6.45 kW`; en configuraciones ligeras de `6 µm` con `2/1` capas, `Qp ≈ 3.4 kW`, bastarían `~30–60 L/s` y `~13.5 mL/min`).
  3. **Difusor cónico ancho + alivio inferior:** descarga el flujo templado a baja velocidad (`< 1–1.5 m/s`) evitando puntos calientes focalizados en el techo, mientras el alivio en la parte inferior más fría minimiza la pérdida energética de purga.

---

## Gráficas del sistema (`G1`–`G7`)

1. **`G1` — Esbeltez (`λ`) vs. Energías de Misión y Casco (`L`, `D`, `mtot`)**
2. **`G2` — Sustentación Híbrida**: reparto entre aire caliente (`mflot`, `F`) y rotores (`mres`, `FL`), además de `mbat`.
3. **`G3` — Distancia (`dm`), Viajes (`nv`) y Tiempo (`tm`)** vs. `Etot`, `mgm`, `mbat`, `Cop` y velocidad `v` con viento `vv`.
4. **`G4` — Aislante Mylar Multicapa Asimétrico (`e` y `0/0 → 4/4` capas)** vs. ahorro térmico (`Eah`, `Qp`, `fais`), masa de película (`mc`), potencia (`Pelec` vs. `Pmax`) y batería (`mbat`).
5. **`G5` — Combustible Térmico (`mgm`) y Balance Térmico en Vuelo**.
6. **`G6` — Dimensiones (`L`, `D`), Silueta 2D a escala y Desglose de Masa (`mtot`)**.
7. **`G7` — Temperatura Interior Óptima (`T2`) y Escalabilidad Multi-Viaje (`nv`)**: compara el dirigible frente a un dron puro equivalente.

---

## Estructura del proyecto

- [`modelo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py): Definición simbólica de las **170 variables**, **62 constantes iniciales (`FIJAS_INI`)**, **108 ecuaciones (`ECUACIONES_DEF`)** y **13 categorías (`C1`–`C13`)**.
- [`evaluador.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py): Evaluador numérico puro en `float` con resolución por *tearing* (`area_semielipsoide`, `nuc_hollands`, `resolver_tearing_u`, `resolver_tearing_mbat`, `evaluar_punto`).
- [`diseno.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/diseno.py): Estudio de diseño **Óptimo y Casos Tipo** en `float` puro (6 indicadores ponderados, límites configurables, histórico manual en JSON y 14 familias de Casos Tipo).
- [`formateo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/formateo.py): Notación de ingeniería, renderizado KaTeX/2D y verificación de alertas conservando el signo físico real.
- [`flujo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/flujo.py): Grupos temáticos, conexiones inter-categorías, grafo de ecuaciones y notas técnicas.
- [`graficas.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/graficas.py): Generador de las 7 gráficas (`G1`–`G7`).
- [`app.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/app.py): Servidor FastAPI y API REST (`GET /api/estado`, `GET /api/variable/{nombre}`, `POST /api/equilibrio`, `POST /api/modificar`, `POST /api/reiniciar`, `POST /api/diseno/analizar`, `/api/historico`).
- [`frontend/`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/frontend/index.html): Aplicación web modular (`main.js`, `state.js`, `api.js`, `sidebar.js`, `equations.js`, `charts.js`, `flowchart.js`, `designStudio.js`, `varInput.js`, `balancer.js`, `katex_helper.js` y estilos CSS).
- [`calc.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/calc.py): Calculadora interactiva en terminal (`rich`).
- [`generar_cad_solidworks.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_solidworks.py): Generador de macro VBA referencial para SolidWorks a partir de configuraciones JSON exportadas (macro definitiva actual en [`especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/especf_optm_hist/dirigible_solidworks_referencial_2026-11-27_def.bas)).
- [`CIERRE_AUDITORIAS.md`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/CIERRE_AUDITORIAS.md): Consolidación de las rondas de auditoría V1–V10 y criterios de estabilización del modelo `v2`.
- [`texto.md`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/texto.md): Memoria técnica consolidada del sistema, análisis multicapa, subsistemas térmicos (tierra y etanol aéreo) y exposición completa.

---

## Instalación y ejecución

### Requisitos
Python 3 y las dependencias declaradas en [`requirements.txt`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/requirements.txt) (`sympy`, `fastapi`, `uvicorn`, `rich`, `mpmath`, entre otras).

```bash
python3 -m venv venv_sus_d
./venv_sus_d/bin/pip install -r requirements.txt
```

### Ejecutar la aplicación web
```bash
./venv_sus_d/bin/uvicorn app:app --reload
```
Luego abre el navegador en `http://127.0.0.1:8000`.

### Ejecutar la calculadora por consola (CLI)
```bash
./venv_sus_d/bin/python calc.py
```

### Contribución y notas locales
La carpeta `teoria_a_considerar/` está excluida mediante `.gitignore` para mantener notas de trabajo locales fuera del repositorio.
