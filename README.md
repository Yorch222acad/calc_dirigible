# Calculadora de Sustentación, Geometría, Termodinámica y Propulsión Híbrida para Dirigibles 🎈🚁

Herramienta interactiva en Python basada en un sistema de álgebra computacional (**CAS**) con **SymPy** para el análisis, dimensionamiento geométrico, cálculo de sustentación aerostática, transferencia de calor por aislamiento celular, pérdida térmica, consumo de GLP, resistencia aerodinámica y dimensionamiento propulsivo/energético de un **dirigible híbrido** (aire caliente + 4 motores basculantes Brushless A2212 de 1000KV).

A diferencia de calculadoras tradicionales unidireccionales, este software permite **cálculo bidireccional**: puedes fijar cualquier variable de salida (por ejemplo, la masa de la batería $m_{\text{bat}}$, el excedente de sustentación $F_{\text{exc}}$, la resistencia aerodinámica $F_D$, la potencia eléctrica $P_{\text{elec}}$, la fuerza de sustentación $F$ o el consumo de propano $m_{gm}$) y el motor algebraico-numérico despejará automáticamente las variables de diseño correspondientes.

---

## 🧮 Modelos Físicos y Geométricos Implementados

### 1. Gases Ideales y Densidades
$$\rho = \frac{P}{R_{\text{gas}} \cdot (T + 273.15)}, \qquad \Delta\rho = \rho_1 - \rho_2$$
- Compara el aire ambiente exterior (**Caso 1**: $P_1, T_1, R_1 \rightarrow \rho_1$) frente al aire caliente interior (**Caso 2**: $P_2, T_2, R_2 \rightarrow \rho_2$).
- Valores iniciales calibrados para la **Zona Sur de La Paz, Bolivia a 100 m de altura** (~3.350 m s.n.m., $P \approx 67.120\text{ Pa}$, $T_1 = 15\text{ °C}$, $T_2 = 100\text{ °C}$).

### 2. Geometría del Casco Compuesto (Dos Semielipsoides de Revolución)
El casco se modela mediante dos semielipsoides prolados ($c_f > R$ y $c_r > R$) unidos en el plano de diámetro máximo (dimensionados automáticamente a partir de la carga destinada al aire caliente $m_{\text{flot}} = 3.0\text{ kg}$ y $\lambda = 2.4 \implies R \approx 1.173\text{ m}$, $L \approx 5.631\text{ m}$, $V \approx 16.23\text{ m}^3$):
$$\lambda = \frac{L}{D} = \frac{L}{2R}, \qquad x_f = \frac{c_f}{L}, \qquad L = c_f + c_r, \qquad V = \frac{2}{3} \pi R^2 L$$
$$e_f = \sqrt{1 - \frac{R^2}{c_f^2}}, \qquad e_r = \sqrt{1 - \frac{R^2}{c_r^2}}$$
$$S_f = \frac{\pi R c_f}{e_f} \arcsin(e_f), \qquad S_r = \frac{\pi R c_r}{e_r} \arcsin(e_r), \qquad S = S_f + S_r$$

### 3. Aire Caliente y Termodinámica
$$m = \rho_2 \cdot V, \qquad dT = T_2 - T_1, \qquad Q = m \cdot c_p \cdot dT$$

### 4. Sustentación Aerostática (Arquímedes)
$$F = \Delta\rho \cdot g \cdot V$$
- Calcula la fuerza de empuje aerostático neto del aire caliente ($g = 9.775\text{ m/s}^2$). Con la asignación inicial de $m_{\text{flot}} = 3.0\text{ kg}$, el aire caliente aporta $F \approx 29.33\text{ N}$ (85.7% del peso total) y los 4 motores sostienen los $m_{\text{res}} = 500\text{ g}$ restantes.

