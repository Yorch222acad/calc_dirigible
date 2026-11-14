import sympy as sp
from rich.cells import cell_len
from rich.console import Console, Group
from rich.markup import escape
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

import modelo
from formateo import (
    PREFIJOS,
    K_SIMBOLO,
    LOG10_FUNC,
    VARS_SUSTENTACION,
    unidad_con_guion as _unidad_con_guion,
    formatear_ingenieria,
    evaluar_alertas_y_vista,
    preparar_eq_vista as _preparar_eq_vista,
    renderizar_general,
    renderizar_sustitucion,
)

console = Console()


# =============================================================
# Presentación en pantalla
# =============================================================
def limpiar_pantalla() -> None:
    """Limpia la terminal y el historial para actualizar en sitio sin acumular texto."""
    print("\033[H\033[2J\033[3J", end="", flush=True)


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


def _tabla_candidatas(
    candidatas: list[str],
    valores: dict[str, float],
    color: str,
) -> Table:
    """Construye una tabla compacta a 2 columnas con nombre, valor actual y descripción."""
    tabla = Table(box=None, padding=(0, 2), show_header=False, expand=True)
    tabla.add_column("C1", ratio=1)
    tabla.add_column("Sep", width=1, style="grey42", justify="center")
    tabla.add_column("C2", ratio=1)

    mitad = (len(candidatas) + 1) // 2
    izq = candidatas[:mitad]
    der = candidatas[mitad:]

    for i in range(mitad):
        n1 = izq[i]
        d1 = modelo.VARIABLES[n1][0]
        v1 = formatear_ingenieria(n1, valores[n1])
        txt1 = f"[bold {color}]{n1}[/bold {color}] = [white]{escape(v1)}[/white] [grey62]— {escape(d1)}[/grey62]"

        if i < len(der):
            n2 = der[i]
            d2 = modelo.VARIABLES[n2][0]
            v2 = formatear_ingenieria(n2, valores[n2])
            txt2 = f"[bold {color}]{n2}[/bold {color}] = [white]{escape(v2)}[/white] [grey62]— {escape(d2)}[/grey62]"
        else:
            txt2 = ""

        tabla.add_row(txt1, "│", txt2)
    return tabla


def _mostrar_detalle_variable(objetivo: str, valores: dict[str, float], fijas: set[str]) -> list[str]:
    """
    Muestra abajo del catálogo el detalle de `objetivo`:
    1. Valor actual y estado (FIJA o CALCULADA).
    2. Ecuaciones completas donde interviene (fórmula general + valores reemplazados en 2D + tabla de variables).
    3. Variables calculadas que se pueden volver fijas (si `objetivo` es fija) o variables fijas que
       se pueden liberar (si `objetivo` es calculada) para mantener el sentido matemático.
    """
    desc, unidad, _ = modelo.VARIABLES[objetivo]
    es_fija = objetivo in fijas
    estado = "[bold yellow]FIJA (amarilla)[/bold yellow]" if es_fija else "[bold green]CALCULADA (verde)[/bold green]"
    val_ing = formatear_ingenieria(objetivo, valores[objetivo])
    valores_vista, alertas = evaluar_alertas_y_vista(valores)
    penalizado = bool(alertas)

    elementos = [
        Text.from_markup(
            f"[bold cyan]{objetivo}[/bold cyan] — [grey82]{escape(desc)}[/grey82]   "
            f"Estado: {estado}   "
            f"Actual: [bold yellow]{valores[objetivo]:.6g} {escape(unidad)}[/bold yellow] [grey62]({escape(val_ing)})[/grey62]"
        ),
        Text(""),
        Text.from_markup(f"[bold white]Ecuaciones donde interviene '{objetivo}' (con valores reemplazados):[/bold white]"),
        Text(""),
    ]

    separador_eq = Text("─" * 60, style="grey42")
    eqs_var = modelo.ecuaciones_de_variable(objetivo)
    for idx, (cat, nom_eq, eq) in enumerate(eqs_var):
        if idx > 0:
            elementos += [Text(""), separador_eq, Text("")]
        titulo_eq = f"{nom_eq}  [grey58]({escape(cat)})[/grey58]"
        elementos.append(bloque_ecuacion(titulo_eq, eq, valores_vista, fijas, penalizado=penalizado))

    elementos.append(Text(""))
    elementos.append(Text("═" * 60, style="cyan"))
    elementos.append(Text(""))

    if es_fija:
        candidatas = modelo.calculadas_fijables(fijas, objetivo)
        elementos.append(
            Text.from_markup(
                f"[bold white]Variables calculadas (verdes) que se pueden volver fijas si liberas "
                f"[yellow]{objetivo}[/yellow] ({len(candidatas)} disponibles):[/bold white]"
            )
        )
        if candidatas:
            elementos.append(_tabla_candidatas(candidatas, valores, "green"))
        else:
            elementos.append(Text.from_markup("  [red]Ninguna variable calculada individual permite liberar esta variable.[/red]"))
    else:
        candidatas = modelo.variables_liberables(fijas, objetivo)
        elementos.append(
            Text.from_markup(
                f"[bold white]Variables fijas (amarillas) que se pueden liberar (volver calculadas) al fijar "
                f"[green]{objetivo}[/green] ({len(candidatas)} disponibles):[/bold white]"
            )
        )
        if candidatas:
            elementos.append(_tabla_candidatas(candidatas, valores, "yellow"))
        else:
            elementos.append(Text.from_markup("  [red]Ninguna variable fija individual permite despejar esta variable.[/red]"))

    console.print(Panel(
        Group(*elementos),
        title=f"[bold cyan]Detalle de '{objetivo}'[/bold cyan]",
        border_style="cyan",
        padding=(0, 1),
    ))
    return candidatas


