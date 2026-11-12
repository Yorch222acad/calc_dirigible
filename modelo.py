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
# Geometría inicial: L = 6 m, D = 2.5 m -> R = 1.25 m, cf = 2.1 m (0.35 L), cr = 3.9 m (0.65 L)
# =============================================================
VARIABLES = {
    # Caso 1: gas a temperatura ambiente (exterior)
    "P1":    ("Presión caso 1 (ambiente)",              "Pa",          67120.0),
    "T1":    ("Temperatura caso 1 (ambiente)",          "°C",          15.0),
    "R1":    ("Constante R caso 1",                     "J/(kg·K)",    287.058),
    "rho1":  ("Densidad caso 1 (ambiente)",             "kg/m³",       None),
    # Caso 2: mismo gas a mayor temperatura (aire caliente interior)
    "P2":    ("Presión caso 2 (aire caliente)",         "Pa",          67120.0),
    "T2":    ("Temperatura caso 2 (aire caliente)",     "°C",          100.0),
    "R2":    ("Constante R caso 2",                     "J/(kg·K)",    287.058),
    "rho2":  ("Densidad caso 2 (aire caliente)",        "kg/m³",       None),
    "drho":  ("Diferencia de densidades",               "kg/m³",       None),
    # Geometría del casco (dos semielipsoides prolados, cf > R y cr > R)
    "R":     ("Radio máximo transversal",               "m",           1.25),
    "cf":    ("Longitud semielipsoide nariz",           "m",           2.1),
    "cr":    ("Longitud semielipsoide cola",            "m",           3.9),
    "L":     ("Longitud total del casco",               "m",           None),
    "V":     ("Volumen total del casco",                "m³",          None),
    "ef":    ("Excentricidad frontal",                  "adim",        None),
    "er":    ("Excentricidad trasera",                  "adim",        None),
    "Sf":    ("Área superficial frontal",               "m²",          None),
    "Sr":    ("Área superficial trasera",               "m²",          None),
    "S":     ("Área superficial total",                 "m²",          None),
    # Masa de aire caliente y calor sensible
    "m":     ("Masa de aire caliente",                  "kg",          None),
    "cp":    ("Calor específico del aire",              "J/(kg·K)",    1005.0),
    "dT":    ("Gradiente térmico (T2 - T1)",            "K",           None),
    "Q":     ("Calor sensible total",                   "J",           None),
    # Sustentación (Arquímedes)
    "g":     ("Aceleración de la gravedad",             "m/s²",        9.775),
    "F":     ("Fuerza de sustentación",                 "N",           None),
    # Aislamiento por capa intermedia de celdas (con orificios de ecualización de 3 mm)
    "e":     ("Espesor de capa intermedia celular",     "m",           0.02),
    "W":     ("Ancho de celda cuadrada",                "m",           0.20),
    "beta":  ("Coef. expansión térmica del aire",       "K⁻¹",         0.00302),
    "nu":    ("Viscosidad cinemática del aire",         "m²/s",        2.65e-5),
    "alpha": ("Difusividad térmica del aire",           "m²/s",        3.80e-5),
    "Rae":   ("Número de Rayleigh en la celda",         "adim",        None),
    "Rac":   ("Rayleigh crítico de convección",         "adim",        2000.0),
    "Nuc":   ("Número de Nusselt en la celda",          "adim",        None),
    "ka":    ("Conductividad térmica del aire",         "W/(m·K)",     0.0285),
    "U0":    ("Coef. global sin capa celular",          "W/(m²·K)",    5.0),
    "U":     ("Coef. global con capa celular",          "W/(m²·K)",    None),
    "Qp0":   ("Potencia perdida sin capa celular",      "W",           None),
    "Qp":    ("Potencia perdida con capa celular",      "W",           None),
    "dQp":   ("Potencia ahorrada por capa celular",     "W",           None),
    "fais":  ("Fracción de ahorro térmico celular",     "adim",        None),
    "Sc":    ("Área de película de la cuadrícula",      "m²",          None),
    "sigma": ("Gramaje de película HDPE",               "kg/m²",       0.0095),
    "mc":    ("Masa total de la cuadrícula celular",    "kg",          None),
    # Pérdida de calor y enfriamiento (con aislante celular incorporado)
    "vT":    ("Velocidad de enfriamiento (dT/dt)",      "K/s",         None),
    "dTc":   ("Caída admisible de temperatura",         "K",           20.0),
    "Qc":    ("Energía perdida en caída dTc",           "J",           None),
    "tc":    ("Tiempo de enfriamiento para dTc",        "s",           None),
    # Quemador de propano/butano (GLP) para compensación térmica
    "PC":    ("Poder calorífico del GLP (propano)",     "J/kg",        4.6e7),
    "mgc":   ("Masa de GLP para recuperar caída dTc",   "kg",          None),
    "tm":    ("Tiempo de misión (mantenimiento)",       "s",           1800.0),
    "Em":    ("Energía para mantener T en misión",      "J",           None),
    "mgm":   ("Masa de GLP para mantener T en misión",  "kg",          None),
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
}

