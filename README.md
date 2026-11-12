# Calculadora de Sustentación, Geometría y Termodinámica para Dirigibles 🎈

Herramienta interactiva en Python basada en un sistema de álgebra computacional (**CAS**) con **SymPy** para el análisis, dimensionamiento geométrico, cálculo de sustentación, transferencia de calor por aislamiento celular, pérdida térmica y consumo de combustible para dirigibles y globos térmicos de un solo casco.

A diferencia de calculadoras tradicionales unidireccionales, este software permite **cálculo bidireccional**: puedes fijar cualquier variable de salida (por ejemplo, la fuerza de sustentación $F$, la potencia ahorrada por el aislante $dQ_p$, el tiempo de enfriamiento $t_c$, el número de Rayleigh $Ra_e$, la masa de la cuadrícula celular $m_c$ o el consumo de propano $m_{gm}$) y el motor algebraico-numérico despejará automáticamente las variables de diseño correspondientes.

---

## 🧮 Modelos Físicos y Geométricos Implementados

### 1. Gases Ideales y Densidades
$$\rho = \frac{P}{R_{\text{gas}} \cdot (T + 273.15)}, \qquad \Delta\rho = \rho_1 - \rho_2$$
- Compara el aire ambiente exterior (**Caso 1**: $P_1, T_1, R_1 \rightarrow \rho_1$) frente al aire caliente interior (**Caso 2**: $P_2, T_2, R_2 \rightarrow \rho_2$).
- Valores iniciales calibrados para la **Zona Sur de La Paz, Bolivia a 100 m de altura** (~3.350 m s.n.m., $P \approx 67.120\text{ Pa}$, $T_1 = 15\text{ °C}$, $T_2 = 100\text{ °C}$).

### 2. Geometría del Casco Compuesto (Dos Semielipsoides de Revolución)
El casco se modela mediante dos semielipsoides prolados ($c_f > R$ y $c_r > R$) unidos en el plano de diámetro máximo ($R = 1.25\text{ m}$, $L = 6.0\text{ m}$):
$$L = c_f + c_r, \qquad V = \frac{2}{3} \pi R^2 L$$
$$e_f = \sqrt{1 - \frac{R^2}{c_f^2}}, \qquad e_r = \sqrt{1 - \frac{R^2}{c_r^2}}$$
$$S_f = \frac{\pi R c_f}{e_f} \arcsin(e_f), \qquad S_r = \frac{\pi R c_r}{e_r} \arcsin(e_r), \qquad S = S_f + S_r$$

### 3. Aire Caliente y Termodinámica
Vincula el volumen del casco ($V$) con la densidad del aire caliente ($\rho_2$):
$$m = \rho_2 \cdot V, \qquad dT = T_2 - T_1, \qquad Q = m \cdot c_p \cdot dT$$

### 4. Sustentación (Arquímedes)
$$F = \Delta\rho \cdot g \cdot V$$
- Calcula la fuerza de empuje aerostático neto en función de la diferencia de densidades, el volumen del casco y la gravedad local ($g = 9.775\text{ m/s}^2$).

### 5. Aislamiento por Capa Intermedia de Celdas y Aporte Térmico
Modela una capa aislante intermedia dividida en celdas cuadradas de espesor $e = 2\text{ cm}$ ($20\text{ m\_m}$) y ancho $W = 20\text{ cm}$ ($200\text{ m\_m}$), con orificios de ecualización de presión de $3\text{ mm}$, y cuantifica su aporte térmico frente al casco sin aislar:
- **Número de Rayleigh ($Ra_e$) y Número de Nusselt ($Nu_c$) en la cavidad celular:**
  $$Ra_e = \frac{g \cdot \beta \cdot dT \cdot e^3}{\nu \cdot \alpha}, \qquad Nu_c = \left(\frac{Ra_e}{Ra_c}\right)^{1/4}$$
- **Coeficiente global de transferencia de calor con capa celular ($U$) frente a sin capa celular ($U_0$):**
  $$U = \frac{1}{\frac{1}{U_0} + \frac{e}{k_a \cdot Nu_c}}$$
- **Comparación de pérdidas térmicas y ahorro del aislante celular:**
  $$Q_{p0} = U_0 \cdot S \cdot dT \quad (\text{sin celdas}), \qquad Q_p = U \cdot S \cdot dT \quad (\text{con celdas})$$
  $$dQ_p = Q_{p0} - Q_p \quad (\text{potencia ahorrada}), \qquad f_{\text{ais}} = \frac{dQ_p}{Q_{p0}} \quad (\text{fracción de ahorro})$$
- **Área total de película HDPE ($S_c$) y masa de la cuadrícula celular ($m_c$):**
  $$S_c = S \cdot \left(1 + \frac{2 \cdot e}{W}\right), \qquad m_c = S_c \cdot \sigma$$

### 6. Pérdida de Calor y Enfriamiento (con Aislante Incorporado)
Analiza la inercia térmica de la masa de aire caliente ($m$) ante la potencia de pérdida térmica con aislamiento ($Q_p$) y una caída admisible de temperatura $dT_c$ (por defecto $20\text{ K}$):
$$v_T = \frac{Q_p}{m \cdot c_p}, \qquad Q_c = m \cdot c_p \cdot dT_c, \qquad t_c = \frac{Q_c}{Q_p}$$

### 7. Quemador de Propano/Butano (Compensación Térmica)
Dimensiona el requerimiento de gas GLP (poder calorífico $PC = 46\text{ M\_J/K\_g}$) para recuperar o sostener la temperatura:
$$m_{gc} = \frac{Q_c}{PC}, \qquad E_m = Q_p \cdot t_m, \qquad m_{gm} = \frac{E_m}{PC}$$

---

## ✨ Características Principales

- **Motor CAS + Numérico con SymPy:** Resuelve analíticamente (`solve`) o numéricamente (`nsolve`) cualquiera de las 52 variables a partir de las 29 ecuaciones acopladas.
- **Notación de Ingeniería Personalizada:**
  - Prefijos positivos en mayúsculas (`K, M, G, T`) y negativos en minúsculas (`m, u, n, p`).
  - Separación mediante guión bajo entre prefijo y unidad (ej. `67.120 (K_Pa)`, `4.243 (K_W)`, `20.000 (m_m)`, `1.051 (M_J)`).
- **Columnas Explicativas Laterales:** Cada ecuación muestra a su derecha las variables que intervienen con su descripción y el nombre completo de su unidad (`metros`, `Pascales`, `kilogramos`, `Watts`, etc.).

---

## 🚀 Instalación y Ejecución

```bash
source venv_sus_d/bin/activate
python calc.py
```
