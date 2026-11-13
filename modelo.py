"""
Modelo del sistema basado en CAS (SymPy).

Para ampliar el programa solo hay que:
  1. Agregar la variable en VARIABLES (nombre, descripción, unidad, valor inicial).
  2. Registrar su formato ingenieril en UNIDAD_ING y nombre completo de unidad en UNIDAD_NOMBRE.
  3. Agregar la ecuación en la categoría correspondiente de CATEGORIAS (como sp.Eq).
  4. Si la variable es un dato de entrada, incluirla en FIJAS_INI
     (regla: nº de variables calculadas == nº de ecuaciones independientes).
"""
from itertools import combinations
import sympy as sp

# =============================================================
# VARIABLES: nombre -> (descripción, unidad, valor inicial o None)
# Calibradas para La Paz - Zona Sur a 100 m (~3.350 m s.n.m.)
# Geometría inicial calculada para mflot = 3.0 kg y mres = 0.5 kg: R ≈ 1.173 m, L ≈ 5.631 m, V ≈ 16.23 m³
# =============================================================
VARIABLES = {
    # Caso 1: gas a temperatura ambiente (exterior)
    "P1":     ("Presión caso 1 (ambiente)",              "Pa",          67120.0),
    "T1":     ("Temperatura caso 1 (ambiente)",          "°C",          15.0),
    "R1":     ("Constante R caso 1",                     "J/(kg·K)",    287.058),
    "rho1":   ("Densidad caso 1 (ambiente)",             "kg/m³",       None),
    # Caso 2: mismo gas a mayor temperatura (aire caliente interior)
    "P2":     ("Presión caso 2 (aire caliente)",         "Pa",          67120.0),
    "T2":     ("Temperatura caso 2 (aire caliente)",     "°C",          100.0),
    "R2":     ("Constante R caso 2",                     "J/(kg·K)",    287.058),
    "rho2":   ("Densidad caso 2 (aire caliente)",        "kg/m³",       None),
    "drho":   ("Diferencia de densidades",               "kg/m³",       None),
    # Geometría del casco (dos semielipsoides prolados, cf > R y cr > R)
    "R":      ("Radio máximo transversal",               "m",           None),
    "lam":    ("Relación de esbeltez (L/D)",             "adim",        2.4),
    "xf":     ("Fracción de nariz (cf/L)",               "adim",        0.35),
    "cf":     ("Longitud semielipsoide nariz",           "m",           None),
    "cr":     ("Longitud semielipsoide cola",            "m",           None),
    "L":      ("Longitud total del casco",               "m",           None),
    "V":      ("Volumen total del casco",                "m³",          None),
    "ef":     ("Excentricidad frontal",                  "adim",        None),
    "er":     ("Excentricidad trasera",                  "adim",        None),
    "Sf":     ("Área superficial frontal",               "m²",          None),
    "Sr":     ("Área superficial trasera",               "m²",          None),
    "S":      ("Área superficial total",                 "m²",          None),
    # Masa de aire caliente y calor sensible
    "m":      ("Masa de aire caliente",                  "kg",          None),
    "cp":     ("Calor específico del aire",              "J/(kg·K)",    1005.0),
    "dT":     ("Gradiente térmico (T2 - T1)",            "K",           None),
    "Q":      ("Calor sensible total",                   "J",           None),
    # Sustentación aerostática (Arquímedes)
    "g":      ("Aceleración de la gravedad",             "m/s²",        9.775),
    "F":      ("Fuerza de sustentación aerostática",     "N",           None),
    # Aislamiento por capa intermedia de celdas (con orificios de ecualización de 3 mm)
    "e":      ("Espesor de capa intermedia celular",     "m",           0.02),
    "W":      ("Ancho de celda cuadrada",                "m",           0.20),
    "beta":   ("Coef. expansión térmica del aire",       "K⁻¹",         0.00302),
    "nu":     ("Viscosidad cinemática del aire",         "m²/s",        2.65e-5),
    "alpha":  ("Difusividad térmica del aire",           "m²/s",        3.80e-5),
    "Rae":    ("Número de Rayleigh en la celda",         "adim",        None),
    "Rac":    ("Rayleigh crítico de convección",         "adim",        2000.0),
    "Nuc":    ("Número de Nusselt en la celda",          "adim",        None),
    "ka":     ("Conductividad térmica del aire",         "W/(m·K)",     0.0285),
    "U0":     ("Coef. global sin capa celular",          "W/(m²·K)",    5.0),
    "U":      ("Coef. global con capa celular",          "W/(m²·K)",    None),
    "Qp0":    ("Potencia perdida sin capa celular",      "W",           None),
    "Qp":     ("Potencia perdida con capa celular",      "W",           None),
    "dQp":    ("Potencia ahorrada por capa celular",     "W",           None),
    "fais":   ("Fracción de ahorro térmico celular",     "adim",        None),
    "Sc":     ("Área de película de la cuadrícula",      "m²",          None),
    "sigma":  ("Gramaje de película HDPE",               "kg/m²",       0.0095),
    "mc":     ("Masa total de la cuadrícula celular",    "kg",          None),
    # Pérdida de calor y enfriamiento (con aislante celular incorporado)
    "vT":     ("Velocidad de enfriamiento (dT/dt)",      "K/s",         None),
    "dTc":    ("Caída admisible de temperatura",         "K",           20.0),
    "Qc":     ("Energía perdida en caída dTc",           "J",           None),
    "tc":     ("Tiempo de enfriamiento para dTc",        "s",           None),
    # Quemador de propano/butano (GLP) para compensación térmica
    "PC":     ("Poder calorífico del GLP (propano)",     "J/kg",        4.6e7),
    "mgc":    ("Masa de GLP para recuperar caída dTc",   "kg",          None),
    "tm":     ("Tiempo de misión (vuelo/mantenimiento)", "s",           None),
    "Em":     ("Energía térmica para mantener T",        "J",           None),
    "mgm":    ("Masa de GLP consumida en misión",        "kg",          None),
    # Resistencia aerodinámica en el desplazamiento (arrastre)
    "v":      ("Velocidad relativa al aire",             "m/s",         6.5),
    "mu":     ("Viscosidad dinámica del aire",           "Pa·s",        1.75e-5),
    "ReL":    ("Número de Reynolds longitudinal",        "adim",        None),
    "Cf":     ("Coef. de fricción superficial",          "adim",        None),
    "CDVc":   ("Coef. volumétrico del casco limpio",     "adim",        None),
    "kp":     ("Factor de penalización parásita",        "adim",        1.4),
    "CDV":    ("Coef. de resistencia volumétrico",       "adim",        None),
    "FD":     ("Fuerza de resistencia aerodinámica",     "N",           None),
    # Masas y balance de peso del dirigible híbrido
    "N":      ("Número de motores activos",              "adim",        4.0),
    "mmot":   ("Masa de cada motor A2212 (1000KV)",      "kg",          0.047),
    "mp":     ("Masa de combustible propano a bordo",    "kg",          0.220),
    "mad":    ("Masa adicional de componentes",          "kg",          1.1),
    "mart":   ("Masa del artefacto con componentes",     "kg",          None),
    "mcarga": ("Carga útil",                             "kg",          1.0),
    "mtot":   ("Masa total del dirigible",               "kg",          None),
    "mflot":  ("Masa compensada por aire caliente",      "kg",          3.0),
    "mres":   ("Masa residual a sostener por motores",   "kg",          0.5),
    "fap":    ("Factor de masa aparente virtual",        "adim",        1.15),
    "map":    ("Masa aparente traslacional",             "kg",          None),
    # Propulsión vectorial y motores Brushless A2212 (1000KV)
    "vz":     ("Velocidad de ascenso objetivo",          "m/s",         0.8),
    "vx":     ("Velocidad de traslación objetivo",       "m/s",         3.0),
    "ta":     ("Tiempo de aceleración de maniobra",      "s",           5.0),
    "az":     ("Aceleración vertical de ascenso",        "m/s²",        None),
    "ax":     ("Aceleración horizontal de avance",       "m/s²",        None),
    "FL":     ("Sustentación dinámica vertical motores", "N",           None),
    "FX":     ("Fuerza horizontal de avance motores",    "N",           None),
    "Ttot":   ("Empuje total de los 4 motores",          "N",           None),
    "theta":  ("Ángulo de rotación de motores",          "°",           None),
    "thmax":  ("Ángulo máximo de rotación admisible",    "°",           75.0),
    "dth":    ("Margen de ángulo de rotación",           "°",           None),
    "Tmax1":  ("Empuje máximo por motor A2212",          "N",           5.5),
    "FLmax":  ("Sustentación vertical máx. de motores",  "N",           None),
    "Fexc":   ("Excedente de sustentación total",        "N",           None),
    "dp":     ("Diámetro de cada hélice (10 pulg)",      "m",           0.254),
    "Ap":     ("Área de disco barrida por hélice",       "m²",          None),
    "nprop":  ("Eficiencia aerodinámica de hélice",      "adim",        0.60),
    "nm":     ("Eficiencia electromecánica A2212",       "adim",        0.78),
    "nESC":   ("Eficiencia de variadores ESC",           "adim",        0.95),
    "ntot":   ("Eficiencia propulsiva global",           "adim",        None),
    "km":     ("Factor de margen de control/maniobra",   "adim",        1.20),
    "Pelec":  ("Potencia eléctrica de los 4 motores",    "W",           None),
    # Batería requerida y energía eléctrica de misión
    "Ereq":   ("Energía eléctrica requerida en misión",  "Wh",          None),
    "ebat":   ("Energía específica de batería",          "Wh/kg",       150.0),
    "DoD":    ("Profundidad de descarga máxima (DoD)",   "adim",        0.80),
    "ntemp":  ("Factor de derateo térmico de batería",   "adim",        0.92),
    "mbat":   ("Masa de batería requerida",              "kg",          None),
    "mbmax":  ("Masa máxima admisible de batería",       "kg",          1.0),
    "dmbat":  ("Margen de masa de batería",              "kg",          None),
}

