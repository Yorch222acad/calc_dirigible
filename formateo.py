"""
Módulo compartido de presentación y reglas visuales:
- Notación de ingeniería con guion bajo (ej. 67.120 (K_Pa), 20.000 (m_m), 3.000 (K_g)).
- Evaluación de alertas de diseño (mbat > mbmax, theta > thmax) y penalización en negativo
  de las variables de sustentación (F, mflot, FL, FLmax, Fexc).
- Generación de ecuaciones en formato 2D (para terminal con Rich) y en formato LaTeX/KaTeX
  coloreado (para el frontend web).
"""
import math
import re

import sympy as sp
from rich.markup import escape

import modelo

# Prefijos negativos en minúsculas (m, u, n, p...) y positivos en mayúsculas (K, M, G, T...)
PREFIJOS = {
    -24: "y", -21: "z", -18: "a", -15: "f", -12: "p", -9: "n", -6: "u", -3: "m",
    0: "", 3: "K", 6: "M", 9: "G", 12: "T", 15: "P", 18: "E", 21: "Z", 24: "Y",
}
K_SIMBOLO = sp.Symbol("273.15 (K)")  # constante de conversión °C -> K
LOG10_FUNC = sp.Function("log₁₀")
VARS_SUSTENTACION = ("F", "mflot", "FL", "FLmax", "Fexc")

# Colores hexadecimales para KaTeX en el frontend web
COLOR_HEX = {
    "general": "#94a3b8",   # gris claro para la ecuación simbólica general
    "yellow":  "#facc15",   # amarillo para variables fijas
    "green":   "#4ade80",   # verde para variables calculadas
    "red":     "#f87171",   # rojo para variables de sustentación penalizadas
}


def unidad_con_guion(unidad: str) -> str:
    """Convierte prefijos SI en unidades base (ej. 'kg' -> 'K_g') en todas las vistas."""
    return unidad.replace("kg", "K_g")


def formatear_ingenieria_partes(nombre: str, valor: float) -> tuple[str, str, bool]:
    """
    Calcula la mantisa (3 decimales), la cadena de unidad con prefijo ingenieril
    separado por guion bajo y si el valor es negativo.
    """
    base, resto, factor = modelo.UNIDAD_ING[nombre]
    resto = unidad_con_guion(resto)
    v = valor * factor
    exp = 0
    if base is not None and v != 0:
        exp = int(math.floor(math.log10(abs(v)) / 3)) * 3
        exp = max(-24, min(24, exp))
        if abs(round(v / 10 ** exp, 3)) >= 1000 and exp < 24:  # p.ej. 999.9996 -> 1.000
            exp += 3
    mantisa = v / 10 ** exp if base is not None else v
    if base is not None:
        pref = PREFIJOS[exp]
        unidad = f"{pref}_{base}{resto}" if pref else f"{base}{resto}"
    else:
        unidad = resto
    return f"{mantisa:.3f}", unidad, (mantisa < 0)


def formatear_ingenieria(nombre: str, valor: float) -> str:
    """Ej.: 67120 Pa -> '67.120 (K_Pa)', 0.02 m -> '20.000 (m_m)'. Hasta 3 enteros y 3 decimales."""
    mantisa_str, unidad, es_neg = formatear_ingenieria_partes(nombre, valor)
    texto = f"{mantisa_str} ({unidad})"
    return f"({texto})" if es_neg else texto


def evaluar_alertas_y_vista(valores: dict[str, float]) -> tuple[dict[str, float], list[str]]:
    """
    Verifica si se excede el peso máximo de batería (mbmax) o el ángulo máximo de
    rotación (thmax). Si se supera algún límite, pone en negativo los valores de
    sustentación en la vista y devuelve los mensajes de alerta correspondientes.
    """
    alertas: list[str] = []
    if valores["mbat"] > valores["mbmax"]:
        alertas.append(
            f"PESO DE BATERÍA EXCEDIDO: mbat = {formatear_ingenieria('mbat', valores['mbat'])} "
            f"supera el máximo permitido mbmax = {formatear_ingenieria('mbmax', valores['mbmax'])}. "
            "Cálculos de sustentación puestos en NEGATIVO."
        )
    if valores["theta"] > valores["thmax"]:
        alertas.append(
            f"ÁNGULO DE ROTACIÓN EXCEDIDO: theta = {valores['theta']:.2f}° "
            f"supera el máximo permitido thmax = {valores['thmax']:.2f}°. "
            "Cálculos de sustentación puestos en NEGATIVO."
        )

    vista = dict(valores)
    if alertas:
        for var_s in VARS_SUSTENTACION:
            if var_s in vista:
                vista[var_s] = -abs(vista[var_s])
    return vista, alertas


