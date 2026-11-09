# Calculadora de Sustentación y Termodinámica para Dirigibles 🎈

Herramienta interactiva en Python basada en un sistema de álgebra computacional (**CAS**) con **SymPy** para el análisis, dimensionamiento y cálculo de sustentación mediante densidades de gas y requerimientos de energía térmica (calor sensible) para dirigibles y globos térmicos.

A diferencia de calculadoras tradicionales unidireccionales, este software permite **cálculo bidireccional**: puedes fijar cualquier variable de salida (por ejemplo, el calor sensible $Q$ o la diferencia de densidades $\Delta\rho$) y el motor algebraico despejará automáticamente las variables de entrada correspondientes para satisfacer el estado del sistema.

---

## 🧮 Modelos Físicos Implementados

1. **Ecuación de Estado de los Gases Ideales (Densidad del Gas):**
   $$\rho = \frac{P}{R \cdot (T + 273.15)}$$
   - Permite comparar dos estados térmicos:
     - **Caso 1 (Ambiente exterior):** $P_1, T_1, R_1 \rightarrow \rho_1$
     - **Caso 2 (Gas interior calentado):** $P_2, T_2, R_2 \rightarrow \rho_2$
   - **Diferencia de densidades (Sustentación estática unitaria):**
     $$\Delta\rho = \rho_1 - \rho_2$$
   - Valores iniciales de referencia calibrados para la **Zona Sur de La Paz, Bolivia a 100 m de altura** (~3.350 m s.n.m., $P \approx 67.120\text{ Pa}$, $T_1 = 15\text{ °C}$, $T_2 = 100\text{ °C}$, $R_{\text{aire}} = 287.058\text{ J/(kg}\cdot\text{K)}$).

2. **Gradiente Térmico y Calor Sensible (Termodinámica):**
   $$\Delta T = T_2 - T_1$$
   $$Q = m_{\text{aire}} \cdot c_p \cdot \Delta T$$
   - Calcula la energía térmica necesaria para calentar la masa del gas ($m_{\text{aire}} = 9\text{ kg}$, $c_p = 1.005\text{ J/(kg}\cdot\text{K)}$).

---

## ✨ Características Principales

- **Motor CAS con SymPy:** Resuelve analíticamente cualquier incógnita del sistema de ecuaciones según los grados de libertad fijados.
- **Visualización Matemática 2D en Terminal:** Presentación de fracciones y fórmulas matemáticas en dos dimensiones usando `rich` y renderizado de texto Unicode.
- **Representación Dual por Ecuación:**
  1. **Ecuación general (en gris):** Muestra la fórmula con las unidades de cada variable entre paréntesis (ej. $P_1\text{ (Pa)}$, $T_1\text{ (°C)}$).
  2. **Ecuación sustituida con valores:** Muestra la relación con los valores numéricos actuales.
- **Código de Colores Dinámico:**
  - 🟨 **Amarillo:** Variables fijadas por el usuario.
  - 🟩 **Verde:** Variables calculadas/despejadas automáticamente por el CAS.
- **Notación de Ingeniería:** Valores formateados automáticamente con hasta 3 enteros y 3 decimales junto a prefijos estándar del SI (ej. `67.120 (kPa)`, `811.454 (g/m³)`, `768.825 (kJ)`).

---

## 📁 Estructura del Proyecto

- **[`modelo.py`](modelo.py):** Núcleo matemático y físico. Define el catálogo de variables, unidades del SI/ingeniería, ecuaciones simbólicas de SymPy y el solucionador por grados de libertad (`resolver`).
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

---

## 💡 Cómo Usar la Calculadora

- **Modificar una variable fija:** Ingresa el nombre de la variable (por ejemplo, `T1` o `m`) y escribe el nuevo valor. El resto de variables calculadas se actualizarán al instante.
- **Invertir el cálculo (Cálculo bidireccional):** Ingresa una variable que actualmente sea calculada (por ejemplo, `Q` o `drho`). El programa te consultará qué variable fija deseas liberar para ajustarse a ese nuevo requerimiento.
- **Salir:** Presiona `Enter` sin escribir texto y confirma con `s`.