# Nombre completo de cada unidad para las columnas explicativas junto a las ecuaciones
UNIDAD_NOMBRE = {
    "Pa":       "Pascales",
    "°C":       "grados Celsius",
    "J/(kg·K)": "Joules por kilogramo Kelvin",
    "kg/m³":    "kilogramos por metro cúbico",
    "m":        "metros",
    "m²":       "metros cuadrados",
    "m³":       "metros cúbicos",
    "adim":     "adimensional",
    "kg":       "kilogramos",
    "K":        "grados Kelvin",
    "J":        "Joules",
    "m/s²":     "metros por segundo cuadrado",
    "N":        "Newtons",
    "W":        "Watts",
    "W/(m·K)":  "Watts por metro Kelvin",
    "W/(m²·K)": "Watts por metro cuadrado Kelvin",
    "K/s":      "grados Kelvin por segundo",
    "s":        "segundos",
    "K⁻¹":      "inverso de grado Kelvin",
    "m²/s":     "metros cuadrados por segundo",
    "kg/m²":    "kilogramos por metro cuadrado",
    "J/kg":     "Joules por kilogramo",
    "m/s":      "metros por segundo",
    "Pa·s":     "Pascales segundo",
    "°":        "grados sexagesimales",
    "Wh":       "Watts hora",
    "Wh/kg":    "Watts hora por kilogramo",
}

