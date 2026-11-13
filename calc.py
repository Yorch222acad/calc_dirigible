import math
import re

import sympy as sp
from rich.cells import cell_len
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import modelo

console = Console()


# =============================================================
# Presentación en pantalla
# =============================================================
def limpiar_pantalla() -> None:
    """Limpia la terminal y el historial para actualizar en sitio sin acumular texto."""
    print("\033[H\033[2J\033[3J", end="", flush=True)


# Prefijos negativos en minúsculas (m, u, n, p...) y positivos en mayúsculas (K, M, G, T...)
PREFIJOS = {
    -24: "y", -21: "z", -18: "a", -15: "f", -12: "p", -9: "n", -6: "u", -3: "m",
    0: "", 3: "K", 6: "M", 9: "G", 12: "T", 15: "P", 18: "E", 21: "Z", 24: "Y",
}
K_SIMBOLO = sp.Symbol("273.15 (K)")  # constante de conversión °C -> K
LOG10_FUNC = sp.Function("log₁₀")
VARS_SUSTENTACION = ("F", "mflot", "FL", "FLmax", "Fexc")


def _preparar_eq_vista(eq: sp.Eq) -> sp.Eq:
    """Reemplaza constantes y logaritmos en base 10 para una presentación 2D limpia."""
    eq = eq.xreplace({modelo.K: K_SIMBOLO})
    if "Cf" in modelo.S and eq.lhs == modelo.S["Cf"]:
        eq = sp.Eq(eq.lhs, sp.Float("0.455") * LOG10_FUNC(modelo.S["ReL"]) ** sp.Float("-2.58"))
    return eq


def _unidad_con_guion(unidad: str) -> str:
    """Convierte prefijos SI en unidades base (ej. 'kg' -> 'K_g') en todas las vistas."""
    return unidad.replace("kg", "K_g")


def formatear_ingenieria(nombre: str, valor: float) -> str:
    """Ej.: 67120 Pa -> '67.120 (K_Pa)', 0.02 m -> '20.000 (m_m)'. Hasta 3 enteros y 3 decimales."""
    base, resto, factor = modelo.UNIDAD_ING[nombre]
    resto = _unidad_con_guion(resto)
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
    texto = f"{mantisa:.3f} ({unidad})"
    return f"({texto})" if mantisa < 0 else texto


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


