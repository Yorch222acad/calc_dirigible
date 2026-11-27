"""
Módulo puro de evaluación multi-criterio (sin SymPy en runtime) para:
  1. Indicadores técnicos ponderados y puntuación normalizada (0-100).
  2. Optimizador de especificaciones técnicas de construcción (en modo sin límites
     de hardware o con límites activos).
  3. Histórico manual persistente en JSON local (`historico_disenos.json`).
  4. Suite de Casos Tipo referenciados al punto óptimo hallado.
"""
from __future__ import annotations

import json
import math
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any

import evaluador
import modelo


HISTORICO_PATH = Path(__file__).resolve().parent / "historico_disenos.json"

CBAT_KG_DEFECTO = 750.0  # Bs/kg de batería LiPo cargada de repuesto (~5 Bs/Wh a 150 Wh/kg)

PESOS_DEFECTO: dict[str, float] = {
    "costo_operativo": 25.0,
    "costo_recambio": 20.0,
    "consumo_energetico": 15.0,
    "masa_elevable": 15.0,
    "autonomia": 15.0,
    "velocidad": 10.0,
}

INDICADORES_META: dict[str, dict[str, str]] = {
    "costo_operativo": {
        "nombre": "Costo operativo total",
        "corto": "Costo op.",
        "unidad": "Bs",
        "sentido": "menor",
        "descripcion": "Suma el precalentamiento en tierra (Cpre), el combustible consumido en vuelo (Ccomb) y la recarga eléctrica (Celec).",
    },
    "costo_recambio": {
        "nombre": "Costo recambio rápido (Comb. vs. Bat. repuesto)",
        "corto": "Recambio",
        "unidad": "Bs",
        "sentido": "menor",
        "descripcion": "Compara el cambio rápido de combustible (mp·ccomb) frente a disponer de otra batería cargada de repuesto (mbat·cbat_kg).",
    },
    "consumo_energetico": {
        "nombre": "Consumo energético total en vuelo",
        "corto": "Energía",
        "unidad": "kJ",
        "sentido": "menor",
        "descripcion": "Energía térmica aportada por combustible (Eprop) más energía eléctrica consumida (Eelec).",
    },
    "masa_elevable": {
        "nombre": "Capacidad de masa elevable",
        "corto": "Masa elev.",
        "unidad": "kg",
        "sentido": "mayor",
        "descripcion": "Carga útil máxima admisible cumpliendo potencia, empuje, inclinación (maniobra/crucero) y batería (permite redimensionar mbat ≤ mbmax en optimización; la ficha muestra capacidad con batería instalada fija).",
    },
    "autonomia": {
        "nombre": "Autonomía antes de recargar",
        "corto": "Autonomía",
        "unidad": "m",
        "sentido": "mayor",
        "descripcion": "Distancia máxima limitada por el primer recurso en agotarse (combustible a bordo mp o batería instalada mbat).",
    },
    "velocidad": {
        "nombre": "Velocidad neta de avance",
        "corto": "Velocidad",
        "unidad": "m/s",
        "sentido": "mayor",
        "descripcion": "Velocidad efectiva respecto al suelo vg = v − vv descontando el viento en contra.",
    },
}

CATALOGO_VARS_CONSTRUCTIVAS: dict[str, dict[str, Any]] = {
    "lam": {"label": "Esbeltez (λ)", "unidad": "adim", "factor": 1.0, "step": 0.05, "min": 1.4, "max": 6.0, "dec": 2, "entera": False, "por_defecto": True, "rango_opt": (1.52, 4.8)},
    "v": {"label": "Vel. aire (v)", "unidad": "m/s", "factor": 1.0, "step": 0.1, "min": 1.0, "max": 15.0, "dec": 2, "entera": False, "por_defecto": True, "rango_opt": (3.0, 12.5)},
    "mflot": {"label": "Aire cal. (mflot)", "unidad": "kg", "factor": 1.0, "step": 0.05, "min": 0.2, "max": 15.0, "dec": 3, "entera": False, "por_defecto": True, "rango_opt": (0.55, 6.8)},
    "e": {"label": "Celda Mylar (e)", "unidad": "mm", "factor": 1000.0, "step": 0.5, "min": 1.0, "max": 50.0, "dec": 1, "entera": False, "por_defecto": True, "rango_opt": (0.008, 0.032)},
    "T2": {"label": "Temp. gas (T₂)", "unidad": "°C", "factor": 1.0, "step": 1.0, "min": 30.0, "max": 150.0, "dec": 1, "entera": False, "por_defecto": True, "rango_opt": (55.0, 140.0)},
    "ncapS": {"label": "Capas sup. (ncapS)", "unidad": "capas", "factor": 1.0, "step": 1.0, "min": 0.0, "max": 6.0, "dec": 0, "entera": True, "por_defecto": True, "rango_opt": (1.0, 4.0)},
    "ncapI": {"label": "Capas inf. (ncapI)", "unidad": "capas", "factor": 1.0, "step": 1.0, "min": 0.0, "max": 6.0, "dec": 0, "entera": True, "por_defecto": True, "rango_opt": (0.0, 3.0)},
    "mp": {"label": "Combustible a bordo (mp)", "unidad": "g", "factor": 1000.0, "step": 5.0, "min": 5.0, "max": 1000.0, "dec": 1, "entera": False, "por_defecto": True, "rango_opt": (0.015, 0.500)},
    # Variables adicionales agregables dinámicamente desde el panel
    "W": {"label": "Ancho celda (W)", "unidad": "cm", "factor": 100.0, "step": 1.0, "min": 8.0, "max": 60.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (0.10, 0.45)},
    "xf": {"label": "Fracción nariz (xf)", "unidad": "adim", "factor": 1.0, "step": 0.01, "min": 0.22, "max": 0.48, "dec": 2, "entera": False, "por_defecto": False, "rango_opt": (0.25, 0.45)},
    "mcarga": {"label": "Carga útil (mcarga)", "unidad": "kg", "factor": 1.0, "step": 0.1, "min": 0.2, "max": 6.0, "dec": 2, "entera": False, "por_defecto": False, "rango_opt": (0.3, 4.0)},
    "nv": {"label": "Nº viajes (nv)", "unidad": "viajes", "factor": 1.0, "step": 1.0, "min": 1.0, "max": 15.0, "dec": 0, "entera": True, "por_defecto": False, "rango_opt": (1.0, 10.0)},
    "d1": {"label": "Distancia viaje (d1)", "unidad": "m", "factor": 1.0, "step": 20.0, "min": 50.0, "max": 2000.0, "dec": 0, "entera": False, "por_defecto": False, "rango_opt": (100.0, 1000.0)},
    "vv": {"label": "Viento en contra (vv)", "unidad": "m/s", "factor": 1.0, "step": 0.5, "min": 0.0, "max": 10.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (0.0, 8.0)},
    "N": {"label": "Nº motores (N)", "unidad": "motores", "factor": 1.0, "step": 1.0, "min": 2.0, "max": 8.0, "dec": 0, "entera": True, "por_defecto": False, "rango_opt": (2.0, 8.0)},
    "dp": {"label": "Diámetro hélice (dp)", "unidad": "cm", "factor": 100.0, "step": 0.5, "min": 15.0, "max": 45.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (0.18, 0.38)},
    "ep": {"label": "Espesor Mylar (ep)", "unidad": "µm", "factor": 1.0e6, "step": 1.0, "min": 4.0, "max": 40.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (5.0e-6, 25.0e-6)},
    "sigma": {"label": "Gramaje Mylar (σ)", "unidad": "g/m²", "factor": 1000.0, "step": 0.5, "min": 5.0, "max": 50.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (0.006, 0.035)},
    "eps": {"label": "Emisividad Mylar (ε)", "unidad": "adim", "factor": 1.0, "step": 0.01, "min": 0.02, "max": 0.95, "dec": 2, "entera": False, "por_defecto": False, "rango_opt": (0.03, 0.90)},
    "mad": {"label": "Masa adicional (mad)", "unidad": "kg", "factor": 1.0, "step": 0.05, "min": 0.3, "max": 4.0, "dec": 2, "entera": False, "por_defecto": False, "rango_opt": (0.5, 2.5)},
    "dTc": {"label": "Caída temp. adm. (dTc)", "unidad": "K", "factor": 1.0, "step": 1.0, "min": 5.0, "max": 40.0, "dec": 1, "entera": False, "por_defecto": False, "rango_opt": (10.0, 35.0)},
    "ncal": {"label": "Efic. calefactor (ncal)", "unidad": "adim", "factor": 1.0, "step": 0.02, "min": 0.4, "max": 0.95, "dec": 2, "entera": False, "por_defecto": False, "rango_opt": (0.55, 0.90)},
}

VARS_OPTIMIZABLES_DISENO = tuple(k for k, m in CATALOGO_VARS_CONSTRUCTIVAS.items() if m["por_defecto"])
_PRIMOS_HALTON = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79)
_ENTRADAS_KEYS = tuple(modelo.FIJAS_INI)

VARIABLES_RESTRICCION: dict[str, dict[str, Any]] = {
    "T2": {"nombre": "Temp. interna máxima (T2)", "unidad": "°C", "factor": 1.0, "op_def": "<=", "valor_def": 130.0, "paso": 1.0, "origen": "sol"},
    "mp": {"nombre": "Combustible a bordo (mp)", "unidad": "g", "factor": 1000.0, "op_def": "<=", "valor_def": 300.0, "paso": 10.0, "origen": "sol"},
    "mbat": {"nombre": "Masa de batería (mbat)", "unidad": "g", "factor": 1000.0, "op_def": "<=", "valor_def": 1000.0, "paso": 50.0, "origen": "sol"},
    "Pelec": {"nombre": "Potencia eléctrica (Pelec)", "unidad": "W", "factor": 1.0, "op_def": "<=", "valor_def": 640.0, "paso": 20.0, "origen": "sol"},
    "Ttot": {"nombre": "Empuje total (Ttot)", "unidad": "N", "factor": 1.0, "op_def": "<=", "valor_def": 22.0, "paso": 0.5, "origen": "sol"},
    "theta": {"nombre": "Inclinación motores (θ máx)", "unidad": "°", "factor": 1.0, "op_def": "<=", "valor_def": 75.0, "paso": 1.0, "origen": "sol"},
    "Fexc": {"nombre": "Empuje excedente (Fexc)", "unidad": "N", "factor": 1.0, "op_def": ">=", "valor_def": 0.0, "paso": 0.5, "origen": "sol"},
    "L": {"nombre": "Longitud del casco (L)", "unidad": "m", "factor": 1.0, "op_def": "<=", "valor_def": 6.5, "paso": 0.1, "origen": "sol"},
    "D": {"nombre": "Diámetro máximo (D)", "unidad": "m", "factor": 1.0, "op_def": "<=", "valor_def": 2.5, "paso": 0.1, "origen": "sol"},
    "V": {"nombre": "Volumen del casco (V)", "unidad": "m³", "factor": 1.0, "op_def": "<=", "valor_def": 25.0, "paso": 0.5, "origen": "sol"},
    "lam": {"nombre": "Relación esbeltez (λ)", "unidad": "adim", "factor": 1.0, "op_def": "<=", "valor_def": 3.5, "paso": 0.1, "origen": "sol"},
    "e": {"nombre": "Espesor celda Mylar (e)", "unidad": "mm", "factor": 1000.0, "op_def": "<=", "valor_def": 25.0, "paso": 1.0, "origen": "sol"},
    "mtot": {"nombre": "Masa total (mtot)", "unidad": "kg", "factor": 1.0, "op_def": "<=", "valor_def": 5.0, "paso": 0.1, "origen": "sol"},
    "mflot": {"nombre": "Carga al aire caliente (mflot)", "unidad": "kg", "factor": 1.0, "op_def": ">=", "valor_def": 2.0, "paso": 0.1, "origen": "sol"},
    "mc": {"nombre": "Masa película Mylar (mc)", "unidad": "g", "factor": 1000.0, "op_def": "<=", "valor_def": 1500.0, "paso": 50.0, "origen": "sol"},
    "Qp": {"nombre": "Potencia térmica perdida (Qp)", "unidad": "W", "factor": 1.0, "op_def": "<=", "valor_def": 1500.0, "paso": 25.0, "origen": "sol"},
    "mgm": {"nombre": "Combustible en vuelo (mgm)", "unidad": "g", "factor": 1000.0, "op_def": "<=", "valor_def": 50.0, "paso": 1.0, "origen": "sol"},
    "Cop": {"nombre": "Costo operativo (Cop)", "unidad": "Bs", "factor": 1.0, "op_def": "<=", "valor_def": 1.0, "paso": 0.05, "origen": "sol"},
    "c_recambio": {"nombre": "Costo recambio rápido", "unidad": "Bs", "factor": 1.0, "op_def": "<=", "valor_def": 400.0, "paso": 10.0, "origen": "crudo"},
    "Etot": {"nombre": "Consumo energético (Etot)", "unidad": "kJ", "factor": 0.001, "op_def": "<=", "valor_def": 500.0, "paso": 10.0, "origen": "sol"},
    "dm_aut": {"nombre": "Autonomía máxima", "unidad": "m", "factor": 1.0, "op_def": ">=", "valor_def": 840.0, "paso": 50.0, "origen": "crudo"},
    "vg": {"nombre": "Velocidad neta (vg)", "unidad": "m/s", "factor": 1.0, "op_def": ">=", "valor_def": 3.0, "paso": 0.2, "origen": "sol"},
}