# Variables de entrada al iniciar (102 variables - 56 ecuaciones = 46 fijas)
# Se fijan mflot (carga aire caliente) y mres (carga motores); R y tm se ajustan automáticamente.
FIJAS_INI = [
    "P1", "T1", "R1", "P2", "T2", "R2",
    "lam", "xf",
    "cp", "g",
    "e", "W", "beta", "nu", "alpha", "Rac", "ka", "U0", "sigma",
    "dTc",
    "PC",
    "v", "mu", "kp",
    "N", "mmot", "mp", "mad", "mcarga", "mflot", "mres", "fap",
    "vz", "vx", "ta", "thmax", "Tmax1", "dp", "nprop", "nm", "nESC", "km",
    "ebat", "DoD", "ntemp", "mbmax",
]

# Variables que físicamente deben ser estrictamente positivas
POSITIVAS = {
    "P1", "R1", "rho1", "P2", "R2", "rho2",
    "R", "lam", "xf", "cf", "cr", "L", "V", "ef", "er", "Sf", "Sr", "S",
    "m", "cp", "g",
    "e", "W", "beta", "nu", "alpha", "Rae", "Rac", "Nuc", "ka", "U0", "U",
    "Qp0", "Qp", "dQp", "fais", "Sc", "sigma", "mc",
    "vT", "dTc", "Qc", "tc",
    "PC", "mgc", "tm", "Em", "mgm",
    "v", "mu", "ReL", "Cf", "CDVc", "kp", "CDV", "FD",
    "N", "mmot", "mp", "mad", "mart", "mcarga", "mtot", "mflot", "mres", "fap", "map",
    "vz", "vx", "ta", "az", "ax", "FL", "FX", "Ttot", "theta", "thmax",
    "Tmax1", "FLmax", "dp", "Ap", "nprop", "nm", "nESC", "ntot", "km", "Pelec",
    "Ereq", "ebat", "DoD", "ntemp", "mbat", "mbmax",
}

# Unidad para notación de ingeniería: nombre -> (unidad prefijable, resto, factor)
# Se muestra como: <prefijo>_<unidad prefijable><resto>. El factor convierte el valor
# SI al de la unidad prefijable (ej. kg -> g: 1000). Si es None no se usan prefijos.
UNIDAD_ING = {
    "P1":     ("Pa", "", 1),        "P2":     ("Pa", "", 1),
    "T1":     (None, "°C", 1),      "T2":     (None, "°C", 1),
    "R1":     ("J", "/(kg·K)", 1),  "R2":     ("J", "/(kg·K)", 1),
    "rho1":   ("g", "/m³", 1000),   "rho2":   ("g", "/m³", 1000),   "drho":  ("g", "/m³", 1000),
    "lam":    (None, "adim", 1),    "xf":     (None, "adim", 1),
    "R":      ("m", "", 1),         "cf":     ("m", "", 1),         "cr":    ("m", "", 1),
    "L":      ("m", "", 1),         "V":      ("m³", "", 1),
    "ef":     (None, "adim", 1),    "er":     (None, "adim", 1),
    "Sf":     ("m²", "", 1),        "Sr":     ("m²", "", 1),        "S":     ("m²", "", 1),
    "m":      ("g", "", 1000),
    "cp":     ("J", "/(kg·K)", 1),
    "dT":     ("K", "", 1),
    "Q":      ("J", "", 1),
    "g":      (None, "m/s²", 1),
    "F":      ("N", "", 1),
    # Capa intermedia de celdas y transferencia de calor
    "e":      ("m", "", 1),
    "W":      ("m", "", 1),
    "beta":   ("K⁻¹", "", 1),
    "nu":     ("m²/s", "", 1),
    "alpha":  ("m²/s", "", 1),
    "Rae":    ("adim", "", 1),
    "Rac":    ("adim", "", 1),
    "Nuc":    (None, "adim", 1),
    "ka":     ("W", "/(m·K)", 1),
    "U0":     ("W", "/(m²·K)", 1),
    "U":      ("W", "/(m²·K)", 1),
    "Qp0":    ("W", "", 1),
    "Qp":     ("W", "", 1),
    "dQp":    ("W", "", 1),
    "fais":   (None, "adim", 1),
    "Sc":     ("m²", "", 1),
    "sigma":  ("g", "/m²", 1000),
    "mc":     ("g", "", 1000),
    # Pérdida de calor y enfriamiento
    "vT":     ("K", "/s", 1),
    "dTc":    ("K", "", 1),
    "Qc":     ("J", "", 1),
    "tc":     ("s", "", 1),
    # Quemador de GLP
    "PC":     ("J", "/kg", 1),
    "mgc":    ("g", "", 1000),
    "tm":     ("s", "", 1),
    "Em":     ("J", "", 1),
    "mgm":    ("g", "", 1000),
    # Resistencia aerodinámica
    "v":      ("m", "/s", 1),
    "mu":     ("Pa·s", "", 1),
    "ReL":    ("adim", "", 1),
    "Cf":     ("adim", "", 1),
    "CDVc":   ("adim", "", 1),
    "kp":     (None, "adim", 1),
    "CDV":    ("adim", "", 1),
    "FD":     ("N", "", 1),
    # Masas y balance de peso
    "N":      (None, "adim", 1),
    "mmot":   ("g", "", 1000),
    "mp":     ("g", "", 1000),
    "mad":    ("g", "", 1000),
    "mart":   ("g", "", 1000),
    "mcarga": ("g", "", 1000),
    "mtot":   ("g", "", 1000),
    "mflot":  ("g", "", 1000),
    "mres":   ("g", "", 1000),
    "fap":    (None, "adim", 1),
    "map":    ("g", "", 1000),
    # Propulsión vectorial y motores A2212
    "vz":     ("m", "/s", 1),
    "vx":     ("m", "/s", 1),
    "ta":     ("s", "", 1),
    "az":     ("m", "/s²", 1),
    "ax":     ("m", "/s²", 1),
    "FL":     ("N", "", 1),
    "FX":     ("N", "", 1),
    "Ttot":   ("N", "", 1),
    "theta":  (None, "°", 1),
    "thmax":  (None, "°", 1),
    "dth":    (None, "°", 1),
    "Tmax1":  ("N", "", 1),
    "FLmax":  ("N", "", 1),
    "Fexc":   ("N", "", 1),
    "dp":     ("m", "", 1),
    "Ap":     ("m²", "", 1),
    "nprop":  (None, "adim", 1),
    "nm":     (None, "adim", 1),
    "nESC":   (None, "adim", 1),
    "ntot":   (None, "adim", 1),
    "km":     (None, "adim", 1),
    "Pelec":  ("W", "", 1),
    # Batería y energía eléctrica
    "Ereq":   ("Wh", "", 1),
    "ebat":   ("Wh", "/kg", 1),
    "DoD":    (None, "adim", 1),
    "ntemp":  (None, "adim", 1),
    "mbat":   ("g", "", 1000),
    "mbmax":  ("g", "", 1000),
    "dmbat":  ("g", "", 1000),
}

