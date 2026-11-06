# Calculadora de Sustentación y Termodinámica para Dirigibles 🎈

Herramienta en Python para el análisis y cálculo de sustentación mediante densidades de gas y requerimientos de energía térmica (calor sensible) para dirigibles y globos térmicos.

## Cálculos Implementados

1. **Ecuación de Estado de los Gases Ideales (Densidad del Gas):**
   $$\rho = \frac{P}{R \cdot T}$$
   - Permite comparar dos estados térmicos (ej. aire ambiente vs. aire caliente interior) y calcula la diferencia positiva de densidades ($\Delta \rho$).
   - Valores iniciales calibrados para la **Zona Sur de La Paz, Bolivia a 100 m de altura** (~3.350 m s.n.m., $P \approx 67.120\text{ Pa}$, $T = 15\text{ °C}$, $R_{\text{aire}} = 287.058\text{ J/(kg}\cdot\text{K)}$).

2. **Ecuación de Calor Sensible (Termodinámica):**
   $$Q = m_{\text{aire}} \cdot c_p \cdot \Delta T$$
   - Calcula la energía térmica necesaria para calentar la masa del gas ($m_{\text{aire}} = 9\text{ kg}$) en función del gradiente térmico $\Delta T = |T_2 - T_1|$.

## Instalación y Ejecución

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