def _valor_equipo_restriccion(rid: str, var_nom: str, datos: dict[str, float]) -> float | None:
    """Calcula el límite físico del equipo instalado para una restricción del grupo hardware."""
    if rid == "hw_mbat" or var_nom == "mbat":
        return float(datos.get("mbmax", 1.0)) * 1000.0
    if rid == "hw_Pelec" or var_nom == "Pelec":
        return float(datos.get("N", 4.0)) * float(datos.get("Pmax1", 160.0))
    if rid == "hw_Ttot" or var_nom == "Ttot":
        return float(datos.get("N", 4.0)) * float(datos.get("Tmax1", 5.5))
    if rid == "hw_theta" or var_nom == "theta":
        return float(datos.get("thmax", 75.0))
    if rid == "hw_Fexc" or var_nom == "Fexc":
        return 0.0
    return None


_HARDWARE_OP_FISICO: dict[str, str] = {
    "hw_mbat": "<=",
    "hw_Pelec": "<=",
    "hw_Ttot": "<=",
    "hw_theta": "<=",
    "hw_Fexc": ">=",
}
_HARDWARE_OP_POR_VAR: dict[str, str] = {
    "mbat": "<=",
    "Pelec": "<=",
    "Ttot": "<=",
    "theta": "<=",
    "Fexc": ">=",
}


def _op_hardware_fisico(rid: str, var_nom: str) -> str:
    if rid in _HARDWARE_OP_FISICO:
        return _HARDWARE_OP_FISICO[rid]
    return _HARDWARE_OP_POR_VAR.get(var_nom, str(VARIABLES_RESTRICCION[var_nom]["op_def"]))


def _op_efectivo_restriccion(r: dict[str, Any]) -> str:
    if r.get("grupo") == "hardware":
        return _op_hardware_fisico(str(r.get("id") or ""), str(r.get("variable") or ""))
    op = str(r.get("op") or "<=")
    return op if op in ("<=", ">=") else "<="


def restricciones_defecto(
    valores_base: dict[str, float] | None = None,
    activar_hardware: bool = True,
) -> list[dict[str, Any]]:
    """Lista inicial de restricciones: T2 <= 130 °C, mp <= 300 g y límites del hardware configurado activos por defecto."""
    base = valores_base or modelo.valores_iniciales()
    n_mot = float(base.get("N", 4.0))
    mbmax_g = round(float(base.get("mbmax", 1.0)) * 1000.0, 1)
    pmax_w = round(n_mot * float(base.get("Pmax1", 160.0)), 1)
    tmax_n = round(n_mot * float(base.get("Tmax1", 5.5)), 2)
    thmax_deg = round(float(base.get("thmax", 75.0)), 1)
    hw_act = bool(activar_hardware)
    return [
        {"id": "lim_T2", "variable": "T2", "op": "<=", "valor": 130.0, "activa": True, "grupo": "general", "usar_equipo": False, "tope_manual": None},
        {"id": "lim_mp", "variable": "mp", "op": "<=", "valor": 300.0, "activa": True, "grupo": "general", "usar_equipo": False, "tope_manual": None},
        {"id": "hw_mbat", "variable": "mbat", "op": "<=", "valor": mbmax_g, "activa": hw_act, "grupo": "hardware", "usar_equipo": hw_act, "tope_manual": None},
        {"id": "hw_Pelec", "variable": "Pelec", "op": "<=", "valor": pmax_w, "activa": hw_act, "grupo": "hardware", "usar_equipo": hw_act, "tope_manual": None},
        {"id": "hw_Ttot", "variable": "Ttot", "op": "<=", "valor": tmax_n, "activa": hw_act, "grupo": "hardware", "usar_equipo": hw_act, "tope_manual": None},
        {"id": "hw_theta", "variable": "theta", "op": "<=", "valor": thmax_deg, "activa": hw_act, "grupo": "hardware", "usar_equipo": hw_act, "tope_manual": None},
        {"id": "hw_Fexc", "variable": "Fexc", "op": ">=", "valor": 0.0, "activa": hw_act, "grupo": "hardware", "usar_equipo": hw_act, "tope_manual": None},
    ]


def normalizar_restricciones(
    restricciones: list[dict[str, Any]] | None,
    valores_base: dict[str, float] | None = None,
    respetar_limites: bool = True,
) -> list[dict[str, Any]]:
    """
    Limpia y valida las restricciones personalizadas enviadas por el cliente.
    Para las restricciones del grupo `hardware`, bloquea el operador en el sentido físico
    del equipo (`<=` para topes y `>=` para Fexc), separa `usar_equipo` de `tope_manual`
    y recalcula `valor` desde los parámetros actuales del equipo (`N·Pmax1`, `N·Tmax1`, `mbmax`, `thmax`).
    """
    if restricciones is None:
        return restricciones_defecto(valores_base, activar_hardware=respetar_limites)

    base_ref = valores_base or modelo.valores_iniciales()
    limpias: list[dict[str, Any]] = []
    for idx, raw in enumerate(restricciones):
        if not isinstance(raw, dict):
            continue
        var_nom = str(raw.get("variable") or "")
        if var_nom not in VARIABLES_RESTRICCION:
            continue
        meta = VARIABLES_RESTRICCION[var_nom]
        rid = str(raw.get("id") or f"lim_{idx}_{var_nom}")
        grupo = str(raw.get("grupo") or "custom")
        if grupo == "hardware":
            op = _op_hardware_fisico(rid, var_nom)
        else:
            op = str(raw.get("op") or meta["op_def"])
            if op not in ("<=", ">="):
                op = str(meta["op_def"])
        activa = bool(raw.get("activa", True))
        usar_equipo = bool(raw["usar_equipo"]) if "usar_equipo" in raw else (grupo == "hardware" and activa)

        tope_manual: float | None = None
        if raw.get("tope_manual") is not None and raw.get("tope_manual") != "":
            try:
                tm_f = float(raw["tope_manual"])
                if math.isfinite(tm_f):
                    tope_manual = round(tm_f, 4)
            except (TypeError, ValueError):
                tope_manual = None

        if grupo == "hardware":
            val_eq = _valor_equipo_restriccion(rid, var_nom, base_ref)
            val = float(val_eq if val_eq is not None else meta["valor_def"])
            if respetar_limites and activa:
                usar_equipo = True
        else:
            try:
                val = float(raw.get("valor", meta["valor_def"]))
            except (TypeError, ValueError):
                val = float(meta["valor_def"])
            if not math.isfinite(val):
                val = float(meta["valor_def"])

        limpias.append({
            "id": rid,
            "variable": var_nom,
            "op": op,
            "valor": round(val, 4),
            "activa": activa,
            "grupo": grupo,
            "usar_equipo": usar_equipo,
            "tope_manual": tope_manual,
        })
    return limpias


def _valor_restriccion(sol: dict[str, float], crudos: dict[str, Any], var_nom: str) -> float:
    meta = VARIABLES_RESTRICCION[var_nom]
    if meta["origen"] == "crudo":
        if var_nom == "c_recambio":
            return float(crudos["valores"]["costo_recambio"])
        if var_nom == "dm_aut":
            return float(crudos["valores"]["autonomia"])
    if var_nom == "Pelec":
        return max(float(sol["Pelec"]), float(sol.get("Pcruc", 0.0)))
    if var_nom == "Ttot":
        return max(float(sol["Ttot"]), float(sol.get("Tcruc", 0.0)))
    if var_nom == "theta":
        return max(float(sol["theta"]), float(sol.get("thcruc", 0.0)))
    return float(sol[var_nom]) * float(meta["factor"])


def _limite_efectivo_restriccion(
    r: dict[str, Any],
    sol: dict[str, float],
    base_fijas: dict[str, float] | None = None,
) -> float:
    """
    Devuelve el umbral numérico efectivo: para restricciones del equipo (`grupo == "hardware"`),
    calcula el límite actual desde `sol` (`N·Pmax1`, `N·Tmax1`, `mbmax`, `thmax`) y combina
    cualquier `tope_manual` tomando siempre la cota más restrictiva según el sentido físico.
    """
    if r.get("grupo") == "hardware":
        rid = str(r.get("id") or "")
        var_nom = str(r.get("variable") or "")
        lim_eq = _valor_equipo_restriccion(rid, var_nom, sol)
        tope_man = r.get("tope_manual")
        usar_eq = bool(r.get("usar_equipo", r.get("activa", True)))
        op_ef = _op_efectivo_restriccion(r)
        if usar_eq and lim_eq is not None:
            if tope_man is not None:
                tm_f = float(tope_man)
                return min(lim_eq, tm_f) if op_ef == "<=" else max(lim_eq, tm_f)
            return lim_eq
        if tope_man is not None:
            return float(tope_man)
        return float(lim_eq if lim_eq is not None else r["valor"])
    return float(r["valor"])


