"""
Modelo del sistema basado en CAS (SymPy).

Para ampliar el programa solo hay que:
  1. Agregar la variable en VARIABLES (nombre, descripción, unidad, valor inicial).
  2. Registrar su formato ingenieril en UNIDAD_ING y nombre completo de unidad en UNIDAD_NOMBRE.
  3. Agregar la ecuación en la categoría correspondiente de CATEGORIAS (como sp.Eq).
  4. Si la variable es un dato de entrada, incluirla en FIJAS_INI
     (regla: nº de variables calculadas == nº de ecuaciones independientes).
"""
from collections.abc import Callable
import math
import sympy as sp

import evaluador

# =============================================================
# VARIABLES: nombre -> (descripción, unidad, valor inicial o None)
# Calibradas para La Paz - Zona Sur a 100 m (~3.350 m s.n.m.)
# Diseño base: 3 viajes (nv=3, d1=280 m), Mylar 6 um (3/2 capas 14 mm), T2=85°C, v=5.5 m/s, lam=2.3
# =============================================================
VARIABLES = {
    # Caso 1: gas a temperatura ambiente (exterior)
    "P1":     ("Presión caso 1 (ambiente)",              "Pa",          67120.0),
    "T1":     ("Temperatura caso 1 (ambiente)",          "°C",          15.0),
    "R1":     ("Constante R caso 1",                     "J/(kg·K)",    287.058),
    "rho1":   ("Densidad caso 1 (ambiente)",             "kg/m³",       None),
    # Caso 2: mismo gas a mayor temperatura (aire caliente interior)
    "P2":     ("Presión caso 2 (aire caliente)",         "Pa",          67120.0),
    "T2":     ("Temperatura caso 2 (aire caliente)",     "°C",          85.0),
    "R2":     ("Constante R caso 2",                     "J/(kg·K)",    287.058),
    "rho2":   ("Densidad caso 2 (aire caliente)",        "kg/m³",       None),
    "drho":   ("Diferencia de densidades",               "kg/m³",       None),
    # Geometría del casco (dos semielipsoides prolados, cf > R y cr > R)
    "R":      ("Radio máximo transversal",               "m",           None),
    "D":      ("Diámetro máximo del dirigible (2R)",     "m",           None),
    "lam":    ("Relación de esbeltez (L/D)",             "adim",        2.3),
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
    # Convección, radiación Mylar, aislamiento celular asimétrico y mamparos internos
    "e":      ("Espesor por capa celular aislante",      "m",           0.014),
    "W":      ("Ancho de celda cuadrada",                "m",           0.20),
    "ncapS":  ("Capas celulares en mitad superior",      "adim",        3.0),
    "ncapI":  ("Capas celulares en mitad inferior",      "adim",        2.0),
    "ncap":   ("Número promedio de capas celulares",     "adim",        None),
    "ep":     ("Espesor de película Mylar aluminizado",  "m",           6.0e-6),
    "ke":     ("Conductividad térmica película Mylar",   "W/(m·K)",     0.15),
    "eps":    ("Emisividad infrarroja de película Mylar","adim",        0.04),
    "fcal":   ("Factor de agitación convectiva calefactor", "adim",     1.15),
    "fmamp":  ("Factor convectivo por mamparos y estratificación", "adim", 0.78),
    "nmamp":  ("Número de mamparos/deflectores internos","adim",        2.0),
    "Smamp":  ("Área de película en mamparos internos",  "m²",          None),
    "mmamp":  ("Masa de mamparos/deflectores internos",  "kg",          None),
    "beta":   ("Coef. expansión térmica del aire",       "K⁻¹",         0.00302),
    "nu":     ("Viscosidad cinemática del aire",         "m²/s",        2.65e-5),
    "alpha":  ("Difusividad térmica del aire",           "m²/s",        3.80e-5),
    "Pr":     ("Número de Prandtl del aire",             "adim",        None),
    "Nue":    ("Número de Nusselt externo del casco",    "adim",        None),
    "he":     ("Coef. convectivo externo del casco",     "W/(m²·K)",    None),
    "hrade":  ("Coef. radiativo externo del casco Mylar","W/(m²·K)",    None),
    "hetot":  ("Coef. externo total (convección + radiación)", "W/(m²·K)", None),
    "dTi0":   ("Caída térmica interna sin aislante",     "K",           None),
    "RaD0":   ("Rayleigh interno del casco sin aislante","adim",        None),
    "Nui0":   ("Nusselt interno del casco sin aislante", "adim",        None),
    "hi0":    ("Coef. convectivo interno sin aislante",  "W/(m²·K)",    None),
    "U0":     ("Coef. global sin capa celular",          "W/(m²·K)",    None),
    "dTi":    ("Caída térmica interna con aislante",     "K",           None),
    "RaD":    ("Rayleigh interno del casco con aislante","adim",        None),
    "Nui":    ("Nusselt interno del casco con aislante", "adim",        None),
    "hi":     ("Coef. convectivo interno con aislante",  "W/(m²·K)",    None),
    "Tm":     ("Temperatura media absoluta de pared",    "K",           None),
    "epsef":  ("Emisividad efectiva entre láminas Mylar","adim",        None),
    "hrad":   ("Coef. radiativo interno entre capas Mylar", "W/(m²·K)", None),
    "dTcel":  ("Caída térmica por celda superior",       "K",           None),
    "Rae":    ("Número de Rayleigh en la celda",         "adim",        None),
    "Rac":    ("Rayleigh crítico de convección",         "adim",        1708.0),
    "Nuc":    ("Número de Nusselt en la celda",          "adim",        None),
    "ka":     ("Conductividad térmica del aire",         "W/(m·K)",     0.0285),
    "Usup":   ("Coef. global mitad superior (ncapS capas)", "W/(m²·K)", None),
    "Uinf":   ("Coef. global mitad inferior (ncapI capas, Nu=1)", "W/(m²·K)", None),
    "U":      ("Coef. global promedio con capa celular", "W/(m²·K)",    None),
    "Qp0":    ("Potencia perdida sin capa celular",      "W",           None),
    "Qp":     ("Potencia perdida con capa celular",      "W",           None),
    "dQp":    ("Potencia ahorrada por capa celular",     "W",           None),
    "fais":   ("Fracción de ahorro térmico celular",     "adim",        None),
    "Sc":     ("Área de película de la cuadrícula",      "m²",          None),
    "sigma":  ("Gramaje de película Mylar aluminizado",  "kg/m²",       0.0084),
    "mc":     ("Masa total de la cuadrícula celular",    "kg",          None),
    # Pérdida de calor y enfriamiento (con aislante celular incorporado)
    "vT":     ("Velocidad de enfriamiento (dT/dt)",      "K/s",         None),
    "dTc":    ("Caída admisible de temperatura",         "K",           20.0),
    "Qc":     ("Energía perdida en caída dTc",           "J",           None),
    "tc":     ("Tiempo de enfriamiento para dTc",        "s",           None),
    # Precalentamiento en tierra y quemador térmico en vuelo (etanol/GLP genérico)
    "npre":   ("Eficiencia de precalentamiento en tierra", "adim",      0.65),
    "Epre":   ("Energía total de precalentamiento en tierra", "J",      None),
    "cpre":   ("Costo unitario de energía en tierra",    "Bs/MJ",       0.24),
    "Cpre":   ("Costo de precalentamiento en tierra",    "Bs",          None),
    "PC":     ("Poder calorífico del combustible térmico", "J/kg",      2.5e7),
    "ncal":   ("Eficiencia térmica calefactor indirecto","adim",        0.75),
    "mgc":    ("Masa de combustible para recuperar caída dTc", "kg",    None),
    "tm":     ("Tiempo de misión (vuelo/mantenimiento)", "s",           None),
    "Em0":    ("Energía perdida sin aislante en misión", "J",           None),
    "Em":     ("Energía térmica perdida en misión",      "J",           None),
    "Eah":    ("Energía ahorrada gracias al aislante",   "J",           None),
    "Eprop":  ("Energía suministrada por combustible en misión", "J",   None),
    "mgm":    ("Masa de combustible consumida en misión","kg",          None),
    # Resistencia aerodinámica y desplazamiento multi-viaje
    "v":      ("Velocidad relativa al aire",             "m/s",         5.5),
    "vv":     ("Velocidad del viento en contra",         "m/s",         2.5),
    "vg":     ("Velocidad neta respecto al suelo (v-vv)","m/s",         None),
    "d1":     ("Distancia de un viaje base",             "m",           280.0),
    "nv":     ("Número de viajes consecutivos en misión","adim",        3.0),
    "dm":     ("Distancia total de misión (nv·d1)",      "m",           None),
    "mu":     ("Viscosidad dinámica del aire",           "Pa·s",        1.75e-5),
    "ReL":    ("Número de Reynolds longitudinal",        "adim",        None),
    "Cf":     ("Coef. de fricción superficial",          "adim",        None),
    "CDVc":   ("Coef. volumétrico del casco limpio",     "adim",        None),
    "kp":     ("Factor de penalización parásita",        "adim",        1.45),
    "CDV":    ("Coef. de resistencia volumétrico",       "adim",        None),
    "FD":     ("Fuerza de resistencia aerodinámica",     "N",           None),
    "ED":     ("Energía perdida por resistencia aerodinámica", "J",     None),
    # Masas y balance de peso del dirigible híbrido
    "N":      ("Número de motores activos",              "adim",        4.0),
    "mmot":   ("Masa de cada motor A2212 (1000KV)",      "kg",          0.047),
    "mp":     ("Masa de combustible térmico a bordo",    "kg",          0.220),
    "mad":    ("Masa adicional de componentes",          "kg",          1.15),
    "mart":   ("Masa del artefacto con componentes",     "kg",          None),
    "mcarga": ("Carga útil",                             "kg",          1.0),
    "mtot":   ("Masa total del dirigible",               "kg",          None),
    "mflot":  ("Masa compensada por aire caliente",      "kg",          3.20),
    "mres":   ("Masa residual a sostener por motores",   "kg",          None),
    "fap":    ("Factor de masa aparente virtual",        "adim",        1.15),
    "map":    ("Masa aparente traslacional",             "kg",          None),
    # Propulsión vectorial y motores Brushless A2212 (1000KV)
    "vz":     ("Velocidad de ascenso objetivo",          "m/s",         0.8),
    "vx":     ("Velocidad de traslación objetivo",       "m/s",         2.5),
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
    "dTtot":  ("Margen de empuje de los 4 motores",      "N",           None),
    "FLmax":  ("Sustentación vertical máx. de motores",  "N",           None),
    "Fexc":   ("Excedente de sustentación total",        "N",           None),
    "dp":     ("Diámetro de cada hélice (10 pulg)",      "m",           0.254),
    "Ap":     ("Área de disco barrida por hélice",       "m²",          None),
    "nprop0": ("Eficiencia máx. de hélice (estática)",   "adim",        0.60),
    "vpitch": ("Velocidad de paso nulo de hélice",       "m/s",         14.0),
    "nprop":  ("Eficiencia aerodinámica de hélice",      "adim",        None),
    "nm":     ("Eficiencia electromecánica A2212",       "adim",        0.78),
    "nESC":   ("Eficiencia de variadores ESC",           "adim",        0.95),
    "ntot":   ("Eficiencia propulsiva global",           "adim",        None),
    "km":     ("Factor de margen de control/maniobra",   "adim",        1.20),
    "Pelec":  ("Potencia eléctrica de los 4 motores",    "W",           None),
    "Pmax1":  ("Potencia eléctrica máx. continua/motor", "W",           160.0),
    "Pmax":   ("Potencia eléctrica máx. de 4 motores",   "W",           None),
    "dPelec": ("Margen de potencia eléctrica motores",   "W",           None),
    "Pad":    ("Potencia adicional (placa, cámara, antena, ventilador)", "W", 45.0),
    "Ptot":   ("Potencia eléctrica total a bordo (motores + electr.)", "W", None),
    # Batería requerida, costes energéticos y económicos de misión
    "Ereq":   ("Energía eléctrica requerida en misión",  "Wh",          None),
    "Eelec":  ("Energía eléctrica total usada en misión","J",           None),
    "celec":  ("Coste energético eléctrico por metro",   "Wh/m",        None),
    "Etot":   ("Energía total en misión (eléc. + comb.)","J",           None),
    "ctot":   ("Coste energético total por metro",       "J/m",         None),
    "ccomb":  ("Costo unitario de combustible térmico",  "Bs/kg",       18.0),
    "Ccomb":  ("Costo de combustible térmico en vuelo",  "Bs",          None),
    "celecU": ("Costo unitario de electricidad (batería)","Bs/kWh",     0.85),
    "Celec":  ("Costo de recarga eléctrica de batería",  "Bs",          None),
    "Cop":    ("Costo operativo total de misión (tierra + vuelo)", "Bs", None),
    "ebat":   ("Energía específica de batería",          "Wh/kg",       150.0),
    "DoD":    ("Profundidad de descarga máxima (DoD)",   "adim",        0.80),
    "ntemp":  ("Factor de derateo térmico de batería",   "adim",        0.92),
    "Cmax":   ("Tasa máx. de descarga continua batería", "h⁻¹",         10.0),
    "mbe":    ("Masa de batería por energía requerida",  "kg",          None),
    "mbp":    ("Masa de batería por potencia pico",      "kg",          None),
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
    "h⁻¹":      "inverso de hora (tasa C)",
    "m²/s":     "metros cuadrados por segundo",
    "kg/m²":    "kilogramos por metro cuadrado",
    "J/kg":     "Joules por kilogramo",
    "m/s":      "metros por segundo",
    "Pa·s":     "Pascales segundo",
    "°":        "grados sexagesimales",
    "Wh":       "Watts hora",
    "Wh/kg":    "Watts hora por kilogramo",
    "Wh/m":     "Watts hora por metro",
    "J/m":      "Joules por metro",
    "Bs":       "Bolivianos",
    "Bs/MJ":    "Bolivianos por MegaJoule",
    "Bs/kg":    "Bolivianos por kilogramo",
    "Bs/kWh":   "Bolivianos por kilovatio hora",
}