def _pedir_valor_fijo(var: str, valores: dict[str, float]) -> float | None:
    """Pide el valor numérico para fijar `var` (Enter conserva su valor actual)."""
    desc, unidad, _ = modelo.VARIABLES[var]
    actual = valores[var]
    val_ing = formatear_ingenieria(var, actual)
    resp = input(
        f"Valor fijo para {var} ({desc}) [actual: {actual:.6g} {unidad} ({val_ing}) | Enter = mantener actual]: "
    ).strip()
    if not resp:
        return actual
    try:
        return float(resp)
    except ValueError:
        console.print("[red]Valor numérico inválido.[/red]")
        return None


def _equilibrar_sistema(
    nuevas_fijas: set[str],
    entradas: dict[str, float],
    valores: dict[str, float],
    protegidas: set[str],
) -> bool:
    """
    Guía paso a paso al usuario mostrando cuántas y cuáles variables calculadas
    faltan por volver fijas (o cuántas y cuáles variables fijas faltan por liberar)
    hasta que el sistema tenga sentido matemático.
    """
    while True:
        faltan_fijar, candidatas_fijar, faltan_liberar, candidatas_liberar = modelo.estado_equilibrio(
            nuevas_fijas, excluidas=protegidas
        )
        if faltan_fijar == 0 and faltan_liberar == 0:
            return True

        # Caso 1: Faltan variables calculadas por volver fijas
        if faltan_fijar > 0:
            plural = "s" if faltan_fijar > 1 else ""
            console.print(Panel(
                Group(
                    Text.from_markup(
                        f"[bold yellow]Falta{'n' if faltan_fijar > 1 else ''} {faltan_fijar} variable{plural} "
                        f"calculada{plural} (verde{plural}) por volver fija{plural} para lograr el sentido matemático:[/bold yellow]"
                    ),
                    _tabla_candidatas(candidatas_fijar, valores, "green") if candidatas_fijar else Text(""),
                ),
                title=f"[bold cyan]Equilibrio Matemático — Faltan {faltan_fijar} por volver fijas[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
            ))
            eleccion = input(
                f"Variable calculada a volver fija (faltan {faltan_fijar} | o escribe otra fija para liberarla | Enter cancela): "
            ).strip()
            if not eleccion:
                return False
            if eleccion not in modelo.VARIABLES:
                console.print(f"[red]Variable desconocida: '{eleccion}'[/red]")
                continue
            if eleccion in protegidas:
                console.print(f"[yellow]'{eleccion}' ya fue modificada en este paso.[/yellow]")
                continue
            if eleccion in nuevas_fijas:
                # El usuario decidió liberar una variable fija adicional
                nuevas_fijas.remove(eleccion)
                entradas.pop(eleccion, None)
                protegidas.add(eleccion)
                console.print(f"[cyan]Se liberó la variable fija '{eleccion}' (pasa a ser calculada).[/cyan]")
                continue

            # Es una variable calculada que pasará a ser fija
            nuevo_val = _pedir_valor_fijo(eleccion, valores)
            if nuevo_val is None:
                continue
            nuevas_fijas.add(eleccion)
            entradas[eleccion] = nuevo_val
            protegidas.add(eleccion)
            continue

        # Caso 2: Faltan variables fijas por liberar (volver calculadas)
        if faltan_liberar > 0:
            plural = "s" if faltan_liberar > 1 else ""
            console.print(Panel(
                Group(
                    Text.from_markup(
                        f"[bold yellow]Falta{'n' if faltan_liberar > 1 else ''} {faltan_liberar} variable{plural} "
                        f"fija{plural} (amarilla{plural}) por liberar (volver calculada{plural}) para lograr el sentido matemático:[/bold yellow]"
                    ),
                    _tabla_candidatas(candidatas_liberar, valores, "yellow") if candidatas_liberar else Text(""),
                ),
                title=f"[bold cyan]Equilibrio Matemático — Faltan {faltan_liberar} por liberar[/bold cyan]",
                border_style="yellow",
                padding=(0, 1),
            ))
            eleccion = input(
                f"Variable fija a liberar (faltan {faltan_liberar} | o escribe otra calculada para volverla fija | Enter cancela): "
            ).strip()
            if not eleccion:
                return False
            if eleccion not in modelo.VARIABLES:
                console.print(f"[red]Variable desconocida: '{eleccion}'[/red]")
                continue
            if eleccion in protegidas:
                console.print(f"[yellow]'{eleccion}' ya fue modificada en este paso.[/yellow]")
                continue
            if eleccion not in nuevas_fijas:
                # El usuario decidió volver fija otra variable calculada adicional
                nuevo_val = _pedir_valor_fijo(eleccion, valores)
                if nuevo_val is None:
                    continue
                nuevas_fijas.add(eleccion)
                entradas[eleccion] = nuevo_val
                protegidas.add(eleccion)
                console.print(f"[cyan]Se fijó también la variable calculada '{eleccion}'.[/cyan]")
                continue

            nuevas_fijas.remove(eleccion)
            entradas.pop(eleccion, None)
            protegidas.add(eleccion)


