# Calculadora de Sustentación, Geometría y Termodinámica para Dirigibles 🎈

Herramienta interactiva en Python basada en un sistema de álgebra computacional (**CAS**) con **SymPy** para el análisis, dimensionamiento geométrico, cálculo de sustentación mediante densidades de gas y requerimientos de energía térmica (calor sensible) para dirigibles y globos térmicos de un solo casco.

A diferencia de calculadoras tradicionales unidireccionales, este software permite **cálculo bidireccional**: puedes fijar cualquier variable de salida (por ejemplo, el calor sensible $Q$, la masa de aire caliente $m$, el volumen $V$ o el área superficial de tela $S$) y el motor algebraico-numérico despejará automáticamente las variables geométricas o termodinámicas correspondientes.

---

## 🧮 Modelos Físicos y Geométricos Implementados

### 1. Ecuación de Estado de los Gases Ideales (Densidad del Gas)
$$\rho = \frac{P}{R_{\text{gas}} \cdot (T + 273.15)}$$
- Compara dos estados térmicos:
  - **Caso 1 (Ambiente exterior):** $P_1, T_1, R_1 \rightarrow \rho_1$
  - **Caso 2 (Aire caliente interior):** $P_2, T_2, R_2 \rightarrow \rho_2$
- **Diferencia de densidades (Sustentación estática unitaria):**
  $$\Delta\rho = \rho_1 - \rho_2$$
- Valores iniciales de referencia calibrados para la **Zona Sur de La Paz, Bolivia a 100 m de altura** (~3.350 m s.n.m., $P \approx 67.120\text{ Pa}$, $T_1 = 15\text{ °C}$, $T_2 = 100\text{ °C}$, $R_{\text{aire}} = 287.058\text{ J/(kg}\cdot\text{K)}$).

### 2. Geometría del Casco Compuesto (Dos Semielipsoides de Revolución)
El casco se modela mediante dos semielipsoides prolados ($c_f > R$ y $c_r > R$) que comparten una base circular común de radio máximo $R$:
- **Longitud total del casco:**
  $$L = c_f + c_r$$
  *(Valores iniciales para un dirigible de $L = 6\text{ m}$ y $D = 2.5\text{ m}$: $R = 1.25\text{ m}$, con relación típica $c_f \approx 0.35 L = 2.1\text{ m}$ para la nariz y $c_r \approx 0.65 L = 3.9\text{ m}$ para la cola).*
- **Volumen total del casco:**
  $$V = \frac{2}{3} \pi R^2 L$$
- **Excentricidades longitudinales:**
  $$e_f = \sqrt{1 - \frac{R^2}{c_f^2}}, \qquad e_r = \sqrt{1 - \frac{R^2}{c_r^2}}$$
- **Áreas superficiales laterales (frontal, trasera y total de la envoltura):**
  $$S_f = \frac{\pi R c_f}{e_f} \arcsin(e_f), \qquad S_r = \frac{\pi R c_r}{e_r} \arcsin(e_r), \qquad S = S_f + S_r$$

### 3. Acoplamiento Aerostático y Calor Sensible (Aire Caliente)
El volumen del casco ($V$) se vincula directamente con el aire caliente del Caso 2 ($\rho_2$):
- **Masa de aire caliente contenida en el casco:**
  $$m = \rho_2 \cdot V$$
- **Gradiente térmico y Calor sensible requerido:**
  $$\Delta T = T_2 - T_1$$
  $$Q = m \cdot c_p \cdot \Delta T$$

### 4. Fuerza de Sustentación (Arquímedes)
$$F = \Delta\rho \cdot g \cdot V = \Delta\rho \cdot g \cdot \frac{m}{\rho_2}$$
- Usa la diferencia de densidades, el volumen del casco (equivalente a la masa de aire caliente $m = \rho_2 V$) y la gravedad $g = 9.775\text{ m/s}^2$ (valor aproximado para La Paz, editable en `modelo.py`).

---

## ✨ Características Principales

- **Motor CAS + Numérico con SymPy:** Resuelve analíticamente (`solve`) o numéricamente (`nsolve` para ecuaciones trascendentes con $\arcsin$) cualquier subsistema según los grados de libertad fijados.
- **Ecuaciones categorizadas:** Gases ideales y densidades, geometría del casco, aire caliente y termodinámica, y sustentación, cada una con su encabezado en pantalla.
- **Visualización Matemática 2D en Terminal:** Presentación de fracciones, raíces cuadradas y potencias en dos dimensiones usando `rich` y renderizado Unicode.
- **Representación Dual por Ecuación:**
  1. **Ecuación general (en gris):** Muestra la fórmula con las unidades de cada variable entre paréntesis.
  2. **Ecuación sustituida con valores:** Muestra la relación con los valores numéricos actuales.
- **Código de Colores Dinámico:**
  - 🟨 **Amarillo:** Variables fijadas por el usuario.
  - 🟩 **Verde:** Variables calculadas/despejadas automáticamente por el sistema.
- **Notación de Ingeniería:** Valores formateados automáticamente con hasta 3 enteros y 3 decimales junto a prefijos estándar del SI (ej. `67.120 (kPa)`, `811.454 (g/m³)`, `769.071 (kJ)`).

---

## 📁 Estructura del Proyecto

- **[`modelo.py`](modelo.py):** Núcleo matemático, geométrico y físico. Define el catálogo de 25 variables, unidades del SI/ingeniería, 14 ecuaciones simbólicas agrupadas por categoría de SymPy y el solucionador escalonado por bloques (`resolver`).
- **[`calc.py`](calc.py):** Interfaz interactiva de terminal con `rich`. Maneja el ciclo de actualización de pantalla en sitio, el formateo ingenieril y el menú de modificación bidireccional.
- **[`requirements.txt`](requirements.txt):** Dependencias del proyecto (`sympy`, `rich`, `mpmath`, etc.).

---

## 🚀 Instalación y Ejecución

1. **Crear y activar el entorno virtual:**
   ```bash
   python3 -m venv venv_sus_d
   source venv_sus_d/bin/activate
   ```

2. **Instalar dependencias:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Ejecutar el programa interactivo:**
   ```bash
   python calc.py
   ```
