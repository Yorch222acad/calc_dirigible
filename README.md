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

## ✨ Características Principales

- **Motor CAS + Numérico con SymPy:** Resuelve analíticamente (`solve`) o numéricamente (`nsolve` con poda de hojas en grafos bipartitos) cualquiera de las **102 variables** a partir de las **56 ecuaciones** acopladas.
- **Notación de Ingeniería Personalizada:**
  - Prefijos positivos en mayúsculas (`K, M, G, T`) y negativos en minúsculas (`m, u, n, p`).
  - Separación mediante guión bajo entre prefijo y unidad (ej. `67.120 (K_Pa)`, `299.565 (W)`, `452.242 (g)`, `1.113 (M_adim)`).
- **Columnas Explicativas Laterales:** Cada ecuación muestra a su derecha las variables que intervienen con su descripción y el nombre completo de su unidad.

---

## 🚀 Instalación y Ejecución

```bash
source venv_sus_d/bin/activate
python calc.py
```