### 5. Aislamiento por Capa Intermedia de Celdas y Aporte Térmico
Modela una capa aislante intermedia dividida en celdas cuadradas de espesor $e = 2\text{ cm}$ ($20\text{ m\_m}$) y ancho $W = 20\text{ cm}$ ($200\text{ m\_m}$), con orificios de ecualización de presión de $3\text{ mm}$:
$$Ra_e = \frac{g \cdot \beta \cdot dT \cdot e^3}{\nu \cdot \alpha}, \qquad Nu_c = \left(\frac{Ra_e}{Ra_c}\right)^{1/4}, \qquad U = \frac{1}{\frac{1}{U_0} + \frac{e}{k_a \cdot Nu_c}}$$
$$Q_{p0} = U_0 \cdot S \cdot dT, \qquad Q_p = U \cdot S \cdot dT, \qquad dQ_p = Q_{p0} - Q_p, \qquad f_{\text{ais}} = \frac{dQ_p}{Q_{p0}}$$
$$S_c = S \cdot \left(1 + \frac{2 \cdot e}{W}\right), \qquad m_c = S_c \cdot \sigma$$

### 6. Pérdida de Calor y Enfriamiento (con Aislante Incorporado)
$$v_T = \frac{Q_p}{m \cdot c_p}, \qquad Q_c = m \cdot c_p \cdot dT_c, \qquad t_c = \frac{Q_c}{Q_p}$$

### 7. Quemador de Propano/Butano (Compensación Térmica)
$$m_{gc} = \frac{Q_c}{PC}, \qquad E_m = Q_p \cdot t_m, \qquad m_{gm} = \frac{E_m}{PC}$$

### 8. Resistencia Aerodinámica en el Desplazamiento (Correlación de Hoerner)
Vincula directamente la relación de esbeltez ($\lambda = L/D$) y el volumen ($V$) con la fuerza de arrastre ($F_D$) a una velocidad relativa al aire $v = 6.5\text{ m/s}$ y factor de interferencia parásita $k_p = 1.4$:
$$Re_L = \frac{\rho_1 \cdot v \cdot L}{\mu}, \qquad C_f = \frac{0.455}{(\log_{10} Re_L)^{2.58}}$$
$$C_{DV,\text{casco}} = C_f \left[ 4 \cdot \lambda^{1/3} + 6 \cdot \lambda^{-1.2} + 24 \cdot \lambda^{-2.7} \right], \qquad C_{DV} = k_p \cdot C_{DV,\text{casco}}$$
$$F_D = \frac{1}{2} \rho_1 \cdot v^2 \cdot C_{DV} \cdot V^{2/3}$$

### 9. Masas y Balance de Peso (Dirigible Híbrido)
Integra todas las masas en un lazo cerrado con la masa de la batería ($m_{\text{bat}}$):
- **Masa del artefacto ($m_{\text{art}}$):** cuadrícula/envolvente ($m_c$) + 4 motores A2212 ($4 \times 47\text{ g}$) + combustible propano ($m_p = 220\text{ g}$) + masa adicional ($m_{\text{ad}} = 1.1\text{ kg}$) + batería ($m_{\text{bat}}$):
  $$m_{\text{art}} = m_c + N \cdot m_{\text{mot}} + m_p + m_{\text{ad}} + m_{\text{bat}}$$
- **Masa total, flotación aerostática, masa residual y masa aparente:**
  $$m_{\text{tot}} = m_{\text{art}} + m_{\text{carga}} \quad (m_{\text{carga}} = 1\text{ kg}), \qquad m_{\text{flot}} = \frac{F}{g}$$
  $$m_{\text{res}} = m_{\text{tot}} - m_{\text{flot}}, \qquad m_{\text{ap}} = f_{\text{ap}} \cdot m_{\text{tot}} \quad (f_{\text{ap}} = 1.15)$$

