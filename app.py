"""
Servidor Backend FastAPI para la Calculadora de Sustentación, Termodinámica y
Propulsión Híbrida de Dirigibles.

Conecta el motor algebraico-numérico (modelo.py) y las reglas de visualización
(formateo.py) con el frontend web modular en ./frontend.
"""
from pathlib import Path
from typing import Any

import sympy as sp
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import formateo
import modelo

BASE_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Calculadora de Sustentación y Propulsión Híbrida de Dirigibles (CAS)",
    description="API Backend conectada al motor simbólico-numérico SymPy.",
    version="1.0.0",
)


# =============================================================
# Estado en memoria del sistema
# =============================================================
class EstadoSistema:
    def __init__(self) -> None:
        self.reiniciar()

    def reiniciar(self) -> None:
        self.fijas: set[str] = set(modelo.FIJAS_INI)
        entradas_ini = modelo.valores_iniciales()
        self.valores: dict[str, float] = modelo.resolver(entradas_ini)


estado = EstadoSistema()


# =============================================================
# Funciones auxiliares de serialización
# =============================================================
def _serializar_variable(
    nombre: str,
    valores: dict[str, float],
    valores_vista: dict[str, float],
    fijas: set[str],
    penalizado: bool,
) -> dict[str, Any]:
    desc, unidad, _ = modelo.VARIABLES[nombre]
    es_fija = nombre in fijas
    es_penalizada = bool(penalizado and nombre in formateo.VARS_SUSTENTACION)
    color = "red" if es_penalizada else ("yellow" if es_fija else "green")
    return {
        "nombre": nombre,
        "simbolo": sp.pretty(modelo.S[nombre], use_unicode=True),
        "descripcion": desc,
        "unidad": unidad,
        "unidad_guion": formateo.unidad_con_guion(unidad),
        "unidad_nombre": modelo.UNIDAD_NOMBRE.get(unidad, unidad),
        "fija": es_fija,
        "penalizada": es_penalizada,
        "color": color,
        "valor": valores[nombre],
        "valor_vista": valores_vista[nombre],
        "valor_ing": formateo.formatear_ingenieria(nombre, valores[nombre]),
        "valor_vista_ing": formateo.formatear_ingenieria(nombre, valores_vista[nombre]),
    }


def _serializar_ecuacion(
    categoria: str,
    nombre_eq: str,
    eq: sp.Eq,
    valores_vista: dict[str, float],
    fijas: set[str],
    penalizado: bool,
) -> dict[str, Any]:
    vars_eq = formateo.variables_de_ecuacion(eq, valores_vista, fijas, penalizado=penalizado)
    tiene_penalizada = any(v["penalizada"] for v in vars_eq)
    return {
        "categoria": categoria,
        "nombre": nombre_eq,
        "latex_general": formateo.renderizar_general_latex(eq),
        "latex_sustitucion": formateo.renderizar_sustitucion_latex(
            eq, valores_vista, fijas, penalizado=penalizado
        ),
        "variables": vars_eq,
        "tiene_penalizada": tiene_penalizada,
    }


def construir_respuesta_estado() -> dict[str, Any]:
    valores_vista, alertas = formateo.evaluar_alertas_y_vista(estado.valores)
    penalizado = bool(alertas)

    categorias_out = []
    for idx, (cat_nombre, ecuaciones) in enumerate(modelo.CATEGORIAS.items()):
        eqs_out = [
            _serializar_ecuacion(cat_nombre, nom_eq, eq, valores_vista, estado.fijas, penalizado)
            for nom_eq, eq in ecuaciones.items()
        ]
        vars_cat = {
            v["nombre"]
            for eq_item in eqs_out
            for v in eq_item["variables"]
        }
        fijas_cat = sum(1 for n in vars_cat if n in estado.fijas)
        calc_cat = len(vars_cat) - fijas_cat
        categorias_out.append({
            "id": idx,
            "nombre": cat_nombre,
            "num_ecuaciones": len(eqs_out),
            "num_fijas": fijas_cat,
            "num_calculadas": calc_cat,
            "tiene_penalizada": any(e["tiene_penalizada"] for e in eqs_out),
            "ecuaciones": eqs_out,
        })

    variables_out = [
        _serializar_variable(nom, estado.valores, valores_vista, estado.fijas, penalizado)
        for nom in modelo.VARIABLES
    ]

    return {
        "alertas": alertas,
        "penalizado": penalizado,
        "categorias": categorias_out,
        "variables": variables_out,
        "fijas": [n for n in modelo.VARIABLES if n in estado.fijas],
        "resumen": {
            "total_variables": len(modelo.VARIABLES),
            "total_fijas": len(estado.fijas),
            "total_calculadas": len(modelo.VARIABLES) - len(estado.fijas),
            "total_ecuaciones": len(modelo.ECUACIONES),
            "total_categorias": len(modelo.CATEGORIAS),
        },
    }