# Variables de entrada al iniciar (52 variables - 29 ecuaciones = 23 fijas)
FIJAS_INI = [
    "P1", "T1", "R1", "P2", "T2", "R2",
    "R", "cf", "cr",
    "cp", "g",
    "e", "W", "beta", "nu", "alpha", "Rac", "ka", "U0", "sigma",
    "dTc",
    "PC", "tm",
]

# Variables que físicamente deben ser estrictamente positivas
POSITIVAS = {
    "P1", "R1", "rho1", "P2", "R2", "rho2",
    "R", "cf", "cr", "L", "V", "ef", "er", "Sf", "Sr", "S",
    "m", "cp", "g",
    "e", "W", "beta", "nu", "alpha", "Rae", "Rac", "Nuc", "ka", "U0", "U",
    "Qp0", "Qp", "dQp", "fais", "Sc", "sigma", "mc",
    "vT", "dTc", "Qc", "tc",
    "PC", "mgc", "tm", "Em", "mgm",
}

# Unidad para notación de ingeniería: nombre -> (unidad prefijable, resto, factor)
# Se muestra como: <prefijo>_<unidad prefijable><resto>. El factor convierte el valor
# SI al de la unidad prefijable (ej. kg -> g: 1000). Si es None no se usan prefijos.
UNIDAD_ING = {
    "P1":    ("Pa", "", 1),        "P2":    ("Pa", "", 1),
    "T1":    (None, "°C", 1),      "T2":    (None, "°C", 1),
    "R1":    ("J", "/(kg·K)", 1),  "R2":    ("J", "/(kg·K)", 1),
    "rho1":  ("g", "/m³", 1000),   "rho2":  ("g", "/m³", 1000),   "drho": ("g", "/m³", 1000),
    "R":     ("m", "", 1),         "cf":    ("m", "", 1),         "cr":   ("m", "", 1),
    "L":     ("m", "", 1),         "V":     ("m³", "", 1),
    "ef":    (None, "adim", 1),    "er":    (None, "adim", 1),
    "Sf":    ("m²", "", 1),        "Sr":    ("m²", "", 1),        "S":    ("m²", "", 1),
    "m":     ("g", "", 1000),
    "cp":    ("J", "/(kg·K)", 1),
    "dT":    ("K", "", 1),
    "Q":     ("J", "", 1),
    "g":     (None, "m/s²", 1),
    "F":     ("N", "", 1),
    # Capa intermedia de celdas y transferencia de calor
    "e":     ("m", "", 1),
    "W":     ("m", "", 1),
    "beta":  ("K⁻¹", "", 1),
    "nu":    ("m²/s", "", 1),
    "alpha": ("m²/s", "", 1),
    "Rae":   ("adim", "", 1),
    "Rac":   ("adim", "", 1),
    "Nuc":   (None, "adim", 1),
    "ka":    ("W", "/(m·K)", 1),
    "U0":    ("W", "/(m²·K)", 1),
    "U":     ("W", "/(m²·K)", 1),
    "Qp0":   ("W", "", 1),
    "Qp":    ("W", "", 1),
    "dQp":   ("W", "", 1),
    "fais":  (None, "adim", 1),
    "Sc":    ("m²", "", 1),
    "sigma": ("g", "/m²", 1000),
    "mc":    ("g", "", 1000),
    # Pérdida de calor y enfriamiento
    "vT":    ("K", "/s", 1),
    "dTc":   ("K", "", 1),
    "Qc":    ("J", "", 1),
    "tc":    ("s", "", 1),
    # Quemador de GLP
    "PC":    ("J", "/kg", 1),
    "mgc":   ("g", "", 1000),
    "tm":    ("s", "", 1),
    "Em":    ("J", "", 1),
    "mgm":   ("g", "", 1000),
}