### 10. Propulsión Vectorial y 4 Motores Brushless A2212 (1000KV)
Modela los 4 motores basculantes con velocidades objetivo de ascenso ($v_z = 0.8\text{ m/s}$) y traslación ($v_x = 3.0\text{ m/s}$) en un tiempo de maniobra $t_a = 5\text{ s}$:
$$a_z = \frac{v_z}{t_a}, \qquad a_x = \frac{v_x}{t_a}$$
$$F_L = m_{\text{res}} \cdot g + m_{\text{tot}} \cdot a_z, \qquad F_X = F_D + m_{\text{ap}} \cdot a_x$$
$$T_{\text{tot}} = \sqrt{F_L^2 + F_X^2}, \qquad \theta = \frac{180}{\pi} \arctan\left(\frac{F_X}{F_L}\right), \qquad \Delta\theta = \theta_{\text{max}} - \theta \quad (\theta_{\text{max}} = 75^\circ)$$
- **Sustentación vertical máxima de motores y excedente de sustentación ($F_{\text{exc}}$):**
  $$F_{L,\text{max}} = \sqrt{(N \cdot T_{\text{max1}})^2 - F_X^2}, \qquad F_{\text{exc}} = F + F_{L,\text{max}} - m_{\text{tot}} \cdot g$$
- **Potencia eléctrica demandada (teoría de disco actuador + potencia parásita):**
  $$A_p = \frac{\pi}{4} d_p^2, \qquad \eta_{\text{tot}} = \eta_{\text{prop}} \cdot \eta_m \cdot \eta_{\text{ESC}}$$
  $$P_{\text{elec}} = \frac{k_m}{\eta_{\text{tot}}} \left[ \frac{T_{\text{tot}}^{3/2}}{\sqrt{2 \cdot \rho_1 \cdot N \cdot A_p}} + F_X \cdot v \right]$$

### 11. Batería Requerida y Límites de Diseño
Vincula la autonomía resultante ($t_m \approx 921.4\text{ s} \approx 15.36\text{ min}$) con la energía específica de la batería ($e_{\text{bat}} = 150\text{ Wh/kg}$), la profundidad de descarga ($DoD = 0.80$) y el derateo térmico ($\eta_{\text{temp}} = 0.92$):
$$E_{\text{req}} = \frac{P_{\text{elec}} \cdot t_m}{3600}, \qquad m_{\text{bat}} = \frac{E_{\text{req}}}{e_{\text{bat}} \cdot DoD \cdot \eta_{\text{temp}}}, \qquad \Delta m_{\text{bat}} = m_{\text{bmax}} - m_{\text{bat}}$$
- **Límite de peso de batería ($m_{\text{bmax}} = 1\text{ kg}$) y ángulo ($\theta_{\text{max}} = 75^\circ$):** Si $m_{\text{bat}} > 1\text{ kg}$ o $\theta > 75^\circ$, el programa muestra una **alerta en rojo** y pone automáticamente en **negativo** todos los valores de sustentación (`F`, `mflot`, `FL`, `FLmax`, `Fexc`).

---

## 🔄 Reparto de Sustentación e Interacción Bidireccional

### Reparto Directo de Carga (`mflot` y `mres`)
Por defecto, el reparto de sustentación del dirigible híbrido está definido como dato de entrada (**fijo / amarillo**):
- **$m_{\text{flot}} = 3.0\text{ kg}$**: masa compensada por el empuje aerostático del aire caliente ($F \approx 29.33\text{ N}$, equivalente al **85.7%** del peso total).
- **$m_{\text{res}} = 0.5\text{ kg}$ ($500\text{ g}$)**: masa residual que sostienen dinámicamente los 4 motores Brushless A2212 (**14.3%** del peso total).