def _limites_efectivos_mapa(
    sol: dict[str, float],
    restricciones: list[dict[str, Any]] | None,
    base_fijas: dict[str, float] | None = None,
) -> dict[str, dict[str, float | None]]:
    """Consolida por variable las cotas activas más restrictivas separadas en `min` y `max`."""
    mapa: dict[str, dict[str, float | None]] = {}
    if not restricciones:
        return mapa
    for r in restricciones:
        if not r.get("activa", True):
            continue
        var_nom = str(r["variable"])
        op = _op_efectivo_restriccion(r)
        lim = _limite_efectivo_restriccion(r, sol, base_fijas)
        entrada = mapa.setdefault(var_nom, {"min": None, "max": None})
        if op == "<=":
            prev_max = entrada["max"]
            entrada["max"] = lim if prev_max is None else min(prev_max, lim)
        else:
            prev_min = entrada["min"]
            entrada["min"] = lim if prev_min is None else max(prev_min, lim)
    return mapa


def _cumple_restricciones(
    sol: dict[str, float],
    crudos: dict[str, Any],
    restricciones: list[dict[str, Any]],
    base_fijas: dict[str, float] | None = None,
) -> bool:
    for r in restricciones:
        if not r.get("activa", True):
            continue
        val = _valor_restriccion(sol, crudos, r["variable"])
        lim = _limite_efectivo_restriccion(r, sol, base_fijas)
        op = _op_efectivo_restriccion(r)
        if op == "<=" and val > lim + 1e-6:
            return False
        if op == ">=" and val < lim - 1e-6:
            return False
    return True


def _avisos_restricciones(
    sol: dict[str, float],
    crudos: dict[str, Any],
    restricciones: list[dict[str, Any]],
    base_fijas: dict[str, float] | None = None,
) -> list[str]:
    avisos: list[str] = []
    if sol["mp"] < sol["mgm"]:
        avisos.append(f"mp={sol['mp']*1000:.1f}g (< mgm={sol['mgm']*1000:.1f}g)")
    for r in restricciones:
        if not r.get("activa", True):
            continue
        meta = VARIABLES_RESTRICCION[r["variable"]]
        val = _valor_restriccion(sol, crudos, r["variable"])
        lim = _limite_efectivo_restriccion(r, sol, base_fijas)
        op = _op_efectivo_restriccion(r)
        if op == "<=" and val > lim + 1e-6:
            exc = val - lim
            avisos.append(f"{r['variable']}={val:.2f}{meta['unidad']} ({op} {lim:g}, exceso {exc:.2f}{meta['unidad']})")
        elif op == ">=" and val < lim - 1e-6:
            defic = lim - val
            avisos.append(f"{r['variable']}={val:.2f}{meta['unidad']} ({op} {lim:g}, déficit {defic:.2f}{meta['unidad']})")
    return avisos


def _violacion_candidato(
    sol: dict[str, float],
    crudos: dict[str, Any],
    restricciones: list[dict[str, Any]],
    base_fijas: dict[str, float] | None = None,
    vg_min_fisico: float = 0.35,
) -> float:
    """Calcula la violación normalizada acumulada (>= 0; exactamente 0 si cumple todo)."""
    viol = 0.0
    if sol["cf"] <= sol["R"]:
        viol += (sol["R"] - sol["cf"]) / max(0.1, sol["R"]) + 0.05
    if sol["cr"] <= sol["R"]:
        viol += (sol["R"] - sol["cr"]) / max(0.1, sol["R"]) + 0.05
    if sol["mres"] <= 0.05:
        viol += (0.05 - sol["mres"]) + 0.05
    if sol["vg"] <= vg_min_fisico:
        viol += (vg_min_fisico - sol["vg"]) + 0.05
    if sol["mp"] < sol["mgm"]:
        viol += (sol["mgm"] - sol["mp"]) / max(0.01, sol["mgm"])
    for r in restricciones:
        if not r.get("activa", True):
            continue
        val = _valor_restriccion(sol, crudos, r["variable"])
        lim = _limite_efectivo_restriccion(r, sol, base_fijas)
        op = _op_efectivo_restriccion(r)
        escala = max(1.0, abs(lim))
        if op == "<=" and val > lim + 1e-6:
            viol += (val - lim) / escala
        elif op == ">=" and val < lim - 1e-6:
            viol += (lim - val) / escala
    return viol


def _halton(indice: int, base: int) -> float:
    f = 1.0
    r = 0.0
    i = indice
    while i > 0:
        f /= base
        r += f * (i % base)
        i //= base
    return r


def normalizar_pesos(pesos: dict[str, float] | None) -> dict[str, float]:
    """Limpia y garantiza pesos no negativos para los 6 indicadores."""
    out: dict[str, float] = {}
    for k, v_def in PESOS_DEFECTO.items():
        try:
            val = float((pesos or {}).get(k, v_def))
        except (TypeError, ValueError):
            val = v_def
        out[k] = max(0.0, val) if math.isfinite(val) else v_def
    if sum(out.values()) <= 1e-9:
        return dict(PESOS_DEFECTO)
    return out


def extraer_entradas_fijas(valores: dict[str, Any]) -> dict[str, float]:
    """Proyecta un diccionario completo o parcial al conjunto exacto de 62 entradas FIJAS_INI."""
    ini = modelo.valores_iniciales()
    return {k: float(valores.get(k, ini[k])) for k in _ENTRADAS_KEYS}


def _validar_entradas_fijas_diseno(entradas: dict[str, float]) -> None:
    """Valida el dominio físico estricto de las entradas fijas antes de evaluar o optimizar."""
    for k, v in entradas.items():
        if not modelo._es_valida_float(k, float(v)):
            raise ValueError(f"Valor fuera de dominio físico para '{k}' ({v}).")
    if entradas["N"] < 1.0 or abs(entradas["N"] - round(entradas["N"])) > 1e-7:
        raise ValueError(f"El número de motores N debe ser un entero >= 1 (recibido {entradas['N']}).")
    if entradas["ncapS"] < 0.0 or abs(entradas["ncapS"] - round(entradas["ncapS"])) > 1e-7:
        raise ValueError(f"ncapS debe ser un entero >= 0 (recibido {entradas['ncapS']}).")
    if entradas["ncapI"] < 0.0 or abs(entradas["ncapI"] - round(entradas["ncapI"])) > 1e-7:
        raise ValueError(f"ncapI debe ser un entero >= 0 (recibido {entradas['ncapI']}).")
    dT_base = float(entradas["T2"]) - float(entradas["T1"])
    if dT_base <= 0.0:
        raise ValueError(
            f"El gradiente térmico T2 - T1 debe ser positivo (T1={entradas['T1']}, T2={entradas['T2']})."
        )
    if float(entradas["dTc"]) >= dT_base:
        raise ValueError(
            f"La caída admisible dTc ({entradas['dTc']}) debe ser menor que dT = T2 - T1 ({dT_base:g})."
        )
    vg_base = float(entradas["v"]) - float(entradas["vv"])
    if vg_base <= 0.0:
        raise ValueError(
            f"La velocidad neta de avance vg = v - vv debe ser positiva "
            f"(v={entradas['v']} m/s, vv={entradas['vv']} m/s, vg={vg_base:g} m/s)."
        )


def _metricas_indicadores_crudos(
    sol: dict[str, float],
    cbat_kg: float,
    restricciones: list[dict[str, Any]] | None = None,
    incluir_rango_fijo: bool = True,
) -> dict[str, Any]:
    cop = float(sol["Cop"])
    dm = float(sol["dm"])
    d1 = float(sol["d1"])
    if dm <= 0.0 or d1 <= 0.0:
        raise ValueError(f"La distancia de misión debe ser positiva (dm={dm}, d1={d1}).")

    mp = float(sol["mp"])
    ccomb = float(sol["ccomb"])
    mbat = float(sol["mbat"])
    c_rec_comb = mp * ccomb
    c_bat_rep = mbat * max(0.0, float(cbat_kg))
    c_recambio = c_rec_comb + c_bat_rep

    etot_kj = float(sol["Etot"]) / 1000.0
    eprop_kj = float(sol["Eprop"]) / 1000.0
    eelec_kj = float(sol["Eelec"]) / 1000.0

    mcarga = float(sol["mcarga"])
    fexc = float(sol["Fexc"])
    g = float(sol["g"])
    mflot = float(sol["mflot"])
    mtot = float(sol["mtot"])
    thcruc = float(sol.get("thcruc", math.degrees(math.atan2(sol["FD"], sol["mres"] * g)) if sol["mres"] > 0.0 else 90.0))

    lim_map = _limites_efectivos_mapa(sol, restricciones)
    rango_redim = evaluador.evaluar_rango_carga_mision(
        sol, redimensionar_bateria=True, mres_min=0.05, limites_efectivos=lim_map, cbat_kg=cbat_kg,
    )
    capacidad_redim_kg = float(rango_redim["mcarga_max"]) if rango_redim["factible"] else 0.0

    if incluir_rango_fijo:
        rango_fijo = evaluador.evaluar_rango_carga_mision(
            sol, redimensionar_bateria=False, mres_min=1e-4, limites_efectivos=lim_map, cbat_kg=cbat_kg,
        )
        capacidad_util_kg = float(rango_fijo["mcarga_max"]) if rango_fijo["factible"] else 0.0
        mcarga_min_kg = float(rango_fijo["mcarga_min"]) if rango_fijo["factible"] else 0.0
        carga_factible_inst = bool(rango_fijo["factible"])
        limitante_carga = str(rango_fijo["limitante_max"])
        diag_fases = evaluador.diagnosticar_fases_y_limites(sol, limites_efectivos=lim_map)
    else:
        capacidad_util_kg = capacidad_redim_kg
        mcarga_min_kg = float(rango_redim["mcarga_min"]) if rango_redim["factible"] else 0.0
        carga_factible_inst = bool(rango_redim["factible"])
        limitante_carga = str(rango_redim["limitante_max"])
        diag_fases = {"fase_limitante": "Maniobra", "componente_limitante": "Potencia eléctrica"}

    mgm = max(1e-9, float(sol["mgm"]))
    mbe = max(1e-9, float(sol["mbe"]))
    dm_aut_comb = dm * (mp / mgm)
    dm_aut_bat = dm * (mbat / mbe)
    dm_aut = min(dm_aut_comb, dm_aut_bat)
    nv_aut = dm_aut / d1
    limitante_aut = "Batería" if dm_aut_bat <= dm_aut_comb else "Combustible"

    vg = float(sol["vg"])

    return {
        "valores": {
            "costo_operativo": cop,
            "costo_recambio": c_recambio,
            "consumo_energetico": etot_kj,
            "masa_elevable": capacidad_redim_kg,
            "autonomia": dm_aut,
            "velocidad": vg,
        },
        "desglose": {
            "Cpre": float(sol["Cpre"]),
            "Ccomb": float(sol["Ccomb"]),
            "Celec": float(sol["Celec"]),
            "cop_por_km": cop / (dm / 1000.0),
            "c_rec_comb": c_rec_comb,
            "c_bat_rep": c_bat_rep,
            "pct_bateria_recambio": (100.0 * c_bat_rep / c_recambio) if c_recambio > 1e-9 else 0.0,
            "ratio_bat_comb": c_bat_rep / max(0.05, c_rec_comb),
            "Eprop_kj": eprop_kj,
            "Eelec_kj": eelec_kj,
            "mgm_g": float(sol["mgm"]) * 1000.0,
            "Ereq_wh": float(sol["Ereq"]),
            "capacidad_util_kg": capacidad_util_kg,
            "mcarga_min_kg": mcarga_min_kg,
            "capacidad_redim_kg": capacidad_redim_kg,
            "mcarga_min_redim_kg": float(rango_redim["mcarga_min"]) if rango_redim["factible"] else 0.0,
            "carga_factible_instalada": carga_factible_inst,
            "limitante_carga": limitante_carga,
            "limitante_carga_redim": str(rango_redim["limitante_max"]),
            "thcruc_deg": thcruc,
            "fase_limitante": str(diag_fases["fase_limitante"]),
            "componente_limitante": str(diag_fases["componente_limitante"]),
            "fexc_N": fexc,
            "mcarga_kg": mcarga,
            "mflot_kg": mflot,
            "mtot_kg": mtot,
            "mres_kg": float(sol["mres"]),
            "frac_aire_pct": 100.0 * mflot / max(1e-6, mtot),
            "dm_aut_m": dm_aut,
            "nv_aut": nv_aut,
            "dm_aut_comb_m": dm_aut_comb,
            "dm_aut_bat_m": dm_aut_bat,
            "limitante_aut": limitante_aut,
            "vg_ms": vg,
            "v_ms": float(sol["v"]),
            "tm_s": float(sol["tm"]),
        },
    }


