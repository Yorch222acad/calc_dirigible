# Calculadora de Sustentación para Dirigible Híbrido (Aire Caliente + Motores)

Herramienta de ingeniería y modelado físico-económico para el diseño, análisis térmico, aerodinámico, energético y de costos de un **dirigible híbrido no rígido de aire caliente** con propulsión y empuje vectorial mediante rotores eléctricos.

El proyecto cuenta con dos interfaces sobre un mismo núcleo matemático:
- **Interfaz Web (FastAPI + HTML/JS/KaTeX/Canvas)**: panel lateral con **167 variables** agrupadas en **13 categorías**, vista de ecuaciones en tiempo real con resaltado por dependencias, diagramas de flujo interactivos, **7 gráficas** de sensibilidad/escalabilidad, simulador por fases de vuelo y optimizador de diseño.
- **Interfaz CLI (`calc.py`)**: consola interactiva con `rich` para inspeccionar, modificar y equilibrar variables rápidamente.

---

## ¿Qué cambió y por qué? (Resumen de mejoras recientes)

Esta versión incorpora una actualización integral de la física térmica, la contabilidad energética/económica y la arquitectura de cálculo rápido:

### 1. Aislamiento multicapa asimétrico con Mylar (`ncapS = 3`, `ncapI = 2`)
- **Qué cambió**: Se reemplazó la capa única de aislante por un arreglo **asimétrico de celdas de aire** recubiertas con película reflectante **Mylar**: `ncapS = 3` capas en la mitad superior (donde el gradiente térmico y la convección libre ascendente son mayores) y `ncapI = 2` capas en la mitad inferior (donde el aire frío queda estratificado de forma estable y no recircula).
- **Detalles**: Espesor de celda `e = 14 mm`, paso entre costillas `W = 20 cm`, espesor de lámina `ep = 6 µm`, densidad superficial `sigma = 8.4 g/m²` y conductividad `ke = 0.15 W/(m·K)`. Se calculan transmitancias separadas (`Usup` con convección `Nuc` y `Uinf` con conducción pura `ka/e`) y un promedio `U = (Usup + Uinf)/2`.
- **Por qué**: Añadir múltiples capas delgadas reduce drásticamente las pérdidas globales `Qp` (bajando de `7528.3 W` sin aislar a `1328.8 W`, es decir `fais = 82.3 %` de ahorro térmico) manteniendo una masa de aislante contenida (`mc = 708.1 g`).

### 2. Radiación térmica infrarroja y emisividad baja (`eps = 0.04`)
- **Qué cambió**: Se incorporó el cálculo explícito de intercambio radiativo mediante la ley de Stefan-Boltzmann (`σ_SB`), modelando tanto la radiación hacia el entorno exterior (`hrade`, `hetot = he + hrade`) como la radiación interna entre láminas de Mylar (`Tm`, `epsef = eps/(2 - eps)`, `hrad = 4·epsef·σ_SB·Tm³`).
- **Por qué**: A `85 °C`, una superficie opaca de alta emisividad pierde calor significativo por infrarrojo. La baja emisividad del Mylar (`eps = 0.04`) suprime casi por completo el acoplamiento radiativo entre celdas (`hrad = 0.156 W/(m²·K)` y `hrade = 0.217 W/(m²·K)` en el punto base).

### 3. Correlación de Hollands (1976) para `Nuc` y aislamiento estricto de `U0`
- **Qué cambió**: Se corrigió el número de Nusselt dentro de las celdas inclinadas/superiores mediante la correlación de Hollands con límite inferior físico en `1.0`:
  $$Nu_c = 1 + 1.44 \cdot \max\!\left(0,\; 1 - \frac{Ra_c}{Ra_e}\right) + \max\!\left(0,\; \left(\frac{Ra_e}{5830}\right)^{1/3} - 1\right)$$
  con `Rac = 1708`. Además, la referencia sin aislar `U0` quedó estrictamente aislada de las variables de aislamiento y mamparos (`e`, `W`, `ncapS`, `ncapI`, `fmamp`, `nmamp`, `Nuc`, `hrad`).
- **Por qué**: Evita que el modelo produzca valores artificiales de `Nuc < 1` (lo cual equivaldría a conducir menos calor que el aire inmóvil) y garantiza que `U0` (`3.636 W/(m²·K)`) sea una línea base invariante al comparar variantes de aislamiento. Con `e = 14 mm`, la convección intracelular queda suprimida (`Nuc = 1.000`).