S = {
    n: sp.Symbol(n, real=True, positive=(True if n in POSITIVAS else None))
    for n in VARIABLES
}
K = sp.Rational("273.15")  # °C -> K
S_POR_H = sp.Integer(3600)  # s -> h

# =============================================================
# Ecuaciones agrupadas por categoría (se muestran así en pantalla)
# =============================================================
CATEGORIAS = {
    "Gases ideales y densidades": {
        "Gas ideal (caso 1 - ambiente)": sp.Eq(S["rho1"], S["P1"] / (S["R1"] * (S["T1"] + K))),
        "Gas ideal (caso 2 - caliente)": sp.Eq(S["rho2"], S["P2"] / (S["R2"] * (S["T2"] + K))),
        "Diferencia de densidades":      sp.Eq(S["drho"], S["rho1"] - S["rho2"]),
    },
    "Geometría del casco (dos semielipsoides)": {
        # Esbeltez: λ = L/D. λ → 1 se parece a una esfera; λ alto se parece a una "aguja"
        "Relación de esbeltez (L/D)":     sp.Eq(S["lam"], S["L"] / (2 * S["R"])),
        "Fracción de nariz (cf/L)":       sp.Eq(S["xf"], S["cf"] / S["L"]),
        "Longitud total del casco":       sp.Eq(S["L"],  S["cf"] + S["cr"]),
        "Volumen total del casco":        sp.Eq(S["V"],  sp.Rational(2, 3) * sp.pi * S["R"] ** 2 * S["L"]),
        "Excentricidad frontal (cf > R)": sp.Eq(S["ef"], sp.sqrt(1 - S["R"] ** 2 / S["cf"] ** 2)),
        "Excentricidad trasera (cr > R)": sp.Eq(S["er"], sp.sqrt(1 - S["R"] ** 2 / S["cr"] ** 2)),
        "Área superficial frontal":       sp.Eq(S["Sf"], sp.pi * S["R"] * S["cf"] * sp.asin(S["ef"]) / S["ef"]),
        "Área superficial trasera":       sp.Eq(S["Sr"], sp.pi * S["R"] * S["cr"] * sp.asin(S["er"]) / S["er"]),
        "Área superficial total":         sp.Eq(S["S"],  S["Sf"] + S["Sr"]),
    },
    "Aire caliente y termodinámica": {
        "Masa de aire caliente": sp.Eq(S["m"],  S["rho2"] * S["V"]),
        "Gradiente térmico":     sp.Eq(S["dT"], S["T2"] - S["T1"]),
        "Calor sensible":        sp.Eq(S["Q"],  S["m"] * S["cp"] * S["dT"]),
    },
    "Sustentación": {
        # Arquímedes: F = Δρ·g·V  (equivale a Δρ·g·m/ρ₂, pues m = ρ₂·V)
        "Fuerza de sustentación aerostática": sp.Eq(S["F"], S["drho"] * S["g"] * S["V"]),
    },
    "Aislamiento por capa intermedia de celdas": {
        "Número de Rayleigh en cavidad (Rae)": sp.Eq(
            S["Rae"], (S["g"] * S["beta"] * S["dT"] * S["e"] ** 3) / (S["nu"] * S["alpha"])
        ),
        "Número de Nusselt en celda (Nuc)": sp.Eq(
            S["Nuc"], (S["Rae"] / S["Rac"]) ** sp.Rational(1, 4)
        ),
        "Coeficiente global con capa celular (U)": sp.Eq(
            S["U"], 1 / (1 / S["U0"] + S["e"] / (S["ka"] * S["Nuc"]))
        ),
        "Potencia perdida sin capa celular (Qp0)": sp.Eq(
            S["Qp0"], S["U0"] * S["S"] * S["dT"]
        ),
        "Potencia perdida con capa celular (Qp)": sp.Eq(
            S["Qp"], S["U"] * S["S"] * S["dT"]
        ),
        "Potencia ahorrada por capa celular (dQp)": sp.Eq(
            S["dQp"], S["Qp0"] - S["Qp"]
        ),
        "Fracción de ahorro térmico celular (fais)": sp.Eq(
            S["fais"], S["dQp"] / S["Qp0"]
        ),
        "Área total de película celular": sp.Eq(
            S["Sc"], S["S"] * (1 + 2 * S["e"] / S["W"])
        ),
        "Masa de la cuadrícula celular": sp.Eq(
            S["mc"], S["Sc"] * S["sigma"]
        ),
    },
    "Pérdida de calor y enfriamiento": {
        "Velocidad de enfriamiento (dT/dt)": sp.Eq(S["vT"], S["Qp"] / (S["m"] * S["cp"])),
        "Energía cedida en caída admisible": sp.Eq(S["Qc"], S["m"] * S["cp"] * S["dTc"]),
        "Tiempo de enfriamiento sin aporte": sp.Eq(S["tc"], S["Qc"] / S["Qp"]),
    },
    "Quemador de propano/butano (compensación térmica)": {
        "Masa de gas para recuperar caída dTc": sp.Eq(S["mgc"], S["Qc"] / S["PC"]),
        "Energía para mantener T en misión":    sp.Eq(S["Em"],  S["Qp"] * S["tm"]),
        "Masa de gas para mantener T en misión": sp.Eq(S["mgm"], S["Em"] / S["PC"]),
    },
    "Resistencia aerodinámica (arrastre)": {
        "Número de Reynolds longitudinal (ReL)": sp.Eq(
            S["ReL"], (S["rho1"] * S["v"] * S["L"]) / S["mu"]
        ),
        "Coeficiente de fricción superficial (Cf)": sp.Eq(
            S["Cf"], sp.Float("0.455") / (sp.log(S["ReL"], 10) ** sp.Float("2.58"))
        ),
        "Coeficiente volumétrico del casco (CDVc - Hoerner)": sp.Eq(
            S["CDVc"],
            S["Cf"] * (
                4 * S["lam"] ** sp.Rational(1, 3)
                + 6 * S["lam"] ** sp.Float("-1.2")
                + 24 * S["lam"] ** sp.Float("-2.7")
            ),
        ),
        "Coeficiente de resistencia volumétrico total (CDV)": sp.Eq(
            S["CDV"], S["kp"] * S["CDVc"]
        ),
        "Fuerza de resistencia aerodinámica (FD)": sp.Eq(
            S["FD"], sp.Rational(1, 2) * S["rho1"] * S["v"] ** 2 * S["CDV"] * S["V"] ** sp.Rational(2, 3)
        ),
    },
    "Masas y balance de peso (dirigible híbrido)": {
        "Masa del artefacto con sus componentes (mart)": sp.Eq(
            S["mart"], S["mc"] + S["N"] * S["mmot"] + S["mp"] + S["mad"] + S["mbat"]
        ),
        "Masa total del dirigible con carga útil (mtot)": sp.Eq(
            S["mtot"], S["mart"] + S["mcarga"]
        ),
        "Masa compensada por aire caliente (mflot)": sp.Eq(
            S["mflot"], S["F"] / S["g"]
        ),
        "Masa residual a compensar por motores (mres)": sp.Eq(
            S["mres"], S["mtot"] - S["mflot"]
        ),
        "Masa aparente traslacional (map)": sp.Eq(
            S["map"], S["fap"] * S["mtot"]
        ),
    },
    "Propulsión vectorial y motores A2212 (1000KV)": {
        "Aceleración vertical de ascenso (az)": sp.Eq(
            S["az"], S["vz"] / S["ta"]
        ),
        "Aceleración horizontal de traslación (ax)": sp.Eq(
            S["ax"], S["vx"] / S["ta"]
        ),
        "Componente vertical de sustentación de motores (FL)": sp.Eq(
            S["FL"], S["mres"] * S["g"] + S["mtot"] * S["az"]
        ),
        "Componente horizontal de avance de motores (FX)": sp.Eq(
            S["FX"], S["FD"] + S["map"] * S["ax"]
        ),
        "Empuje vectorial total de los 4 motores (Ttot)": sp.Eq(
            S["Ttot"], sp.sqrt(S["FL"] ** 2 + S["FX"] ** 2)
        ),
        "Ángulo de rotación respecto a la vertical (theta)": sp.Eq(
            S["theta"], sp.Integer(180) * sp.atan(S["FX"] / S["FL"]) / sp.pi
        ),
        "Margen respecto al ángulo máximo de rotación (dth)": sp.Eq(
            S["dth"], S["thmax"] - S["theta"]
        ),
        "Sustentación vertical máxima de los 4 motores (FLmax)": sp.Eq(
            S["FLmax"], sp.sqrt((S["N"] * S["Tmax1"]) ** 2 - S["FX"] ** 2)
        ),
        "Excedente de sustentación total (Fexc)": sp.Eq(
            S["Fexc"], S["F"] + S["FLmax"] - S["mtot"] * S["g"]
        ),
        "Área de disco barrida por cada hélice (Ap)": sp.Eq(
            S["Ap"], sp.pi * S["dp"] ** 2 / 4
        ),
        "Eficiencia propulsiva global (ntot)": sp.Eq(
            S["ntot"], S["nprop"] * S["nm"] * S["nESC"]
        ),
        "Potencia eléctrica demandada por los 4 motores (Pelec)": sp.Eq(
            S["Pelec"],
            (S["km"] / S["ntot"]) * (
                S["Ttot"] ** sp.Rational(3, 2) / sp.sqrt(2 * S["rho1"] * S["N"] * S["Ap"])
                + S["FX"] * S["v"]
            ),
        ),
    },
    "Batería requerida y energía eléctrica": {
        "Energía eléctrica requerida en misión (Ereq)": sp.Eq(
            S["Ereq"], (S["Pelec"] * S["tm"]) / S_POR_H
        ),
        "Masa de batería requerida (mbat)": sp.Eq(
            S["mbat"], S["Ereq"] / (S["ebat"] * S["DoD"] * S["ntemp"])
        ),
        "Margen respecto al peso máximo de batería (dmbat)": sp.Eq(
            S["dmbat"], S["mbmax"] - S["mbat"]
        ),
    },
}