def preparar_eq_vista(eq: sp.Eq) -> sp.Eq:
    """Reemplaza constantes y logaritmos en base 10 para una presentación 2D limpia."""
    eq = eq.xreplace({modelo.K: K_SIMBOLO})
    if "Cf" in modelo.S and eq.lhs == modelo.S["Cf"]:
        eq = sp.Eq(eq.lhs, sp.Float("0.455") * LOG10_FUNC(modelo.S["ReL"]) ** sp.Float("-2.58"))
    return eq


def renderizar_general(eq: sp.Eq) -> str:
    """Ecuación simbólica 2D (en gris) para terminal con la unidad de cada variable entre paréntesis."""
    eq = preparar_eq_vista(eq)
    marcadores = {}
    reemplazo = {}
    for i, simbolo in enumerate(sorted(eq.free_symbols, key=str)):
        nombre = str(simbolo)
        if nombre in modelo.VARIABLES:
            unidad = unidad_con_guion(modelo.VARIABLES[nombre][1])
            texto = f"{sp.pretty(simbolo, use_unicode=True)} ({unidad})"
            marca = chr(0xE000 + i)
            marcadores[marca] = texto
            reemplazo[simbolo] = sp.Symbol(marca * len(texto))
    eq_m = eq.xreplace(reemplazo)
    eq_m = sp.Eq(sp.powsimp(eq_m.lhs, force=True), sp.powsimp(eq_m.rhs, force=True))
    dibujo = escape(sp.pretty(eq_m, use_unicode=True, wrap_line=False))
    for marca, texto in marcadores.items():
        dibujo = re.sub(f"{marca}+", lambda _m, t=escape(texto): t, dibujo)
    return f"[grey58]{dibujo}[/grey58]"


def renderizar_sustitucion(
    eq: sp.Eq,
    valores: dict[str, float],
    fijas: set[str],
    penalizado: bool = False,
) -> str:
    """
    Dibuja la ecuación en 2D para terminal con los valores numéricos en lugar de las variables.
    Cada valor se colorea: amarillo si la variable es fija, verde si es calculada
    (o rojo si es una variable de sustentación penalizada en negativo).
    """
    eq = preparar_eq_vista(eq)
    marcadores = {}
    reemplazo = {}
    for i, simbolo in enumerate(sorted(eq.free_symbols, key=str)):
        nombre = str(simbolo)
        if nombre not in valores:  # constantes (273.15 K)
            continue
        texto = formatear_ingenieria(nombre, valores[nombre])
        marca = chr(0xE000 + i)
        if penalizado and nombre in VARS_SUSTENTACION:
            color = "red"
        else:
            color = "yellow" if nombre in fijas else "green"
        marcadores[marca] = (texto, color)
        reemplazo[simbolo] = sp.Symbol(marca * len(texto))

    eq_m = eq.xreplace(reemplazo)
    eq_m = sp.Eq(sp.powsimp(eq_m.lhs, force=True), sp.powsimp(eq_m.rhs, force=True))
    dibujo = escape(sp.pretty(eq_m, use_unicode=True, wrap_line=False))
    for marca, (texto, color) in marcadores.items():
        dibujo = re.sub(
            f"{marca}+",
            lambda _m, t=escape(texto), c=color: f"[bold {c}]{t}[/bold {c}]",
            dibujo,
        )
    return dibujo


# =============================================================
# Renderizado LaTeX / KaTeX para el Frontend Web
# =============================================================
def _escapar_texto_latex(texto: str) -> str:
    """Escapa caracteres especiales dentro de bloques \\text{...} de KaTeX."""
    return (
        texto.replace("\\", "\\textbackslash ")
        .replace("_", "\\_")
        .replace("%", "\\%")
        .replace("&", "\\&")
        .replace("#", "\\#")
    )


def _factor_unidad_a_latex(factor: str) -> str:
    """
    Convierte un factor individual de unidad (sin '/' ni '·') a LaTeX matemático,
    manejando exponentes (², ³, ⁻¹), grados (°C, °) y guiones bajos (K_g, m_m).
    """
    f = factor.strip()
    if not f:
        return ""
    if f == "°C":
        return r"{^\circ\text{C}}"
    if f == "°":
        return r"{^\circ}"

    exp = None
    base = f
    if f.endswith("⁻¹"):
        base = f[:-2]
        exp = "-1"
    elif f.endswith("²"):
        base = f[:-1]
        exp = "2"
    elif f.endswith("³"):
        base = f[:-1]
        exp = "3"

    base_esc = _escapar_texto_latex(base)
    base_latex = rf"\text{{{base_esc}}}"
    if exp is not None:
        return rf"{base_latex}^{{{exp}}}"
    return base_latex


