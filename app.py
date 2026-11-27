"""
Servidor Backend FastAPI para la Calculadora de Sustentación, Termodinámica y
Propulsión Híbrida de Dirigibles.

Conecta el motor algebraico-numérico (modelo.py) y las reglas de visualización
(formateo.py) con el frontend web modular en ./frontend.
"""
from pathlib import Path
from typing import Any

import sympy as sp
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import diseno
import flujo
import formateo
import graficas
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
    vars_alerta: set[str] | None = None,
) -> dict[str, Any]:
    desc, unidad, _ = modelo.VARIABLES[nombre]
    es_fija = nombre in fijas
    en_alerta = vars_alerta if vars_alerta is not None else (formateo.variables_en_alerta(valores) if penalizado else set())
    es_penalizada = bool(penalizado and nombre in en_alerta)
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


_CAT_INDICES = {nombre: idx for idx, nombre in enumerate(modelo.CATEGORIAS)}


def _serializar_ecuacion(
    categoria: str | None,
    nombre_eq: str,
    eq: sp.Eq,
    valores_vista: dict[str, float],
    fijas: set[str],
    penalizado: bool,
) -> dict[str, Any]:
    vars_eq = formateo.variables_de_ecuacion(eq, valores_vista, fijas, penalizado=penalizado)
    tiene_penalizada = any(v["penalizada"] for v in vars_eq)
    cats_num = modelo.categorias_numeradas_de_ecuacion(nombre_eq)
    categorias_list = [
        {"id": cid, "codigo": cod, "nombre": cnom, "eq_num": enum, "eq_codigo": eq_cod}
        for cid, cod, cnom, enum, eq_cod in cats_num
    ]
    cat_idx = _CAT_INDICES[categoria] if categoria in _CAT_INDICES else (cats_num[0][0] if cats_num else 0)
    cat_nombre = categoria if categoria in _CAT_INDICES else (cats_num[0][2] if cats_num else "")
    eq_num_actual = modelo.numero_ecuacion_en_categoria(cat_idx, nombre_eq)
    eq_codigo_actual = f"(C{cat_idx + 1}, E{eq_num_actual})"
    return {
        "categoria": cat_nombre,
        "categoria_id": cat_idx,
        "categoria_codigo": f"C{cat_idx + 1}",
        "ecuacion_num": eq_num_actual,
        "ecuacion_codigo": eq_codigo_actual,
        "categorias": categorias_list,
        "categorias_codigo_str": ", ".join(c["eq_codigo"] for c in categorias_list),
        "es_compartida": len(categorias_list) > 1,
        "nombre": nombre_eq,
        "latex_general": formateo.renderizar_general_latex(eq),
        "latex_sustitucion": formateo.renderizar_sustitucion_latex(
            eq, valores_vista, fijas, penalizado=penalizado
        ),
        "variables": vars_eq,
        "tiene_penalizada": tiene_penalizada,
        "nota_fisica": flujo.nota_ecuacion(nombre_eq),
        "notas_bloques": flujo.bloques_nota_ecuacion(nombre_eq),
    }


def construir_respuesta_estado() -> dict[str, Any]:
    valores_vista, alertas = formateo.evaluar_alertas_y_vista(estado.valores)
    penalizado = bool(alertas)
    vars_alerta = formateo.variables_en_alerta(estado.valores) if penalizado else set()

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
            "num_compartidas": sum(1 for e in eqs_out if e["es_compartida"]),
            "num_fijas": fijas_cat,
            "num_calculadas": calc_cat,
            "tiene_penalizada": any(e["tiene_penalizada"] for e in eqs_out),
            "ecuaciones": eqs_out,
            "flujo": flujo.construir_flujo_categoria(idx),
        })

    variables_out = [
        _serializar_variable(nom, estado.valores, valores_vista, estado.fijas, penalizado, vars_alerta)
        for nom in modelo.VARIABLES
    ]

    graficas_out = graficas.construir_datos_graficas(estado.valores, estado.fijas)

    return {
        "alertas": alertas,
        "penalizado": penalizado,
        "categorias": categorias_out,
        "mapa_flujo": flujo.construir_mapa_global(),
        "graficas": graficas_out,
        "variables": variables_out,
        "fijas": [n for n in modelo.VARIABLES if n in estado.fijas],
        "resumen": {
            "total_variables": len(modelo.VARIABLES),
            "total_fijas": len(estado.fijas),
            "total_calculadas": len(modelo.VARIABLES) - len(estado.fijas),
            "total_ecuaciones": len(modelo.ECUACIONES),
            "total_categorias": len(modelo.CATEGORIAS),
            "total_graficas": len(graficas_out),
        },
    }