# Lista plana de ecuaciones para el solucionador
ECUACIONES = {nombre: eq for cat in CATEGORIAS.values() for nombre, eq in cat.items()}


def valores_iniciales() -> dict[str, float]:
    return {n: v[2] for n, v in VARIABLES.items() if n in FIJAS_INI}


def ecuaciones_de_variable(nombre: str) -> list[tuple[str, str, sp.Eq]]:
    """Devuelve [(categoria, nombre_eq, eq)] donde interviene la variable `nombre`."""
    sim = S[nombre]
    return [
        (cat, nom_eq, eq)
        for cat, eqs in CATEGORIAS.items()
        for nom_eq, eq in eqs.items()
        if sim in eq.free_symbols
    ]


def _tamano_emparejamiento(incognitas: set[str]) -> int:
    """Calcula el tamaño del emparejamiento máximo bipartito (ecuaciones <-> incógnitas)."""
    eq_vars = [
        [str(sim) for sim in eq.free_symbols if str(sim) in incognitas]
        for eq in ECUACIONES.values()
    ]
    match_var: dict[str, int] = {}

    def dfs(u: int, visto: set[str]) -> bool:
        for v in eq_vars[u]:
            if v in visto:
                continue
            visto.add(v)
            if v not in match_var or dfs(match_var[v], visto):
                match_var[v] = u
                return True
        return False

    emparejadas = 0
    for u in range(len(eq_vars)):
        if dfs(u, set()):
            emparejadas += 1
    return emparejadas