def _producto_unidad_a_latex(prod: str) -> str:
    """
    Convierte un producto de unidades separadas por '·' (ej. 'K_g·K' o 'u_Pa·s')
    a LaTeX usando '\\cdot' en modo matemático para evitar el error \\cdotp en \\text{}.
    """
    p = prod.strip()
    if p.startswith("(") and p.endswith(")"):
        p = p[1:-1].strip()
    partes = [_factor_unidad_a_latex(tok) for tok in p.split("·") if tok.strip()]
    return r" \cdot ".join(partes)


def unidad_a_latex(unidad: str) -> str:
    """
    Convierte cualquier unidad (ej. 'J/(kg·K)', 'g/m³', 'W/(m²·K)', 'K_Pa')
    en LaTeX con fracción vertical \\frac{numerador}{denominador} cuando tiene '/'.
    """
    u = unidad_con_guion(unidad.strip())
    if "/" in u:
        num_str, den_str = u.split("/", 1)
        num_l = _producto_unidad_a_latex(num_str)
        den_l = _producto_unidad_a_latex(den_str)
        return rf"\frac{{{num_l}}}{{{den_l}}}"
    return _producto_unidad_a_latex(u)


def formatear_ingenieria_latex(nombre: str, valor: float) -> str:
    """
    Formatea el valor en notación de ingeniería con su unidad como fracción vertical LaTeX.
    """
    mantisa_str, unidad, es_neg = formatear_ingenieria_partes(nombre, valor)
    u_latex = unidad_a_latex(unidad)
    interno = rf"\textbf{{{mantisa_str}}}\,\left({u_latex}\right)"
    return rf"\left({interno}\right)" if es_neg else interno


def _preparar_eq_latex(eq: sp.Eq) -> sp.Eq:
    """Ajusta constantes para exportación limpia a LaTeX."""
    return eq.xreplace({modelo.K: K_SIMBOLO})


def _postprocesar_latex(codigo: str) -> str:
    """
    Usa \\dfrac en las fracciones de la ecuación principal para que numeradores y
    denominadores se vean grandes y legibles, y limpia nombres trigonométricos.
    """
    codigo = codigo.replace(r"\frac", r"\dfrac")
    codigo = codigo.replace(r"\operatorname{asin}", r"\arcsin")
    codigo = codigo.replace(r"\operatorname{atan}", r"\arctan")
    return codigo


def _simbolo_linea_unica(nombre: str) -> str:
    """
    Devuelve el símbolo legible en una sola línea (sin saltos de línea 2D de SymPy)
    para mostrar junto a su unidad en las ecuaciones generales de KaTeX.
    """
    mapa_especial = {
        "P1": "P₁", "T1": "T₁", "R1": "R₁", "rho1": "ρ₁",
        "P2": "P₂", "T2": "T₂", "R2": "R₂", "rho2": "ρ₂",
        "drho": "Δρ", "lam": "λ",
        "beta": "β", "nu": "ν", "alpha": "α", "sigma": "σ",
        "mu": "μ", "theta": "θ", "thmax": "θmax", "dth": "Δθ",
    }
    return mapa_especial.get(nombre, nombre)


def _token_general_latex(nombre: str) -> str:
    """Construye el bloque LaTeX de una variable simbólica con su unidad en fracción vertical."""
    sim_txt = _escapar_texto_latex(_simbolo_linea_unica(nombre))
    u_latex = unidad_a_latex(modelo.VARIABLES[nombre][1])
    return rf"{{\textbf{{{sim_txt}}}\,\left({u_latex}\right)}}"