def modificar(valores: dict[str, float], fijas: set[str]) -> tuple[dict[str, float], set[str]]:
    """
    Permite modificar una variable fija o calculada mostrando sus ecuaciones reemplazadas
    y guiando el intercambio entre variables fijas y calculadas para conservar el sentido matemático.
    """
    mostrar_menu_variables(fijas)
    objetivo = pedir_variable("Variable a cambiar (o Enter para salir): ")
    if objetivo is None:
        return valores, fijas

    _mostrar_detalle_variable(objetivo, valores, fijas)

    desc, unidad, _ = modelo.VARIABLES[objetivo]
    val_ing = formatear_ingenieria(objetivo, valores[objetivo])
    nuevas_fijas = set(fijas)
    entradas = {n: valores[n] for n in nuevas_fijas}
    protegidas: set[str] = {objetivo}

    if objetivo in fijas:
        resp = input(
            f"Nuevo valor numérico para '{objetivo}' ({desc}) [actual: {valores[objetivo]:.6g} {unidad} ({val_ing})],\n"
            f"o escribe el nombre de una variable calculada para volverla fija y liberar '{objetivo}' "
            f"(o 'liberar' / Enter para cancelar): "
        ).strip()
        if not resp:
            return valores, fijas

        # ¿Ingresó un número para cambiar directamente el valor de la variable fija?
        try:
            nuevo = float(resp)
            entradas[objetivo] = nuevo
        except ValueError:
            # El usuario quiere liberar `objetivo` (volverla calculada) y fijar variable(s) calculada(s)
            nuevas_fijas.remove(objetivo)
            entradas.pop(objetivo, None)

            if resp.lower() not in ("liberar", "l"):
                if resp not in modelo.VARIABLES:
                    console.print(f"[red]Entrada no válida o variable desconocida: '{resp}'[/red]")
                    input("Enter para continuar...")
                    return valores, fijas
                if resp in nuevas_fijas:
                    # Liberó una segunda variable fija además de `objetivo`
                    nuevas_fijas.remove(resp)
                    entradas.pop(resp, None)
                    protegidas.add(resp)
                else:
                    # Eligió directamente una variable calculada para volverla fija
                    val_c = _pedir_valor_fijo(resp, valores)
                    if val_c is None:
                        input("Enter para continuar...")
                        return valores, fijas
                    nuevas_fijas.add(resp)
                    entradas[resp] = val_c
                    protegidas.add(resp)

            if not _equilibrar_sistema(nuevas_fijas, entradas, valores, protegidas):
                return valores, fijas
    else:
        # `objetivo` es CALCULADA (verde): pasa a ser FIJA (amarilla)
        try:
            nuevo = float(input(
                f"Nuevo valor para volver fija '{objetivo}' - {desc} "
                f"[actual: {valores[objetivo]:.6g} {unidad} ({val_ing})]: "
            ))
        except ValueError:
            console.print("[red]Valor inválido.[/red]")
            input("Enter para continuar...")
            return valores, fijas

        nuevas_fijas.add(objetivo)
        entradas[objetivo] = nuevo

        if not _equilibrar_sistema(nuevas_fijas, entradas, valores, protegidas):
            return valores, fijas

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