def _tiene_emparejamiento_perfecto(incognitas: set[str]) -> bool:
    """Comprueba en el grafo bipartito (ecuaciones <-> incógnitas) si el sistema es resoluble."""
    return len(incognitas) == len(ECUACIONES) and _tamano_emparejamiento(incognitas) == len(ECUACIONES)


def variables_liberables(fijas: set[str], objetivo: str) -> list[str]:
    """
    Dada una variable calculada `objetivo` que pasará a ser fija, devuelve las
    variables fijas que pueden volverse calculadas (liberarse) manteniendo el sentido matemático.
    """
    inc_actual = set(VARIABLES) - fijas
    return [
        f for f in VARIABLES
        if f in fijas and _tiene_emparejamiento_perfecto((inc_actual - {objetivo}) | {f})
    ]


def calculadas_fijables(fijas: set[str], fija_a_liberar: str) -> list[str]:
    """
    Dada una variable fija `fija_a_liberar` que pasará a ser calculada, devuelve
    cuáles variables calculadas pueden volverse fijas manteniendo el sentido matemático.
    """
    inc_actual = set(VARIABLES) - fijas
    return [
        c for c in VARIABLES
        if c in inc_actual and _tiene_emparejamiento_perfecto((inc_actual - {c}) | {fija_a_liberar})
    ]


