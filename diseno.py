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
        "descripcion": "Carga útil elevable disponible con margen aerostático y motriz (mcarga + Fexc/g), junto a la carga total mtot.",
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

VARS_OPTIMIZABLES_DISENO = ("lam", "v", "mflot", "e", "T2", "ncapS", "ncapI")
_PRIMOS_HALTON = (2, 3, 5, 7, 11, 13, 17)
_ENTRADAS_KEYS = tuple(modelo.FIJAS_INI)

VARIABLES_RESTRICCION: dict[str, dict[str, Any]] = {
    "T2": {"nombre": "Temp. interna máxima (T2)", "unidad": "°C", "factor": 1.0, "op_def": "<=", "valor_def": 95.0, "paso": 1.0, "origen": "sol"},
    "mbat": {"nombre": "Masa de batería (mbat)", "unidad": "g", "factor": 1000.0, "op_def": "<=", "valor_def": 1000.0, "paso": 50.0, "origen": "sol"},
    "Pelec": {"nombre": "Potencia eléctrica (Pelec)", "unidad": "W", "factor": 1.0, "op_def": "<=", "valor_def": 640.0, "paso": 20.0, "origen": "sol"},
    "Ttot": {"nombre": "Empuje total (Ttot)", "unidad": "N", "factor": 1.0, "op_def": "<=", "valor_def": 34.5, "paso": 0.5, "origen": "sol"},
    "theta": {"nombre": "Inclinación motores (θ)", "unidad": "°", "factor": 1.0, "op_def": "<=", "valor_def": 65.0, "paso": 1.0, "origen": "sol"},
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


def restricciones_defecto(
    valores_base: dict[str, float] | None = None,
    activar_hardware: bool = False,
) -> list[dict[str, Any]]:
    """Lista inicial de restricciones: T2 <= 95 °C activo por defecto + límites editables de hardware."""
    base = valores_base or modelo.valores_iniciales()
    mbmax_g = round(float(base.get("mbmax", 1.0)) * 1000.0, 1)
    pmax_w = round(float(base.get("Pmax", 640.0)), 1)
    tmax_n = round(float(base.get("N", 4.0)) * float(base.get("Tmax1", 8.625)), 2)
    thmax_deg = round(float(base.get("thmax", 65.0)), 1)
    hw_act = bool(activar_hardware)
    return [
        {"id": "lim_T2", "variable": "T2", "op": "<=", "valor": 95.0, "activa": True, "grupo": "general"},
        {"id": "hw_mbat", "variable": "mbat", "op": "<=", "valor": mbmax_g, "activa": hw_act, "grupo": "hardware"},
        {"id": "hw_Pelec", "variable": "Pelec", "op": "<=", "valor": pmax_w, "activa": hw_act, "grupo": "hardware"},
        {"id": "hw_Ttot", "variable": "Ttot", "op": "<=", "valor": tmax_n, "activa": hw_act, "grupo": "hardware"},
        {"id": "hw_theta", "variable": "theta", "op": "<=", "valor": thmax_deg, "activa": hw_act, "grupo": "hardware"},
        {"id": "hw_Fexc", "variable": "Fexc", "op": ">=", "valor": 0.0, "activa": hw_act, "grupo": "hardware"},
    ]


def normalizar_restricciones(
    restricciones: list[dict[str, Any]] | None,
    valores_base: dict[str, float] | None = None,
    respetar_limites: bool = False,
) -> list[dict[str, Any]]:
    """Limpia y valida las restricciones personalizadas enviadas por el cliente."""
    if restricciones is None:
        return restricciones_defecto(valores_base, activar_hardware=respetar_limites)

    limpias: list[dict[str, Any]] = []
    for idx, raw in enumerate(restricciones):
        if not isinstance(raw, dict):
            continue
        var_nom = str(raw.get("variable") or "")
        if var_nom not in VARIABLES_RESTRICCION:
            continue
        meta = VARIABLES_RESTRICCION[var_nom]
        op = str(raw.get("op") or meta["op_def"])
        if op not in ("<=", ">="):
            op = str(meta["op_def"])
        try:
            val = float(raw.get("valor", meta["valor_def"]))
        except (TypeError, ValueError):
            val = float(meta["valor_def"])
        if not math.isfinite(val):
            val = float(meta["valor_def"])
        grupo = str(raw.get("grupo") or "custom")
        limpias.append({
            "id": str(raw.get("id") or f"lim_{idx}_{var_nom}"),
            "variable": var_nom,
            "op": op,
            "valor": round(val, 4),
            "activa": bool(raw.get("activa", True)),
            "grupo": grupo,
        })
    return limpias


def _valor_restriccion(sol: dict[str, float], crudos: dict[str, Any], var_nom: str) -> float:
    meta = VARIABLES_RESTRICCION[var_nom]
    if meta["origen"] == "crudo":
        if var_nom == "c_recambio":
            return float(crudos["valores"]["costo_recambio"])
        if var_nom == "dm_aut":
            return float(crudos["valores"]["autonomia"])
    return float(sol[var_nom]) * float(meta["factor"])


def _cumple_restricciones(
    sol: dict[str, float],
    crudos: dict[str, Any],
    restricciones: list[dict[str, Any]],
) -> bool:
    for r in restricciones:
        if not r.get("activa", True):
            continue
        val = _valor_restriccion(sol, crudos, r["variable"])
        lim = float(r["valor"])
        if r["op"] == "<=" and val > lim + 1e-6:
            return False
        if r["op"] == ">=" and val < lim - 1e-6:
            return False
    return True


def _avisos_restricciones(
    sol: dict[str, float],
    crudos: dict[str, Any],
    restricciones: list[dict[str, Any]],
) -> list[str]:
    avisos: list[str] = []
    for r in restricciones:
        if not r.get("activa", True):
            continue
        meta = VARIABLES_RESTRICCION[r["variable"]]
        val = _valor_restriccion(sol, crudos, r["variable"])
        lim = float(r["valor"])
        if (r["op"] == "<=" and val > lim + 1e-6) or (r["op"] == ">=" and val < lim - 1e-6):
            avisos.append(f"{r['variable']}={val:.2f}{meta['unidad']} ({r['op']} {lim:g})")
    return avisos


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


def _metricas_indicadores_crudos(sol: dict[str, float], cbat_kg: float) -> dict[str, Any]:
    cop = float(sol["Cop"])
    dm = max(1.0, float(sol["dm"]))
    d1 = max(1.0, float(sol["d1"]))

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
    capacidad_util_kg = max(0.05, mcarga + fexc / g)

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
            "masa_elevable": capacidad_util_kg,
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
    crudos = _metricas_indicadores_crudos(sol_ini, CBAT_KG_DEFECTO)
    return {k: max(1e-6, float(v)) for k, v in crudos["valores"].items()}


ANCLAS_BASE: dict[str, float] = _calcular_anclas_base()


def _avisos_hardware(sol: dict[str, float]) -> list[str]:
    avisos: list[str] = []
    if sol["mbat"] > sol["mbmax"]:
        avisos.append(f"mbat={sol['mbat']*1000:.0f}g > {sol['mbmax']*1000:.0f}g")
    if sol["Pelec"] > sol["Pmax"]:
        avisos.append(f"Pelec={sol['Pelec']:.0f}W > {sol['Pmax']:.0f}W")
    tmax_tot = sol["N"] * sol["Tmax1"]
    if sol["Ttot"] > tmax_tot:
        avisos.append(f"Ttot={sol['Ttot']:.1f}N > {tmax_tot:.1f}N")
    if sol["theta"] > sol["thmax"]:
        avisos.append(f"θ={sol['theta']:.1f}° > {sol['thmax']:.0f}°")
    if sol["Fexc"] < 0.0:
        avisos.append(f"Fexc={sol['Fexc']:.1f}N < 0")
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
        "v": round(float(sol["v"]), 2),
        "vv": round(float(sol["vv"]), 2),
        "vg": round(float(sol["vg"]), 2),
        "tm_s": round(float(sol["tm"]), 1),
        "dm": round(float(sol["dm"]), 1),
        "nv": round(float(sol["nv"]), 2),
        "mflot": round(float(sol["mflot"]), 3),
        "mres": round(float(sol["mres"]), 3),
        "mcarga": round(float(sol["mcarga"]), 2),
        "mtot": round(float(sol["mtot"]), 3),
        "frac_aire_pct": round(float(d["frac_aire_pct"]), 1),
        "capacidad_util_kg": round(float(d["capacidad_util_kg"]), 2),
        "FD": round(float(sol["FD"]), 2),
        "Ttot": round(float(sol["Ttot"]), 2),
        "theta": round(float(sol["theta"]), 1),
        "Pelec": round(float(sol["Pelec"]), 1),
        "Ptot": round(float(sol["Ptot"]), 1),
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
) -> dict[str, Any]:
    """Calcula puntuaciones individuales (0-100), score ponderado y ficha técnica."""
    pesos_limpios = normalizar_pesos(pesos)
    refs = anclas or ANCLAS_BASE
    crudos_calc = crudos if crudos is not None else _metricas_indicadores_crudos(sol, cbat_kg)
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
            sc = 100.0 / (1.0 + (ref / max(1e-6, val)) ** 1.35)
        scores[key] = round(sc, 2)
        suma_ponderada += pesos_limpios[key] * sc

    score_total = round(suma_ponderada / max(1e-9, suma_pesos), 2)
    avisos = _avisos_hardware(sol)

    return {
        "score_total": score_total,
        "scores": scores,
        "indicadores": {k: round(float(v), 4) for k, v in vals.items()},
        "desglose": {
            k: (round(float(v), 4) if isinstance(v, (int, float)) else v)
            for k, v in crudos_calc["desglose"].items()
        },
        "especificaciones": extraer_especificaciones(sol, crudos_calc),
        "avisos": avisos,
        "valido_hardware": bool(sol.get("valido", False)),
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
    if sol["cf"] <= sol["R"] or sol["cr"] <= sol["R"] or sol["mres"] <= 0.05 or sol["vg"] <= 0.35:
        return None
    crudos = _metricas_indicadores_crudos(sol, cbat_kg)
    if not _cumple_restricciones(sol, crudos, restricciones):
        return None
    ev = evaluar_indicadores(sol, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos)
    return ev["score_total"], sol, ev


def optimizar_especificaciones(
    valores_base: dict[str, float],
    pesos: dict[str, float] | None = None,
    vars_libres: list[str] | None = None,
    cbat_kg: float = CBAT_KG_DEFECTO,
    respetar_limites: bool = False,
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
        elegidas = [v for v in vars_libres if v in VARS_OPTIMIZABLES_DISENO]

    sol_actual = evaluador.evaluar_punto(base_fijas, estricto_prolado=False)
    if sol_actual is None:
        raise ValueError("El estado base indicado no pudo evaluarse físicamente.")
    crudos_actual = _metricas_indicadores_crudos(sol_actual, cbat_kg)
    ev_actual = evaluar_indicadores(sol_actual, pesos_limpios, cbat_kg=cbat_kg, crudos=crudos_actual)
    avisos_restr_act = _avisos_restricciones(sol_actual, crudos_actual, restr_limpias)

    xf = base_fijas["xf"]
    lam_min = max(1.52, (0.5 / max(0.05, min(xf, 1.0 - xf))) * 1.06)
    v_min = max(base_fijas["vv"] + 0.8, 3.0)
    v_max = min(base_fijas["vpitch"] * 0.88, 11.5)
    if v_max <= v_min + 0.5:
        v_max = v_min + 2.0

    mtot_ref = sol_actual["mtot"]
    limites: dict[str, tuple[float, float]] = {
        "lam": (lam_min, 4.8),
        "v": (v_min, v_max),
        "mflot": (max(0.55, 0.30 * mtot_ref), max(6.8, 1.85 * mtot_ref)),
        "e": (0.008, 0.032),
        "T2": (max(base_fijas["T1"] + 35.0, 55.0), 115.0),
        "ncapS": (1.0, 4.0),
        "ncapI": (1.0, 3.0),
    }

    # Acotar rangos de búsqueda según restricciones activas sobre variables libres
    for r in restr_limpias:
        if not r.get("activa", True):
            continue
        vn = r["variable"]
        if vn not in limites:
            continue
        meta = VARIABLES_RESTRICCION[vn]
        thr = float(r["valor"]) / float(meta["factor"])
        lo, hi = limites[vn]
        if r["op"] == "<=":
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

    ov_actual = {v: float(sol_actual[v]) for v in elegidas}
    res_act = _evaluar_score_candidato(
        base_fijas, ov_actual, pesos_limpios, cbat_kg, restr_limpias
    )
    evaluaciones += 1
    if res_act is not None:
        sc, s_sol, s_ev = res_act
        candidatos.append((sc, ov_actual, s_sol, s_ev))

    if elegidas:
        n_muestras = 300
        for idx in range(1, n_muestras + 1):
            ov: dict[str, float] = {}
            for dim, v_nom in enumerate(elegidas):
                lo, hi = limites[v_nom]
                u = _halton(idx, _PRIMOS_HALTON[dim])
                val = lo + u * (hi - lo)
                if v_nom in ("ncapS", "ncapI"):
                    val = float(round(val))
                ov[v_nom] = val
            if "ncapS" in ov and "ncapI" in ov and ov["ncapI"] > ov["ncapS"]:
                ov["ncapI"] = ov["ncapS"]
            res = _evaluar_score_candidato(base_fijas, ov, pesos_limpios, cbat_kg, restr_limpias)
            evaluaciones += 1
            if res is not None:
                sc, s_sol, s_ev = res
                candidatos.append((sc, ov, s_sol, s_ev))

    if not candidatos:
        dt_ms = round((time.perf_counter() - t0) * 1000.0, 2)
        return {
            "encontrado": False,
            "mensaje_error": (
                "Ninguna combinación cumplió simultáneamente todas las restricciones activas."
                if elegidas
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

    if elegidas:
        for _, ov_ini, sol_ini, ev_ini in candidatos[:4]:
            curr_sc = ev_ini["score_total"]
            curr_ov = dict(ov_ini)
            curr_sol = sol_ini
            curr_ev = ev_ini

            for frac in (0.08, 0.04, 0.02, 0.01):
                for var_nom in elegidas:
                    lo, hi = limites[var_nom]
                    if var_nom in ("ncapS", "ncapI"):
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
                            break

            if curr_sc > mejor_sc:
                mejor_sc, mejor_ov, mejor_sol, mejor_ev = curr_sc, curr_ov, curr_sol, curr_ev

    entradas_opt = dict(base_fijas)
    for var_nom in elegidas:
        entradas_opt[var_nom] = float(mejor_sol[var_nom])

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
) -> float | None:
    """Encuentra por bisección 1D el valor de `mflot` tal que `mflot / mtot == frac_aire_objetivo`."""
    def f_res(mf: float) -> float | None:
        ov = {**overrides_extra, "mflot": mf}
        sol = evaluador.evaluar_punto(base_fijas, estricto_prolado=False, **ov)
        if sol is None:
            return None
        return (sol["mflot"] / max(1e-6, sol["mtot"])) - frac_aire_objetivo

    lo, hi = 0.18, 12.0
    r_lo = f_res(lo)
    r_hi = f_res(hi)
    if r_lo is None or r_hi is None or r_lo * r_hi > 0.0:
        return None
    for _ in range(24):
        mid = 0.5 * (lo + hi)
        r_mid = f_res(mid)
        if r_mid is None:
            return mid
        if abs(r_mid) < 1e-4:
            return mid
        if r_lo * r_mid <= 0.0:
            hi, r_hi = mid, r_mid
        else:
            lo, r_lo = mid, r_mid
    return 0.5 * (lo + hi)


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
    sol_ref = evaluador.evaluar_punto(base_fijas, estricto_prolado=False)
    if sol_ref is None:
        raise ValueError("El punto de referencia para Casos Tipo no es físicamente válido.")
    ev_ref = evaluar_indicadores(sol_ref, pesos_limpios, cbat_kg=cbat_kg)
    score_ref = ev_ref["score_total"]

    lam_o = float(base_fijas["lam"])
    v_o = float(base_fijas["v"])
    vv_o = float(base_fijas["vv"])
    mflot_o = float(base_fijas["mflot"])
    ncapS_o = float(base_fijas["ncapS"])
    ncapI_o = float(base_fijas["ncapI"])

    # Pre-cálculo rápido de casos con porcentaje exacto de masa residual / aire caliente
    mflot_35pct = _resolver_mflot_fraccion(base_fijas, {}, 0.35) or 1.2
    mflot_mres10 = _resolver_mflot_fraccion(base_fijas, {}, 0.90) or (sol_ref["mtot"] * 0.90)
    mflot_mres20 = _resolver_mflot_fraccion(base_fijas, {}, 0.80) or (sol_ref["mtot"] * 0.80)
    mflot_mres30 = _resolver_mflot_fraccion(base_fijas, {}, 0.70) or (sol_ref["mtot"] * 0.70)
    mflot_mres40 = _resolver_mflot_fraccion(base_fijas, {}, 0.60) or (sol_ref["mtot"] * 0.60)

    specs: list[tuple[str, str, str, str, dict[str, float]]] = [
        ("referencia", "Referencia", "★ Punto óptimo base", "Configuración de referencia", {}),

        # 1. Relaciones de esbeltez
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez muy baja (compacta)", f"λ = {max(1.52, lam_o - 0.8):.2f}", {"lam": max(1.52, lam_o - 0.8)}),
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez alta (+1.5)", f"λ = {lam_o + 1.5:.2f}", {"lam": lam_o + 1.5}),
        ("esbeltez", "1. Esbeltez (λ)", "Esbeltez muy alta (+2.5)", f"λ = {lam_o + 2.5:.2f}", {"lam": lam_o + 2.5}),

        # 2. Distancias largas y cortas
        ("distancias", "2. Distancias de misión", "Misión corta (1 tramo)", "dm = 280 m (nv = 1)", {"nv": 1.0}),
        ("distancias", "2. Distancias de misión", "Misión larga (6 tramos)", "dm = 1680 m (nv = 6)", {"nv": 6.0}),
        ("distancias", "2. Distancias de misión", "Misión muy larga (3 km)", "dm = 3000 m (nv ≈ 10.7)", {"nv": 3000.0 / float(base_fijas["d1"])}),

        # 3. Nivel del mar
        ("altitud", "3. Densidad a nivel del mar", "Operación a nivel del mar (0 m)", "P = 101.3 kPa, g = 9.807, ν/α nivel del mar", {
            "P1": 101325.0, "P2": 101325.0, "g": 9.807, "nu": 1.78e-5, "alpha": 2.55e-5,
        }),

        # 4. Mayor parte del peso en motores con batería eléctrica
        ("motores_bateria", "4. Carga a motores eléctricos", "Casi sin aire caliente (mflot=0.5 kg)", "mflot = 0.50 kg (motores + batería)", {"mflot": 0.50}),
        ("motores_bateria", "4. Carga a motores eléctricos", "Mayoría eléctrica (35% aire caliente)", f"mflot = {mflot_35pct:.2f} kg (~35% aire)", {"mflot": round(mflot_35pct, 4)}),

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

        # 10. Cantidad de viajes (1, 3, 5, 7)
        ("viajes", "10. Viajes consecutivos (nv)", "1 viaje (280 m)", "nv = 1", {"nv": 1.0}),
        ("viajes", "10. Viajes consecutivos (nv)", "3 viajes (840 m)", "nv = 3", {"nv": 3.0}),
        ("viajes", "10. Viajes consecutivos (nv)", "5 viajes (1400 m)", "nv = 5", {"nv": 5.0}),
        ("viajes", "10. Viajes consecutivos (nv)", "7 viajes (1960 m)", "nv = 7", {"nv": 7.0}),

        # 11. Distintas velocidades relativas
        ("velocidades", "11. Velocidades relativas (v)", "Crucero lento (4.0 m/s)", f"v = 4.0 m/s (vg = {4.0 - vv_o:.1f} m/s)", {"v": 4.0}),
        ("velocidades", "11. Velocidades relativas (v)", "Crucero medio (6.0 m/s)", f"v = 6.0 m/s (vg = {6.0 - vv_o:.1f} m/s)", {"v": 6.0}),
        ("velocidades", "11. Velocidades relativas (v)", "Crucero rápido (8.0 m/s)", f"v = 8.0 m/s (vg = {8.0 - vv_o:.1f} m/s)", {"v": 8.0}),
        ("velocidades", "11. Velocidades relativas (v)", "Alta velocidad (10.0 m/s)", f"v = 10.0 m/s (vg = {10.0 - vv_o:.1f} m/s)", {"v": 10.0}),

        # 12. Distintos valores de masa residual (mayoría en aire caliente)
        ("masa_residual", "12. Masa residual a motores", "10% residual (90% aire caliente)", f"mflot={mflot_mres10:.2f} kg", {"mflot": round(mflot_mres10, 4)}),
        ("masa_residual", "12. Masa residual a motores", "20% residual (80% aire caliente)", f"mflot={mflot_mres20:.2f} kg", {"mflot": round(mflot_mres20, 4)}),
        ("masa_residual", "12. Masa residual a motores", "30% residual (70% aire caliente)", f"mflot={mflot_mres30:.2f} kg", {"mflot": round(mflot_mres30, 4)}),
        ("masa_residual", "12. Masa residual a motores", "40% residual (60% aire caliente)", f"mflot={mflot_mres40:.2f} kg", {"mflot": round(mflot_mres40, 4)}),

        # 13. Casos adicionales de entorno/operación
        ("entorno", "13. Entorno y temperatura (extra)", "Sin viento (vv = 0 m/s)", "vv = 0.0 m/s", {"vv": 0.0}),
        ("entorno", "13. Entorno y temperatura (extra)", "Viento fuerte en contra (4.2 m/s)", f"vv = 4.2 m/s, v = {max(v_o, 6.2):.1f} m/s", {"vv": 4.2, "v": max(v_o, 6.2)}),
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
) -> dict[str, Any]:
    entradas_limpias = extraer_entradas_fijas(entradas_fijas)
    sol = evaluador.evaluar_punto(entradas_limpias, estricto_prolado=False)
    if sol is None:
        raise ValueError("La configuración a guardar no pudo evaluarse físicamente.")
    pesos_limpios = normalizar_pesos(pesos)
    ev = evaluar_indicadores(sol, pesos_limpios, cbat_kg=cbat_kg)
    return {
        "id": reg_id or uuid.uuid4().hex[:10],
        "fecha": fecha or datetime.now().strftime("%Y-%m-%d %H:%M"),
        "nombre": (nombre or "Configuración guardada").strip()[:80],
        "nota": (nota or "").strip()[:240],
        "origen": origen or "manual",
        "cbat_kg": float(cbat_kg),
        "pesos": pesos_limpios,
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
) -> dict[str, Any]:
    reg = _construir_registro(nombre, nota, origen, entradas_fijas, pesos, cbat_kg)
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


def importar_historico(registros_nuevos: list[dict[str, Any]]) -> list[dict[str, Any]]:
    actuales = _leer_json_historico()
    ids_existentes = {r.get("id") for r in actuales}
    for raw in registros_nuevos:
        if not isinstance(raw, dict) or not isinstance(raw.get("entradas"), dict):
            continue
        rid = str(raw.get("id") or "")
        if rid and rid in ids_existentes:
            continue
        reg = _construir_registro(
            nombre=str(raw.get("nombre") or "Importado"),
            nota=str(raw.get("nota") or ""),
            origen=str(raw.get("origen") or "importado"),
            entradas_fijas=raw["entradas"],
            pesos=raw.get("pesos"),
            cbat_kg=float(raw.get("cbat_kg", CBAT_KG_DEFECTO)),
            reg_id=rid or None,
            fecha=str(raw.get("fecha")) if raw.get("fecha") else None,
        )
        actuales.append(reg)
        ids_existentes.add(reg["id"])
    _escribir_json_historico(actuales)
    return actuales