# Variables de entrada al iniciar (167 variables - 103 ecuaciones = 64 fijas)
# Se fijan d1 y nv (multi-viaje), capas asimétricas Mylar (ncapS, ncapI, eps), mamparos (fmamp, nmamp),
# precalentamiento y costos (npre, cpre, ccomb, celecU), vv, Pad y mflot; dm, U0, U, Cop, mbat y mres se despejan automáticamente.
FIJAS_INI = [
    "P1", "T1", "R1", "P2", "T2", "R2",
    "lam", "xf",
    "cp", "g",
    "e", "W", "ncapS", "ncapI", "ep", "ke", "eps", "fcal", "fmamp", "nmamp",
    "beta", "nu", "alpha", "Rac", "ka", "sigma",
    "dTc",
    "npre", "cpre", "PC", "ncal",
    "v", "vv", "d1", "nv", "mu", "kp",
    "N", "mmot", "mp", "mad", "mcarga", "mflot", "fap",
    "vz", "vx", "ta", "thmax", "Tmax1", "dp", "nprop0", "vpitch", "nm", "nESC", "km", "Pmax1", "Pad",
    "ccomb", "celecU",
    "ebat", "DoD", "ntemp", "Cmax", "mbmax",
]

# Variables que físicamente deben ser estrictamente positivas
POSITIVAS = {
    "P1", "R1", "rho1", "P2", "R2", "rho2",
    "R", "D", "lam", "xf", "cf", "cr", "L", "V", "ef", "er", "Sf", "Sr", "S",
    "m", "cp", "g",
    "e", "W", "ncapS", "ncapI", "ncap", "ep", "ke", "eps", "epsef", "fcal", "fmamp",
    "beta", "nu", "alpha",
    "Pr", "Nue", "he", "hrade", "hetot",
    "dTi0", "RaD0", "Nui0", "hi0", "U0",
    "dTi", "RaD", "Nui", "hi", "Tm", "hrad",
    "dTcel", "Rae", "Rac", "Nuc", "ka", "Usup", "Uinf", "U",
    "Qp0", "Qp", "dQp", "fais", "Sc", "sigma", "mc",
    "vT", "dTc", "Qc", "tc",
    "npre", "Epre", "PC", "ncal", "mgc", "tm", "Em0", "Em", "Eah", "Eprop", "mgm",
    "v", "vg", "d1", "nv", "dm", "mu", "ReL", "Cf", "CDVc", "kp", "CDV", "FD", "ED",
    "N", "mmot", "mp", "mad", "mart", "mcarga", "mtot", "mflot", "mres", "fap", "map",
    "vz", "vx", "ta", "az", "ax", "FL", "FX", "Ttot", "theta", "thmax",
    "Tmax1", "FLmax", "dp", "Ap", "nprop0", "vpitch", "nprop", "nm", "nESC", "ntot", "km", "Pelec", "Pmax1", "Pmax", "Ptot",
    "Ereq", "Eelec", "celec", "Etot", "ctot", "ebat", "DoD", "ntemp", "Cmax", "mbe", "mbp", "mbat", "mbmax",
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
    "R":      ("m", "", 1),         "D":      ("m", "", 1),         "cf":     ("m", "", 1),         "cr":    ("m", "", 1),
    "L":      ("m", "", 1),         "V":      ("m³", "", 1),
    "ef":     (None, "adim", 1),    "er":     (None, "adim", 1),
    "Sf":     ("m²", "", 1),        "Sr":     ("m²", "", 1),        "S":     ("m²", "", 1),
    "m":      ("g", "", 1000),
    "cp":     ("J", "/(kg·K)", 1),
    "dT":     ("K", "", 1),
    "Q":      ("J", "", 1),
    "g":      (None, "m/s²", 1),
    "F":      ("N", "", 1),
    # Convección, radiación Mylar, capas asimétricas y mamparos
    "e":      ("m", "", 1),
    "W":      ("m", "", 1),
    "ncapS":  (None, "adim", 1),
    "ncapI":  (None, "adim", 1),
    "ncap":   (None, "adim", 1),
    "ep":     ("m", "", 1),
    "ke":     ("W", "/(m·K)", 1),
    "eps":    (None, "adim", 1),
    "fcal":   (None, "adim", 1),
    "fmamp":  (None, "adim", 1),
    "nmamp":  (None, "adim", 1),
    "Smamp":  ("m²", "", 1),
    "mmamp":  ("g", "", 1000),
    "beta":   ("K⁻¹", "", 1),
    "nu":     ("m²/s", "", 1),
    "alpha":  ("m²/s", "", 1),
    "Pr":     (None, "adim", 1),
    "Nue":    ("adim", "", 1),
    "he":     ("W", "/(m²·K)", 1),
    "hrade":  ("W", "/(m²·K)", 1),
    "hetot":  ("W", "/(m²·K)", 1),
    "dTi0":   ("K", "", 1),
    "RaD0":   ("adim", "", 1),
    "Nui0":   ("adim", "", 1),
    "hi0":    ("W", "/(m²·K)", 1),
    "U0":     ("W", "/(m²·K)", 1),
    "dTi":    ("K", "", 1),
    "RaD":    ("adim", "", 1),
    "Nui":    ("adim", "", 1),
    "hi":     ("W", "/(m²·K)", 1),
    "Tm":     ("K", "", 1),
    "epsef":  (None, "adim", 1),
    "hrad":   ("W", "/(m²·K)", 1),
    "dTcel":  ("K", "", 1),
    "Rae":    ("adim", "", 1),
    "Rac":    ("adim", "", 1),
    "Nuc":    (None, "adim", 1),
    "ka":     ("W", "/(m·K)", 1),
    "Usup":   ("W", "/(m²·K)", 1),
    "Uinf":   ("W", "/(m²·K)", 1),
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
    # Precalentamiento en tierra y quemador térmico
    "npre":   (None, "adim", 1),
    "Epre":   ("J", "", 1),
    "cpre":   (None, "Bs/MJ", 1),
    "Cpre":   (None, "Bs", 1),
    "PC":     ("J", "/kg", 1),
    "ncal":   (None, "adim", 1),
    "mgc":    ("g", "", 1000),
    "tm":     ("s", "", 1),
    "Em0":    ("J", "", 1),
    "Em":     ("J", "", 1),
    "Eah":    ("J", "", 1),
    "Eprop":  ("J", "", 1),
    "mgm":    ("g", "", 1000),
    # Resistencia aerodinámica y multi-viaje
    "v":      ("m", "/s", 1),
    "vv":     ("m", "/s", 1),
    "vg":     ("m", "/s", 1),
    "d1":     ("m", "", 1),
    "nv":     (None, "adim", 1),
    "dm":     ("m", "", 1),
    "mu":     ("Pa·s", "", 1),
    "ReL":    ("adim", "", 1),
    "Cf":     ("adim", "", 1),
    "CDVc":   ("adim", "", 1),
    "kp":     (None, "adim", 1),
    "CDV":    ("adim", "", 1),
    "FD":     ("N", "", 1),
    "ED":     ("J", "", 1),
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
    "dTtot":  ("N", "", 1),
    "FLmax":  ("N", "", 1),
    "Fexc":   ("N", "", 1),
    "dp":     ("m", "", 1),
    "Ap":     ("m²", "", 1),
    "nprop0": (None, "adim", 1),
    "vpitch": ("m", "/s", 1),
    "nprop":  (None, "adim", 1),
    "nm":     (None, "adim", 1),
    "nESC":   (None, "adim", 1),
    "ntot":   (None, "adim", 1),
    "km":     (None, "adim", 1),
    "Pelec":  ("W", "", 1),
    "Pmax1":  ("W", "", 1),
    "Pmax":   ("W", "", 1),
    "dPelec": ("W", "", 1),
    "Pad":    ("W", "", 1),
    "Ptot":   ("W", "", 1),
    # Batería, distancia, costes energéticos y económicos
    "Ereq":   ("Wh", "", 1),
    "Eelec":  ("J", "", 1),
    "celec":  ("Wh", "/m", 1),
    "Etot":   ("J", "", 1),
    "ctot":   ("J", "/m", 1),
    "ccomb":  (None, "Bs/kg", 1),
    "Ccomb":  (None, "Bs", 1),
    "celecU": (None, "Bs/kWh", 1),
    "Celec":  (None, "Bs", 1),
    "Cop":    (None, "Bs", 1),
    "ebat":   ("Wh", "/kg", 1),
    "DoD":    (None, "adim", 1),
    "ntemp":  (None, "adim", 1),
    "Cmax":   (None, "h⁻¹", 1),
    "mbe":    ("g", "", 1000),
    "mbp":    ("g", "", 1000),
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
SIGMA_SB = sp.Float("5.670374419e-8")  # Constante de Stefan-Boltzmann [W/(m²·K⁴)]

# =============================================================
# Definición única de las 103 ecuaciones del modelo (fuente de verdad del solver)
# =============================================================
ECUACIONES_DEF: dict[str, sp.Eq] = {
    # Gases ideales, aire caliente y flotabilidad
    "Gas ideal (caso 1 - ambiente)": sp.Eq(S["rho1"], S["P1"] / (S["R1"] * (S["T1"] + K))),
    "Gas ideal (caso 2 - caliente)": sp.Eq(S["rho2"], S["P2"] / (S["R2"] * (S["T2"] + K))),
    "Diferencia de densidades":      sp.Eq(S["drho"], S["rho1"] - S["rho2"]),
    "Gradiente térmico":             sp.Eq(S["dT"], S["T2"] - S["T1"]),
    "Masa de aire caliente":         sp.Eq(S["m"], S["rho2"] * S["V"]),
    "Calor sensible":                sp.Eq(S["Q"], S["m"] * S["cp"] * S["dT"]),
    "Fuerza de sustentación aerostática": sp.Eq(S["F"], S["drho"] * S["g"] * S["V"]),
    # Geometría del casco (dos semielipsoides) y película/mamparos
    "Diámetro máximo transversal (2R)": sp.Eq(S["D"], 2 * S["R"]),
    "Relación de esbeltez (L/D)":       sp.Eq(S["lam"], S["L"] / (2 * S["R"])),
    "Fracción de nariz (cf/L)":         sp.Eq(S["xf"], S["cf"] / S["L"]),
    "Longitud total del casco":         sp.Eq(S["L"], S["cf"] + S["cr"]),
    "Volumen total del casco":          sp.Eq(S["V"], sp.Rational(2, 3) * sp.pi * S["R"] ** 2 * S["L"]),
    "Excentricidad frontal (cf > R)":   sp.Eq(S["ef"], sp.sqrt(1 - S["R"] ** 2 / S["cf"] ** 2)),
    "Excentricidad trasera (cr > R)":   sp.Eq(S["er"], sp.sqrt(1 - S["R"] ** 2 / S["cr"] ** 2)),
    "Área superficial frontal":         sp.Eq(S["Sf"], sp.pi * S["R"] * S["cf"] * sp.asin(S["ef"]) / S["ef"]),
    "Área superficial trasera":         sp.Eq(S["Sr"], sp.pi * S["R"] * S["cr"] * sp.asin(S["er"]) / S["er"]),
    "Área superficial total":           sp.Eq(S["S"], S["Sf"] + S["Sr"]),
    "Número promedio de capas celulares (ncap)": sp.Eq(S["ncap"], (S["ncapS"] + S["ncapI"]) / 2),
    "Área total de película celular": sp.Eq(
        S["Sc"], S["ncap"] * S["S"] * (1 + 2 * S["e"] / S["W"])
    ),
    "Masa de la cuadrícula celular": sp.Eq(
        S["mc"], S["Sc"] * S["sigma"]
    ),
    "Área de película de mamparos internos (Smamp)": sp.Eq(
        S["Smamp"], S["nmamp"] * sp.Rational(2, 3) * sp.pi * S["R"] ** 2
    ),
    "Masa de mamparos/deflectores internos (mmamp)": sp.Eq(
        S["mmamp"], S["Smamp"] * S["sigma"]
    ),
    # Convección externa, radiación Mylar exterior y modelo térmico base (U0)
    # NOTA: U0 es estrictamente independiente de e, W, ncapS, ncapI, fmamp, nmamp, Nuc y hrad.
    "Número de Prandtl del aire (Pr)": sp.Eq(
        S["Pr"], S["nu"] / S["alpha"]
    ),
    "Número de Nusselt externo por viento (Nue)": sp.Eq(
        S["Nue"], sp.Float("0.037") * S["ReL"] ** sp.Rational(4, 5) * S["Pr"] ** sp.Rational(1, 3)
    ),
    "Coeficiente convectivo externo del casco (he)": sp.Eq(
        S["he"], (S["Nue"] * S["ka"]) / S["L"]
    ),
    "Coeficiente radiativo externo del casco (hrade)": sp.Eq(
        S["hrade"], 4 * S["eps"] * SIGMA_SB * (S["T1"] + K) ** 3
    ),
    "Coeficiente externo total del casco (hetot)": sp.Eq(
        S["hetot"], S["he"] + S["hrade"]
    ),
    "Caída térmica interna sin capa celular (dTi0)": sp.Eq(
        S["dTi0"], (S["U0"] / S["hi0"]) * S["dT"]
    ),
    "Número de Rayleigh interno sin capa celular (RaD0)": sp.Eq(
        S["RaD0"], (S["g"] * S["beta"] * S["dTi0"] * S["D"] ** 3) / (S["nu"] * S["alpha"])
    ),
    "Número de Nusselt interno sin capa celular (Nui0)": sp.Eq(
        S["Nui0"], sp.Float("0.13") * S["RaD0"] ** sp.Rational(1, 3)
    ),
    "Coeficiente convectivo interno sin capa celular (hi0)": sp.Eq(
        S["hi0"], S["fcal"] * (S["Nui0"] * S["ka"]) / S["D"]
    ),
    "Coeficiente global sin capa celular (U0)": sp.Eq(
        S["U0"], 1 / (1 / S["hi0"] + S["ep"] / S["ke"] + 1 / S["hetot"])
    ),
    # Aislamiento Mylar multicapa asimétrico, radiación interna y mamparos (U)
    "Caída térmica interna con capa celular (dTi)": sp.Eq(
        S["dTi"], (S["U"] / S["hi"]) * S["dT"]
    ),
    "Número de Rayleigh interno con capa celular (RaD)": sp.Eq(
        S["RaD"], (S["g"] * S["beta"] * S["dTi"] * S["D"] ** 3) / (S["nu"] * S["alpha"])
    ),
    "Número de Nusselt interno con capa celular (Nui)": sp.Eq(
        S["Nui"], sp.Float("0.13") * S["RaD"] ** sp.Rational(1, 3)
    ),
    "Coeficiente convectivo interno con capa celular (hi)": sp.Eq(
        S["hi"], S["fcal"] * S["fmamp"] * (S["Nui"] * S["ka"]) / S["D"]
    ),
    "Temperatura media absoluta de pared (Tm)": sp.Eq(
        S["Tm"], (S["T1"] + S["T2"]) / 2 + K
    ),
    "Emisividad efectiva entre láminas (epsef)": sp.Eq(
        S["epsef"], S["eps"] / (2 - S["eps"])
    ),
    "Coeficiente radiativo interno de cavidad (hrad)": sp.Eq(
        S["hrad"], 4 * S["epsef"] * SIGMA_SB * S["Tm"] ** 3
    ),
    "Caída térmica en la celda aislante (dTcel)": sp.Eq(
        S["dTcel"], (S["Usup"] / ((S["ka"] * S["Nuc"]) / S["e"] + S["hrad"])) * S["dT"]
    ),
    "Número de Rayleigh en cavidad celular (Rae)": sp.Eq(
        S["Rae"], (S["g"] * S["beta"] * S["dTcel"] * S["e"] ** 3) / (S["nu"] * S["alpha"])
    ),
    "Número de Nusselt efectivo en celda (Nuc)": sp.Eq(
        S["Nuc"],
        1
        + sp.Float("1.44") * sp.Max(0, 1 - S["Rac"] / S["Rae"])
        + sp.Max(0, (S["Rae"] / sp.Integer(5830)) ** sp.Rational(1, 3) - 1),
    ),
    "Coeficiente global mitad superior (Usup)": sp.Eq(
        S["Usup"],
        1 / (
            1 / S["hi"]
            + ((S["ncapS"] + 1) * S["ep"]) / S["ke"]
            + S["ncapS"] / ((S["ka"] * S["Nuc"]) / S["e"] + S["hrad"])
            + 1 / S["hetot"]
        ),
    ),
    "Coeficiente global mitad inferior (Uinf)": sp.Eq(
        S["Uinf"],
        1 / (
            1 / S["hi"]
            + ((S["ncapI"] + 1) * S["ep"]) / S["ke"]
            + S["ncapI"] / (S["ka"] / S["e"] + S["hrad"])
            + 1 / S["hetot"]
        ),
    ),
    "Coeficiente global con capa celular (U)": sp.Eq(
        S["U"], (S["Usup"] + S["Uinf"]) / 2
    ),
    # Pérdida de calor, ahorro y enfriamiento
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
    "Velocidad de enfriamiento (dT/dt)": sp.Eq(S["vT"], S["Qp"] / (S["m"] * S["cp"])),
    "Energía cedida en caída admisible": sp.Eq(S["Qc"], S["m"] * S["cp"] * S["dTc"]),
    "Tiempo de enfriamiento sin aporte": sp.Eq(S["tc"], S["Qc"] / S["Qp"]),
    # Precalentamiento en tierra y quemador térmico en vuelo
    "Energía de precalentamiento en tierra (Epre)": sp.Eq(S["Epre"], S["Q"] / S["npre"]),
    "Costo de precalentamiento en tierra (Cpre)": sp.Eq(
        S["Cpre"], (S["Epre"] / sp.Integer(1000000)) * S["cpre"]
    ),
    "Masa de combustible térmico para recuperar caída dTc":            sp.Eq(S["mgc"], S["Qc"] / (S["ncal"] * S["PC"])),
    "Energía perdida sin aislante en misión":          sp.Eq(S["Em0"], S["Qp0"] * S["tm"]),
    "Energía perdida con aislante en misión":          sp.Eq(S["Em"],  S["Qp"] * S["tm"]),
    "Energía ahorrada gracias al aislante":            sp.Eq(S["Eah"], S["dQp"] * S["tm"]),
    "Energía suministrada por combustible térmico en misión (Eprop)": sp.Eq(S["Eprop"], S["Em"] / S["ncal"]),
    "Masa de combustible térmico para mantener T en misión":           sp.Eq(S["mgm"], S["Eprop"] / S["PC"]),
    # Desplazamiento multi-viaje y resistencia aerodinámica
    "Velocidad neta de avance respecto al suelo (vg)": sp.Eq(
        S["vg"], S["v"] - S["vv"]
    ),
    "Distancia total por viajes (nv·d1)": sp.Eq(
        S["dm"], S["nv"] * S["d1"]
    ),
    "Distancia recorrida en misión (dm)": sp.Eq(
        S["dm"], S["vg"] * S["tm"]
    ),
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
    "Energía perdida por resistencia aerodinámica (ED)": sp.Eq(
        S["ED"], S["FD"] * S["dm"]
    ),
    # Masas y balance de peso (dirigible híbrido)
    "Masa del artefacto con sus componentes (mart)": sp.Eq(
        S["mart"], S["mc"] + S["mmamp"] + S["N"] * S["mmot"] + S["mp"] + S["mad"] + S["mbat"]
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
    # Dinámica vectorial y empuje (motores A2212)
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
    "Margen de empuje disponible de los 4 motores (dTtot)": sp.Eq(
        S["dTtot"], S["N"] * S["Tmax1"] - S["Ttot"]
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
    # Eficiencia y potencia eléctrica propulsiva
    "Área de disco barrida por cada hélice (Ap)": sp.Eq(
        S["Ap"], sp.pi * S["dp"] ** 2 / 4
    ),
    "Eficiencia aerodinámica de hélice según velocidad (nprop)": sp.Eq(
        S["nprop"], S["nprop0"] * (1 - (S["v"] / S["vpitch"]) ** 2)
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
    "Potencia eléctrica máxima continua de 4 motores (Pmax)": sp.Eq(
        S["Pmax"], S["N"] * S["Pmax1"]
    ),
    "Margen de potencia eléctrica de los motores (dPelec)": sp.Eq(
        S["dPelec"], S["Pmax"] - S["Pelec"]
    ),
    "Potencia eléctrica total a bordo (Ptot)": sp.Eq(
        S["Ptot"], S["Pelec"] + S["Pad"]
    ),
    # Energía y costes operativos de misión
    "Energía eléctrica requerida en misión (Ereq)": sp.Eq(
        S["Ereq"], (S["Ptot"] * S["tm"]) / S_POR_H
    ),
    "Energía eléctrica total usada en misión (Eelec)": sp.Eq(
        S["Eelec"], S_POR_H * S["Ereq"]
    ),
    "Coste energético eléctrico por distancia (celec)": sp.Eq(
        S["celec"], S["Ereq"] / S["dm"]
    ),
    "Energía total consumida en misión (Etot)": sp.Eq(
        S["Etot"], S["Eprop"] + S["Eelec"]
    ),
    "Coste energético total por distancia (ctot)": sp.Eq(
        S["ctot"], S["Etot"] / S["dm"]
    ),
    "Costo de combustible térmico en vuelo (Ccomb)": sp.Eq(
        S["Ccomb"], S["mgm"] * S["ccomb"]
    ),
    "Costo de recarga eléctrica de batería (Celec)": sp.Eq(
        S["Celec"], (S["Ereq"] / sp.Integer(1000)) * S["celecU"]
    ),
    "Costo operativo total de misión (Cop)": sp.Eq(
        S["Cop"], S["Cpre"] + S["Ccomb"] + S["Celec"]
    ),
    # Dimensionamiento de batería y límites
    "Masa de batería por energía de misión (mbe)": sp.Eq(
        S["mbe"], S["Ereq"] / (S["ebat"] * S["DoD"] * S["ntemp"])
    ),
    "Masa de batería por potencia pico (mbp)": sp.Eq(
        S["mbp"], S["Ptot"] / (S["ebat"] * S["Cmax"] * S["ntemp"])
    ),
    "Masa de batería requerida (mbat)": sp.Eq(
        S["mbat"], sp.Max(S["mbe"], S["mbp"])
    ),
    "Margen respecto al peso máximo de batería (dmbat)": sp.Eq(
        S["dmbat"], S["mbmax"] - S["mbat"]
    ),
}

# =============================================================
# 13 categorías homogéneas (ecuaciones puente compartidas entre bloques)
# =============================================================
_CATEGORIAS_NOMBRES: dict[str, list[str]] = {
    "Gases ideales, aire caliente y flotabilidad": [
        "Gas ideal (caso 1 - ambiente)",
        "Gas ideal (caso 2 - caliente)",
        "Diferencia de densidades",
        "Gradiente térmico",
        "Masa de aire caliente",
        "Calor sensible",
        "Fuerza de sustentación aerostática",
        "Masa compensada por aire caliente (mflot)",
    ],
    "Dimensiones principales y volumen del casco": [
        "Fuerza de sustentación aerostática",
        "Diámetro máximo transversal (2R)",
        "Relación de esbeltez (L/D)",
        "Fracción de nariz (cf/L)",
        "Longitud total del casco",
        "Volumen total del casco",
        "Área superficial total",
    ],
    "Superficies del casco, capas Mylar y mamparos": [
        "Excentricidad frontal (cf > R)",
        "Excentricidad trasera (cr > R)",
        "Área superficial frontal",
        "Área superficial trasera",
        "Área superficial total",
        "Número promedio de capas celulares (ncap)",
        "Área total de película celular",
        "Masa de la cuadrícula celular",
        "Área de película de mamparos internos (Smamp)",
        "Masa de mamparos/deflectores internos (mmamp)",
    ],
    "Convección externa, radiación y modelo térmico base (U0)": [
        "Número de Prandtl del aire (Pr)",
        "Número de Nusselt externo por viento (Nue)",
        "Coeficiente convectivo externo del casco (he)",
        "Coeficiente radiativo externo del casco (hrade)",
        "Coeficiente externo total del casco (hetot)",
        "Caída térmica interna sin capa celular (dTi0)",
        "Número de Rayleigh interno sin capa celular (RaD0)",
        "Número de Nusselt interno sin capa celular (Nui0)",
        "Coeficiente convectivo interno sin capa celular (hi0)",
        "Coeficiente global sin capa celular (U0)",
    ],
    "Aislamiento Mylar multicapa asimétrico y mamparos (U)": [
        "Coeficiente externo total del casco (hetot)",
        "Caída térmica interna con capa celular (dTi)",
        "Número de Rayleigh interno con capa celular (RaD)",
        "Número de Nusselt interno con capa celular (Nui)",
        "Coeficiente convectivo interno con capa celular (hi)",
        "Temperatura media absoluta de pared (Tm)",
        "Emisividad efectiva entre láminas (epsef)",
        "Coeficiente radiativo interno de cavidad (hrad)",
        "Caída térmica en la celda aislante (dTcel)",
        "Número de Rayleigh en cavidad celular (Rae)",
        "Número de Nusselt efectivo en celda (Nuc)",
        "Coeficiente global mitad superior (Usup)",
        "Coeficiente global mitad inferior (Uinf)",
        "Coeficiente global con capa celular (U)",
    ],
    "Pérdidas de calor, ahorro del aislante y enfriamiento": [
        "Potencia perdida sin capa celular (Qp0)",
        "Potencia perdida con capa celular (Qp)",
        "Potencia ahorrada por capa celular (dQp)",
        "Fracción de ahorro térmico celular (fais)",
        "Velocidad de enfriamiento (dT/dt)",
        "Energía cedida en caída admisible",
        "Tiempo de enfriamiento sin aporte",
    ],
    "Precalentamiento en tierra, energía térmica y quemador": [
        "Distancia recorrida en misión (dm)",
        "Energía de precalentamiento en tierra (Epre)",
        "Costo de precalentamiento en tierra (Cpre)",
        "Masa de combustible térmico para recuperar caída dTc",
        "Energía perdida sin aislante en misión",
        "Energía perdida con aislante en misión",
        "Energía ahorrada gracias al aislante",
        "Energía suministrada por combustible térmico en misión (Eprop)",
        "Masa de combustible térmico para mantener T en misión",
    ],
    "Cinemática multi-viaje, viento y arrastre aerodinámico": [
        "Velocidad neta de avance respecto al suelo (vg)",
        "Distancia total por viajes (nv·d1)",
        "Distancia recorrida en misión (dm)",
        "Número de Reynolds longitudinal (ReL)",
        "Coeficiente de fricción superficial (Cf)",
        "Coeficiente volumétrico del casco (CDVc - Hoerner)",
        "Coeficiente de resistencia volumétrico total (CDV)",
        "Fuerza de resistencia aerodinámica (FD)",
        "Energía perdida por resistencia aerodinámica (ED)",
    ],
    "Masas del dirigible y reparto de sustentación híbrida": [
        "Masa de la cuadrícula celular",
        "Masa de mamparos/deflectores internos (mmamp)",
        "Masa de batería requerida (mbat)",
        "Masa del artefacto con sus componentes (mart)",
        "Masa total del dirigible con carga útil (mtot)",
        "Fuerza de sustentación aerostática",
        "Masa compensada por aire caliente (mflot)",
        "Masa residual a compensar por motores (mres)",
        "Masa aparente traslacional (map)",
    ],
    "Dinámica vectorial, empuje y límites de actitud (A2212)": [
        "Fuerza de resistencia aerodinámica (FD)",
        "Aceleración vertical de ascenso (az)",
        "Aceleración horizontal de traslación (ax)",
        "Componente vertical de sustentación de motores (FL)",
        "Componente horizontal de avance de motores (FX)",
        "Empuje vectorial total de los 4 motores (Ttot)",
        "Margen de empuje disponible de los 4 motores (dTtot)",
        "Ángulo de rotación respecto a la vertical (theta)",
        "Margen respecto al ángulo máximo de rotación (dth)",
    ],
    "Capacidad vertical, eficiencia y potencia eléctrica": [
        "Empuje vectorial total de los 4 motores (Ttot)",
        "Sustentación vertical máxima de los 4 motores (FLmax)",
        "Excedente de sustentación total (Fexc)",
        "Área de disco barrida por cada hélice (Ap)",
        "Eficiencia aerodinámica de hélice según velocidad (nprop)",
        "Eficiencia propulsiva global (ntot)",
        "Potencia eléctrica demandada por los 4 motores (Pelec)",
        "Potencia eléctrica máxima continua de 4 motores (Pmax)",
        "Margen de potencia eléctrica de los motores (dPelec)",
    ],
    "Balance energético global y costos operativos de misión": [
        "Energía suministrada por combustible térmico en misión (Eprop)",
        "Energía perdida por resistencia aerodinámica (ED)",
        "Costo de precalentamiento en tierra (Cpre)",
        "Potencia eléctrica demandada por los 4 motores (Pelec)",
        "Potencia eléctrica total a bordo (Ptot)",
        "Energía eléctrica requerida en misión (Ereq)",
        "Energía eléctrica total usada en misión (Eelec)",
        "Coste energético eléctrico por distancia (celec)",
        "Energía total consumida en misión (Etot)",
        "Coste energético total por distancia (ctot)",
        "Costo de combustible térmico en vuelo (Ccomb)",
        "Costo de recarga eléctrica de batería (Celec)",
        "Costo operativo total de misión (Cop)",
    ],
    "Dimensionamiento y límites de la batería": [
        "Potencia eléctrica total a bordo (Ptot)",
        "Energía eléctrica requerida en misión (Ereq)",
        "Masa de batería por energía de misión (mbe)",
        "Masa de batería por potencia pico (mbp)",
        "Masa de batería requerida (mbat)",
        "Margen respecto al peso máximo de batería (dmbat)",
        "Masa del artefacto con sus componentes (mart)",
    ],
}

CATEGORIAS: dict[str, dict[str, sp.Eq]] = {
    cat_nombre: {nom_eq: ECUACIONES_DEF[nom_eq] for nom_eq in nombres_eqs}
    for cat_nombre, nombres_eqs in _CATEGORIAS_NOMBRES.items()
}

# Lista plana de ecuaciones únicas y estructuras precalculadas para emparejamiento y evaluación rápida
ECUACIONES: dict[str, sp.Eq] = dict(ECUACIONES_DEF)
assert len(ECUACIONES) == len(ECUACIONES_DEF) == 103
assert {nom for eqs in _CATEGORIAS_NOMBRES.values() for nom in eqs} == set(ECUACIONES_DEF), (
    "Las categorías deben cubrir exactamente todas las ecuaciones de ECUACIONES_DEF"
)

_EQ_CATEGORIAS: dict[str, list[tuple[int, str, str]]] = {}
for _cat_idx, (_cat_nom, _eq_dict) in enumerate(CATEGORIAS.items()):
    _cat_cod = f"C{_cat_idx + 1}"
    for _nom_eq in _eq_dict:
        _EQ_CATEGORIAS.setdefault(_nom_eq, []).append((_cat_idx, _cat_cod, _cat_nom))

_ECUACIONES_LIST: list[tuple[str, sp.Eq]] = list(ECUACIONES.items())
_EQ_VARS: list[frozenset[str]] = [
    frozenset(sim.name for sim in eq.free_symbols if sim.name in VARIABLES)
    for _, eq in _ECUACIONES_LIST
]
_FIJAS_INI_SET: frozenset[str] = frozenset(FIJAS_INI)
_DIRECT_EVAL_CACHE: dict[tuple[int, str], tuple[tuple[str, ...], Callable[..., float]]] = {}
_BLT_PLAN_CACHE: dict[frozenset[str], list[dict[str, object]]] = {}
_RESIDUAL_EVAL_CACHE: list[tuple[str, tuple[str, ...], Callable[..., tuple[float, float]]]] | None = None


def valores_iniciales() -> dict[str, float]:
    return {n: v[2] for n, v in VARIABLES.items() if n in FIJAS_INI}


def categorias_de_ecuacion(nombre_eq: str) -> list[tuple[int, str, str]]:
    """Devuelve [(categoria_id, 'Cx', nombre_categoria), ...] a las que pertenece `nombre_eq`."""
    return list(_EQ_CATEGORIAS.get(nombre_eq, []))


def ecuaciones_detalladas_de_variable(
    nombre: str,
) -> list[tuple[list[tuple[int, str, str]], str, sp.Eq]]:
    """Devuelve [(categorias, nombre_eq, eq)] sin duplicar ecuaciones cuando pertenecen a varias categorías."""
    sim = S[nombre]
    return [
        (categorias_de_ecuacion(nom_eq), nom_eq, eq)
        for nom_eq, eq in ECUACIONES.items()
        if sim in eq.free_symbols
    ]


def ecuaciones_de_variable(nombre: str) -> list[tuple[str, str, sp.Eq]]:
    """Devuelve [(codigos_categorias, nombre_eq, eq)] sin duplicados donde interviene `nombre`."""
    return [
        (", ".join(cod for _, cod, _ in cats), nom_eq, eq)
        for cats, nom_eq, eq in ecuaciones_detalladas_de_variable(nombre)
    ]


def _emparejar_bipartito(incognitas: set[str]) -> dict[str, int]:
    """Calcula un emparejamiento máximo bipartito (`nombre_incognita -> idx_ecuacion`)."""
    eq_vars = [
        [v for v in vars_eq if v in incognitas]
        for vars_eq in _EQ_VARS
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

    for u in range(len(eq_vars)):
        dfs(u, set())
    return match_var


def _tamano_emparejamiento(incognitas: set[str]) -> int:
    """Calcula el tamaño del emparejamiento máximo bipartito (ecuaciones <-> incógnitas)."""
    return len(_emparejar_bipartito(incognitas))


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


_FRACCIONES_UNITARIAS = frozenset({
    "ef", "er", "fais", "xf", "eps", "epsef", "npre",
    "nprop0", "nprop", "nm", "nESC", "ntot", "DoD", "ntemp"
})
_NO_NEGATIVAS = frozenset({
    "vv", "Pad", "nmamp", "Smamp", "mmamp", "cpre", "ccomb", "celecU", "Cpre", "Ccomb", "Celec", "Cop"
})
_SEMILLAS_DEFECTO = {
    "mbat": 0.25,
    "mbe": 0.20,
    "mbp": 0.25,
    "mres": 0.35,
    "dTi0": 48.0,
    "dTi": 12.0,
    "dTcel": 15.0,
    "Usup": 0.6,
    "Uinf": 0.75,
    "U": 0.65,
    "U0": 3.6,
    "hi0": 4.8,
    "hi": 3.2,
    "Nuc": 1.05,
}


def _es_valida_float(nombre: str, v: float) -> bool:
    """Verifica de forma rápida que un float respete los dominios físicos del modelo."""
    if not math.isfinite(v):
        return False
    if nombre in POSITIVAS and v <= 0.0:
        return False
    if nombre in _NO_NEGATIVAS and v < 0.0:
        return False
    if nombre in _FRACCIONES_UNITARIAS and not (0.0 < v < 1.0):
        return False
    if nombre == "theta" and not (0.0 < v < 90.0):
        return False
    return True


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
    return _es_valida_float(nombre, v)


def _resolver_lineal(A: list[list[float]], b: list[float]) -> list[float] | None:
    """Resuelve Ax = b mediante eliminación gaussiana con pivoteo parcial."""
    n = len(b)
    M = [row[:] + [b[i]] for i, row in enumerate(A)]
    for col in range(n):
        piv_row = max(range(col, n), key=lambda r: abs(M[r][col]))
        if abs(M[piv_row][col]) < 1e-14:
            return None
        if piv_row != col:
            M[col], M[piv_row] = M[piv_row], M[col]
        piv = M[col][col]
        for r in range(col + 1, n):
            factor = M[r][col] / piv
            if factor == 0.0:
                continue
            for c in range(col, n + 1):
                M[r][c] -= factor * M[col][c]
    x = [0.0] * n
    for r in range(n - 1, -1, -1):
        suma = M[r][n] - sum(M[r][c] * x[c] for c in range(r + 1, n))
        x[r] = suma / M[r][r]
    return x


def _newton_rapido_compilado(
    fn_res: Callable[..., list[float]] | None,
    nombres: list[str],
    params_vals: tuple[float, ...],
    valores_semilla: list[float],
) -> list[float] | None:
    """
    Resuelve `fn_res(*x, *params_vals) = 0` en aritmética `float` nativa usando
    Newton-Raphson amortiguado con diferencias finitas. Devuelve None si falla.
    """
    n = len(nombres)
    if fn_res is None or n == 0:
        return None

    def eval_f(vec: list[float]) -> list[float]:
        out = fn_res(*vec, *params_vals)
        res = [float(val) for val in out]
        if any(not math.isfinite(val) for val in res):
            raise ValueError("Residual no finito")
        return res

    def en_dominio(vec: list[float]) -> bool:
        return all(_es_valida_float(nombres[i], vec[i]) for i in range(n))

    x = [float(v) for v in valores_semilla]
    if not en_dominio(x):
        return None
    try:
        f0 = eval_f(x)
    except Exception:
        return None

    norm0 = max(abs(r) for r in f0)
    if norm0 < 1e-10:
        return x

    for _ in range(40):
        J: list[list[float]] = [[0.0] * n for _ in range(n)]
        for j in range(n):
            h = 1e-7 * max(1.0, abs(x[j]))
            x_pert = x[:]
            x_pert[j] = x[j] + h
            signo = 1.0
            try:
                f_pert = eval_f(x_pert)
            except Exception:
                x_pert[j] = x[j] - h
                signo = -1.0
                if not _es_valida_float(nombres[j], x_pert[j]):
                    return None
                try:
                    f_pert = eval_f(x_pert)
                except Exception:
                    return None
            inv_h = signo / h
            for i in range(n):
                J[i][j] = (f_pert[i] - f0[i]) * inv_h

        dx = _resolver_lineal(J, [-r for r in f0])
        if dx is None:
            return None

        alpha = 1.0
        acepto = False
        for _ in range(12):
            x_try = [x[i] + alpha * dx[i] for i in range(n)]
            if en_dominio(x_try):
                try:
                    f_try = eval_f(x_try)
                    norm_try = max(abs(r) for r in f_try)
                    if norm_try < norm0 or norm_try < 1e-10:
                        x = x_try
                        f0 = f_try
                        norm0 = norm_try
                        acepto = True
                        break
                except Exception:
                    pass
            alpha *= 0.5

        if not acepto:
            return None

        step_rel = max(abs(alpha * dx[i]) / max(1.0, abs(x[i])) for i in range(n))
        if norm0 < 1e-10 or (norm0 < 1e-8 and step_rel < 1e-11):
            return x

    return x if norm0 < 1e-7 else None


def _brent_bloque_1d(
    fn_res: Callable[..., list[float]] | None,
    inc_nom: str,
    params_vals: tuple[float, ...],
    semilla_0: float,
) -> float | None:
    """Busca un cambio de signo alrededor de `semilla_0` y aplica `evaluador.brent_1d`."""
    if fn_res is None:
        return None
    s0 = max(1e-4, abs(semilla_0))
    malla = sorted({
        val
        for val in (
            1e-4, 1e-3, 0.01, 0.05,
            0.1 * s0, 0.25 * s0, 0.5 * s0, 0.75 * s0, 0.9 * s0,
            s0, 1.1 * s0, 1.35 * s0, 1.8 * s0, 2.5 * s0, 4.0 * s0, 7.0 * s0,
            12.0, 25.0, 60.0, 120.0, 300.0, 800.0,
        )
        if _es_valida_float(inc_nom, val)
    })
    if not malla:
        return None

    def eval_1d(x: float) -> float:
        out = fn_res(x, *params_vals)
        v = float(out[0])
        if not math.isfinite(v):
            raise ValueError("Residual no finito")
        return v

    prev_x: float | None = None
    prev_f: float | None = None
    for x in malla:
        try:
            fx = eval_1d(x)
        except Exception:
            continue
        if abs(fx) < 1e-11:
            return x
        if prev_x is not None and prev_f is not None and prev_f * fx <= 0.0:
            raiz = evaluador.brent_1d(eval_1d, prev_x, x, tol=1e-11, max_iter=60)
            if raiz is not None and _es_valida_float(inc_nom, raiz):
                return raiz
        prev_x, prev_f = x, fx
    return None


def _resolver_bloque_sympy(
    paso: dict[str, object],
    conocidas: dict[str, float],
    semilla: dict[str, float],
) -> dict[str, float]:
    """Respaldo simbólico (SymPy solve + nsolve acotado) para un bloque no resuelto en float."""
    params: tuple[str, ...] = paso["params"]  # type: ignore[assignment]
    sub_eqs_orig: list[sp.Eq] = paso["sub_eqs_orig"]  # type: ignore[assignment]
    inc_syms: list[sp.Symbol] = paso["inc_syms"]  # type: ignore[assignment]
    inc_reducidas: list[sp.Symbol] = paso["inc_reducidas"]  # type: ignore[assignment]
    exprs_sym: list[sp.Expr] = paso["exprs_sym"]  # type: ignore[assignment]
    orden_elim: list[tuple[sp.Symbol, sp.Expr]] = paso["orden_elim"]  # type: ignore[assignment]

    sust_bloque = {S[v]: sp.Float(conocidas[v]) for v in params}
    sub_eqs_sust = [eq.xreplace(sust_bloque) for eq in sub_eqs_orig]

    if len(sub_eqs_sust) == 1 and len(inc_syms) == 1:
        eq = sub_eqs_sust[0]
        inc = inc_syms[0]
        if eq.lhs == inc and inc not in eq.rhs.free_symbols and _es_valida(inc.name, eq.rhs):
            return {inc.name: float(sp.re(eq.rhs.evalf()))}
        if eq.rhs == inc and inc not in eq.lhs.free_symbols and _es_valida(inc.name, eq.lhs):
            return {inc.name: float(sp.re(eq.lhs.evalf()))}

    if len(sub_eqs_sust) <= 3:
        try:
            soluciones = sp.solve(sub_eqs_sust, inc_syms, dict=True)
            validas = [
                s for s in soluciones
                if len(s) == len(inc_syms)
                and all(_es_valida(str(k), v) for k, v in s.items())
            ]
            if validas:
                return {str(k): float(sp.re(v.evalf())) for k, v in validas[0].items()}
        except Exception:
            pass

    exprs_sust = [ex.xreplace(sust_bloque) for ex in exprs_sym]
    valores_semilla = [
        semilla.get(inc.name, _SEMILLAS_DEFECTO.get(inc.name, 1.0))
        for inc in inc_reducidas
    ]

    try:
        if len(exprs_sust) == 1 and len(inc_reducidas) == 1:
            try:
                sol_unica = sp.nsolve(exprs_sust[0], inc_reducidas[0], valores_semilla[0], maxsteps=25)
            except Exception:
                sol_unica = sp.nsolve(exprs_sust[0], inc_reducidas[0], max(valores_semilla[0], 0.5), maxsteps=25)
            pares = [(inc_reducidas[0], sol_unica)]
        else:
            sol_num = sp.nsolve(exprs_sust, inc_reducidas, valores_semilla, maxsteps=25)
            pares = list(zip(inc_reducidas, sol_num))

        res_sim = {inc: sp.sympify(val).evalf() for inc, val in pares}
        for inc_elim, expr_elim in reversed(orden_elim):
            res_sim[inc_elim] = expr_elim.xreplace({**sust_bloque, **res_sim}).evalf()

        res = {}
        for inc, val in res_sim.items():
            if not _es_valida(inc.name, val):
                raise ValueError(f"Solución fuera de dominio físico para '{inc}'.")
            res[inc.name] = float(sp.re(val))
        return res
    except Exception as exc:
        raise ValueError(
            "Esa combinación no tiene solución única o físicamente válida "
            "(verifica p. ej. que cf > R, cr > R y que el empuje supere el arrastre)."
        ) from exc


def _bloques_tarjan(incognitas: set[str]) -> list[tuple[list[int], list[str]]]:
    """
    Descompone el sistema completo en subsistemas cuadrados irreducibles mínimos
    (forma triangular por bloques / BLT) ya ordenados topológicamente usando
    emparejamiento bipartito + algoritmo de componentes fuertemente conexas de Tarjan.
    """
    n_eq = len(_ECUACIONES_LIST)
    if len(incognitas) != n_eq:
        raise ValueError(
            "Esa combinación de variables está sobre/sub-determinada y no permite despejar el sistema."
        )

    match_var = _emparejar_bipartito(incognitas)
    if len(match_var) != n_eq:
        raise ValueError(
            "Esa combinación de variables está sobre/sub-determinada y no permite despejar el sistema."
        )

    match_eq = {eq_i: var for var, eq_i in match_var.items()}
    # Arista u -> v significa: la ecuación u usa la incógnita asignada a la ecuación v (v debe resolverse antes)
    adj: list[list[int]] = [
        [
            match_var[var]
            for var in (_EQ_VARS[u] & incognitas)
            if match_var[var] != u
        ]
        for u in range(n_eq)
    ]

    indice_actual = 0
    indices_dfs = [-1] * n_eq
    lowlink = [0] * n_eq
    en_pila = [False] * n_eq
    pila: list[int] = []
    bloques: list[tuple[list[int], list[str]]] = []

    def strongconnect(u: int) -> None:
        nonlocal indice_actual
        indices_dfs[u] = indice_actual
        lowlink[u] = indice_actual
        indice_actual += 1
        pila.append(u)
        en_pila[u] = True

        for w in adj[u]:
            if indices_dfs[w] == -1:
                strongconnect(w)
                if lowlink[w] < lowlink[u]:
                    lowlink[u] = lowlink[w]
            elif en_pila[w] and indices_dfs[w] < lowlink[u]:
                lowlink[u] = indices_dfs[w]

        if lowlink[u] == indices_dfs[u]:
            scc_eqs: list[int] = []
            scc_vars: list[str] = []
            while True:
                w = pila.pop()
                en_pila[w] = False
                scc_eqs.append(w)
                scc_vars.append(match_eq[w])
                if w == u:
                    break
            bloques.append((scc_eqs, scc_vars))

    for eq_i in range(n_eq):
        if indices_dfs[eq_i] == -1:
            strongconnect(eq_i)

    return bloques


def _compilar_plan_blt(inc_key: frozenset[str]) -> list[dict[str, object]]:
    """
    Compila y cachea una sola vez el orden BLT y las funciones `float` de cada bloque
    para un conjunto de incógnitas dado (`frozenset`), evitando `xreplace`/`lambdify` en recálculos.
    """
    bloques = _bloques_tarjan(set(inc_key))
    plan: list[dict[str, object]] = []

    for scc_eqs, scc_vars in bloques:
        if len(scc_eqs) == 1:
            eq_idx = scc_eqs[0]
            var_nom = scc_vars[0]
            cache_key = (eq_idx, var_nom)
            entrada = _DIRECT_EVAL_CACHE.get(cache_key)
            if entrada is None:
                _, eq = _ECUACIONES_LIST[eq_idx]
                inc_sym = S[var_nom]
                if eq.lhs == inc_sym and inc_sym not in eq.rhs.free_symbols:
                    expr_aislada = eq.rhs
                elif eq.rhs == inc_sym and inc_sym not in eq.lhs.free_symbols:
                    expr_aislada = eq.lhs
                else:
                    expr_aislada = None

                if expr_aislada is not None:
                    args_ord = tuple(sorted(_EQ_VARS[eq_idx] - {var_nom}))
                    fn_directa = sp.lambdify([S[a] for a in args_ord], expr_aislada, "math")
                    entrada = (args_ord, fn_directa)
                    _DIRECT_EVAL_CACHE[cache_key] = entrada

            if entrada is not None:
                args_ord, fn_directa = entrada
                plan.append({
                    "tipo": "directo",
                    "var": var_nom,
                    "args": args_ord,
                    "fn": fn_directa,
                })
                continue

        scc_var_set = set(scc_vars)
        params_ord = tuple(sorted({
            v for eq_i in scc_eqs for v in _EQ_VARS[eq_i] if v not in scc_var_set
        }))
        sub_eqs_orig = [_ECUACIONES_LIST[eq_i][1] for eq_i in scc_eqs]
        inc_syms = [S[v] for v in sorted(scc_vars)]

        # Reducción simbólica estructural (sin sustituir valores numéricos)
        sust_interna: dict[sp.Symbol, sp.Expr] = {}
        orden_elim: list[tuple[sp.Symbol, sp.Expr]] = []
        eqs_reducidas = list(sub_eqs_orig)
        inc_set = set(inc_syms)
        cambio = True
        while cambio and len(eqs_reducidas) > 1:
            cambio = False
            for idx, eq in enumerate(eqs_reducidas):
                if eq.lhs in inc_set and eq.lhs not in eq.rhs.free_symbols:
                    v_elim, expr_elim = eq.lhs, eq.rhs
                elif eq.rhs in inc_set and eq.rhs not in eq.lhs.free_symbols:
                    v_elim, expr_elim = eq.rhs, eq.lhs
                else:
                    continue
                eqs_reducidas.pop(idx)
                eqs_reducidas = [e.xreplace({v_elim: expr_elim}) for e in eqs_reducidas]
                sust_interna = {k: v.xreplace({v_elim: expr_elim}) for k, v in sust_interna.items()}
                sust_interna[v_elim] = expr_elim
                orden_elim.append((v_elim, expr_elim))
                cambio = True
                break

        inc_reducidas = [inc for inc in inc_syms if inc not in sust_interna]
        exprs_sym = [e.lhs - e.rhs for e in eqs_reducidas]
        all_args = [*inc_reducidas, *(S[p] for p in params_ord)]
        try:
            fn_res = sp.lambdify(all_args, exprs_sym, "math")
        except Exception:
            fn_res = None

        retrosust: list[tuple[str, tuple[str, ...], Callable[..., float]]] = []
        retro_ok = True
        for inc_elim, expr_elim in reversed(orden_elim):
            args_retro = tuple(sorted(
                sim.name for sim in expr_elim.free_symbols if sim.name in VARIABLES
            ))
            try:
                fn_retro = sp.lambdify([S[a] for a in args_retro], expr_elim, "math")
                retrosust.append((inc_elim.name, args_retro, fn_retro))
            except Exception:
                retro_ok = False
                break

        plan.append({
            "tipo": "bloque",
            "params": params_ord,
            "inc_syms": inc_syms,
            "inc_reducidas": inc_reducidas,
            "inc_red_names": [sym.name for sym in inc_reducidas],
            "exprs_sym": exprs_sym,
            "sub_eqs_orig": sub_eqs_orig,
            "orden_elim": orden_elim,
            "fn_res": fn_res if retro_ok else None,
            "retrosust": retrosust,
        })

    return plan


def _ejecutar_retrosustitucion(
    sol_reducida: dict[str, float],
    retrosust: list[tuple[str, tuple[str, ...], Callable[..., float]]],
    conocidas: dict[str, float],
) -> dict[str, float] | None:
    """Completa un bloque reducido ejecutando la retrosustitución compilada en float."""
    res = dict(sol_reducida)
    try:
        for var_nom, args_retro, fn_retro in retrosust:
            val_f = float(fn_retro(*(res[a] if a in res else conocidas[a] for a in args_retro)))
            if not _es_valida_float(var_nom, val_f):
                return None
            res[var_nom] = val_f
        return res
    except Exception:
        return None


def _verificar_consistencia_global(conocidas: dict[str, float]) -> None:
    """Verifica condición geométrica prolada (cf > R, cr > R) y residuo de las 103 ecuaciones."""
    global _RESIDUAL_EVAL_CACHE

    if conocidas["cf"] <= conocidas["R"] or conocidas["cr"] <= conocidas["R"]:
        raise ValueError("El modelo prolado requiere que cf > R y cr > R.")

    if _RESIDUAL_EVAL_CACHE is None:
        cache_res = []
        for idx, (nombre_eq, eq) in enumerate(_ECUACIONES_LIST):
            args_ord = tuple(sorted(_EQ_VARS[idx]))
            fn_eq = sp.lambdify([S[a] for a in args_ord], (eq.lhs, eq.rhs), "math")
            cache_res.append((nombre_eq, args_ord, fn_eq))
        _RESIDUAL_EVAL_CACHE = cache_res

    for nombre_eq, args_ord, fn_eq in _RESIDUAL_EVAL_CACHE:
        try:
            lhs_v, rhs_v = fn_eq(*(conocidas[a] for a in args_ord))
            lhs_f = float(lhs_v)
            rhs_f = float(rhs_v)
        except Exception:
            sust_final = {S[a]: sp.Float(conocidas[a]) for a in args_ord}
            eq = ECUACIONES[nombre_eq]
            lhs_f = float(sp.re(eq.lhs.xreplace(sust_final).evalf()))
            rhs_f = float(sp.re(eq.rhs.xreplace(sust_final).evalf()))
        escala = max(abs(lhs_f), abs(rhs_f), 1.0)
        if abs(lhs_f - rhs_f) / escala > 1e-4:
            raise ValueError(f"Inconsistencia en '{nombre_eq}': la combinación no es válida.")


def resolver(
    fijas: dict[str, float],
    referencia: dict[str, float] | None = None,
) -> dict[str, float]:
    """
    Dadas las variables fijas (nombre -> valor), calcula todas las demás:
      - Vía ultrarrápida (< 1 ms, 0 SymPy) con tearing cuando se usan las fijas estándar.
      - Vía BLT compilada y cacheada por conjunto de incógnitas para intercambios libres.
    Lanza ValueError si el sistema no tiene solución única real.
    """
    conocidas: dict[str, float] = {k: float(v) for k, v in fijas.items()}
    incognitas = set(VARIABLES) - set(conocidas)

    # 1. Vía rápida causal con variables de corte (tearing) para calibración estándar
    if frozenset(conocidas.keys()) == _FIJAS_INI_SET:
        sol_rapida = evaluador.evaluar_punto(conocidas, estricto_prolado=True)
        if sol_rapida is None:
            raise ValueError(
                "Esa combinación no tiene solución única o físicamente válida "
                "(verifica p. ej. que cf > R, cr > R, v < vpitch y que la batería sea suficiente)."
            )
        res_map = {k: float(sol_rapida[k]) for k in VARIABLES}
        _verificar_consistencia_global(res_map)
        return res_map

    # 2. Vía general con plan BLT compilado y cacheado por conjunto de incógnitas
    semilla = referencia if referencia is not None else conocidas
    inc_key = frozenset(incognitas)
    plan = _BLT_PLAN_CACHE.get(inc_key)
    if plan is None:
        plan = _compilar_plan_blt(inc_key)
        _BLT_PLAN_CACHE[inc_key] = plan

    for paso in plan:
        if paso["tipo"] == "directo":
            var_nom: str = paso["var"]  # type: ignore[assignment]
            args_ord: tuple[str, ...] = paso["args"]  # type: ignore[assignment]
            fn_directa: Callable[..., float] = paso["fn"]  # type: ignore[assignment]
            try:
                val = float(fn_directa(*(conocidas[a] for a in args_ord)))
            except Exception as exc:
                raise ValueError(
                    "Esa combinación no tiene solución única o físicamente válida "
                    "(verifica p. ej. que cf > R, cr > R y que el empuje supere el arrastre)."
                ) from exc
            if not _es_valida_float(var_nom, val):
                raise ValueError(
                    "Esa combinación no tiene solución única o físicamente válida "
                    "(verifica p. ej. que cf > R, cr > R y que el empuje supere el arrastre)."
                )
            conocidas[var_nom] = val
            continue

        params_ord: tuple[str, ...] = paso["params"]  # type: ignore[assignment]
        params_vals = tuple(conocidas[p] for p in params_ord)
        inc_red_names: list[str] = paso["inc_red_names"]  # type: ignore[assignment]
        fn_res = paso["fn_res"]
        retrosust: list[tuple[str, tuple[str, ...], Callable[..., float]]] = paso["retrosust"]  # type: ignore[assignment]
        semillas_red = [semilla.get(nom, _SEMILLAS_DEFECTO.get(nom, 1.0)) for nom in inc_red_names]

        res_bloque: dict[str, float] | None = None
        if fn_res is not None:
            sol_fast = _newton_rapido_compilado(fn_res, inc_red_names, params_vals, semillas_red)  # type: ignore[arg-type]
            if sol_fast is not None:
                res_cand = {inc_red_names[i]: sol_fast[i] for i in range(len(inc_red_names))}
                res_bloque = _ejecutar_retrosustitucion(res_cand, retrosust, conocidas)

            if res_bloque is None and len(inc_red_names) == 1:
                raiz_1d = _brent_bloque_1d(fn_res, inc_red_names[0], params_vals, semillas_red[0])  # type: ignore[arg-type]
                if raiz_1d is not None:
                    res_bloque = _ejecutar_retrosustitucion(
                        {inc_red_names[0]: raiz_1d}, retrosust, conocidas
                    )

        if res_bloque is None:
            res_bloque = _resolver_bloque_sympy(paso, conocidas, semilla)

        conocidas.update(res_bloque)

    if len(conocidas) != len(VARIABLES):
        raise ValueError("Quedaron variables sin determinar.")

    _verificar_consistencia_global(conocidas)
    return conocidas