A partir de este reparto, el solucionador despeja de forma automática (**calculadas / verdes**):
- **Geometría del casco**: $R \approx 1.173\text{ m}$, $D \approx 2.346\text{ m}$, $L \approx 5.631\text{ m}$, $V \approx 16.23\text{ m}^3$, $S \approx 26.16\text{ m}^2$.
- **Balance de masas y autonomía**: masa de cuadrícula celular $m_c \approx 298\text{ g}$, masa de batería $m_{\text{bat}} \approx 764\text{ g}$, masa del artefacto $m_{\text{art}} = 2.50\text{ kg}$, masa total $m_{\text{tot}} = 3.50\text{ kg}$ (con $m_{\text{carga}} = 1.0\text{ kg}$) y tiempo de misión $t_m \approx 921.4\text{ s}$ ($\approx 15.36\text{ min}$).
- **Propulsión y márgenes**: potencia eléctrica $P_{\text{elec}} \approx 329.4\text{ W}$, empuje total $T_{\text{tot}} \approx 10.67\text{ N}$ ($\theta \approx 41.3^\circ < 75^\circ$) y excedente de sustentación $F_{\text{exc}} \approx 15.31\text{ N}$.

---

## 🌐 Interfaz Web Modular y Flujo en Terminal

El sistema cuenta con una **interfaz web interactiva** (FastAPI + HTML/CSS/JS ES6 modular + KaTeX) y conserva además su **interfaz original en terminal** (`calc.py`). Ambas comparten exactamente las mismas reglas visuales y numéricas a través de `formateo.py`.

### 1. Interfaz Web (`app.py` + `frontend/`)
1. **Barra Superior y Alertas de Diseño:**
   - Muestra el conteo en vivo de variables fijas (`46`) y calculadas (`56`), la leyenda de colores y el botón para restaurar los valores iniciales.
   - Si se excede `mbmax` o `thmax`, despliega un **banner de alerta en rojo** y penaliza en negativo (`rojo`) las variables de sustentación (`F`, `mflot`, `FL`, `FLmax`, `Fexc`).
2. **Panel Izquierdo (Categorías):**
   - Lista las **11 categorías** físicas (más la vista global *"Ver todas las categorías"*) con el conteo de ecuaciones y un indicador visual si alguna categoría tiene variables penalizadas.
3. **Panel Central de Ecuaciones (3 Columnas con Desplazamiento Vertical):**
   - Muestra en filas de arriba hacia abajo todas las ecuaciones de la categoría seleccionada:
     - **Izquierda:** Ecuación simbólica general (en gris) con la unidad de cada variable entre paréntesis.
     - **Centro:** Ecuación con los valores actuales reemplazados en **notación de ingeniería** (`amarillo` = fija, `verde` = calculada, `rojo` = sustentación penalizada).
     - **Derecha:** Lista clicable de las variables que participan en la ecuación con su descripción y el nombre completo de su unidad.
   - Las unidades compuestas se renderizan con **fracciones verticales en LaTeX/KaTeX** (ej. $\frac{\text{J}}{\text{K\_g} \cdot \text{K}}$) para ahorrar ancho horizontal y mejorar la legibilidad.
4. **Panel Inferior (Ingreso de Variable, Catálogo y Equilibrio Matemático):**
   - **Ingreso rápido por teclado:** Permite escribir el nombre de cualquier variable con autocompletado y pulsar `Enter` (también se puede seleccionar haciendo clic sobre cualquier variable de las ecuaciones o del **catálogo desplegable de 102 variables** a 2 columnas).
   - **Detalle de variable:** Muestra estado, valor SI, valor de ingeniería y **todas las ecuaciones donde participa** en el mismo formato de 3 columnas.
   - **Asistente de equilibrio matemático:** Permite editar valores fijos o intercambiar variables fijas $\leftrightarrow$ calculadas guiando paso a paso cuántas y cuáles faltan por fijar o liberar mediante el grafo bipartito.

### 2. Interfaz en Terminal (`calc.py`)
1. **Panel Principal:** Renderiza en 2D con `SymPy` y `Rich` las **56 ecuaciones** en **11 categorías**.
2. **Catálogo del Sistema:** Lista las **102 variables** en dos columnas con su código de color (`Amarillo = Fija`, `Verde = Calculada`).
3. **Panel Inferior (`Detalle de '<variable>'`):** Permite consultar ecuaciones involucradas, editar valores y ejecutar el asistente `_equilibrar_sistema`.