def construir_detalle_variable(nombre: str) -> dict[str, Any]:
    if nombre not in modelo.VARIABLES:
        raise HTTPException(status_code=404, detail=f"Variable desconocida: '{nombre}'")

    valores_vista, alertas = formateo.evaluar_alertas_y_vista(estado.valores)
    penalizado = bool(alertas)
    var_info = _serializar_variable(nombre, estado.valores, valores_vista, estado.fijas, penalizado)

    eqs_var = [
        _serializar_ecuacion(
            cats[0][2] if cats else None,
            nom_eq,
            eq,
            valores_vista,
            estado.fijas,
            penalizado,
        )
        for cats, nom_eq, eq in modelo.ecuaciones_detalladas_de_variable(nombre)
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


class PeticionAnalisisDiseno(BaseModel):
    pesos: dict[str, float] | None = None
    variables: list[str] | None = None
    cbat_kg: float = diseno.CBAT_KG_DEFECTO
    respetar_limites: bool = True
    restricciones: list[dict[str, Any]] | None = None
    base_overrides: dict[str, float] | None = None
    ejecutar_optimizador: bool = True
    usar_optimo_como_base: bool = True


class PeticionGuardarHistorico(BaseModel):
    nombre: str
    nota: str = ""
    origen: str = "actual"
    entradas: dict[str, float] | None = None
    pesos: dict[str, float] | None = None
    cbat_kg: float = diseno.CBAT_KG_DEFECTO
    respetar_limites: bool = True
    restricciones: list[dict[str, Any]] | None = None


class PeticionImportarHistorico(BaseModel):
    registros: list[dict[str, Any]]


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


@app.post("/api/diseno/analizar")
def analizar_diseno(req: PeticionAnalisisDiseno) -> dict[str, Any]:
    """
    Evalúa los 6 indicadores ponderados, optimiza especificaciones técnicas de construcción
    (sin SymPy en runtime) y genera los Casos Tipo referenciados al punto óptimo.
    """
    import time

    t_ini = time.perf_counter()
    pesos_limpios = diseno.normalizar_pesos(req.pesos)
    cbat_kg = max(0.0, float(req.cbat_kg))

    try:
        if req.ejecutar_optimizador:
            opt_res = diseno.optimizar_especificaciones(
                estado.valores,
                pesos=pesos_limpios,
                vars_libres=req.variables,
                cbat_kg=cbat_kg,
                respetar_limites=req.respetar_limites,
                restricciones=req.restricciones,
                base_overrides=req.base_overrides,
            )
        else:
            opt_res = diseno.optimizar_especificaciones(
                estado.valores,
                pesos=pesos_limpios,
                vars_libres=[],
                cbat_kg=cbat_kg,
                respetar_limites=req.respetar_limites,
                restricciones=req.restricciones,
                base_overrides=req.base_overrides,
            )
            opt_res["vars_optimizadas"] = list(
                req.variables if req.variables is not None else diseno.VARS_OPTIMIZABLES_DISENO
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    base_casos = (
        opt_res["entradas_optimo"]
        if req.usar_optimo_como_base and opt_res["encontrado"] and opt_res["entradas_optimo"] is not None
        else opt_res.get("entradas_actual", diseno.extraer_entradas_fijas(estado.valores))
    )
    casos_res = diseno.generar_casos_tipo(base_casos, pesos=pesos_limpios, cbat_kg=cbat_kg)
    tiempo_total_ms = round((time.perf_counter() - t_ini) * 1000.0, 2)

    return {
        **opt_res,
        "tiempo_opt_ms": opt_res["tiempo_ms"],
        "tiempo_total_ms": tiempo_total_ms,
        "casos_tipo": casos_res["casos"],
        "familias": casos_res["familias"],
        "referencia_score": casos_res["referencia_score"],
        "referencia_capas": casos_res["referencia_capas"],
        "indicadores_meta": diseno.INDICADORES_META,
        "variables_restriccion": diseno.VARIABLES_RESTRICCION,
        "catalogo_vars_constructivas": diseno.CATALOGO_VARS_CONSTRUCTIVAS,
        "pesos": pesos_limpios,
        "cbat_kg": cbat_kg,
        "anclas": diseno.ANCLAS_BASE,
        "requiere_cambio_fijas": set(modelo.FIJAS_INI) != estado.fijas,
    }


@app.get("/api/historico")
def listar_historico() -> dict[str, Any]:
    """Devuelve la lista de configuraciones e indicadores guardados manualmente."""
    return {"registros": diseno.cargar_historico()}


@app.post("/api/historico")
def guardar_en_historico(req: PeticionGuardarHistorico) -> dict[str, Any]:
    """Guarda manualmente una configuración y sus puntuaciones en `historico_disenos.json`."""
    entradas = (
        req.entradas
        if req.entradas is not None
        else diseno.extraer_entradas_fijas(estado.valores)
    )
    try:
        reg = diseno.guardar_registro_historico(
            nombre=req.nombre,
            nota=req.nota,
            origen=req.origen,
            entradas_fijas=entradas,
            pesos=req.pesos,
            cbat_kg=req.cbat_kg,
            restricciones=req.restricciones,
            respetar_limites=req.respetar_limites,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"registro": reg, "registros": diseno.cargar_historico()}


@app.delete("/api/historico/{item_id}")
def borrar_de_historico(item_id: str) -> dict[str, Any]:
    """Elimina un registro guardado del histórico manual por ID."""
    ok = diseno.eliminar_registro_historico(item_id)
    if not ok:
        raise HTTPException(status_code=404, detail=f"Registro '{item_id}' no encontrado en el histórico.")
    return {"eliminado": item_id, "registros": diseno.cargar_historico()}


@app.post("/api/historico/importar")
def importar_en_historico(req: PeticionImportarHistorico) -> dict[str, Any]:
    """Importa registros desde un JSON exportado previamente al histórico local."""
    try:
        registros = diseno.importar_historico(req.registros)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"registros": registros}


@app.post("/api/historico/{item_id}/reevaluar")
def reevaluar_de_historico(item_id: str) -> dict[str, Any]:
    """Crea un nuevo registro evaluado con el motor v2 a partir de un registro histórico archivado."""
    try:
        reg = diseno.reevaluar_registro_historico(item_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if reg is None:
        raise HTTPException(status_code=404, detail=f"Registro '{item_id}' no encontrado en el histórico.")
    return {"registro": reg, "registros": diseno.cargar_historico()}


# =============================================================
# Archivos estáticos del Frontend
# =============================================================
app.mount("/static", StaticFiles(directory=str(FRONTEND_DIR)), name="static")


@app.middleware("http")
async def desactivar_cache_estaticos(request: Request, call_next):
    """Evita que el navegador use copias antiguas en caché de JS/CSS/HTML tras cambios."""
    response = await call_next(request)
    if request.url.path == "/" or request.url.path.startswith("/static"):
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    return response


@app.get("/")
def servir_index() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "index.html")