def renderizar_general_latex(eq: sp.Eq) -> str:
    """
    Devuelve la ecuación simbólica general en formato KaTeX/LaTeX (en gris),
    mostrando cada variable con su unidad entre paréntesis (con fracciones verticales).
    """
    if "Cf" in modelo.S and eq.lhs == modelo.S["Cf"]:
        t_cf = _token_general_latex("Cf")
        t_rel = _token_general_latex("ReL")
        cuerpo = (
            rf"{t_cf} = "
            rf"\dfrac{{0.455}}{{\left(\log_{{10}}\left({t_rel}\right)\right)^{{2.58}}}}"
        )
        return rf"\textcolor{{{COLOR_HEX['general']}}}{{{cuerpo}}}"

    eq_l = _preparar_eq_latex(eq)
    # Primero generamos la estructura de la ecuación con marcadores seguros y luego
    # insertamos las unidades (para que \postprocesar_latex convierta a \dfrac las fracciones
    # de la ecuación y mantenga \frac en las unidades).
    marcadores: dict[str, str] = {}
    nombres_simbolos: dict[sp.Basic, str] = {}
    for idx, simbolo in enumerate(sorted(eq_l.free_symbols, key=str)):
        nombre = str(simbolo)
        clave = f"__TOK_{idx}__"
        if simbolo == K_SIMBOLO:
            marcadores[clave] = r"{\textbf{273.15}\,\left(\text{K}\right)}"
            nombres_simbolos[simbolo] = clave
        elif nombre in modelo.VARIABLES:
            marcadores[clave] = _token_general_latex(nombre)
            nombres_simbolos[simbolo] = clave

    cuerpo = _postprocesar_latex(
        sp.latex(eq_l, symbol_names=nombres_simbolos, mul_symbol="dot", ln_notation=True)
    )
    for clave, valor_latex in marcadores.items():
        cuerpo = cuerpo.replace(clave, valor_latex)

    return rf"\textcolor{{{COLOR_HEX['general']}}}{{{cuerpo}}}"


def renderizar_sustitucion_latex(
    eq: sp.Eq,
    valores: dict[str, float],
    fijas: set[str],
    penalizado: bool = False,
) -> str:
    """
    Devuelve la ecuación en formato KaTeX/LaTeX con las variables reemplazadas
    por sus valores en notación de ingeniería (con unidades en fracción vertical) y coloreadas:
    - Amarillo: variable fija
    - Verde: variable calculada
    - Rojo: variable de sustentación penalizada en negativo
    """
    def _token_valor(nombre: str) -> str:
        val_latex = formatear_ingenieria_latex(nombre, valores[nombre])
        if penalizado and nombre in VARS_SUSTENTACION:
            color = COLOR_HEX["red"]
        else:
            color = COLOR_HEX["yellow"] if nombre in fijas else COLOR_HEX["green"]
        return rf"{{\textcolor{{{color}}}{{{val_latex}}}}}"

    if "Cf" in modelo.S and eq.lhs == modelo.S["Cf"]:
        t_cf = _token_valor("Cf")
        t_rel = _token_valor("ReL")
        return rf"{t_cf} = \dfrac{{0.455}}{{\left(\log_{{10}}\left({t_rel}\right)\right)^{{2.58}}}}"

    eq_l = _preparar_eq_latex(eq)
    marcadores: dict[str, str] = {}
    nombres_simbolos: dict[sp.Basic, str] = {}
    for idx, simbolo in enumerate(sorted(eq_l.free_symbols, key=str)):
        nombre = str(simbolo)
        clave = f"__VAL_{idx}__"
        if simbolo == K_SIMBOLO:
            marcadores[clave] = r"{\textbf{273.15}\,\left(\text{K}\right)}"
            nombres_simbolos[simbolo] = clave
        elif nombre in valores:
            marcadores[clave] = _token_valor(nombre)
            nombres_simbolos[simbolo] = clave

    cuerpo = _postprocesar_latex(
        sp.latex(eq_l, symbol_names=nombres_simbolos, mul_symbol="dot", ln_notation=True)
    )
    for clave, valor_latex in marcadores.items():
        cuerpo = cuerpo.replace(clave, valor_latex)

    return cuerpo


def variables_de_ecuacion(eq: sp.Eq, valores: dict[str, float], fijas: set[str], penalizado: bool = False) -> list[dict]:
    """
    Devuelve la lista ordenada de variables que intervienen en `eq` con su metadato,
    estado, color y valor formateado.
    """
    nombres = {str(simbolo) for simbolo in eq.free_symbols}
    resultado = []
    for nombre, (desc, unidad, _) in modelo.VARIABLES.items():
        if nombre in nombres:
            es_fija = nombre in fijas
            es_penalizada = bool(penalizado and nombre in VARS_SUSTENTACION)
            color = "red" if es_penalizada else ("yellow" if es_fija else "green")
            unidad_completa = modelo.UNIDAD_NOMBRE.get(unidad, unidad)
            resultado.append({
                "nombre": nombre,
                "simbolo": sp.pretty(modelo.S[nombre], use_unicode=True),
                "descripcion": desc,
                "unidad": unidad,
                "unidad_guion": unidad_con_guion(unidad),
                "unidad_nombre": unidad_completa,
                "fija": es_fija,
                "penalizada": es_penalizada,
                "color": color,
                "valor": valores[nombre],
                "valor_ing": formatear_ingenieria(nombre, valores[nombre]),
            })
    return resultado