def estado_equilibrio(
    fijas_actuales: set[str],
    excluidas: set[str] | None = None,
) -> tuple[int, list[str], int, list[str]]:
    """
    Analiza el estado matemático actual dado `fijas_actuales`:
    Devuelve `(faltan_fijar, candidatas_calculadas_a_fijar, faltan_liberar, candidatas_fijas_a_liberar)`.
    - `faltan_fijar`: cuántas variables calculadas faltan por volver fijas.
    - `candidatas_calculadas_a_fijar`: cuáles variables calculadas se pueden volver fijas en este paso.
    - `faltan_liberar`: cuántas variables fijas faltan por liberar (volver calculadas).
    - `candidatas_fijas_a_liberar`: cuáles variables fijas se pueden liberar en este paso.
    """
    excl = excluidas or set()
    inc_actual = set(VARIABLES) - fijas_actuales
    n_eq = len(ECUACIONES)
    m = _tamano_emparejamiento(inc_actual)

    faltan_fijar = len(inc_actual) - m
    faltan_liberar = n_eq - m

    candidatas_fijar: list[str] = []
    if faltan_fijar > 0:
        candidatas_fijar = [
            c for c in VARIABLES
            if c in inc_actual and c not in excl and _tamano_emparejamiento(inc_actual - {c}) == m
        ]

    candidatas_liberar: list[str] = []
    if faltan_liberar > 0:
        candidatas_liberar = [
            f for f in VARIABLES
            if f in fijas_actuales and f not in excl and _tamano_emparejamiento(inc_actual | {f}) == m + 1
        ]

    return faltan_fijar, candidatas_fijar, faltan_liberar, candidatas_liberar


def _es_valida(nombre: str, val: sp.Expr) -> bool:
    """Verifica que un valor simbólico sea numérico, real y respete dominios físicos."""
    try:
        val_num = sp.sympify(val).evalf()
        if not val_num.is_number:
            return False
        if abs(float(sp.im(val_num))) > 1e-7:
            return False
        v = float(sp.re(val_num))
    except Exception:
        return False
    if nombre in POSITIVAS and v <= 0:
        return False
    if nombre in ("ef", "er", "fais", "xf", "nprop", "nm", "nESC", "ntot", "DoD", "ntemp") and not (0 < v < 1):
        return False
    if nombre == "theta" and not (0 < v < 90):
        return False
    return True


def _resolver_bloque(
    eqs_bloque: list[sp.Eq],
    incognitas_bloque: list[sp.Symbol],
    semilla: dict[str, float],
) -> dict[str, float]:
    """Resuelve un subsistema mínimo de k ecuaciones con k incógnitas."""
    # Caso rápido: 1 ecuación donde la incógnita ya está despejada en un miembro
    if len(eqs_bloque) == 1 and len(incognitas_bloque) == 1:
        eq = eqs_bloque[0]
        inc = incognitas_bloque[0]
        nombre = str(inc)
        if eq.lhs == inc and inc not in eq.rhs.free_symbols:
            if _es_valida(nombre, eq.rhs):
                return {nombre: float(sp.re(eq.rhs.evalf()))}
        elif eq.rhs == inc and inc not in eq.lhs.free_symbols:
            if _es_valida(nombre, eq.lhs):
                return {nombre: float(sp.re(eq.lhs.evalf()))}

    # Intento 1: resolución simbólica con SymPy (para bloques pequeños sin potencias fraccionarias acopladas)
    if len(eqs_bloque) <= 3:
        try:
            soluciones = sp.solve(eqs_bloque, incognitas_bloque, dict=True)
            validas = [
                s for s in soluciones
                if len(s) == len(incognitas_bloque)
                and all(_es_valida(str(k), v) for k, v in s.items())
            ]
            if validas:
                return {str(k): float(sp.re(v.evalf())) for k, v in validas[0].items()}
        except Exception:
            pass

    # Intento 2: reducción simbólica + resolución numérica (para ciclos acoplados o ecuaciones trascendentes)
    try:
        # Reducción por sustitución simbólica dentro del bloque
        sust_interna: dict[sp.Symbol, sp.Expr] = {}
        orden_elim: list[tuple[sp.Symbol, sp.Expr]] = []
        eqs_reducidas = list(eqs_bloque)
        cambio = True
        while cambio and len(eqs_reducidas) > 1:
            cambio = False
            for idx, eq in enumerate(eqs_reducidas):
                if eq.lhs in incognitas_bloque and eq.lhs not in eq.rhs.free_symbols:
                    v_elim = eq.lhs
                    expr_elim = eq.rhs
                elif eq.rhs in incognitas_bloque and eq.rhs not in eq.lhs.free_symbols:
                    v_elim = eq.rhs
                    expr_elim = eq.lhs
                else:
                    continue
                eqs_reducidas.pop(idx)
                eqs_reducidas = [e.xreplace({v_elim: expr_elim}) for e in eqs_reducidas]
                sust_interna = {k: v.xreplace({v_elim: expr_elim}) for k, v in sust_interna.items()}
                sust_interna[v_elim] = expr_elim
                orden_elim.append((v_elim, expr_elim))
                cambio = True
                break

        inc_reducidas = [inc for inc in incognitas_bloque if inc not in sust_interna]
        exprs = [e.lhs - e.rhs for e in eqs_reducidas]
        valores_semilla = [semilla.get(str(inc), 1.0) for inc in inc_reducidas]
        if len(exprs) == 1 and len(inc_reducidas) == 1:
            try:
                sol_unica = sp.nsolve(exprs[0], inc_reducidas[0], valores_semilla[0])
            except Exception:
                sol_unica = sp.nsolve(exprs[0], inc_reducidas[0], max(valores_semilla[0], 0.5))
            pares = [(inc_reducidas[0], sol_unica)]
        else:
            sol_num = sp.nsolve(exprs, inc_reducidas, valores_semilla)
            pares = list(zip(inc_reducidas, sol_num))

        res_sim = {inc: sp.sympify(val).evalf() for inc, val in pares}
        for inc_elim, expr_elim in reversed(orden_elim):
            res_sim[inc_elim] = expr_elim.xreplace(res_sim).evalf()

        res = {}
        for inc, val in res_sim.items():
            if not _es_valida(str(inc), val):
                raise ValueError(f"Solución fuera de dominio físico para '{inc}'.")
            res[str(inc)] = float(sp.re(val))
        return res
    except Exception as exc:
        raise ValueError(
            "Esa combinación no tiene solución única o físicamente válida "
            "(verifica p. ej. que cf > R, cr > R y que el empuje supere el arrastre)."
        ) from exc


