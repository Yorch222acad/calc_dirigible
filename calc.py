from rich.console import Console
from rich.panel import Panel

console = Console()

# =============================================================
# VALORES INICIALES / CONFIGURACIÓN (La Paz - Zona Sur a 100 m)
# =============================================================
# Caso 1: Gas a temperatura ambiente (15 °C)
P1_INI = 67120.0       # Presión (Pa)
T1_INI = 15.0          # Temperatura (°C)
R1_INI = 287.058       # Constante R del aire (J/(kg·K))

# Caso 2: Mismo gas a mayor temperatura (50 °C)
P2_INI = 67120.0       # Presión (Pa)
T2_INI = 100.0          # Temperatura (°C)
R2_INI = 287.058       # Constante R del aire (J/(kg·K))

# Parámetros de Calor Sensible
M_AIRE_INI = 9.0       # Masa de aire en kg
CP_AIRE_INI = 1005.0   # Calor específico a presión constante del aire en J/(kg·K)


# =============================================================
# MÓDULO 1: Cálculo de Densidad de Gases Ideales (ρ = P / (R · T))
# =============================================================
def calcular_densidad(p: float, t_c: float, r: float) -> tuple[float, float]:
    """
    Calcula la densidad de un gas a partir de la ecuación de estado.
    Retorna: (rho en kg/m³, t_k en Kelvin).
    """
    t_k = t_c + 273.15
    rho = p / (r * t_k)
    return rho, t_k


# =============================================================
# MÓDULO 2: Ecuación de Calor Sensible (Q = m_aire · cp · ΔT)
# =============================================================
def calcular_calor_sensible(m_aire: float, cp: float, delta_t: float) -> float:
    """
    Calcula el calor sensible necesario para elevar la temperatura del aire.
    Retorna: Q en Joules (J).
    """
    return m_aire * cp * delta_t


# =============================================================
# MÓDULO 3: Presentación en Pantalla (Estilo KaTeX 2D)
# =============================================================
def limpiar_pantalla() -> None:
    """Limpia la terminal y el historial para actualizar en sitio sin acumular texto."""
    print("\033[H\033[2J\033[3J", end="", flush=True)


def formatear_fraccion_2d(simbolo_izq: str, numerador: str, denominador: str, resultado: str) -> str:
    """
    Genera una representación matemática bidimensional estilo KaTeX:
           numerador
    símb = ─────────── = resultado
          denominador
    """
    ancho = max(len(numerador), len(denominador)) + 4
    barra = "─" * ancho
    num_pad = numerador.center(ancho)
    den_pad = denominador.center(ancho)
    espacios = " " * len(simbolo_izq)

    return (
        f"{espacios}{num_pad}\n"
        f"{simbolo_izq}{barra} = {resultado}\n"
        f"{espacios}{den_pad}"
    )


def mostrar_pantalla(p1: float, t1_c: float, r1: float, rho1: float, t1_k: float,
                     p2: float, t2_c: float, r2: float, rho2: float, t2_k: float,
                     delta_rho: float,
                     m_aire: float, cp: float, delta_t: float, q_joules: float) -> None:
    """Muestra el panel visual actualizado con formato matemático 2D."""
    limpiar_pantalla()

    # 1. Ecuación general compartida de la ley de los gases ideales
    ec_general_gas = (
        "[bold cyan]Ley de Gases Ideales (Ecuación General Compartida):[/bold cyan]\n"
        "        P\n"
        "  ρ = ─────\n"
        "      R · T"
    )

    # 2. Caso 1: Sustitución con formato 2D
    caso1_2d = formatear_fraccion_2d(
        simbolo_izq="  ρ₁ = ",
        numerador=f"{p1:,.2f} Pa",
        denominador=f"{r1:.3f} J/(kg·K) · {t1_k:.2f} K",
        resultado=f"[bold yellow]{rho1:.5f} kg/m³[/bold yellow]  ({t1_c:.1f} °C)"
    )
    texto_caso1 = f"[bold cyan]Caso 1 (Ambiente):[/bold cyan]\n{caso1_2d}"

    # 3. Caso 2: Sustitución con formato 2D
    caso2_2d = formatear_fraccion_2d(
        simbolo_izq="  ρ₂ = ",
        numerador=f"{p2:,.2f} Pa",
        denominador=f"{r2:.3f} J/(kg·K) · {t2_k:.2f} K",
        resultado=f"[bold yellow]{rho2:.5f} kg/m³[/bold yellow]  ({t2_c:.1f} °C)"
    )
    texto_caso2 = f"[bold cyan]Caso 2 (Mayor Temperatura):[/bold cyan]\n{caso2_2d}"

    # 4. Diferencia positiva de densidades
    texto_diff = (
        f"[bold green]▶ Diferencia de densidades (|ρ₁ - ρ₂|):[/bold green] "
        f"[bold white on blue] Δρ = {delta_rho:.5f} kg/m³ [/bold white on blue]"
    )

    # 5. Ecuación de Calor Sensible (General y Sustitución)
    q_kj = q_joules / 1000.0
    texto_calor = (
        "[bold cyan]Calor Sensible de la Termodinámica (Ecuación General):[/bold cyan]\n"
        "  Q = m_aire · c_p · ΔT\n\n"
        f"[bold cyan]Sustitución con valores (ΔT = |T₂ - T₁| = {delta_t:.2f} °C):[/bold cyan]\n"
        f"  Q = {m_aire:.2f} kg · {cp:.1f} J/(kg·K) · {delta_t:.2f} K\n"
        f"  [bold green]▶ Calor requerido (Q):[/bold green] [bold yellow]{q_joules:,.2f} J[/bold yellow] ([bold magenta]{q_kj:.2f} kJ[/bold magenta])"
    )

    separador = "─" * 68
    panel_completo = (
        f"{ec_general_gas}\n\n"
        f"{texto_caso1}\n\n"
        f"{texto_caso2}\n\n"
        f"{texto_diff}\n\n"
        f"{separador}\n\n"
        f"{texto_calor}"
    )

    console.print(Panel(
        panel_completo,
        title="[bold yellow]Sustentación & Termodinámica de Dirigibles[/bold yellow]",
        border_style="bright_blue",
        padding=(1, 2)
    ))