### 4. Mamparos internos anti-convección (`nmamp = 2`, `fmamp = 0.78`)
- **Qué cambió**: Se añadieron tabiques internos transversales (`nmamp = 2`) con pequeños orificios de ecualización de presión. Modelan tanto la reducción de la convección interna sobre la pared (`hi = fcal·fmamp·Nui·ka/D`, factor `fmamp = 0.78`) como su área y masa extra (`Smamp = nmamp·(2/3)·π·R²`, `mmamp = Smamp·sigma = 57.6 g`).
- **Por qué**: Compartimentar el casco frena las corrientes convectivas de gran escala a lo largo del dirigible a un costo de masa muy bajo.

### 5. Precalentamiento en tierra y modelo de costos (`Cop`)
- **Qué cambió**: Se integró el costo y eficiencia del llenado y calentamiento inicial en tierra (`npre = 0.65`, `cpre = 0.24 Bs/MJ`, `Epre = Q/npre`, `Cpre = (Epre/10^6)·cpre`) junto al costo del combustible térmico en vuelo (`ccomb = 18.0 Bs/kg`, `Ccomb = mgm·ccomb`), el costo eléctrico de recarga (`celecU = 0.85 Bs/kWh`, `Celec = (Ereq/1000)·celecU`) y el costo operativo total `Cop = Cpre + Ccomb + Celec`.
- **Por qué**: Permite modelar el aire caliente precalentado en tierra como una "batería térmica" de muy bajo costo (`Cpre = 0.34 Bs` por ciclo) para que el quemador en vuelo solo compense las pérdidas durante la misión (`Ccomb = 0.36 Bs`).

### 6. Combustible térmico genérico (calibrado para etanol) y calibración multi-viaje (`nv = 3`)
- **Qué cambió**: Se reemplazaron las referencias explícitas a "Propano / GLP" por la denominación genérica **combustible térmico** en ecuaciones, flujo, gráficas e interfaz web. Los valores iniciales se calibraron para etanol al 96 % (`PC = 2.5e7 J/kg`, `ncal = 0.75`, `mp = 0.220 kg`), temperatura interior reducida (`T2 = 85 °C` frente a mayor `mflot = 3.20 kg` y volumen `20.18 m³`), esbeltez `lam = 2.3`, velocidad `v = 5.5 m/s` y una misión base de **`nv = 3` viajes** de `d1 = 280 m` (`dm = 840 m`, `tm = 280 s` con viento en contra `vv = 2.5 m/s`).
- **Por qué**: Bajar `T2` y aumentar el volumen disminuye el gradiente térmico `ΔT` y la relación superficie/volumen; usar etanol reduce drásticamente el costo por kg de combustible frente a gas presurizado; y evaluar `nv = 3` viajes permite demostrar tanto el tramo mínimo de `280 m` como la escalabilidad operativa frente a un dron puro.

### 7. Optimización sin SymPy en runtime (Tearing + BLT + Simulación RK2)
- **Qué cambió**: Aunque las 103 ecuaciones siguen definidas simbólicamente en `modelo.py`, toda la evaluación numérica, los barridos de las 7 gráficas, las derivadas e intercambios BLT (`dm → nv`, `Cop → nv`, `mres → mflot`, `U → e`, etc.) y el optimizador multi-variable (`optimizar_diseno` con soporte para `T2` y objetivo `Cop`) corren en Python puro mediante **`evaluador.py`** con resolución por *tearing* (~`0.17 ms` por evaluación). Además, **`simulacion.py`** ejecuta integración RK2 por fases térmicas (despegue, ascenso, crucero y descenso) y **`flujo.py`** / **`graficas.py`** (`G1`–`G7`) fueron actualizados con el nuevo gráfico **`G7`** de temperatura óptima y escalabilidad multi-viaje.
- **Por qué**: Mantiene la trazabilidad exacta del sistema de 103 ecuaciones simbólicas sin sacrificar velocidad interactiva al mover deslizadores, cambiar variables objetivo o ejecutar cientos de iteraciones de optimización.

### 8. Limpieza del historial Git
- Se añadió `teoria_a_considerar/` a `.gitignore` y se depuró esa carpeta de notas personales del historial de commits de la rama `main`.

---

## Valores base verificados (Condiciones de La Paz, ~3.350 m s.n.m.)

Con los parámetros iniciales en `modelo.py` (`P1 = 67120 Pa`, `T1 = 15 °C`, `T2 = 85 °C`, `lam = 2.3`, `mflot = 3.20 kg`, `v = 5.5 m/s`, `vv = 2.5 m/s`, `d1 = 280 m`, `nv = 3`, `mcarga = 1.0 kg`, `mad = 1.15 kg`, `N = 4`):