def _calcular_anclas_base() -> dict[str, float]:
    base_ini = modelo.valores_iniciales()
    sol_ini = evaluador.evaluar_punto(base_ini, estricto_prolado=False)
    assert sol_ini is not None
    crudos = _metricas_indicadores_crudos(sol_ini, CBAT_KG_DEFECTO, incluir_rango_fijo=False)
    anclas = {k: max(1e-6, float(v)) for k, v in crudos["valores"].items()}
    if crudos["valores"]["masa_elevable"] <= 1e-6:
        anclas["masa_elevable"] = max(1.0, float(sol_ini["mcarga"]))
    return anclas


ANCLAS_BASE: dict[str, float] = _calcular_anclas_base()


def _avisos_hardware(
    sol: dict[str, float],
    restricciones: list[dict[str, Any]] | None = None,
) -> list[str]:
    avisos: list[str] = []
    lim_map = _limites_efectivos_mapa(sol, restricciones)
    mb_u = lim_map.get("mbat", {}).get("max")
    p_u = lim_map.get("Pelec", {}).get("max")
    t_u = lim_map.get("Ttot", {}).get("max")
    th_u = lim_map.get("theta", {}).get("max")
    f_l = lim_map.get("Fexc", {}).get("min")

    mbmax_base = sol["mbmax"] * 1000.0
    pmax_base = sol["Pmax"]
    tmax_base = sol["N"] * sol["Tmax1"]
    thmax_base = sol["thmax"]

    mbmax_g = min(mbmax_base, mb_u) if mb_u is not None else mbmax_base
    pmax_w = min(pmax_base, p_u) if p_u is not None else pmax_base
    tmax_tot = min(tmax_base, t_u) if t_u is not None else tmax_base
    thmax_deg = min(thmax_base, th_u) if th_u is not None else thmax_base
    fexc_min = max(0.0, f_l) if f_l is not None else 0.0

    mbat_g = sol["mbat"] * 1000.0
    if mbat_g > mbmax_g + 1e-6:
        avisos.append(f"mbat={mbat_g:.0f}g > {mbmax_g:.0f}g (+{mbat_g - mbmax_g:.0f}g)")
    if sol["Pelec"] > pmax_w + 1e-6:
        avisos.append(f"Pelec={sol['Pelec']:.1f}W > {pmax_w:.1f}W (déficit {sol['Pelec'] - pmax_w:.1f}W)")
    if sol["Pcruc"] > pmax_w + 1e-6:
        avisos.append(f"Pcruc={sol['Pcruc']:.1f}W > {pmax_w:.1f}W (déficit {sol['Pcruc'] - pmax_w:.1f}W)")
    if sol["Ttot"] > tmax_tot + 1e-6:
        avisos.append(f"Ttot={sol['Ttot']:.1f}N > {tmax_tot:.1f}N (+{sol['Ttot'] - tmax_tot:.1f}N)")
    if sol["Tcruc"] > tmax_tot + 1e-6:
        avisos.append(f"Tcruc={sol['Tcruc']:.1f}N > {tmax_tot:.1f}N (+{sol['Tcruc'] - tmax_tot:.1f}N)")
    if sol["theta"] > thmax_deg + 1e-6:
        avisos.append(f"θman={sol['theta']:.1f}° > {thmax_deg:.1f}°")
    thcruc = float(sol.get("thcruc", 0.0))
    if thcruc > thmax_deg + 1e-6:
        avisos.append(f"θcruc={thcruc:.1f}° > {thmax_deg:.1f}°")
    if sol["Fexc"] < fexc_min - 1e-6:
        avisos.append(f"Fexc={sol['Fexc']:.1f}N < {fexc_min:.1f}N")
    if sol["mp"] < sol["mgm"] - 1e-9:
        avisos.append(f"mp={sol['mp']*1000:.1f}g < mgm={sol['mgm']*1000:.1f}g")
    return avisos


def extraer_especificaciones(sol: dict[str, float], crudos: dict[str, Any]) -> dict[str, float | str]:
    """Extrae los parámetros técnicos clave de construcción para ficha técnica y tabla de casos tipo."""
    d = crudos["desglose"]
    return {
        "L": round(float(sol["L"]), 3),
        "D": round(float(sol["D"]), 3),
        "R": round(float(sol["R"]), 3),
        "cf": round(float(sol["cf"]), 3),
        "cr": round(float(sol["cr"]), 3),
        "lam": round(float(sol["lam"]), 2),
        "V": round(float(sol["V"]), 2),
        "Vnuc": round(float(sol["Vnuc"]), 2),
        "Vcel": round(float(sol["Vcel"]), 2),
        "S": round(float(sol["S"]), 2),
        "ncapS": round(float(sol["ncapS"]), 1),
        "ncapI": round(float(sol["ncapI"]), 1),
        "e_mm": round(float(sol["e"]) * 1000.0, 1),
        "W_cm": round(float(sol["W"]) * 100.0, 1),
        "ep_um": round(float(sol["ep"]) * 1.0e6, 1),
        "sigma_gm2": round(float(sol["sigma"]) * 1000.0, 1),
        "eps": round(float(sol["eps"]), 3),
        "Sc": round(float(sol["Sc"]), 2),
        "mc_g": round(float(sol["mc"]) * 1000.0, 1),
        "T1": round(float(sol["T1"]), 1),
        "T2": round(float(sol["T2"]), 1),
        "Qp_w": round(float(sol["Qp"]), 1),
        "U": round(float(sol["U"]), 3),
        "fais_pct": round(float(sol["fais"]) * 100.0, 1),
        "Epre_kj": round(float(sol["Epre"]) / 1000.0, 1),
        "mgm_g": round(float(sol["mgm"]) * 1000.0, 2),
        "mp_g": round(float(sol["mp"]) * 1000.0, 1),
        "tc_s": round(float(sol["tc"]), 1),
        "dTc": round(float(sol["dTc"]), 1),
        "v": round(float(sol["v"]), 2),
        "vv": round(float(sol["vv"]), 2),
        "vg": round(float(sol["vg"]), 2),
        "tm_s": round(float(sol["tm"]), 3) if float(sol["tm"]) < 10.0 else round(float(sol["tm"]), 1),
        "dm": round(float(sol["dm"]), 3) if float(sol["dm"]) < 10.0 else round(float(sol["dm"]), 1),
        "nv": round(float(sol["nv"]), 2),
        "mflot": round(float(sol["mflot"]), 3),
        "mres": round(float(sol["mres"]), 3),
        "mcarga": round(float(sol["mcarga"]), 2),
        "mtot": round(float(sol["mtot"]), 3),
        "frac_aire_pct": round(float(d["frac_aire_pct"]), 1),
        "capacidad_util_kg": float(d["capacidad_util_kg"]),
        "mcarga_min_kg": float(d["mcarga_min_kg"]),
        "capacidad_redim_kg": float(d["capacidad_redim_kg"]),
        "mcarga_min_redim_kg": float(d["mcarga_min_redim_kg"]),
        "carga_factible_instalada": bool(d["carga_factible_instalada"]),
        "limitante_carga": str(d["limitante_carga"]),
        "limitante_carga_redim": str(d["limitante_carga_redim"]),
        "FD": round(float(sol["FD"]), 2),
        "Ttot": round(float(sol["Ttot"]), 2),
        "Tcruc": round(float(sol["Tcruc"]), 2),
        "theta": round(float(sol["theta"]), 1),
        "thcruc": round(float(d["thcruc_deg"]), 1),
        "Pelec": round(float(sol["Pelec"]), 1),
        "Pcruc": round(float(sol["Pcruc"]), 1),
        "Ptot": round(float(sol["Ptot"]), 1),
        "fase_limitante": str(d["fase_limitante"]),
        "componente_limitante": str(d["componente_limitante"]),
        "mbat_g": round(float(sol["mbat"]) * 1000.0, 1),
        "Ereq_wh": round(float(sol["Ereq"]), 2),
        "Etot_kj": round(float(sol["Etot"]) / 1000.0, 1),
        "Eprop_kj": round(float(d["Eprop_kj"]), 1),
        "Eelec_kj": round(float(d["Eelec_kj"]), 1),
        "Cop": round(float(sol["Cop"]), 3),
        "Cpre": round(float(sol["Cpre"]), 3),
        "Ccomb": round(float(sol["Ccomb"]), 3),
        "Celec": round(float(sol["Celec"]), 3),
        "cop_por_km": round(float(d["cop_por_km"]), 3),
        "cop_por_viaje": round(float(sol["Cop"]) / max(1e-6, float(sol["nv"])), 3),
        "pct_cpre": round(100.0 * float(sol["Cpre"]) / max(1e-9, float(sol["Cop"])), 1),
        "pct_ccomb": round(100.0 * float(sol["Ccomb"]) / max(1e-9, float(sol["Cop"])), 1),
        "pct_celec": round(100.0 * float(sol["Celec"]) / max(1e-9, float(sol["Cop"])), 1),
        "c_rec_comb": round(float(d["c_rec_comb"]), 2),
        "c_bat_rep": round(float(d["c_bat_rep"]), 2),
        "c_recambio": round(float(crudos["valores"]["costo_recambio"]), 2),
        "pct_bateria_recambio": round(float(d["pct_bateria_recambio"]), 1),
        "ratio_bat_comb": round(float(d["ratio_bat_comb"]), 1),
        "dm_aut": round(float(d["dm_aut_m"]), 0),
        "nv_aut": round(float(d["nv_aut"]), 1),
        "limitante_aut": str(d["limitante_aut"]),
    }