# =============================================================
# MÓDULO 4: Entrada de Usuario y Modificaciones
# =============================================================
def solicitar_modificacion(p1: float, t1_c: float, r1: float,
                           p2: float, t2_c: float, r2: float,
                           m_aire: float) -> tuple[bool, float, float, float, float, float, float, float]:
    """
    Gestiona la interacción para elegir y modificar variables.
    Retorna: (continuar, p1, t1_c, r1, p2, t2_c, r2, m_aire)
    """
    print("¿Qué deseas modificar?")
    print(f"  1. Modificar Caso 1 (T1 = {t1_c:.1f} °C, P1 = {p1:,.0f} Pa)")
    print(f"  2. Modificar Caso 2 (T2 = {t2_c:.1f} °C, P2 = {p2:,.0f} Pa)")
    print(f"  3. Modificar Masa de aire m_aire ({m_aire:.2f} kg)")
    print("  4. Salir")

    opcion = input("\nElige una opción (1-4): ").strip()

    if opcion in ("1", "2"):
        es_ec1 = (opcion == "1")
        nombre_ec = "Caso 1" if es_ec1 else "Caso 2"

        print(f"\nVariables de {nombre_ec}:")
        print("  1. Presión (P en Pa)")
        print("  2. Temperatura (T en °C)")
        print("  3. Constante (R)")
        var_op = input("Selecciona variable (1-3): ").strip()

        try:
            if var_op == "1":
                val = float(input("Nueva Presión (Pa): "))
                if es_ec1: p1 = val
                else: p2 = val
            elif var_op == "2":
                val = float(input("Nueva Temperatura (°C): "))
                if es_ec1: t1_c = val
                else: t2_c = val
            elif var_op == "3":
                val = float(input("Nueva Constante R (J/(kg·K)): "))
                if es_ec1: r1 = val
                else: r2 = val
        except ValueError:
            pass
        return True, p1, t1_c, r1, p2, t2_c, r2, m_aire

    elif opcion == "3":
        try:
            val = float(input("\nNueva Masa de aire en kg: "))
            if val > 0:
                m_aire = val
            else:
                print("La masa debe ser mayor a 0.")
        except ValueError:
            pass
        return True, p1, t1_c, r1, p2, t2_c, r2, m_aire

    elif opcion == "4":
        console.print("[bold cyan]¡Programa finalizado![/bold cyan]")
        return False, p1, t1_c, r1, p2, t2_c, r2, m_aire

    return True, p1, t1_c, r1, p2, t2_c, r2, m_aire


# =============================================================
# Flujo Principal
# =============================================================
def main() -> None:
    # Cargar valores iniciales desde la configuración superior
    p1, t1_c, r1 = P1_INI, T1_INI, R1_INI
    p2, t2_c, r2 = P2_INI, T2_INI, R2_INI
    m_aire = M_AIRE_INI
    cp = CP_AIRE_INI

    while True:
        # Cálculos de Densidad
        rho1, t1_k = calcular_densidad(p1, t1_c, r1)
        rho2, t2_k = calcular_densidad(p2, t2_c, r2)
        delta_rho = abs(rho1 - rho2)

        # Cálculo de Calor Sensible usando ΔT entre Caso 2 y Caso 1
        delta_t = abs(t2_c - t1_c)
        q_joules = calcular_calor_sensible(m_aire, cp, delta_t)

        # Mostrar en pantalla
        mostrar_pantalla(p1, t1_c, r1, rho1, t1_k,
                         p2, t2_c, r2, rho2, t2_k,
                         delta_rho,
                         m_aire, cp, delta_t, q_joules)

        # Solicitar modificaciones al usuario
        continuar, p1, t1_c, r1, p2, t2_c, r2, m_aire = solicitar_modificacion(
            p1, t1_c, r1, p2, t2_c, r2, m_aire
        )
        if not continuar:
            break


if __name__ == "__main__":
    main()