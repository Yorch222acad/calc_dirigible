import math
import re

import sympy as sp
from rich.console import Console
from rich.markup import escape
from rich.panel import Panel

import modelo

console = Console()


# =============================================================
# Presentación en pantalla
# =============================================================
def limpiar_pantalla() -> None:
    """Limpia la terminal y el historial para actualizar en sitio sin acumular texto."""
    print("\033[H\033[2J\033[3J", end="", flush=True)


PREFIJOS = {
    -24: "y", -21: "z", -18: "a", -15: "f", -12: "p", -9: "n", -6: "µ", -3: "m",
    0: "", 3: "k", 6: "M", 9: "G", 12: "T", 15: "P", 18: "E", 21: "Z", 24: "Y",
}
K_SIMBOLO = sp.Symbol("273.15 (K)")  # constante de conversión °C -> K


def formatear_ingenieria(nombre: str, valor: float) -> str:
    """Ej.: 67120 Pa -> '67.120 (kPa)'. Hasta 3 enteros y 3 decimales."""
    base, resto, factor = modelo.UNIDAD_ING[nombre]
    v = valor * factor
    exp = 0
    if base is not None and v != 0:
        exp = int(math.floor(math.log10(abs(v)) / 3)) * 3
        exp = max(-24, min(24, exp))
        if abs(round(v / 10 ** exp, 3)) >= 1000 and exp < 24:  # p.ej. 999.9996 -> 1.000
            exp += 3
    mantisa = v / 10 ** exp if base is not None else v
    unidad = f"{PREFIJOS[exp]}{base}{resto}" if base is not None else resto
    texto = f"{mantisa:.3f} ({unidad})"
    return f"({texto})" if mantisa < 0 else texto


def renderizar_general(eq: sp.Eq) -> str:
    """Ecuación simbólica (en gris) con la unidad de cada variable entre paréntesis."""
    eq = eq.xreplace({modelo.K: K_SIMBOLO})
    reemplazo = {}
    for simbolo in eq.free_symbols:
        nombre = str(simbolo)
        if nombre in modelo.VARIABLES:
            unidad = modelo.VARIABLES[nombre][1]
            reemplazo[simbolo] = sp.Symbol(f"{sp.pretty(simbolo, use_unicode=True)} ({unidad})")
    dibujo = escape(sp.pretty(eq.xreplace(reemplazo), use_unicode=True))
    return f"[grey58]{dibujo}[/grey58]"


def renderizar_sustitucion(eq: sp.Eq, valores: dict[str, float], fijas: set[str]) -> str:
    """
    Dibuja la ecuación con los valores numéricos en lugar de las variables, en 2D.
    Cada valor se colorea: amarillo si la variable es fija, verde si es calculada.
    Se usan símbolos marcadores del mismo ancho que el valor para no romper
    la alineación de las fracciones; luego se reemplazan por el texto coloreado.
    """
    eq = eq.xreplace({modelo.K: K_SIMBOLO})
    marcadores = {}   # caracter marcador -> (texto del valor, color)
    reemplazo = {}
    for i, simbolo in enumerate(sorted(eq.free_symbols, key=str)):
        nombre = str(simbolo)
        if nombre not in valores:  # constantes (273.15 K)
            continue
        texto = formatear_ingenieria(nombre, valores[nombre])
        marca = chr(0xE000 + i)
        marcadores[marca] = (texto, "yellow" if nombre in fijas else "green")
        reemplazo[simbolo] = sp.Symbol(marca * len(texto))

    dibujo = escape(sp.pretty(eq.xreplace(reemplazo), use_unicode=True))
    for marca, (texto, color) in marcadores.items():
        dibujo = re.sub(
            f"{marca}+",
            lambda _m, t=texto, c=color: f"[bold {c}]{t}[/bold {c}]",
            dibujo,
        )
    return dibujo


def mostrar_pantalla(valores: dict[str, float], fijas: set[str]) -> None:
    limpiar_pantalla()

    bloques = []
    for nombre, eq in modelo.ECUACIONES.items():
        bloques.append(
            f"[bold cyan]{nombre}[/bold cyan]\n{renderizar_general(eq)}\n\n"
            f"{renderizar_sustitucion(eq, valores, fijas)}"
        )

    leyenda = "[yellow]■ fija[/yellow]   [green]■ calculada[/green]"
    console.print(Panel(
        ("\n\n" + "─" * 60 + "\n\n").join(bloques) + "\n\n" + leyenda,
        title="[bold yellow]Sustentación & Termodinámica de Dirigibles (CAS)[/bold yellow]",
        border_style="bright_blue",
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


def modificar(valores: dict[str, float], fijas: set[str]) -> tuple[dict[str, float], set[str]]:
    """
    Fija `objetivo = valor` y libera otra variable (`ajuste`) para que se ajuste.
    Si el objetivo ya es una variable fija, basta con cambiar su valor.
    """
    print("\nVariables:", ", ".join(modelo.VARIABLES))
    objetivo = pedir_variable("Variable a cambiar (o Enter para salir): ")
    if objetivo is None:
        return valores, fijas

    try:
        nuevo = float(input(f"Nuevo valor de {objetivo}: "))
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
        return modelo.resolver(entradas), nuevas_fijas
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