def construir_detalle_variable(nombre: str) -> dict[str, Any]:
    if nombre not in modelo.VARIABLES:
        raise HTTPException(status_code=404, detail=f"Variable desconocida: '{nombre}'")

    valores_vista, alertas = formateo.evaluar_alertas_y_vista(estado.valores)
    penalizado = bool(alertas)
    var_info = _serializar_variable(nombre, estado.valores, valores_vista, estado.fijas, penalizado)

    eqs_var = [
        _serializar_ecuacion(cat, nom_eq, eq, valores_vista, estado.fijas, penalizado)
        for cat, nom_eq, eq in modelo.ecuaciones_de_variable(nombre)
    ]

    if var_info["fija"]:
        nombres_cand = modelo.calculadas_fijables(estado.fijas, nombre)
        tipo_candidatas = "calculadas_a_fijar"
    else:
        nombres_cand = modelo.variables_liberables(estado.fijas, nombre)
        tipo_candidatas = "fijas_a_liberar"

    candidatas_out = [
        _serializar_variable(c, estado.valores, valores_vista, estado.fijas, penalizado)
        for c in nombres_cand
    ]

    return {
        "variable": var_info,
        "ecuaciones": eqs_var,
        "tipo_candidatas": tipo_candidatas,
        "candidatas": candidatas_out,
    }


# =============================================================
# Esquemas Pydantic para peticiones POST
# =============================================================
class PeticionEquilibrio(BaseModel):
    fijas: list[str]
    protegidas: list[str] = []


class PeticionModificar(BaseModel):
    entradas: dict[str, float]


# =============================================================
# Endpoints de la API
# =============================================================
@app.get("/api/estado")
def obtener_estado() -> dict[str, Any]:
    """Devuelve el estado global: categorías, ecuaciones renderizadas, variables y alertas."""
    return construir_respuesta_estado()


@app.get("/api/variable/{nombre}")
def obtener_detalle_variable(nombre: str) -> dict[str, Any]:
    """Devuelve el detalle de una variable, sus ecuaciones y candidatas de intercambio."""
    return construir_detalle_variable(nombre)


@app.post("/api/equilibrio")
def verificar_equilibrio(req: PeticionEquilibrio) -> dict[str, Any]:
    """
    Evalúa el grafo bipartito (ecuaciones <-> incógnitas) para guiar paso a paso
    al usuario indicando cuántas y cuáles variables faltan por fijar o liberar.
    """
    fijas_set = {n for n in req.fijas if n in modelo.VARIABLES}
    prot_set = {n for n in req.protegidas if n in modelo.VARIABLES}

    faltan_fijar, cand_fijar, faltan_liberar, cand_liberar = modelo.estado_equilibrio(
        fijas_set, excluidas=prot_set
    )
    valores_vista, alertas = formateo.evaluar_alertas_y_vista(estado.valores)
    penalizado = bool(alertas)

    return {
        "equilibrado": faltan_fijar == 0 and faltan_liberar == 0,
        "faltan_fijar": faltan_fijar,
        "candidatas_fijar": [
            _serializar_variable(c, estado.valores, valores_vista, fijas_set, penalizado)
            for c in cand_fijar
        ],
        "faltan_liberar": faltan_liberar,
        "candidatas_liberar": [
            _serializar_variable(f, estado.valores, valores_vista, fijas_set, penalizado)
            for f in cand_liberar
        ],
    }


@app.post("/api/modificar")
def modificar_sistema(req: PeticionModificar) -> dict[str, Any]:
    """
    Resuelve el sistema con el nuevo conjunto de variables fijas y sus valores.
    Si el sistema está desbalanceado o fuera del dominio físico, devuelve error 400.
    """
    desconocidas = [k for k in req.entradas if k not in modelo.VARIABLES]
    if desconocidas:
        raise HTTPException(
            status_code=400,
            detail=f"Variables desconocidas: {', '.join(desconocidas)}",
        )

    nuevas_fijas = set(req.entradas.keys())
    faltan_fijar, _, faltan_liberar, _ = modelo.estado_equilibrio(nuevas_fijas)
    if faltan_fijar != 0 or faltan_liberar != 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"El sistema aún no está en equilibrio matemático "
                f"(faltan {faltan_fijar} por fijar y {faltan_liberar} por liberar)."
            ),
        )

    try:
        nuevos_valores = modelo.resolver(req.entradas, referencia=estado.valores)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    estado.fijas = nuevas_fijas
    estado.valores = nuevos_valores
    return construir_respuesta_estado()


@app.post("/api/reiniciar")
def reiniciar_sistema() -> dict[str, Any]:
    """Restaura las variables fijas y valores de calibración iniciales (La Paz - Zona Sur)."""
    estado.reiniciar()
    return construir_respuesta_estado()


# =============================================================
# Archivos estáticos del Frontend
# =============================================================
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.get("/")
def servir_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
