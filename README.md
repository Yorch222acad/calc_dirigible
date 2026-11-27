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

## Gráficas del sistema (`G1`–`G7`)

1. **`G1` — Esbeltez (`λ`) vs. Energías de Misión y Casco (`L`, `D`, `mtot`)**
2. **`G2` — Sustentación Híbrida**: reparto entre aire caliente (`mflot`, `F`) y rotores (`mres`, `FL`), además de `mbat`.
3. **`G3` — Distancia (`dm`), Viajes (`nv`) y Tiempo (`tm`)** vs. `Etot`, `mgm`, `mbat`, `Cop` y velocidad `v` con viento `vv`.
4. **`G4` — Aislante Mylar Multicapa Asimétrico (`e`)** vs. energía ahorrada (`Eah`) y perdida (`Em`, `Em0`).
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
- [`generar_cad_solidworks.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/generar_cad_solidworks.py): Generador de macro VBA referencial para SolidWorks a partir de configuraciones JSON exportadas.

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