| Magnitud | Símbolo | Valor base |
|---|---|---|
| Diámetro / Longitud / Volumen | `D` / `L` / `V` | `2.559 m` / `5.885 m` / `20.18 m³` |
| Área superficial del casco | `S` | `29.58 m²` |
| Coef. global sin / con aislante | `U0` / `U` | `3.636` / `0.642 W/(m²·K)` (`Usup = 0.550`, `Uinf = 0.734`) |
| Pérdida térmica sin / con aislante | `Qp0` / `Qp` | `7528.3 W` / `1328.8 W` (`fais = 82.3 %`) |
| Constante de enfriamiento (20 K) | `tc` | `199.3 s` |
| Masa cubierta / mamparos / batería | `mc` / `mmamp` / `mbat` | `708.1 g` / `57.6 g` / `228.8 g` |
| Masa residual por motores / Masa total | `mres` / `mtot` | `352.5 g` / `3.553 kg` |
| Potencia eléctrica / Empuje / Ángulo | `Pelec` / `Ttot` / `theta` | `270.7 W` / `8.53 N` / `61.9°` |
| Energía precalentamiento / térmica / eléctrica | `Epre` / `Eprop` / `Eelec` | `1425.7 kJ` / `496.1 kJ` (`mgm = 19.84 g`) / `88.4 kJ` |
| Energía total en vuelo (`nv = 3`, `dm = 840 m`) | `Etot` | `584.5 kJ` (`tm = 280 s`) |
| Costo operativo total | `Cop` | `0.72 Bs` (`Cpre = 0.34`, `Ccomb = 0.36`, `Celec = 0.021 Bs`) |
| Alertas de diseño activas | — | Ninguna (`0` alertas) |

---

## Gráficas del sistema (`G1`–`G7`)

1. **`G1` — Esbeltez (`λ`) vs. Energías de Misión y Casco (`L`, `D`, `mtot`)**
2. **`G2` — Sustentación Híbrida**: reparto entre aire caliente (`mflot`, `F`) y rotores (`mres`, `FL`), además de `mbat`.
3. **`G3` — Distancia (`dm`), Viajes (`nv`) y Tiempo (`tm`)** vs. `Etot`, `mgm`, `mbat`, `Cop` y velocidad `v` con viento `vv`.
4. **`G4` — Aislante Mylar Multicapa Asimétrico (`e`)** vs. energía ahorrada (`Eah`) y perdida (`Em`, `Em0`).
5. **`G5` — Combustible Térmico (`mgm`) y Balance Térmico en Vuelo**.
6. **`G6` — Dimensiones (`L`, `D`), Silueta 2D a escala y Desglose de Masa (`mtot`)** (incluyendo `mmamp`).
7. **`G7` — Temperatura Interior Óptima (`T2`) y Escalabilidad Multi-Viaje (`nv`)**: compara la eficiencia energética y de costo frente a un dron puro equivalente.

---

## Estructura del proyecto

- [`modelo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/modelo.py): Definición simbólica de las **167 variables**, **64 constantes iniciales (`FIJAS_INI`)**, **103 ecuaciones (`ECUACIONES_DEF`)** y **13 categorías (`C1`–`C13`)**.
- [`evaluador.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/evaluador.py): Evaluador numérico puro en float con resolución por *tearing* (`nuc_hollands`, `resolver_tearing_u`, `evaluar_termica_T2`, `evaluar_punto`).
- [`formateo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/formateo.py): Notación de ingeniería, renderizado KaTeX/2D y verificación de las 4 alertas de diseño (`mbat > mbmax`, `theta > thmax`, `Pelec > Pmax`, `Ttot > N·Tmax1`).
- [`flujo.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/flujo.py): Grupos temáticos, conexiones inter-categorías, grafo de ecuaciones y notas técnicas.
- [`graficas.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/graficas.py): Generador de las 7 gráficas (`G1`–`G7`).
- [`simulacion.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/simulacion.py): Simulación temporal RK2 por fases de misión (`simular_mision_fases`) y optimizador de diseño (`optimizar_diseno` con soporte para `T2` y `Cop`).
- [`app.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/app.py): Servidor FastAPI y API REST (`GET /api/estado`, `GET /api/variable/{nombre}`, `POST /api/equilibrio`, `POST /api/modificar`, `POST /api/reiniciar`, `POST /api/optimizar`).
- [`frontend/`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/frontend/index.html): Aplicación web modular (`main.js`, `state.js`, `api.js`, `sidebar.js`, `equations.js`, `charts.js`, `flowchart.js`, `simulation.js`, `varInput.js`, `balancer.js`, `katex_helper.js` y estilos CSS).
- [`calc.py`](file:///home/yorch/Documentos/archivos-de-programa/vis_std_code/sustentacion_dirigible/calc.py): Calculadora interactiva en terminal (`rich`).

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
