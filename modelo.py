"""
Modelo del sistema basado en CAS (SymPy).

Para ampliar el programa solo hay que:
  1. Agregar la variable en VARIABLES (nombre, descripción, unidad, valor inicial).
  2. Agregar la ecuación en ECUACIONES (como sp.Eq).
  3. Si la variable es un dato de entrada, incluirla en FIJAS_INI
     (regla: nº de variables calculadas == nº de ecuaciones independientes).
"""
import sympy as sp

# =============================================================
# VARIABLES: nombre -> (descripción, unidad, valor inicial o None)
# Calibradas para La Paz - Zona Sur a 100 m (~3.350 m s.n.m.)
# =============================================================
VARIABLES = {
    # Caso 1: gas a temperatura ambiente
    "P1":    ("Presión caso 1",             "Pa",        67120.0),
    "T1":    ("Temperatura caso 1",         "°C",        15.0),
    "R1":    ("Constante R caso 1",         "J/(kg·K)",  287.058),
    "rho1":  ("Densidad caso 1",            "kg/m³",     None),
    # Caso 2: mismo gas a mayor temperatura
    "P2":    ("Presión caso 2",             "Pa",        67120.0),
    "T2":    ("Temperatura caso 2",         "°C",        100.0),
    "R2":    ("Constante R caso 2",         "J/(kg·K)",  287.058),
    "rho2":  ("Densidad caso 2",            "kg/m³",     None),
    "drho":  ("Diferencia de densidades",   "kg/m³",     None),
    # Calor sensible
    "m":     ("Masa de aire",               "kg",        9.0),
    "cp":    ("Calor específico del aire",  "J/(kg·K)",  1005.0),
    "dT":    ("Gradiente térmico",          "K",         None),
    "Q":     ("Calor sensible",             "J",         None),
}

# Variables de entrada al iniciar (las demás se calculan)
FIJAS_INI = ["P1", "T1", "R1", "P2", "T2", "R2", "m", "cp"]

# Unidad para notación de ingeniería: nombre -> (unidad prefijable, resto, factor)
# Se muestra como: <prefijo><unidad prefijable><resto>. El factor convierte el valor
# SI al de la unidad prefijable (ej. kg -> g: 1000). Si es None no se usan prefijos.
UNIDAD_ING = {
    "P1": ("Pa", "", 1),         "P2": ("Pa", "", 1),
    "T1": (None, "°C", 1),       "T2": (None, "°C", 1),
    "R1": ("J", "/(kg·K)", 1),   "R2": ("J", "/(kg·K)", 1),
    "rho1": ("g", "/m³", 1000),  "rho2": ("g", "/m³", 1000),  "drho": ("g", "/m³", 1000),
    "m": ("g", "", 1000),
    "cp": ("J", "/(kg·K)", 1),
    "dT": ("K", "", 1),
    "Q": ("J", "", 1),
}

S = {n: sp.Symbol(n, real=True) for n in VARIABLES}
K = sp.Rational("273.15")  # °C -> K

# =============================================================
# ECUACIONES (las temperaturas están en °C; se convierte a K aquí)
# =============================================================
ECUACIONES = {
    "Gas ideal (caso 1)":  sp.Eq(S["rho1"], S["P1"] / (S["R1"] * (S["T1"] + K))),
    "Gas ideal (caso 2)":  sp.Eq(S["rho2"], S["P2"] / (S["R2"] * (S["T2"] + K))),
    "Diferencia densidad": sp.Eq(S["drho"], S["rho1"] - S["rho2"]),
    "Gradiente térmico":   sp.Eq(S["dT"],   S["T2"] - S["T1"]),
    "Calor sensible":      sp.Eq(S["Q"],    S["m"] * S["cp"] * S["dT"]),
}


def valores_iniciales() -> dict[str, float]:
    return {n: v[2] for n, v in VARIABLES.items() if n in FIJAS_INI}


def resolver(fijas: dict[str, float]) -> dict[str, float]:
    """
    Dadas las variables fijas (nombre -> valor), calcula todas las demás.
    Lanza ValueError si el sistema no tiene solución única real.
    """
    incognitas = [S[n] for n in VARIABLES if n not in fijas]
    sustitucion = {S[n]: sp.nsimplify(v, rational=True) for n, v in fijas.items()}
    eqs = [e.subs(sustitucion) for e in ECUACIONES.values()]

    try:
        soluciones = sp.solve(eqs, incognitas, dict=True)
    except Exception as exc:  # SymPy puede fallar con sistemas raros
        raise ValueError(f"No se pudo resolver el sistema: {exc}")

    # Descartar soluciones indeterminadas o no reales
    validas = [
        s for s in soluciones
        if len(s) == len(incognitas) and all(v.is_number and v.is_real for v in s.values())
    ]
    if not validas:
        raise ValueError(
            "Esa combinación no tiene solución única (sobre/sub-determinada o físicamente imposible)."
        )

    sol = validas[0]
    resultado = dict(fijas)
    resultado.update({str(k): float(v) for k, v in sol.items()})
    return resultado