---

## ✨ Características Técnicas Principales

- **Motor CAS + Numérico con SymPy:** Resuelve analíticamente (`solve`) o numéricamente (`nsolve` con reducción simbólica interna y poda iterativa de incógnitas de grado 1) cualquiera de las **102 variables** a partir de las **56 ecuaciones** acopladas.
- **Verificación Estructural por Grafo Bipartito:** Determina instantáneamente qué intercambios entre variables fijas (`46`) y calculadas (`56`) mantienen el sistema libre de bloques sobredeterminados o subdeterminados.
- **Notación de Ingeniería Personalizada:**
  - Prefijos positivos en mayúsculas (`K, M, G, T`) y negativos en minúsculas (`m, u, n, p`).
  - Separación mediante guion bajo entre prefijo y unidad base (ej. `67.120 (K_Pa)`, `3.000 (K_g)`, `764.442 (g)`, `20.000 (m_m)`, `1.697 (M_adim)`).
  - En la web, las unidades con cocientes se renderizan como fracciones verticales mediante KaTeX (`\frac{...}{...}`).
- **API REST con FastAPI (`app.py`):**
  - `GET /api/estado`: devuelve categorías, ecuaciones en LaTeX/KaTeX, variables, resumen y alertas activas.
  - `GET /api/variable/{nombre}`: devuelve metadatos, ecuaciones donde participa y candidatas de intercambio.
  - `POST /api/equilibrio`: evalúa el emparejamiento en el grafo bipartito para el asistente paso a paso.
  - `POST /api/modificar` y `POST /api/reiniciar`: resuelven el sistema con nuevas entradas o restauran la calibración inicial.
- **Estructura Modular del Proyecto:**
  - `modelo.py`: definición declarativa de las 102 variables (`VARIABLES`), unidades (`UNIDAD_ING`, `UNIDAD_NOMBRE`), variables fijas iniciales (`FIJAS_INI`), 11 categorías de ecuaciones simbólicas (`CATEGORIAS`), análisis de equilibrio (`calculadas_fijables`, `variables_liberables`, `estado_equilibrio`) y solucionador híbrido (`resolver`).
  - `formateo.py`: reglas compartidas de notación de ingeniería con guion bajo, evaluación de alertas de diseño (`mbat > mbmax`, `theta > thmax`), penalización negativa de sustentación y generadores de ecuaciones en 2D y LaTeX/KaTeX coloreado con fracciones verticales en unidades.
  - `calc.py`: interfaz interactiva en terminal con `rich`, renderizado 2D con `SymPy`, panel de detalle de variable y asistente de equilibrio matemático (`_equilibrar_sistema`).
  - `app.py`: servidor backend con `FastAPI` que expone la API REST del sistema y sirve el frontend web.
  - `frontend/`: interfaz web modular sin dependencias de Node.js:
    - `index.html`: estructura base de los paneles y carga de KaTeX.
    - `css/` (`base.css`, `layout.css`, `components.css`): tokens de color, rejilla principal con scroll vertical y tarjetas de ecuaciones en 3 columnas.
    - `js/` (`main.js`, `api.js`, `state.js`, `katex_helper.js`) y `js/components/` (`sidebar.js`, `equations.js`, `varInput.js`, `balancer.js`).

---

## 🚀 Instalación y Ejecución

Si instalas por primera vez:
```bash
python3 -m venv venv_sus_d
source venv_sus_d/bin/activate
pip install -r requirements.txt
```

### Interfaz Web (Frontend + Backend FastAPI)
```bash
./venv_sus_d/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```
*(O activando antes el entorno con `source venv_sus_d/bin/activate` y ejecutando `uvicorn app:app --reload`).*
Luego abre en tu navegador: **`http://127.0.0.1:8000`**

### Interfaz en Terminal (CLI con Rich)
```bash
source venv_sus_d/bin/activate
python calc.py
```