def evaluar_indicadores(
    sol: dict[str, float],
    pesos: dict[str, float] | None = None,
    cbat_kg: float = CBAT_KG_DEFECTO,
    anclas: dict[str, float] | None = None,
    crudos: dict[str, Any] | None = None,
    restricciones: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Calcula puntuaciones individuales (0-100), score ponderado y ficha técnica."""
    pesos_limpios = normalizar_pesos(pesos)
    refs = anclas or ANCLAS_BASE
    crudos_calc = crudos if crudos is not None else _metricas_indicadores_crudos(sol, cbat_kg, restricciones=restricciones)
    vals = crudos_calc["valores"]

    scores: dict[str, float] = {}
    suma_ponderada = 0.0
    suma_pesos = sum(pesos_limpios.values())

    for key, meta in INDICADORES_META.items():
        val = float(vals[key])
        ref = max(1e-6, float(refs.get(key, ANCLAS_BASE[key])))
        if meta["sentido"] == "menor":
            sc = 100.0 / (1.0 + (max(0.0, val) / ref) ** 1.35)
        else:
            sc = 100.0 / (1.0 + (ref / max(1e-6, val)) ** 1.35) if val > 0.0 else 0.0
        scores[key] = round(sc, 2)
        suma_ponderada += pesos_limpios[key] * sc

    score_total = round(suma_ponderada / max(1e-9, suma_pesos), 2)
    avisos = _avisos_hardware(sol, restricciones=restricciones)
    cumple_restr = True if restricciones is None else _cumple_restricciones(sol, crudos_calc, restricciones)
    valido_hw = bool(sol.get("valido", False)) and cumple_restr and not avisos

    _SIN_RETRUNC = {"capacidad_util_kg", "mcarga_min_kg", "capacidad_redim_kg", "mcarga_min_redim_kg"}
    return {
        "score_total": score_total,
        "scores": scores,
        "indicadores": {
            k: (float(v) if k == "masa_elevable" else round(float(v), 4))
            for k, v in vals.items()
        },
        "desglose": {
            k: (
                float(v)
                if k in _SIN_RETRUNC
                else (round(float(v), 4) if isinstance(v, (int, float)) and not isinstance(v, bool) else v)
            )
            for k, v in crudos_calc["desglose"].items()
        },
        "especificaciones": extraer_especificaciones(sol, crudos_calc),
        "avisos": avisos,
        "valido_hardware": valido_hw,
    }


def _evaluar_score_candidato(
    base_fijas: dict[str, float],
    ov: dict[str, float],
    pesos_limpios: dict[str, float],
    cbat_kg: float,
    restricciones: list[dict[str, Any]],
) -> tuple[float, dict[str, float], dict[str, Any]] | None:
    sol = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, **ov)
    if sol is None:
        return None
    if sol["cf"] <= sol["R"] or sol["cr"] <= sol["R"] or sol["mres"] <= 0.05 or sol["vg"] <= 0.35 or sol["mp"] < sol["mgm"]:
        return None
    # Verificar primero las restricciones directas sobre `sol` sin lanzar bisecciones innecesarias
    restr_directas = [r for r in restricciones if VARIABLES_RESTRICCION[r["variable"]]["origen"] != "crudo"]
    if not _cumple_restricciones(sol, {}, restr_directas, base_fijas=base_fijas):
        return None
    crudos = _metricas_indicadores_crudos(sol, cbat_kg, restricciones=restricciones, incluir_rango_fijo=False)
    if not _cumple_restricciones(sol, crudos, restricciones, base_fijas=base_fijas):
        return None
    ev = evaluar_indicadores(sol, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos, restricciones=restricciones)
    return ev["score_total"], sol, ev


def optimizar_especificaciones(
    valores_base: dict[str, float],
    pesos: dict[str, float] | None = None,
    vars_libres: list[str] | None = None,
    cbat_kg: float = CBAT_KG_DEFECTO,
    respetar_limites: bool = True,
    restricciones: list[dict[str, Any]] | None = None,
    base_overrides: dict[str, float] | None = None,
) -> dict[str, Any]:
    """
    Optimizador multi-criterio sobre el evaluador rápido (`evaluador.py`, 0 SymPy)
    que maximiza la puntuación compuesta ponderada de los 6 indicadores respetando
    las restricciones activas configuradas por el usuario.
    """
    t0 = time.perf_counter()
    pesos_limpios = normalizar_pesos(pesos)
    base_fijas = extraer_entradas_fijas(valores_base)
    if base_overrides:
        for k, v in base_overrides.items():
            if k in _ENTRADAS_KEYS:
                try:
                    vf = float(v)
                    if math.isfinite(vf):
                        base_fijas[k] = vf
                except (TypeError, ValueError):
                    pass

    restr_limpias = normalizar_restricciones(
        restricciones, base_fijas, respetar_limites=respetar_limites
    )
    hw_activo = any(r["grupo"] == "hardware" and r["activa"] for r in restr_limpias)

    if vars_libres is None:
        elegidas = list(VARS_OPTIMIZABLES_DISENO)
    else:
        elegidas = list(dict.fromkeys(v for v in vars_libres if v in CATALOGO_VARS_CONSTRUCTIVAS))
    elegidas_canon = sorted(elegidas)

    _validar_entradas_fijas_diseno(base_fijas)
    sol_actual = evaluador.evaluar_punto(base_fijas, estricto_prolado=False)
    if sol_actual is None:
        raise ValueError("El estado base indicado no pudo evaluarse físicamente.")
    crudos_actual = _metricas_indicadores_crudos(sol_actual, cbat_kg, restricciones=restr_limpias, incluir_rango_fijo=True)
    ev_actual = evaluar_indicadores(sol_actual, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos_actual, restricciones=restr_limpias)
    avisos_restr_act = _avisos_restricciones(
        sol_actual, crudos_actual, restr_limpias, base_fijas=base_fijas
    )

    xf = base_fijas["xf"]
    lam_min = max(1.52, (0.5 / max(0.05, min(xf, 1.0 - xf))) * 1.06)
    v_min = 3.0 if "vv" in elegidas_canon else max(base_fijas["vv"] + 0.8, 3.0)
    v_max = min(base_fijas["vpitch"] * 0.89, 12.5)
    if v_max <= v_min + 0.5:
        v_max = min(base_fijas["vpitch"] * 0.94, v_min + 2.0)

    mtot_ref = sol_actual["mtot"]
    limites: dict[str, tuple[float, float]] = {}
    for vn in elegidas_canon:
        if vn == "lam":
            limites[vn] = (lam_min, 4.8)
        elif vn == "v":
            limites[vn] = (v_min, v_max)
        elif vn == "mflot":
            limites[vn] = (max(0.55, 0.30 * mtot_ref), max(6.8, 1.85 * mtot_ref))
        elif vn == "T2":
            limites[vn] = (max(base_fijas["T1"] + 35.0, 55.0), 140.0)
        elif vn == "mp":
            limites[vn] = (max(0.015, sol_actual["mgm"] * 0.7), max(0.500, base_fijas["mp"] * 1.6))
        else:
            rango_def = CATALOGO_VARS_CONSTRUCTIVAS[vn]["rango_opt"]
            val_act_vn = float(base_fijas[vn])
            limites[vn] = (min(float(rango_def[0]), val_act_vn), max(float(rango_def[1]), val_act_vn))

    # Acotar rangos de búsqueda según restricciones activas sobre variables libres
    for r in restr_limpias:
        if not r.get("activa", True):
            continue
        vn = r["variable"]
        if vn not in limites:
            continue
        meta = VARIABLES_RESTRICCION[vn]
        thr = float(_limite_efectivo_restriccion(r, sol_actual, base_fijas)) / float(meta["factor"])
        lo, hi = limites[vn]
        if _op_efectivo_restriccion(r) == "<=":
            hi = min(hi, thr)
        else:
            lo = max(lo, thr)
        limites[vn] = (lo, hi)

    conflicto = next(
        (f"{vn} ({lo:.3g} > {hi:.3g})" for vn, (lo, hi) in limites.items() if lo > hi + 1e-9),
        None,
    )
    if conflicto is not None:
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "encontrado": False,
            "mensaje_error": f"Rango imposible en restricciones para {conflicto}.",
            "tiempo_ms": dt_ms,
            "evaluaciones": 1,
            "evaluaciones_validas": 0,
            "actual": ev_actual,
            "entradas_actual": base_fijas,
            "avisos_restricciones_actual": avisos_restr_act,
            "optimo": None,
            "entradas_optimo": None,
            "mejora_score": 0.0,
            "cambios": {},
            "vars_optimizadas": elegidas,
            "respetar_limites": hw_activo,
            "restricciones": restr_limpias,
        }

    evaluaciones = 0
    candidatos: list[tuple[float, dict[str, float], dict[str, float], dict[str, Any]]] = []
    infactibles: list[tuple[float, float, dict[str, float], dict[str, float], dict[str, Any]]] = []

    def _evaluar_con_viol(ov_cand: dict[str, float]) -> tuple[float, float, dict[str, float], dict[str, Any]] | None:
        sol_c = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, **ov_cand)
        if sol_c is None:
            return None
        crudos_c = _metricas_indicadores_crudos(
            sol_c, cbat_kg, restricciones=restr_limpias, incluir_rango_fijo=False
        )
        ev_c = evaluar_indicadores(
            sol_c, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos_c, restricciones=restr_limpias
        )
        viol_c = _violacion_candidato(
            sol_c,
            crudos_c,
            restr_limpias,
            base_fijas=base_fijas,
            vg_min_fisico=(0.35 if elegidas_canon else 0.0),
        )
        return viol_c, ev_c["score_total"], sol_c, ev_c

    ov_actual = {v: float(sol_actual[v]) for v in elegidas_canon}
    en_rango_act = all(
        (limites[v][0] - 1e-9 <= ov_actual[v] <= limites[v][1] + 1e-9)
        for v in elegidas_canon
    )
    evaluaciones += 1
    if en_rango_act:
        res_act = _evaluar_con_viol(ov_actual)
        if res_act is not None:
            v_a, sc_a, s_sol, s_ev = res_act
            if v_a == 0.0:
                candidatos.append((sc_a, ov_actual, s_sol, s_ev))
            else:
                infactibles.append((v_a, sc_a, ov_actual, s_sol, s_ev))

    if elegidas_canon:
        n_muestras = 1200
        for idx in range(1, n_muestras + 1):
            ov: dict[str, float] = {}
            for dim, v_nom in enumerate(elegidas_canon):
                lo, hi = limites[v_nom]
                u = _halton(idx, _PRIMOS_HALTON[dim % len(_PRIMOS_HALTON)])
                val = lo + u * (hi - lo)
                if CATALOGO_VARS_CONSTRUCTIVAS[v_nom].get("entera"):
                    val = float(round(val))
                ov[v_nom] = val
            if "ncapS" in ov and "ncapI" in ov and ov["ncapI"] > ov["ncapS"]:
                ov["ncapI"] = ov["ncapS"]
            res = _evaluar_con_viol(ov)
            evaluaciones += 1
            if res is not None:
                v_c, sc, s_sol, s_ev = res
                if v_c == 0.0:
                    candidatos.append((sc, ov, s_sol, s_ev))
                else:
                    infactibles.append((v_c, sc, ov, s_sol, s_ev))

    # Fase 1 de factibilidad: si el muestreo inicial no tocó la región factible,
    # descender desde los mejores puntos menos violadores hasta cumplir todas las restricciones.
    if not candidatos and elegidas_canon and infactibles:
        infactibles.sort(key=lambda x: (x[0], -x[1]))
        for v_ini, sc_ini, ov_ini, sol_ini, ev_ini in infactibles[:6]:
            curr_v, curr_sc = v_ini, sc_ini
            curr_ov = dict(ov_ini)
            curr_sol, curr_ev = sol_ini, ev_ini
            for frac in (0.15, 0.08, 0.04, 0.015, 0.005):
                for _ in range(3):
                    mejoro = False
                    for var_nom in elegidas_canon:
                        lo, hi = limites[var_nom]
                        if CATALOGO_VARS_CONSTRUCTIVAS[var_nom].get("entera"):
                            deltas = (-1.0, 1.0)
                        else:
                            paso = frac * (hi - lo)
                            deltas = (-paso, paso)
                        for delta in deltas:
                            cand_x = curr_ov[var_nom] + delta
                            if cand_x < lo or cand_x > hi:
                                continue
                            cand_ov = dict(curr_ov)
                            cand_ov[var_nom] = cand_x
                            if "ncapS" in cand_ov and "ncapI" in cand_ov and cand_ov["ncapI"] > cand_ov["ncapS"]:
                                continue
                            res = _evaluar_con_viol(cand_ov)
                            evaluaciones += 1
                            if res is not None:
                                nv, nsc, nsol, nev = res
                                if nv < curr_v - 1e-7 or (nv == 0.0 and curr_v == 0.0 and nsc > curr_sc + 1e-5):
                                    curr_v, curr_sc, curr_ov, curr_sol, curr_ev = nv, nsc, cand_ov, nsol, nev
                                    mejoro = True
                                    break
                    if not mejoro:
                        break
            if curr_v == 0.0:
                candidatos.append((curr_sc, curr_ov, curr_sol, curr_ev))

    if not candidatos:
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "encontrado": False,
            "mensaje_error": (
                "Ninguna combinación cumplió simultáneamente todas las restricciones activas."
                if elegidas_canon
                else "La configuración fija actual no cumple todas las restricciones activas."
            ),
            "tiempo_ms": dt_ms,
            "evaluaciones": evaluaciones,
            "evaluaciones_validas": 0,
            "actual": ev_actual,
            "entradas_actual": base_fijas,
            "avisos_restricciones_actual": avisos_restr_act,
            "optimo": None,
            "entradas_optimo": None,
            "mejora_score": 0.0,
            "cambios": {},
            "vars_optimizadas": elegidas,
            "respetar_limites": hw_activo,
            "restricciones": restr_limpias,
        }

    candidatos.sort(key=lambda x: x[0], reverse=True)
    mejor_sc, mejor_ov, mejor_sol, mejor_ev = candidatos[0]

    if elegidas_canon:
        for _, ov_ini, sol_ini, ev_ini in candidatos[:8]:
            curr_sc = ev_ini["score_total"]
            curr_ov = dict(ov_ini)
            curr_sol = sol_ini
            curr_ev = ev_ini

            for frac in (0.10, 0.05, 0.025, 0.01, 0.004):
                for _ in range(2):
                    hubo_mejora = False
                    for var_nom in elegidas_canon:
                        lo, hi = limites[var_nom]
                        if CATALOGO_VARS_CONSTRUCTIVAS[var_nom].get("entera"):
                            deltas = (-1.0, 1.0)
                        else:
                            paso = frac * (hi - lo)
                            deltas = (-paso, paso)
                        for delta in deltas:
                            cand_x = curr_ov[var_nom] + delta
                            if cand_x < lo or cand_x > hi:
                                continue
                            cand_ov = dict(curr_ov)
                            cand_ov[var_nom] = cand_x
                            if "ncapS" in cand_ov and "ncapI" in cand_ov and cand_ov["ncapI"] > cand_ov["ncapS"]:
                                continue
                            res = _evaluar_score_candidato(base_fijas, cand_ov, pesos_limpios, cbat_kg, restr_limpias)
                            evaluaciones += 1
                            if res is not None and res[0] > curr_sc + 1e-5:
                                curr_sc, curr_sol, curr_ev = res
                                curr_ov = cand_ov
                                hubo_mejora = True
                                break
                    if not hubo_mejora:
                        break

            if curr_sc > mejor_sc:
                mejor_sc, mejor_ov, mejor_sol, mejor_ev = curr_sc, curr_ov, curr_sol, curr_ev

    entradas_opt = dict(base_fijas)
    for var_nom in elegidas:
        entradas_opt[var_nom] = float(mejor_sol[var_nom])

    # Recalcular la ficha final del óptimo con precisión completa (incluyendo rango de carga con batería instalada fija)
    crudos_opt = _metricas_indicadores_crudos(mejor_sol, cbat_kg, restricciones=restr_limpias, incluir_rango_fijo=True)
    mejor_ev = evaluar_indicadores(mejor_sol, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos_opt, restricciones=restr_limpias)

    cambios = {
        var_nom: {
            "actual": round(float(sol_actual[var_nom]), 6),
            "optimo": round(float(mejor_sol[var_nom]), 6),
        }
        for var_nom in elegidas
    }

    dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    return {
        "encontrado": True,
        "tiempo_ms": dt_ms,
        "evaluaciones": evaluaciones,
        "evaluaciones_validas": len(candidatos),
        "actual": ev_actual,
        "entradas_actual": base_fijas,
        "avisos_restricciones_actual": avisos_restr_act,
        "optimo": mejor_ev,
        "entradas_optimo": entradas_opt,
        "mejora_score": round(mejor_ev["score_total"] - ev_actual["score_total"], 2),
        "cambios": cambios,
        "vars_optimizadas": elegidas,
        "respetar_limites": hw_activo,
        "restricciones": restr_limpias,
    }


def _resolver_mflot_fraccion(
    base_fijas: dict[str, float],
    overrides_extra: dict[str, float],
    frac_aire_objetivo: float,
) -> dict[str, float | bool] | None:
    """
    Encuentra el `mflot` que produce `mflot / mtot == frac_aire_objetivo` explorando todo
    el rango factible `[0.20, 12.0]`. Si el objetivo cae fuera del dominio físicamente
    cerrado (por ejemplo, divergencia de batería), devuelve la aproximación factible más
    cercana con `alcanzado=False` y su fracción real verificada.
    """
    def eval_frac(mf: float) -> float | None:
        ov = {**overrides_extra, "mflot": mf}
        sol = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, **ov)
        if sol is None:
            return None
        return float(sol["mflot"]) / max(1e-6, float(sol["mtot"]))

    malla_mf = sorted({
        *[0.20 + (12.0 - 0.20) * (k / 31.0) for k in range(32)],
        float(base_fijas.get("mflot", 1.0)),
    })
    muestras: list[tuple[float, float | None]] = [(mf, eval_frac(mf)) for mf in malla_mf]

    for i in range(len(muestras) - 1):
        mf_a, fr_a = muestras[i]
        mf_b, fr_b = muestras[i + 1]
        if fr_a is None or fr_b is None:
            continue
        ra = fr_a - frac_aire_objetivo
        rb = fr_b - frac_aire_objetivo
        if abs(ra) < 1e-4:
            return {"mflot": mf_a, "frac_real": fr_a, "alcanzado": True}
        if abs(rb) < 1e-4:
            return {"mflot": mf_b, "frac_real": fr_b, "alcanzado": True}
        if ra * rb < 0.0:
            lo, r_lo = mf_a, ra
            hi, _ = mf_b, rb
            best_mf, best_fr = mf_a, fr_a
            for _ in range(26):
                mid = 0.5 * (lo + hi)
                fr_m = eval_frac(mid)
                if fr_m is None:
                    break
                best_mf, best_fr = mid, fr_m
                r_mid = fr_m - frac_aire_objetivo
                if abs(r_mid) < 1e-4:
                    break
                if r_lo * r_mid <= 0.0:
                    hi = mid
                else:
                    lo, r_lo = mid, r_mid
            return {
                "mflot": best_mf,
                "frac_real": best_fr,
                "alcanzado": abs(best_fr - frac_aire_objetivo) <= 0.005,
            }

    # Refinar hacia el borde factible más cercano al objetivo cuando no hubo cruce
    validas = [(mf, fr) for mf, fr in muestras if fr is not None]
    if not validas:
        return None
    best_mf, best_fr = min(validas, key=lambda item: abs(item[1] - frac_aire_objetivo))
    idx_best = next(i for i, (mf, _) in enumerate(muestras) if mf == best_mf)
    for vecino_idx in (idx_best - 1, idx_best + 1):
        if 0 <= vecino_idx < len(muestras) and muestras[vecino_idx][1] is None:
            mf_good, fr_good = best_mf, best_fr
            mf_bad = muestras[vecino_idx][0]
            for _ in range(16):
                mid = 0.5 * (mf_good + mf_bad)
                fr_m = eval_frac(mid)
                if fr_m is not None:
                    mf_good, fr_good = mid, fr_m
                else:
                    mf_bad = mid
            if abs(fr_good - frac_aire_objetivo) < abs(best_fr - frac_aire_objetivo):
                best_mf, best_fr = mf_good, fr_good

    return {
        "mflot": best_mf,
        "frac_real": best_fr,
        "alcanzado": abs(best_fr - frac_aire_objetivo) <= 0.005,
    }


def generar_casos_tipo(
    base_optimo: dict[str, float],
    pesos: dict[str, float] | None = None,
    cbat_kg: float = CBAT_KG_DEFECTO,
) -> dict[str, Any]:
    """
    Genera y evalúa la suite de casos tipo tomando `base_optimo` como punto de referencia,
    retirando límites duros de hardware y manteniendo avisos informativos.
    """
    pesos_limpios = normalizar_pesos(pesos)
    base_fijas = extraer_entradas_fijas(base_optimo)
    _validar_entradas_fijas_diseno(base_fijas)
    sol_ref = evaluador.evaluar_punto(base_fijas, estricto_prolado=False)
    if sol_ref is None:
        raise ValueError("El punto de referencia para Casos Tipo no es físicamente válido.")
    ev_ref = evaluar_indicadores(sol_ref, pesos_limpios, cbat_kg=cbat_kg)
    score_ref = ev_ref["score_total"]

    lam_o = float(base_fijas["lam"])
    v_o = float(base_fijas["v"])
    vv_o = float(base_fijas["vv"])
    d1_o = float(base_fijas["d1"])
    mflot_o = float(base_fijas["mflot"])
    ncapS_o = float(base_fijas["ncapS"])
    ncapI_o = float(base_fijas["ncapI"])

    # Pre-cálculo verificado de casos con porcentaje de masa residual / aire caliente
    frac_35 = _resolver_mflot_fraccion(base_fijas, {}, 0.35)
    frac_90 = _resolver_mflot_fraccion(base_fijas, {}, 0.90)
    frac_80 = _resolver_mflot_fraccion(base_fijas, {}, 0.80)
    frac_70 = _resolver_mflot_fraccion(base_fijas, {}, 0.70)
    frac_60 = _resolver_mflot_fraccion(base_fijas, {}, 0.60)

    def _desc_frac(res_f: dict[str, float | bool] | None, obj_aire_pct: int, titulo_ok: str, titulo_aprox: str) -> tuple[str, str, dict[str, float]] | None:
        if res_f is None:
            return None
        mf_val = round(float(res_f["mflot"]), 4)
        sol_chk = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, mflot=mf_val)
        if sol_chk is None:
            return None
        pct_real = 100.0 * float(sol_chk["mflot"]) / max(1e-6, float(sol_chk["mtot"]))
        alcanzado = abs(pct_real - float(obj_aire_pct)) <= 0.6
        if alcanzado:
            return titulo_ok, f"mflot = {mf_val:.2f} kg ({pct_real:.1f}% aire)", {"mflot": mf_val}
        return (
            f"{titulo_aprox} (obj. {obj_aire_pct}%, alcanzada {pct_real:.1f}%)",
            f"mflot = {mf_val:.2f} kg ({pct_real:.1f}% aire; {obj_aire_pct}% inalcanzable)",
            {"mflot": mf_val},
        )

    caso_35 = _desc_frac(frac_35, 35, "Mayoría eléctrica (35% aire caliente)", "Mayoría eléctrica")
    caso_mres10 = _desc_frac(frac_90, 90, "10% residual (90% aire caliente)", "Residual mín.")
    caso_mres20 = _desc_frac(frac_80, 80, "20% residual (80% aire caliente)", "Residual 20% obj.")
    caso_mres30 = _desc_frac(frac_70, 70, "30% residual (70% aire caliente)", "Residual 30% obj.")
    caso_mres40 = _desc_frac(frac_60, 60, "40% residual (60% aire caliente)", "Residual 40% obj.")

    vp_o = float(base_fijas["vpitch"])
    v_c1 = round(min(vp_o * 0.85, vv_o + 1.5), 1)
    v_c2 = round(min(vp_o * 0.87, vv_o + 2.5), 1)
    v_c3 = round(min(vp_o * 0.89, vv_o + 3.5), 1)
    v_c4 = round(min(vp_o * 0.91, vv_o + 5.0), 1)
    vv_fuerte = round(max(4.2, vv_o + 2.0), 1)
    v_fuerte = round(min(vp_o * 0.89, max(v_o, vv_fuerte + 2.0)), 1)

    fmt_dist = lambda val: f"{val:.0f} m" if val >= 10.0 else f"{round(val, 2):g} m"

    specs: list[tuple[str, str, str, str, dict[str, float]]] = [
        ("referencia", "Referencia", "★ Punto óptimo base", "Configuración de referencia", {}),

        # 1. Relaciones de esbeltez
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez muy baja (compacta)", f"λ = {max(1.52, lam_o - 0.8):.2f}", {"lam": max(1.52, lam_o - 0.8)}),
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez alta (+1.5)", f"λ = {lam_o + 1.5:.2f}", {"lam": lam_o + 1.5}),
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez muy alta (+2.5)", f"λ = {lam_o + 2.5:.2f}", {"lam": lam_o + 2.5}),

        # 2. Distancias largas y cortas (dinámicas respecto a d1)
        ("distancias", "2. Distancias de misión", "Misión corta (1 tramo)", f"dm = {fmt_dist(1.0 * d1_o)} (nv = 1)", {"nv": 1.0}),
        ("distancias", "2. Distancias de misión", "Misión larga (6 tramos)", f"dm = {fmt_dist(6.0 * d1_o)} (nv = 6)", {"nv": 6.0}),
        ("distancias", "2. Distancias de misión", "Misión muy larga (3 km)", f"dm = 3000 m (nv ≈ {3000.0 / max(1e-9, d1_o):.1f})", {"nv": 3000.0 / max(1e-9, d1_o)}),

        # 3. Nivel del mar
        ("altitud", "3. Densidad a nivel del mar", "Operación a nivel del mar (0 m)", "P = 101.3 kPa, g = 9.807, ν/α nivel del mar", {
            "P1": 101325.0, "P2": 101325.0, "g": 9.807, "nu": 1.78e-5, "alpha": 2.55e-5,
        }),

        # 4. Mayor parte del peso en motores con batería eléctrica
        ("motores_bateria", "4. Carga a motores eléctricos", "Casi sin aire caliente (mflot=0.5 kg)", "mflot = 0.50 kg (motores + batería)", {"mflot": 0.50}),
        *([("motores_bateria", "4. Carga a motores eléctricos", caso_35[0], caso_35[1], caso_35[2])] if caso_35 else []),

        # 5. Mayor carga útil
        ("carga_util", "5. Mayor carga útil", "Carga útil 2.0 kg (casco óptimo)", "mcarga = 2.0 kg (motores compensan)", {"mcarga": 2.0}),
        ("carga_util", "5. Mayor carga útil", "Carga útil 2.0 kg (escalando aire)", f"mcarga = 2.0 kg, mflot = {mflot_o + 1.15:.2f} kg", {"mcarga": 2.0, "mflot": mflot_o + 1.15}),
        ("carga_util", "5. Mayor carga útil", "Carga útil 3.0 kg (escalando aire)", f"mcarga = 3.0 kg, mflot = {mflot_o + 2.30:.2f} kg", {"mcarga": 3.0, "mflot": mflot_o + 2.30}),

        # 6. Otros materiales y combustibles
        ("materiales", "6. Materiales y combustibles", "Combustible Propano (lata gas)", "PC=46.4 MJ/kg, ccomb=110 Bs/kg, ncal=0.80", {"PC": 4.64e7, "ccomb": 110.0, "ncal": 0.80}),
        ("materiales", "6. Materiales y combustibles", "Combustible Butano (lata gas)", "PC=45.7 MJ/kg, ccomb=100 Bs/kg, ncal=0.80", {"PC": 4.57e7, "ccomb": 100.0, "ncal": 0.80}),
        ("materiales", "6. Materiales y combustibles", "Etanol hidratado 70%", "PC=15.9 MJ/kg, ccomb=15 Bs/kg, ncal=0.72", {"PC": 1.59e7, "ccomb": 15.0, "ncal": 0.72}),
        ("materiales", "6. Materiales y combustibles", "Casco HDPE opaco (20 µm)", "ε=0.90, ep=20 µm, σ=18.5 g/m², ke=0.45", {"eps": 0.90, "ep": 2.0e-5, "sigma": 0.0185, "ke": 0.45}),
        ("materiales", "6. Materiales y combustibles", "Nylon Ripstop sin recubrir", "ε=0.85, ep=40 µm, σ=42 g/m², ke=0.25", {"eps": 0.85, "ep": 4.0e-5, "sigma": 0.042, "ke": 0.25}),

        # 7. Número de capas celulares (0, 1, 3)
        ("capas", "7. Capas celulares (0 / 1 / 3)", "Sin capa celular (0 / 0)", "ncapS=0, ncapI=0 (piel simple)", {"ncapS": 0.0, "ncapI": 0.0}),
        ("capas", "7. Capas celulares (0 / 1 / 3)", "1 capa celular (1 / 1)", "ncapS=1, ncapI=1", {"ncapS": 1.0, "ncapI": 1.0}),
        ("capas", "7. Capas celulares (0 / 1 / 3)", "3 capas celulares (3 / 3)", "ncapS=3, ncapI=3", {"ncapS": 3.0, "ncapI": 3.0}),

        # 8. Mayor gramaje / grosor de película
        ("gramaje", "8. Mayor gramaje de película", "Mylar más grueso (12 µm)", "ep=12 µm, σ=16.8 g/m²", {"ep": 1.2e-5, "sigma": 0.0168}),
        ("gramaje", "8. Mayor gramaje de película", "Mylar pesado (25 µm)", "ep=25 µm, σ=35.0 g/m²", {"ep": 2.5e-5, "sigma": 0.035}),

        # 9. Estructura simétrica vs asimétrica
        ("simetria", "9. Simétrica vs. Asimétrica", "Estructura simétrica 2 / 2", "ncapS=2, ncapI=2", {"ncapS": 2.0, "ncapI": 2.0}),
        ("simetria", "9. Simétrica vs. Asimétrica", "Estructura simétrica 3 / 3", "ncapS=3, ncapI=3", {"ncapS": 3.0, "ncapI": 3.0}),
        ("simetria", "9. Simétrica vs. Asimétrica", "Asimétrica reforzada 4 / 2", "ncapS=4, ncapI=2", {"ncapS": 4.0, "ncapI": 2.0}),

        # 10. Cantidad de viajes (1, 3, 5, 7) dinámica respecto a d1
        ("viajes", "10. Viajes consecutivos (nv)", f"1 viaje ({fmt_dist(1.0 * d1_o)})", "nv = 1", {"nv": 1.0}),
        ("viajes", "10. Viajes consecutivos (nv)", f"3 viajes ({fmt_dist(3.0 * d1_o)})", "nv = 3", {"nv": 3.0}),
        ("viajes", "10. Viajes consecutivos (nv)", f"5 viajes ({fmt_dist(5.0 * d1_o)})", "nv = 5", {"nv": 5.0}),
        ("viajes", "10. Viajes consecutivos (nv)", f"7 viajes ({fmt_dist(7.0 * d1_o)})", "nv = 7", {"nv": 7.0}),

        # 11. Distintas velocidades relativas respecto al viento
        ("velocidades", "11. Velocidades relativas (v)", f"Crucero lento ({v_c1:.1f} m/s)", f"v = {v_c1:.1f} m/s (vg = {v_c1 - vv_o:.1f} m/s)", {"v": v_c1}),
        ("velocidades", "11. Velocidades relativas (v)", f"Crucero medio ({v_c2:.1f} m/s)", f"v = {v_c2:.1f} m/s (vg = {v_c2 - vv_o:.1f} m/s)", {"v": v_c2}),
        ("velocidades", "11. Velocidades relativas (v)", f"Crucero rápido ({v_c3:.1f} m/s)", f"v = {v_c3:.1f} m/s (vg = {v_c3 - vv_o:.1f} m/s)", {"v": v_c3}),
        ("velocidades", "11. Velocidades relativas (v)", f"Alta velocidad ({v_c4:.1f} m/s)", f"v = {v_c4:.1f} m/s (vg = {v_c4 - vv_o:.1f} m/s)", {"v": v_c4}),

        # 12. Distintos valores de masa residual (mayoría en aire caliente)
        *([("masa_residual", "12. Masa residual a motores", caso_mres10[0], caso_mres10[1], caso_mres10[2])] if caso_mres10 else []),
        *([("masa_residual", "12. Masa residual a motores", caso_mres20[0], caso_mres20[1], caso_mres20[2])] if caso_mres20 else []),
        *([("masa_residual", "12. Masa residual a motores", caso_mres30[0], caso_mres30[1], caso_mres30[2])] if caso_mres30 else []),
        *([("masa_residual", "12. Masa residual a motores", caso_mres40[0], caso_mres40[1], caso_mres40[2])] if caso_mres40 else []),

        # 13. Casos adicionales de entorno/operación
        ("entorno", "13. Entorno y temperatura (extra)", "Sin viento (vv = 0 m/s)", "vv = 0.0 m/s", {"vv": 0.0}),
        ("entorno", "13. Entorno y temperatura (extra)", f"Viento fuerte en contra ({vv_fuerte:.1f} m/s)", f"vv = {vv_fuerte:.1f} m/s, v = {v_fuerte:.1f} m/s", {"vv": vv_fuerte, "v": v_fuerte}),
        ("entorno", "13. Entorno y temperatura (extra)", "Mañana fría La Paz (T1 = 2 °C)", "T1 = 2.0 °C", {"T1": 2.0}),
        ("entorno", "13. Entorno y temperatura (extra)", "T2 baja (65 °C)", "T2 = 65 °C", {"T2": 65.0}),
        ("entorno", "13. Entorno y temperatura (extra)", "T2 alta (110 °C)", "T2 = 110 °C", {"T2": 110.0}),
    ]

    # Evitar duplicar exactamente las capas actuales dentro de simetría si ya son (3,2)
    familias_vistas: dict[str, str] = {}
    casos_out: list[dict[str, Any]] = []

    for idx, (fam_id, fam_tit, nombre, cambios_txt, ov) in enumerate(specs):
        familias_vistas[fam_id] = fam_tit
        if idx == 0:
            ev = ev_ref
            entradas_caso = dict(base_fijas)
        else:
            sol_c = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, **ov)
            if sol_c is None:
                continue
            ev = evaluar_indicadores(sol_c, pesos_limpios, cbat_kg=cbat_kg)
            entradas_caso = {**base_fijas, **ov}

        casos_out.append({
            "id": f"caso_{idx}_{fam_id}",
            "familia": fam_id,
            "familia_titulo": fam_tit,
            "nombre": nombre,
            "cambios_txt": cambios_txt,
            "es_referencia": idx == 0,
            "score_total": ev["score_total"],
            "delta_score": round(ev["score_total"] - score_ref, 2),
            "scores": ev["scores"],
            "indicadores": ev["indicadores"],
            "especificaciones": ev["especificaciones"],
            "avisos": ev["avisos"],
            "valido_hardware": ev["valido_hardware"],
            "entradas": entradas_caso,
        })

    familias_lista = [{"id": fid, "titulo": ftit} for fid, ftit in familias_vistas.items()]
    return {
        "referencia_score": score_ref,
        "referencia_capas": f"{int(round(ncapS_o))}/{int(round(ncapI_o))}",
        "familias": familias_lista,
        "casos": casos_out,
    }


# =============================================================
# Persistencia del Histórico Manual en archivo JSON local
# =============================================================
def _leer_json_historico() -> list[dict[str, Any]]:
    if not HISTORICO_PATH.exists():
        return []
    try:
        raw = HISTORICO_PATH.read_text(encoding="utf-8").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, list):
            return data
        if isinstance(data, dict) and isinstance(data.get("registros"), list):
            return data["registros"]
    except (OSError, json.JSONDecodeError):
        pass
    return []


def _escribir_json_historico(registros: list[dict[str, Any]]) -> None:
    HISTORICO_PATH.write_text(
        json.dumps(registros, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _construir_registro(
    nombre: str,
    nota: str,
    origen: str,
    entradas_fijas: dict[str, float],
    pesos: dict[str, float] | None,
    cbat_kg: float,
    reg_id: str | None = None,
    fecha: str | None = None,
    restricciones: list[dict[str, Any]] | None = None,
    respetar_limites: bool = True,
) -> dict[str, Any]:
    entradas_limpias = extraer_entradas_fijas(entradas_fijas)
    _validar_entradas_fijas_diseno(entradas_limpias)
    sol = evaluador.evaluar_punto(entradas_limpias, estricto_prolado=False)
    if sol is None:
        raise ValueError("La configuración a guardar no pudo evaluarse físicamente.")
    pesos_limpios = normalizar_pesos(pesos)
    restr_limpias = (
        normalizar_restricciones(restricciones, entradas_limpias, respetar_limites=respetar_limites)
        if restricciones is not None
        else None
    )
    hw_activo = (
        any(r["grupo"] == "hardware" and r["activa"] for r in restr_limpias)
        if restr_limpias is not None
        else bool(respetar_limites)
    )
    ev = evaluar_indicadores(sol, pesos_limpios, cbat_kg=cbat_kg, restricciones=restr_limpias)
    return {
        "id": reg_id or uuid.uuid4().hex[:10],
        "modelo_version": "v2",
        "fecha": fecha or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "nombre": (nombre or "Configuración guardada").strip()[:80],
        "nota": (nota or "").strip()[:240],
        "origen": origen or "manual",
        "cbat_kg": float(cbat_kg),
        "pesos": pesos_limpios,
        "respetar_limites": hw_activo,
        "restricciones": restr_limpias,
        "score_total": ev["score_total"],
        "scores": ev["scores"],
        "indicadores": ev["indicadores"],
        "especificaciones": ev["especificaciones"],
        "avisos": ev["avisos"],
        "valido_hardware": ev["valido_hardware"],
        "entradas": entradas_limpias,
    }


def cargar_historico() -> list[dict[str, Any]]:
    return _leer_json_historico()


def guardar_registro_historico(
    nombre: str,
    nota: str,
    origen: str,
    entradas_fijas: dict[str, float],
    pesos: dict[str, float] | None = None,
    cbat_kg: float = CBAT_KG_DEFECTO,
    restricciones: list[dict[str, Any]] | None = None,
    respetar_limites: bool = True,
) -> dict[str, Any]:
    reg = _construir_registro(
        nombre,
        nota,
        origen,
        entradas_fijas,
        pesos,
        cbat_kg,
        restricciones=restricciones,
        respetar_limites=respetar_limites,
    )
    registros = _leer_json_historico()
    registros.insert(0, reg)
    _escribir_json_historico(registros)
    return reg


def eliminar_registro_historico(item_id: str) -> bool:
    registros = _leer_json_historico()
    filtrados = [r for r in registros if r.get("id") != item_id]
    if len(filtrados) == len(registros):
        return False
    _escribir_json_historico(filtrados)
    return True


def _normalizar_registro_importado(raw: dict[str, Any]) -> dict[str, Any]:
    """
    Preserva intactos los registros importados que ya traen métricas calculadas (incluidos los
    archivados en `v1`) sin recalcularlos con el motor `v2` bajo el mismo ID.
    Solo evalúa en `v2` cuando el registro importado contiene únicamente `entradas` sin resultados.
    """
    entradas_raw = raw.get("entradas")
    assert isinstance(entradas_raw, dict)
    rid = str(raw.get("id") or "").strip() or uuid.uuid4().hex[:10]
    fecha = str(raw.get("fecha") or "").strip() or datetime.now().strftime("%Y-%m-%d %H:%M")
    nombre = str(raw.get("nombre") or "Importado").strip()[:80]
    nota = str(raw.get("nota") or "").strip()[:240]
    origen = str(raw.get("origen") or "importado")
    try:
        cbat_val = float(raw.get("cbat_kg", CBAT_KG_DEFECTO))
        if not math.isfinite(cbat_val) or cbat_val < 0.0:
            cbat_val = CBAT_KG_DEFECTO
    except (TypeError, ValueError):
        cbat_val = CBAT_KG_DEFECTO
    pesos_limpios = normalizar_pesos(raw.get("pesos") if isinstance(raw.get("pesos"), dict) else None)

    tiene_resultados_archivados = (
        isinstance(raw.get("especificaciones"), dict)
        and isinstance(raw.get("indicadores"), dict)
        and isinstance(raw.get("scores"), dict)
        and raw.get("score_total") is not None
    )
    if tiene_resultados_archivados:
        modelo_ver = str(raw.get("modelo_version") or "v1").strip() or "v1"
        avisos = [str(a) for a in raw.get("avisos", [])] if isinstance(raw.get("avisos"), list) else []
        reg: dict[str, Any] = {
            "id": rid,
            "modelo_version": modelo_ver,
            "fecha": fecha,
            "nombre": nombre,
            "nota": nota,
            "origen": origen,
            "cbat_kg": cbat_val,
            "pesos": pesos_limpios,
            "score_total": float(raw["score_total"]),
            "scores": dict(raw["scores"]),
            "indicadores": dict(raw["indicadores"]),
            "especificaciones": dict(raw["especificaciones"]),
            "avisos": avisos,
            "valido_hardware": bool(raw.get("valido_hardware", not avisos)),
            "entradas": extraer_entradas_fijas(entradas_raw),
        }
        if raw.get("origen_id"):
            reg["origen_id"] = str(raw["origen_id"])
        if raw.get("origen_version"):
            reg["origen_version"] = str(raw["origen_version"])
        if isinstance(raw.get("restricciones"), list):
            reg["restricciones"] = [dict(r) for r in raw["restricciones"] if isinstance(r, dict)]
        elif raw.get("restricciones") is None and "restricciones" in raw:
            reg["restricciones"] = None
        if "respetar_limites" in raw:
            reg["respetar_limites"] = bool(raw["respetar_limites"])
        return reg

    restr_imp = raw.get("restricciones") if isinstance(raw.get("restricciones"), list) else None
    resp_imp = bool(raw.get("respetar_limites", True))
    return _construir_registro(
        nombre=nombre,
        nota=nota,
        origen=origen,
        entradas_fijas=entradas_raw,
        pesos=pesos_limpios,
        cbat_kg=cbat_val,
        reg_id=rid,
        fecha=fecha,
        restricciones=restr_imp,
        respetar_limites=resp_imp,
    )


def importar_historico(registros_nuevos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actuales = _leer_json_historico()
    ids_existentes = {r.get("id") for r in actuales}
    for raw in registros_nuevos:
        if not isinstance(raw, dict) or not isinstance(raw.get("entradas"), dict):
            continue
        rid = str(raw.get("id") or "")
        if rid and rid in ids_existentes:
            continue
        reg = _normalizar_registro_importado(raw)
        actuales.append(reg)
        ids_existentes.add(reg["id"])
    _escribir_json_historico(actuales)
    return actuales


def reevaluar_registro_historico(item_id: str) -> dict[str, Any] | None:
    """
    Crea un nuevo registro independiente en `v2` a partir de un registro existente en el
    histórico (`item_id`), manteniendo intacto el registro original y trazando `origen_id`.
    """
    actuales = _leer_json_historico()
    orig = next((r for r in actuales if r.get("id") == item_id), None)
    if orig is None:
        return None
    entradas = orig.get("entradas")
    if not isinstance(entradas, dict):
        raise ValueError("El registro seleccionado no contiene entradas válidas para reevaluar.")

    origen_ver = str(orig.get("modelo_version") or "v1")
    nombre_base = str(orig.get("nombre") or "Configuración").strip()
    sufijo = " (reeval. v2)"
    nombre_nuevo = nombre_base if nombre_base.endswith(sufijo) else f"{nombre_base[:80 - len(sufijo)]}{sufijo}"
    nota_prev = str(orig.get("nota") or "").strip()
    ref_txt = f"Reeval. v2 desde {origen_ver} ({orig['id']})"
    nota_nueva = f"{ref_txt} · {nota_prev}" if nota_prev else ref_txt
    restr_orig = orig.get("restricciones") if isinstance(orig.get("restricciones"), list) else None
    resp_orig = bool(orig.get("respetar_limites", True))

    reg = _construir_registro(
        nombre=nombre_nuevo,
        nota=nota_nueva,
        origen="reevaluacion_v2",
        entradas_fijas=entradas,
        pesos=orig.get("pesos") if isinstance(orig.get("pesos"), dict) else None,
        cbat_kg=float(orig.get("cbat_kg", CBAT_KG_DEFECTO)),
        reg_id=None,
        fecha=None,
        restricciones=restr_orig,
        respetar_limites=resp_orig,
    )
    reg["origen_id"] = str(orig["id"])
    reg["origen_version"] = origen_ver
    actuales.insert(0, reg)
    _escribir_json_historico(actuales)
    return reg