def _podar_hojas(eqs_sust: list[sp.Eq]) -> list[int]:
    """
    Descarta iterativamente las ecuaciones que contienen una incógnita que solo
    aparece en esa ecuación (grado 1), pues nunca pueden pertenecer a un ciclo
    cerrado mínimo de tamaño k >= 2.
    """
    activos = list(range(len(eqs_sust)))
    inc_por_eq = {
        i: {sim for sim in eqs_sust[i].free_symbols if str(sim) in VARIABLES}
        for i in activos
    }
    while True:
        conteo: dict[sp.Symbol, int] = {}
        for i in activos:
            for sim in inc_por_eq[i]:
                conteo[sim] = conteo.get(sim, 0) + 1
        quitar = [
            i for i in activos
            if any(conteo[sim] == 1 for sim in inc_por_eq[i])
        ]
        if not quitar:
            break
        activos = [i for i in activos if i not in set(quitar)]
    return activos


def resolver(
    fijas: dict[str, float],
    referencia: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Dadas las variables fijas (nombre -> valor), calcula todas las demás
    resolviendo escalonadamente los subsistemas acoplados.
    Lanza ValueError si el sistema no tiene solución única real.
    """
    conocidas: dict[str, float] = dict(fijas)
    semilla = referencia if referencia is not None else conocidas
    pendientes = list(ECUACIONES.values())

    while pendientes:
        sust = {S[n]: sp.Float(v) for n, v in conocidas.items()}
        # Descartar ecuaciones cuyas variables ya estén todas conocidas (se validan al final)
        pendientes = [
            e for e in pendientes
            if any(str(sim) in VARIABLES for sim in e.xreplace(sust).free_symbols)
        ]
        if not pendientes:
            break

        eqs_sust = [e.xreplace(sust) for e in pendientes]
        avance = False

        # Paso 1: ecuaciones directas de 1 incógnita (k = 1)
        for i, e_s in enumerate(eqs_sust):
            incognitas = sorted(
                {sim for sim in e_s.free_symbols if str(sim) in VARIABLES},
                key=str,
            )
            if len(incognitas) == 1:
                nuevos = _resolver_bloque([e_s], incognitas, semilla)
                conocidas.update(nuevos)
                pendientes.pop(i)
                avance = True
                break

        if avance:
            continue

        # Paso 2: podar incógnitas hoja (grado 1) para aislar ciclos acoplados
        candidatos = _podar_hojas(eqs_sust)
        if not candidatos:
            candidatos = list(range(len(pendientes)))

        # Buscar el subsistema cerrado más pequeño dentro de los candidatos
        for k in range(2, len(candidatos) + 1):
            # Si k es grande y el conjunto completo de candidatos ya es cuadrado, probarlo directo
            if k > 3 and k < len(candidatos):
                inc_cand = sorted(
                    {
                        sim for idx in candidatos for sim in eqs_sust[idx].free_symbols
                        if str(sim) in VARIABLES
                    },
                    key=str,
                )
                if len(inc_cand) == len(candidatos):
                    k = len(candidatos)

            for indices in combinations(candidatos, k):
                sub_eqs_sust = [eqs_sust[i] for i in indices]
                incognitas = sorted(
                    {
                        sim for e in sub_eqs_sust for sim in e.free_symbols
                        if str(sim) in VARIABLES
                    },
                    key=str,
                )
                if len(incognitas) == k:
                    nuevos = _resolver_bloque(sub_eqs_sust, incognitas, semilla)
                    conocidas.update(nuevos)
                    for i in sorted(indices, reverse=True):
                        pendientes.pop(i)
                    avance = True
                    break
            if avance:
                break

        if not avance:
            raise ValueError(
                "Esa combinación de variables está sobre/sub-determinada y no permite despejar el sistema."
            )

    if len(conocidas) != len(VARIABLES):
        raise ValueError("Quedaron variables sin determinar.")

    # Verificación de consistencia global y condición prolada (cf > R, cr > R)
    if conocidas["cf"] <= conocidas["R"] or conocidas["cr"] <= conocidas["R"]:
        raise ValueError("El modelo prolado requiere que cf > R y cr > R.")

    sust_final = {S[n]: sp.Float(v) for n, v in conocidas.items()}
    for nombre_eq, eq in ECUACIONES.items():
        lhs_v = float(sp.re(eq.lhs.xreplace(sust_final).evalf()))
        rhs_v = float(sp.re(eq.rhs.xreplace(sust_final).evalf()))
        escala = max(abs(lhs_v), abs(rhs_v), 1.0)
        if abs(lhs_v - rhs_v) / escala > 1e-4:
            raise ValueError(f"Inconsistencia en '{nombre_eq}': la combinación no es válida.")

    return conocidas