S = {
    n: sp.Symbol(n, real=True, positive=(True if n in POSITIVAS else None))
    for n in VARIABLES
}
K = sp.Rational("273.15")  # °C -> K
RA_CRIT = sp.Integer(2000)  # Umbral crítico de Rayleigh en cavidad celular

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
        "Fuerza de sustentación": sp.Eq(S["F"], S["drho"] * S["g"] * S["V"]),
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
}

# Lista plana de ecuaciones para el solucionador
ECUACIONES = {nombre: eq for cat in CATEGORIAS.values() for nombre, eq in cat.items()}


def valores_iniciales() -> dict[str, float]:
    return {n: v[2] for n, v in VARIABLES.items() if n in FIJAS_INI}


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
    if nombre in ("ef", "er", "fais") and not (0 < v < 1):
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

    # Intento 1: resolución simbólica con SymPy
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

    # Intento 2: resolución numérica (para ecuaciones trascendentes como asin)
    try:
        # Reducción por sustitución simbólica dentro del bloque (ej. sustituir er(cr) en Sr)
        sust_interna: dict[sp.Symbol, sp.Expr] = {}
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
                cambio = True
                break

        inc_reducidas = [inc for inc in incognitas_bloque if inc not in sust_interna]
        exprs = [e.lhs - e.rhs for e in eqs_reducidas]
        valores_semilla = [semilla.get(str(inc), 1.0) for inc in inc_reducidas]
        if len(exprs) == 1 and len(inc_reducidas) == 1:
            sol_unica = sp.nsolve(exprs[0], inc_reducidas[0], valores_semilla[0])
            pares = [(inc_reducidas[0], sol_unica)]
        else:
            sol_num = sp.nsolve(exprs, inc_reducidas, valores_semilla)
            pares = list(zip(inc_reducidas, sol_num))

        res_sim = {inc: sp.sympify(val).evalf() for inc, val in pares}
        for inc_elim, expr_elim in sust_interna.items():
            res_sim[inc_elim] = expr_elim.xreplace(res_sim).evalf()

        res = {}
        for inc, val in res_sim.items():
            if not _es_valida(str(inc), val):
                raise ValueError("Solución fuera de dominio físico.")
            res[str(inc)] = float(sp.re(val))
        return res
    except Exception as exc:
        raise ValueError(
            "Esa combinación no tiene solución única o físicamente válida "
            "(verifica p. ej. que cf > R y cr > R)."
        ) from exc


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

        avance = False
        # Buscamos un subsistema cerrado de tamaño k (1, 2, ..., len(pendientes))
        for k in range(1, len(pendientes) + 1):
            for indices in combinations(range(len(pendientes)), k):
                sub_eqs = [pendientes[i] for i in indices]
                sub_eqs_sust = [e.xreplace(sust) for e in sub_eqs]

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