def renderizar_general(eq: sp.Eq) -> str:
    """Ecuación simbólica (en gris) con la unidad de cada variable entre paréntesis."""
    eq = _preparar_eq_vista(eq)
    marcadores = {}
    reemplazo = {}
    for i, simbolo in enumerate(sorted(eq.free_symbols, key=str)):
        nombre = str(simbolo)
        if nombre in modelo.VARIABLES:
            unidad = _unidad_con_guion(modelo.VARIABLES[nombre][1])
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
    Dibuja la ecuación con los valores numéricos en lugar de las variables, en 2D.
    Cada valor se colorea: amarillo si la variable es fija, verde si es calculada
    (o rojo si es una variable de sustentación penalizada en negativo).
    """
    eq = _preparar_eq_vista(eq)
    marcadores = {}   # caracter marcador -> (texto del valor, color)
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


def tabla_variables_ecuacion(eq: sp.Eq, fijas: set[str]) -> Table:
    """Variables implicadas en una ecuación: nombre, descripción y nombre completo de su unidad."""
    tabla = Table(box=None, show_header=False, padding=(0, 1), pad_edge=False)
    tabla.add_column("Var", no_wrap=True)
    tabla.add_column("Desc")
    nombres = {str(simbolo) for simbolo in eq.free_symbols}
    for nombre, (desc, unidad, _) in modelo.VARIABLES.items():  # orden del catálogo
        if nombre in nombres:
            color = "yellow" if nombre in fijas else "green"
            unidad_completa = modelo.UNIDAD_NOMBRE.get(unidad, unidad)
            tabla.add_row(
                f"[bold {color}]{nombre}[/bold {color}]",
                f"[grey70]{desc}[/grey70] [grey50]({escape(unidad_completa)})[/grey50]",
            )
    return tabla


ANCHO_VARIABLES = 28  # ancho mínimo reservado para la columna de variables a la derecha


def bloque_ecuacion(
    nombre: str,
    eq: sp.Eq,
    valores: dict[str, float],
    fijas: set[str],
    penalizado: bool = False,
):
    """
    Ecuación (general + sustituida) con sus variables a la derecha en columnas.
    Si la terminal es demasiado angosta, las variables se muestran debajo.
    """
    texto_eq = (
        f"{renderizar_general(eq)}\n\n"
        f"{renderizar_sustitucion(eq, valores, fijas, penalizado=penalizado)}"
    )
    ancho_eq = max(cell_len(l) for l in Text.from_markup(texto_eq).plain.splitlines())
    variables = tabla_variables_ecuacion(eq, fijas)
    titulo = Text.from_markup(f"[bold cyan]{nombre}[/bold cyan]")

    # 4 = bordes del panel, 2 = relleno, 6 = separador y márgenes de la rejilla
    if ancho_eq + ANCHO_VARIABLES + 12 <= console.width:
        rejilla = Table.grid(padding=(0, 2))
        rejilla.add_column(no_wrap=True)
        rejilla.add_column(style="grey42", width=1)
        rejilla.add_column(min_width=ANCHO_VARIABLES, ratio=1)
        barra = "\n".join("│" for _ in range(texto_eq.count("\n") + 1))
        rejilla.add_row(Text.from_markup(texto_eq), barra, variables)
        return Group(titulo, rejilla)
    return Group(titulo, Text.from_markup(texto_eq), Text(""), variables)


def mostrar_pantalla(valores: dict[str, float], fijas: set[str]) -> None:
    limpiar_pantalla()
    valores_vista, alertas = evaluar_alertas_y_vista(valores)
    penalizado = bool(alertas)

    elementos = []
    if alertas:
        for alerta in alertas:
            elementos.append(Text.from_markup(f"[bold white on red] ⚠ {escape(alerta)} [/bold white on red]"))
        elementos.append(Text(""))

    separador_eq = Text("─" * 60, style="grey42")
    separador_cat = Text("═" * 60, style="blue")
    for i, (categoria, ecuaciones) in enumerate(modelo.CATEGORIAS.items()):
        if i:
            elementos += [Text(""), separador_cat, Text("")]
        elementos += [Text.from_markup(f"[bold white on blue] ▌ {categoria.upper()} [/bold white on blue]"), Text("")]
        for j, (nombre, eq) in enumerate(ecuaciones.items()):
            if j:
                elementos += [Text(""), separador_eq, Text("")]
            elementos.append(bloque_ecuacion(nombre, eq, valores_vista, fijas, penalizado=penalizado))

    leyenda = "[yellow]■ fija[/yellow]   [green]■ calculada[/green]"
    if penalizado:
        leyenda += "   [red]■ sustentación penalizada (negativa)[/red]"
    elementos += [Text(""), Text.from_markup(leyenda)]

    if alertas:
        elementos.append(Text(""))
        for alerta in alertas:
            elementos.append(Text.from_markup(f"[bold white on red] ⚠ {escape(alerta)} [/bold white on red]"))

    console.print(Panel(
        Group(*elementos),
        title="[bold yellow]Sustentación, Termodinámica & Propulsión Híbrida de Dirigibles (CAS)[/bold yellow]",
        border_style="red" if penalizado else "bright_blue",
        padding=(1, 2),
    ))


# =============================================================
# Entrada de usuario
# =============================================================
def pedir_variable(mensaje: str) -> str | None:
    nombre = input(mensaje).strip()
    if not nombre:
        return None
    if nombre not in modelo.VARIABLES:
        console.print(f"[red]Variable desconocida: '{nombre}'[/red]")
        input("Enter para continuar...")
        return None
    return nombre


def mostrar_menu_variables(fijas: set[str]) -> None:
    """Muestra el catálogo de variables con su descripción y estado en un panel de columnas."""
    tabla = Table(box=None, padding=(0, 2), show_header=False, expand=True)
    tabla.add_column("Var1", style="bold", width=7, no_wrap=True)
    tabla.add_column("Desc1", ratio=1)
    tabla.add_column("Sep", width=2, style="grey42", justify="center")
    tabla.add_column("Var2", style="bold", width=7, no_wrap=True)
    tabla.add_column("Desc2", ratio=1)

    items = list(modelo.VARIABLES.items())
    mitad = (len(items) + 1) // 2
    filas_izq = items[:mitad]
    filas_der = items[mitad:]

    for i in range(mitad):
        # Celda izquierda
        nom1, (desc1, _, _) = filas_izq[i]
        c1 = "yellow" if nom1 in fijas else "green"

        # Celda derecha
        if i < len(filas_der):
            nom2, (desc2, _, _) = filas_der[i]
            c2 = "yellow" if nom2 in fijas else "green"
            var2_txt = f"[{c2}]{nom2}[/{c2}]"
            desc2_txt = f"[grey70]{desc2}[/grey70]"
        else:
            var2_txt = ""
            desc2_txt = ""

        tabla.add_row(
            f"[{c1}]{nom1}[/{c1}]",
            f"[grey70]{desc1}[/grey70]",
            "│",
            var2_txt,
            desc2_txt,
        )

    console.print(Panel(
        tabla,
        title="[bold cyan]Variables del Sistema (Amarillo = Fija, Verde = Calculada)[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    ))


def modificar(valores: dict[str, float], fijas: set[str]) -> tuple[dict[str, float], set[str]]:
    """
    Fija `objetivo = valor` y libera otra variable (`ajuste`) para que se ajuste.
    Si el objetivo ya es una variable fija, basta con cambiar su valor.
    """
    mostrar_menu_variables(fijas)
    objetivo = pedir_variable("Variable a cambiar (o Enter para salir): ")
    if objetivo is None:
        return valores, fijas

    desc, unidad, _ = modelo.VARIABLES[objetivo]
    try:
        nuevo = float(input(
            f"Nuevo valor de {objetivo} - {desc} "
            f"[actual: {valores[objetivo]:.6g} {unidad}]: "
        ))
    except ValueError:
        console.print("[red]Valor inválido.[/red]")
        input("Enter para continuar...")
        return valores, fijas

    nuevas_fijas = set(fijas)
    if objetivo not in fijas:
        ajuste = pedir_variable(
            f"{objetivo} era calculada. ¿Cuál variable fija se ajusta? {sorted(fijas)}: "
        )
        if ajuste is None or ajuste not in fijas:
            if ajuste is not None:
                console.print("[red]Debe ser una variable fija.[/red]")
                input("Enter para continuar...")
            return valores, fijas
        nuevas_fijas.remove(ajuste)
        nuevas_fijas.add(objetivo)

    entradas = {n: valores[n] for n in nuevas_fijas}
    entradas[objetivo] = nuevo
    try:
        return modelo.resolver(entradas, referencia=valores), nuevas_fijas
    except ValueError as exc:
        console.print(f"[red]{exc}[/red]")
        input("Enter para continuar...")
        return valores, fijas


# =============================================================
# Flujo principal
# =============================================================
def main() -> None:
    fijas = set(modelo.FIJAS_INI)
    valores = modelo.resolver(modelo.valores_iniciales())

    while True:
        mostrar_pantalla(valores, fijas)
        nuevos, nuevas_fijas = modificar(valores, fijas)
        if nuevos is valores:  # sin cambios (Enter vacío o error)
            if input("¿Salir? (s/N): ").strip().lower() == "s":
                console.print("[bold cyan]¡Programa finalizado![/bold cyan]")
                break
            continue
        valores, fijas = nuevos, nuevas_fijas


if __name__ == "__main__":
    main()
