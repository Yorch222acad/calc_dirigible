"""
Generador de datos y curvas paramétricas para la sección de Gráficas del Frontend.

Evalúa de forma rápida y exacta las relaciones físicas acopladas entre las variables
clave del dirigible híbrido alrededor del estado de operación actual:
  - Relación de esbeltez (lam)
  - Carga de sustentación aire caliente (mflot) vs. motores de dron (mres)
  - Energía consumida en total (Etot = Em + 3600·Ereq)
  - Distancia (dm) y tiempo de vuelo (tm)
  - Longitud (L) y diámetro máximo del dirigible (D = 2·R)
  - Masa total (mtot)
  - Fuerza vertical de sustentación por fuente (F aire caliente y FL motores)
  - Masa de propano necesaria para terminar el vuelo (mgm)
  - Espesor del aislante de la configuración celular (e)
  - Energía ahorrada gracias al aislante (Eah = dQp·tm y dQp)
  - Energía perdida (Em = Qp·tm con aislante, Em0 = Qp0·tm sin aislante, Qc)
"""
from __future__ import annotations

import math
from typing import Any

import evaluador
import formateo
import modelo


def simular_punto(base: dict[str, float], **overrides: float) -> dict[str, float] | None:
    """
    Delega al evaluador numérico unificado (`evaluador.evaluar_punto`) para evaluar un
    punto paramétrico en microsegundos alrededor del estado `base`.
    """
    return evaluador.evaluar_punto(base, estricto_prolado=False, **overrides)


def _info_var(nombre: str, valores: dict[str, float], fijas: set[str], penalizado: bool) -> dict[str, Any]:
    desc, unidad, _ = modelo.VARIABLES[nombre]
    es_fija = nombre in fijas
    es_penalizada = bool(penalizado and nombre in formateo.VARS_SUSTENTACION)
    color = "red" if es_penalizada else ("yellow" if es_fija else "green")
    val_vista = -abs(valores[nombre]) if es_penalizada else valores[nombre]
    return {
        "nombre": nombre,
        "descripcion": desc,
        "unidad": unidad,
        "fija": es_fija,
        "penalizada": es_penalizada,
        "color": color,
        "valor": valores[nombre],
        "valor_ing": formateo.formatear_ingenieria(nombre, val_vista),
    }


def _linspace(vmin: float, vmax: float, n: int, incluir: float | None = None) -> list[float]:
    if n <= 1:
        return [vmin]
    paso = (vmax - vmin) / (n - 1)
    pts = [vmin + i * paso for i in range(n)]
    if incluir is not None and vmin <= incluir <= vmax:
        if all(abs(x - incluir) > 1e-6 for x in pts):
            pts.append(incluir)
            pts.sort()
    return pts


def construir_datos_graficas(valores: dict[str, float], fijas: set[str]) -> list[dict[str, Any]]:
    """
    Construye las 6 gráficas interactivas del proyecto con sus curvas paramétricas,
    comparaciones de barras y metadatos de las variables involucradas.
    """
    _, alertas = formateo.evaluar_alertas_y_vista(valores)
    penalizado = bool(alertas)

    def vars_meta(lista_nombres: list[str]) -> list[dict[str, Any]]:
        return [_info_var(n, valores, fijas, penalizado) for n in lista_nombres if n in valores]

    # =========================================================
    # 1. ESBELTEZ (lam) vs. ENERGÍA TOTAL, MASA TOTAL, L y D
    # =========================================================
    lam_actual = valores["lam"]
    lam_min = max(1.45, min(1.5, lam_actual * 0.6))
    lam_max = max(5.2, lam_actual * 1.8)
    xs_lam = _linspace(lam_min, lam_max, 45, incluir=lam_actual)
    pts_lam = [p for x in xs_lam if (p := simular_punto(valores, lam=x)) is not None]

    # Encontrar el punto de mínima energía total físicamente válido (límites de motor y batería)
    pts_lam_validos = [p for p in pts_lam if p["valido"]]
    opt_lam = min(pts_lam_validos, key=lambda d: d["Etot"]) if pts_lam_validos else None

    grafica_esbeltez = {
        "id": "esbeltez",
        "indice": 1,
        "titulo": "Esbeltez (λ) vs. Energías de Misión y Dimensiones/Masa (L, D, mtot)",
        "titulo_corto": "Esbeltez vs. Energías y Casco",
        "subtitulo": (
            "Todas las series del Panel A están en la misma unidad de energía total (kJ): Energía suministrada por combustible térmico (Eprop), "
            "Energía calorífica perdida (Em), Energía eléctrica usada en misión (Eelec) y Energía perdida por arrastre aerodinámico (ED). "
            "El Panel B compara Longitud (L), Diámetro máximo (D) y Masa total (mtot) frente a la Relación de Esbeltez (λ = L/D)."
        ),
        "variables": vars_meta(["lam", "v", "vv", "vg", "Eprop", "Em", "Eelec", "ED", "Etot", "Pelec", "Pmax", "mbat", "ncal", "L", "D", "mtot", "mres", "FD"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Relación de Esbeltez (λ) vs. Energías Totales de Misión (kJ)",
                "x_label": "Relación de esbeltez λ = L/D (adim)",
                "x_actual": lam_actual,
                "x_optimo": opt_lam["lam"] if opt_lam else None,
                "x_optimo_label": f"Mín. Etot válido (λ={opt_lam['lam']:.2f})" if opt_lam else "",
                "permitir_escala_unica": True,
                "escala_unica_inicial": False,
                "y1_label": "Energías térmicas: Eprop y Em (kJ)",
                "y2_label": "Energías eléctrica y arrastre: Eelec y ED (kJ)",
                "y_unica_label": "Energía total en misión (kJ) — misma escala",
                "xs": [round(p["lam"], 4) for p in pts_lam],
                "series": [
                    {
                        "nombre": "Energía suministrada por combustible térmico (Eprop)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["Eprop"] / 1000.0, 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Energía calorífica perdida (Em)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#f97316",
                        "dashed": True,
                        "valores": [round(p["Em"] / 1000.0, 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Energía eléctrica usada en misión (Eelec)",
                        "unidad": "kJ",
                        "eje": "y2",
                        "color": "#facc15",
                        "valores": [round(p["Eelec"] / 1000.0, 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Energía perdida por arrastre aerodinámico (ED)",
                        "unidad": "kJ",
                        "eje": "y2",
                        "color": "#f87171",
                        "valores": [round(p["ED"] / 1000.0, 3) for p in pts_lam],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": "B. Relación de Esbeltez (λ) vs. Longitud (L), Diámetro Máximo (D) y Masa Total (mtot)",
                "x_label": "Relación de esbeltez λ = L/D (adim)",
                "x_actual": lam_actual,
                "y1_label": "Dimensiones del casco: L y D (m)",
                "y2_label": "Masa total del dirigible mtot (kg)",
                "xs": [round(p["lam"], 4) for p in pts_lam],
                "series": [
                    {
                        "nombre": "Longitud total del casco (L)",
                        "unidad": "m",
                        "eje": "y1",
                        "color": "#60a5fa",
                        "valores": [round(p["L"], 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Diámetro máximo del dirigible (D = 2R)",
                        "unidad": "m",
                        "eje": "y1",
                        "color": "#a78bfa",
                        "valores": [round(p["D"], 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Masa total del dirigible (mtot)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#4ade80",
                        "valores": [round(p["mtot"], 4) for p in pts_lam],
                    },
                ],
            },
        ],
    }

    # =========================================================
    # 2. SUSTENTACIÓN Y CARGAS: AIRE CALIENTE vs. MOTORES DRON
    # =========================================================
    mflot_actual = valores["mflot"]
    mflot_min = max(1.2, mflot_actual * 0.55)
    mflot_max = min(valores["mtot"] * 1.06, mflot_actual * 1.15)
    if mflot_max <= mflot_min + 0.3:
        mflot_max = mflot_min + 1.5
    xs_mflot = _linspace(mflot_min, mflot_max, 42, incluir=mflot_actual)
    pts_mflot = [p for x in xs_mflot if (p := simular_punto(valores, mflot=x)) is not None]

    grafica_sustentacion = {
        "id": "sustentacion",
        "indice": 2,
        "titulo": "Sustentación Híbrida: Aire Caliente vs. Motores de Dron",
        "titulo_corto": "Aire Caliente vs. Motores",
        "subtitulo": (
            "Comparación directa de la Carga de Sustentación (mflot vs. mres) y de la Fuerza Vertical "
            "ejercida por cada fuente (F del aire caliente vs. FL de los 4 motores) junto con la Masa Total."
        ),
        "variables": vars_meta(["mflot", "mres", "mtot", "mbat", "mbe", "mbp", "F", "FL", "FLmax", "Fexc", "Pelec", "Pad", "Ptot", "Pmax", "Etot"]),
        "paneles": [
            {
                "tipo": "barras_comparativas",
                "titulo": "A. Comparativa en Punto Actual: Cargas de Sustentación (kg) y Fuerzas Verticales (N)",
                "grupos": [
                    {
                        "subtitulo": "Reparto de Carga y Masa Total (kg)",
                        "unidad": "kg",
                        "barras": [
                            {
                                "etiqueta": "Carga Aire Caliente (mflot)",
                                "codigo": "mflot",
                                "valor": round(valores["mflot"], 3),
                                "color": "#f97316",
                                "detalle": f"{(valores['mflot'] / valores['mtot'] * 100):.1f}% de mtot",
                            },
                            {
                                "etiqueta": "Carga Motores Dron (mres)",
                                "codigo": "mres",
                                "valor": round(valores["mres"], 3),
                                "color": "#38bdf8",
                                "detalle": f"{(valores['mres'] / valores['mtot'] * 100):.1f}% de mtot",
                            },
                            {
                                "etiqueta": "Masa Total Dirigible (mtot)",
                                "codigo": "mtot",
                                "valor": round(valores["mtot"], 3),
                                "color": "#4ade80",
                                "detalle": "mflot + mres",
                            },
                        ],
                    },
                    {
                        "subtitulo": "Fuerza Vertical por Fuente y Capacidad (N)",
                        "unidad": "N",
                        "barras": [
                            {
                                "etiqueta": "Fuerza Aire Caliente (F)",
                                "codigo": "F",
                                "valor": round(valores["F"], 3),
                                "color": "#f97316",
                                "detalle": "Empuje de Arquímedes",
                            },
                            {
                                "etiqueta": "Fuerza Vertical Motores (FL)",
                                "codigo": "FL",
                                "valor": round(valores["FL"], 3),
                                "color": "#38bdf8",
                                "detalle": "mres·g + mtot·az",
                            },
                            {
                                "etiqueta": "Sustentación Máx. Motores (FLmax)",
                                "codigo": "FLmax",
                                "valor": round(valores["FLmax"], 3),
                                "color": "#a78bfa",
                                "detalle": f"Excedente Fexc = {valores['Fexc']:.2f} N",
                            },
                        ],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": "B. Variación de Fuerzas (F, FL), Carga de Motores (mres), Batería (mbat) y Masa Total (mtot) según mflot",
                "x_label": "Carga de sustentación destinada al aire caliente mflot (kg)",
                "x_actual": mflot_actual,
                "y1_label": "Fuerza vertical de sustentación (N)",
                "y2_label": "Masas: mres, mbat y mtot (kg)",
                "xs": [round(p["mflot"], 4) for p in pts_mflot],
                "series": [
                    {
                        "nombre": "Fuerza vertical Aire Caliente (F)",
                        "unidad": "N",
                        "eje": "y1",
                        "color": "#f97316",
                        "valores": [round(p["F"], 3) for p in pts_mflot],
                    },
                    {
                        "nombre": "Fuerza vertical Motores Dron (FL)",
                        "unidad": "N",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["FL"], 3) for p in pts_mflot],
                    },
                    {
                        "nombre": "Carga en Motores Dron (mres)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#facc15",
                        "valores": [round(p["mres"], 4) for p in pts_mflot],
                    },
                    {
                        "nombre": "Masa de batería requerida (mbat)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#f472b6",
                        "valores": [round(p["mbat"], 4) for p in pts_mflot],
                    },
                    {
                        "nombre": "Masa Total del Dirigible (mtot)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#4ade80",
                        "dashed": True,
                        "valores": [round(p["mtot"], 4) for p in pts_mflot],
                    },
                ],
            },
        ],
    }

    # =========================================================
    # 3. DISTANCIA (dm), VIAJES (nv) Y TIEMPO DE VUELO (tm)
    # =========================================================
    d1_actual = valores["d1"]
    dm_actual = valores["dm"]
    dm_min = max(40.0, min(d1_actual * 0.5, dm_actual * 0.25))
    dm_max = max(6.0 * d1_actual, dm_actual * 2.5)
    xs_dm = _linspace(dm_min, dm_max, 42, incluir=dm_actual)
    pts_dm = [p for x in xs_dm if (p := simular_punto(valores, dm=x)) is not None]

    v_actual = valores["v"]
    vv_actual = max(0.0, valores.get("vv", 0.0))
    vpitch_actual = valores["vpitch"]
    v_min = max(0.8, vv_actual + 0.35)
    v_max_techo = max(min(vpitch_actual * 0.85, max(9.0, v_actual + 2.5)), min(vpitch_actual * 0.96, v_actual))
    v_max = v_max_techo if v_max_techo > v_min + 0.3 else min(vpitch_actual * 0.96, v_min + 1.5)
    xs_v = _linspace(v_min, v_max, 42, incluir=v_actual)
    pts_v = [p for x in xs_v if (p := simular_punto(valores, v=x)) is not None]
    pts_v_validos = [p for p in pts_v if p["valido"]]
    opt_v = min(pts_v_validos, key=lambda d: d["Etot"]) if pts_v_validos else None

    grafica_distancia = {
        "id": "distancia_tiempo",
        "indice": 3,
        "titulo": "Distancia (dm), Viajes (nv) y Tiempo de Vuelo (tm) vs. Energía, Combustible, Batería y Costo",
        "titulo_corto": "Distancia, Viajes y Tiempo",
        "subtitulo": (
            "Cómo escalan Tiempo de Vuelo (tm), Energía Total (Etot), Combustible (mgm), Batería (mbat) y Costo Operativo (Cop) "
            "con la Distancia total (dm = nv·d1), y el compromiso velocidad/viento en contra (vg = v - vv)."
        ),
        "variables": vars_meta(["d1", "nv", "dm", "tm", "v", "vv", "vg", "nprop", "vpitch", "Etot", "mgm", "mbat", "mbe", "mbp", "mtot", "Pelec", "Pad", "Ptot", "Pmax", "Ttot", "theta", "Cop", "Cpre", "Ccomb", "Celec"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Distancia (dm = nv·d1) vs. Energía (Etot), Combustible (mgm), Batería (mbat) y Costo (Cop)",
                "x_label": f"Distancia total de misión dm (m)  [1 viaje base = {d1_actual:.0f} m]",
                "x_actual": dm_actual,
                "x_optimo": d1_actual,
                "x_optimo_label": f"1 viaje base ({d1_actual:.0f} m)",
                "y1_label": "Energía total Etot (kJ) / Tiempo tm (s)",
                "y2_label": "Combustible mgm y Batería mbat (g) / Costo Cop (Bs)",
                "xs": [round(p["dm"], 2) for p in pts_dm],
                "series": [
                    {
                        "nombre": "Energía consumida en total (Etot)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["Etot"] / 1000.0, 3) for p in pts_dm],
                    },
                    {
                        "nombre": "Tiempo de vuelo (tm)",
                        "unidad": "s",
                        "eje": "y1",
                        "color": "#a78bfa",
                        "dashed": True,
                        "valores": [round(p["tm"], 2) for p in pts_dm],
                    },
                    {
                        "nombre": "Masa de combustible térmico (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(p["mgm"] * 1000.0, 3) for p in pts_dm],
                    },
                    {
                        "nombre": "Masa de batería requerida (mbat)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f472b6",
                        "valores": [round(p["mbat"] * 1000.0, 3) for p in pts_dm],
                    },
                    {
                        "nombre": "Costo operativo total (Cop)",
                        "unidad": "Bs",
                        "eje": "y2",
                        "color": "#4ade80",
                        "dashed": True,
                        "valores": [round(p["Cop"], 3) for p in pts_dm],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": f"B. Velocidad (v) vs. Tiempo (tm = dm/(v - vv)) con viento en contra vv = {vv_actual:.1f} m/s",
                "x_label": "Velocidad relativa al aire v (m/s)  [← más tiempo tm | menos tiempo tm →]",
                "x_actual": v_actual,
                "x_optimo": opt_v["v"] if opt_v else None,
                "x_optimo_label": f"Mín. Etot válido (v={opt_v['v']:.2f} m/s)" if opt_v else "",
                "y1_label": "Energías en misión: Etot y Em (kJ)",
                "y2_label": "Tiempo de vuelo tm (s) / Energía eléc. (kJ)",
                "xs": [round(p["v"], 3) for p in pts_v],
                "series": [
                    {
                        "nombre": "Energía total consumida (Etot)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["Etot"] / 1000.0, 3) for p in pts_v],
                    },
                    {
                        "nombre": "Energía térmica perdida (Em)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#f97316",
                        "dashed": True,
                        "valores": [round(p["Em"] / 1000.0, 3) for p in pts_v],
                    },
                    {
                        "nombre": "Energía eléctrica motores (3600·Ereq)",
                        "unidad": "kJ",
                        "eje": "y2",
                        "color": "#facc15",
                        "valores": [round(p["Eelec_J"] / 1000.0, 3) for p in pts_v],
                    },
                    {
                        "nombre": "Tiempo de vuelo requerido (tm)",
                        "unidad": "s",
                        "eje": "y2",
                        "color": "#a78bfa",
                        "valores": [round(p["tm"], 2) for p in pts_v],
                    },
                ],
            },
        ],
    }

    # =========================================================
    # 4. ESPESOR DEL AISLANTE MYLAR MULTICAPA (e) vs. ENERGÍA AHORRADA Y PERDIDA
    # =========================================================
    e_actual_mm = valores["e"] * 1000.0
    xs_e_mm = _linspace(3.0, 45.0, 46, incluir=e_actual_mm)
    pts_e = [p for x_mm in xs_e_mm if (p := simular_punto(valores, e=x_mm / 1000.0)) is not None]

    # Espesor óptimo donde la pérdida térmica Em es mínima (y el ahorro Eah es máximo)
    opt_e = min(pts_e, key=lambda d: d["Em"]) if pts_e else None
    opt_e_mm = round(opt_e["e"] * 1000.0, 2) if opt_e else None

    grafica_aislante = {
        "id": "aislante",
        "indice": 4,
        "titulo": "Aislante Mylar Multicapa Asimétrico (e) vs. Energía Ahorrada y Perdida",
        "titulo_corto": "Mylar Multicapa: Ahorro vs. e",
        "subtitulo": (
            "Cómo influye el Espesor por Capa (e) con Mylar aluminizado asimétrico (ncapS/ncapI), radiación (hrad) y Hollands (Nuc) "
            "en la Energía Ahorrada (Eah), Energía Perdida (Em vs Em0 constante), Combustible (mgm) y Masa Total (mtot)."
        ),
        "variables": vars_meta(["e", "ncapS", "ncapI", "eps", "hrad", "Nuc", "Usup", "Uinf", "U", "U0", "Eah", "Em", "Em0", "mc", "mmamp", "mtot", "mgm"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Espesor por Capa (e) vs. Energía Ahorrada (Eah), Energía Perdida (Em) y Combustible (mgm)",
                "x_label": "Espesor por capa Mylar e (mm)",
                "x_actual": round(e_actual_mm, 2),
                "x_optimo": opt_e_mm,
                "x_optimo_label": f"Óptimo térmico ({opt_e_mm:.1f} mm)" if opt_e_mm else "",
                "y1_label": "Energía térmica en misión (kJ)",
                "y2_label": "Masa de combustible necesaria mgm (g)",
                "xs": [round(p["e"] * 1000.0, 2) for p in pts_e],
                "series": [
                    {
                        "nombre": "Energía ahorrada gracias al aislante (Eah)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#4ade80",
                        "valores": [round(p["Eah"] / 1000.0, 3) for p in pts_e],
                    },
                    {
                        "nombre": "Energía perdida con aislante (Em)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#f87171",
                        "valores": [round(p["Em"] / 1000.0, 3) for p in pts_e],
                    },
                    {
                        "nombre": "Energía perdida sin aislante (Em0)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#94a3b8",
                        "dashed": True,
                        "valores": [round(p["Em0"] / 1000.0, 3) for p in pts_e],
                    },
                    {
                        "nombre": "Masa de combustible necesaria (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(p["mgm"] * 1000.0, 3) for p in pts_e],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": "B. Espesor del Aislante (e) vs. Potencias Térmicas (dQp, Qp), Masa Celular (mc) y Masa Total (mtot)",
                "x_label": "Espesor del aislante celular e (mm)",
                "x_actual": round(e_actual_mm, 2),
                "x_optimo": opt_e_mm,
                "x_optimo_label": f"Óptimo térmico ({opt_e_mm:.1f} mm)" if opt_e_mm else "",
                "y1_label": "Potencia térmica: Ahorrada dQp y Perdida Qp (W)",
                "y2_label": "Masa cuadrícula mc (g) / Masa total mtot (kg)",
                "xs": [round(p["e"] * 1000.0, 2) for p in pts_e],
                "series": [
                    {
                        "nombre": "Potencia ahorrada por aislante (dQp)",
                        "unidad": "W",
                        "eje": "y1",
                        "color": "#4ade80",
                        "valores": [round(p["dQp"], 2) for p in pts_e],
                    },
                    {
                        "nombre": "Potencia perdida con aislante (Qp)",
                        "unidad": "W",
                        "eje": "y1",
                        "color": "#f87171",
                        "valores": [round(p["Qp"], 2) for p in pts_e],
                    },
                    {
                        "nombre": "Masa de la cuadrícula aislante (mc)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#facc15",
                        "valores": [round(p["mc"] * 1000.0, 2) for p in pts_e],
                    },
                    {
                        "nombre": "Masa total del dirigible (mtot)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#38bdf8",
                        "dashed": True,
                        "valores": [round(p["mtot"], 4) for p in pts_e],
                    },
                ],
            },
        ],
    }

    # =========================================================
    # 5. BALANCE TÉRMICO, ENERGÍA PERDIDA/AHORRADA Y COMBUSTIBLE TÉRMICO EN EL VUELO
    # =========================================================
    tm_actual = valores["tm"]
    ts_vuelo = _linspace(0.0, tm_actual, 36)
    qp0_w = valores["Qp0"]
    qp_w = valores["Qp"]
    dqp_w = valores["dQp"]
    ptot_w = valores["Ptot"]
    pc_ef = valores["ncal"] * valores["PC"]

    grafica_propano = {
        "id": "propano_energia",
        "indice": 5,
        "titulo": "Energía Perdida, Energía Ahorrada y Combustible Térmico (mgm) en el Vuelo",
        "titulo_corto": "Combustible y Balance Térmico",
        "subtitulo": (
            "Evolución acumulada a lo largo del Tiempo de Vuelo (tm) de la Energía Perdida, la Energía Ahorrada "
            "gracias al aislante, la Energía Total Consumida y la Masa de Combustible Térmico necesaria (con eficiencia ncal)."
        ),
        "variables": vars_meta(["mgm", "ncal", "fcal", "Eprop", "Em", "Eah", "Em0", "Etot", "Qc", "mgc", "mp", "mbat", "mbe", "mbp", "mbmax", "dmbat", "Pelec", "Pad", "Ptot", "Pmax", "tm", "dm"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": f"A. Evolución Temporal Acumulada durante el Vuelo (0 → {tm_actual:.1f} s / {valores['dm']:.0f} m)",
                "x_label": "Tiempo transcurrido de vuelo t (s)",
                "x_actual": round(tm_actual, 2),
                "y1_label": "Energía acumulada (kJ)",
                "y2_label": "Masa de combustible térmico consumida mgm (g)",
                "xs": [round(t, 2) for t in ts_vuelo],
                "series": [
                    {
                        "nombre": "Energía perdida sin aislante (Em0)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#94a3b8",
                        "dashed": True,
                        "valores": [round((qp0_w * t) / 1000.0, 3) for t in ts_vuelo],
                    },
                    {
                        "nombre": "Energía ahorrada por aislante (Eah)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#4ade80",
                        "valores": [round((dqp_w * t) / 1000.0, 3) for t in ts_vuelo],
                    },
                    {
                        "nombre": "Energía perdida con aislante (Em)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#f87171",
                        "valores": [round((qp_w * t) / 1000.0, 3) for t in ts_vuelo],
                    },
                    {
                        "nombre": "Energía consumida en total (Etot)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round((((qp_w / valores["ncal"]) + ptot_w) * t) / 1000.0, 3) for t in ts_vuelo],
                    },
                    {
                        "nombre": "Masa de combustible térmico consumida (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(((qp_w * t) / pc_ef) * 1000.0, 3) for t in ts_vuelo],
                    },
                ],
            },
            {
                "tipo": "barras_comparativas",
                "titulo": "B. Resumen Comparativo de Energías de Misión (kJ) y Masas de Combustible/Batería (g)",
                "grupos": [
                    {
                        "subtitulo": "Comparativa de Energías en la Misión (kJ)",
                        "unidad": "kJ",
                        "barras": [
                            {
                                "etiqueta": "Perdida Sin Aislante (Em0)",
                                "codigo": "Em0",
                                "valor": round(valores["Em0"] / 1000.0, 3),
                                "color": "#94a3b8",
                                "detalle": f"Qp0 = {valores['Qp0']:.1f} W",
                            },
                            {
                                "etiqueta": "Ahorrada por Aislante (Eah)",
                                "codigo": "Eah",
                                "valor": round(valores["Eah"] / 1000.0, 3),
                                "color": "#4ade80",
                                "detalle": f"Ahorro del {(valores['fais'] * 100):.1f}%",
                            },
                            {
                                "etiqueta": "Perdida Con Aislante (Em)",
                                "codigo": "Em",
                                "valor": round(valores["Em"] / 1000.0, 3),
                                "color": "#f87171",
                                "detalle": f"Qp = {valores['Qp']:.1f} W",
                            },
                            {
                                "etiqueta": "Suministrada por Combustible Térmico (Eprop)",
                                "codigo": "Eprop",
                                "valor": round(valores["Eprop"] / 1000.0, 3),
                                "color": "#a78bfa",
                                "detalle": f"Em / ncal (ncal = {valores['ncal']:.2f})",
                            },
                            {
                                "etiqueta": "Total Consumida (Etot)",
                                "codigo": "Etot",
                                "valor": round(valores["Etot"] / 1000.0, 3),
                                "color": "#38bdf8",
                                "detalle": f"Eprop + {valores['Eelec'] / 1000.0:.2f} kJ eléc.",
                            },
                        ],
                    },
                    {
                        "subtitulo": "Masas de Combustible Térmico y Batería: Requerida vs. Límite (g)",
                        "unidad": "g",
                        "barras": [
                            {
                                "etiqueta": "Combustible térmico para terminar el vuelo (mgm)",
                                "codigo": "mgm",
                                "valor": round(valores["mgm"] * 1000.0, 3),
                                "color": "#f97316",
                                "detalle": f"Misión de {valores['dm']:.0f} m ({valores['tm']:.1f} s)",
                            },
                            {
                                "etiqueta": "Combustible térmico para recuperar caída dTc (mgc)",
                                "codigo": "mgc",
                                "valor": round(valores["mgc"] * 1000.0, 3),
                                "color": "#facc15",
                                "detalle": f"Caída dTc = {valores['dTc']:.0f} K",
                            },
                            {
                                "etiqueta": "Combustible térmico total a bordo (mp)",
                                "codigo": "mp",
                                "valor": round(valores["mp"] * 1000.0, 3),
                                "color": "#4ade80",
                                "detalle": f"Autonomía térmica x{(valores['mp'] / max(1e-9, valores['mgm'])):.1f} vuelos",
                            },
                            {
                                "etiqueta": "Batería requerida (mbat)",
                                "codigo": "mbat",
                                "valor": round(valores["mbat"] * 1000.0, 3),
                                "color": "#f472b6",
                                "detalle": f"Energía: {valores['mbe'] * 1000.0:.1f} g | Potencia: {valores['mbp'] * 1000.0:.1f} g",
                            },
                            {
                                "etiqueta": "Límite máximo batería (mbmax)",
                                "codigo": "mbmax",
                                "valor": round(valores["mbmax"] * 1000.0, 3),
                                "color": "#94a3b8",
                                "detalle": f"Margen dmbat = {valores['dmbat'] * 1000.0:.1f} g",
                            },
                        ],
                    },
                ],
            },
        ],
    }

    # =========================================================
    # 6. DIMENSIONES (L, D) vs. FUERZAS DE SUSTENTACIÓN Y MASA TOTAL
    # =========================================================
    grafica_geometria = {
        "id": "geometria_masas",
        "indice": 6,
        "titulo": "Longitud (L) y Diámetro (D) vs. Sustentación y Masa Total",
        "titulo_corto": "Dimensiones (L, D) y Masas",
        "subtitulo": (
            "Cómo escalan la Longitud (L) y el Diámetro Máximo (D = 2R) con la Fuerza de Sustentación "
            "del Aire Caliente (F), junto con la silueta a escala del casco y el desglose de la Masa Total (mtot)."
        ),
        "variables": vars_meta(["L", "D", "R", "lam", "V", "S", "F", "FL", "mflot", "mres", "mtot"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Longitud (L), Diámetro Máximo (D) y Volumen (V) según la Carga de Aire Caliente (mflot)",
                "x_label": "Carga de sustentación del aire caliente mflot (kg)",
                "x_actual": mflot_actual,
                "y1_label": "Longitud L y Diámetro máximo D (m)",
                "y2_label": "Volumen V (m³) y Superficie S (m²)",
                "xs": [round(p["mflot"], 4) for p in pts_mflot],
                "series": [
                    {
                        "nombre": "Longitud total del dirigible (L)",
                        "unidad": "m",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["L"], 3) for p in pts_mflot],
                    },
                    {
                        "nombre": "Diámetro máximo del dirigible (D = 2R)",
                        "unidad": "m",
                        "eje": "y1",
                        "color": "#a78bfa",
                        "valores": [round(p["D"], 3) for p in pts_mflot],
                    },
                    {
                        "nombre": "Volumen del casco (V)",
                        "unidad": "m³",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(p["V"], 3) for p in pts_mflot],
                    },
                    {
                        "nombre": "Área superficial total (S)",
                        "unidad": "m²",
                        "eje": "y2",
                        "color": "#4ade80",
                        "dashed": True,
                        "valores": [round(p["S"], 3) for p in pts_mflot],
                    },
                ],
            },
            {
                "tipo": "silueta_y_masas",
                "titulo": "B. Silueta Geométrica a Escala (L × D) y Desglose Completo de la Masa Total (mtot)",
                "geometria": {
                    "L": round(valores["L"], 3),
                    "D": round(valores["D"], 3),
                    "R": round(valores["R"], 3),
                    "cf": round(valores["cf"], 3),
                    "cr": round(valores["cr"], 3),
                    "lam": round(valores["lam"], 3),
                    "V": round(valores["V"], 3),
                    "S": round(valores["S"], 3),
                    "e_mm": round(valores["e"] * 1000.0, 1),
                },
                "desglose_masas": [
                    {
                        "etiqueta": "Carga útil (mcarga)",
                        "codigo": "mcarga",
                        "valor_g": round(valores["mcarga"] * 1000.0, 2),
                        "color": "#38bdf8",
                    },
                    {
                        "etiqueta": "Componentes adicionales (mad)",
                        "codigo": "mad",
                        "valor_g": round(valores["mad"] * 1000.0, 2),
                        "color": "#60a5fa",
                    },
                    {
                        "etiqueta": "Cuadrícula aislante Mylar (mc)",
                        "codigo": "mc",
                        "valor_g": round(valores["mc"] * 1000.0, 2),
                        "color": "#4ade80",
                    },
                    {
                        "etiqueta": "Mamparos internos (mmamp)",
                        "codigo": "mmamp",
                        "valor_g": round(valores["mmamp"] * 1000.0, 2),
                        "color": "#2dd4bf",
                    },
                    {
                        "etiqueta": "Combustible térmico a bordo (mp)",
                        "codigo": "mp",
                        "valor_g": round(valores["mp"] * 1000.0, 2),
                        "color": "#f97316",
                    },
                    {
                        "etiqueta": "4 Motores Brushless A2212 (N·mmot)",
                        "codigo": "mmot",
                        "valor_g": round(valores["N"] * valores["mmot"] * 1000.0, 2),
                        "color": "#a78bfa",
                    },
                    {
                        "etiqueta": "Batería requerida (mbat)",
                        "codigo": "mbat",
                        "valor_g": round(valores["mbat"] * 1000.0, 2),
                        "color": "#facc15",
                    },
                ],
                "mtot_kg": round(valores["mtot"], 3),
                "mflot_kg": round(valores["mflot"], 3),
                "mres_kg": round(valores["mres"], 3),
            },
        ],
    }

    # =========================================================
    # 7. TEMPERATURA INTERIOR ÓPTIMA (T2) Y ESCALABILIDAD MULTI-VIAJE (nv)
    # =========================================================
    T2_actual = valores["T2"]
    xs_T2 = _linspace(max(valores["T1"] + 30.0, 50.0), 115.0, 40, incluir=T2_actual)
    pts_T2: list[dict[str, float]] = []
    for t2_x in xs_T2:
        p_t2 = simular_punto(valores, T2=t2_x)
        if p_t2 is not None:
            rho2_drop = p_t2["P2"] / (p_t2["R2"] * (t2_x - 10.0 + 273.15))
            drho_drop = p_t2["rho1"] - rho2_drop
            pct_loss_10k = 100.0 * (1.0 - drho_drop / max(1e-9, p_t2["drho"]))
            p_t2["pct_loss_10k"] = pct_loss_10k
            pts_T2.append(p_t2)

    pts_T2_seguros = [p for p in pts_T2 if p["valido"] and p["pct_loss_10k"] <= 16.0]
    opt_T2 = min(pts_T2_seguros, key=lambda d: d["Etot"]) if pts_T2_seguros else None

    nv_actual = valores["nv"]
    xs_nv = _linspace(1.0, max(14.0, nv_actual * 2.5), 28, incluir=nv_actual)
    pts_nv: list[dict[str, float]] = []
    for nv_x in xs_nv:
        p_nv = simular_punto(valores, nv=nv_x)
        if p_nv is not None:
            # Batería equivalente de un dron puro con la misma masa mtot en el mismo perfil de vuelo
            fl_dron = p_nv["mtot"] * p_nv["g"] + p_nv["mtot"] * p_nv["az"]
            fx_dron = max(1.2, 0.35 * p_nv["FD"]) + p_nv["map"] * p_nv["ax"]
            t_dron = math.hypot(fl_dron, fx_dron)
            p_dron = (p_nv["km"] / p_nv["ntot"]) * (
                (t_dron ** 1.5) / math.sqrt(2.0 * p_nv["rho1"] * p_nv["N"] * p_nv["Ap"])
                + fx_dron * p_nv["v"]
            ) + p_nv["Pad"]
            ereq_dron = (p_dron * p_nv["tm"]) / 3600.0
            mbe_dron = ereq_dron / (p_nv["ebat"] * p_nv["DoD"] * p_nv["ntemp"])
            mbp_dron = p_dron / (p_nv["ebat"] * p_nv["Cmax"] * p_nv["ntemp"])
            p_nv["mbat_dron_g"] = max(mbe_dron, mbp_dron) * 1000.0
            pts_nv.append(p_nv)

    grafica_temp_escalabilidad = {
        "id": "temperatura_escalabilidad",
        "indice": 7,
        "titulo": "Temperatura Interior Óptima (T2) y Escalabilidad Multi-Viaje (nv)",
        "titulo_corto": "T2 Óptima y Escalabilidad",
        "subtitulo": (
            "Delimitación del punto dulce de temperatura T2 (~80–90 °C): bajar T2 reduce Qp y Etot hasta que el crecimiento del volumen V "
            "y la sensibilidad a caídas térmicas (-10 K) dominan. El Panel B demuestra la escalabilidad del dirigible frente a un dron puro."
        ),
        "variables": vars_meta(["T2", "dT", "V", "Qp", "Etot", "nv", "d1", "dm", "mbat", "mbmax", "mgm", "Cop", "Cpre"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Temperatura Interior (T2) vs. Pérdida (Qp), Energía (Etot), Volumen (V) y Sensibilidad (-10 K)",
                "x_label": "Temperatura interior T2 (°C)",
                "x_actual": round(T2_actual, 1),
                "x_optimo": round(opt_T2["T2"], 1) if opt_T2 else None,
                "x_optimo_label": f"Óptimo seguro (T2={opt_T2['T2']:.1f}°C)" if opt_T2 else "",
                "y1_label": "Potencia perdida Qp (W) / Energía Etot (kJ)",
                "y2_label": "Volumen V (m³) / Pérdida sustentación -10 K (%)",
                "xs": [round(p["T2"], 2) for p in pts_T2],
                "series": [
                    {
                        "nombre": "Potencia perdida con aislante (Qp)",
                        "unidad": "W",
                        "eje": "y1",
                        "color": "#f87171",
                        "valores": [round(p["Qp"], 1) for p in pts_T2],
                    },
                    {
                        "nombre": "Energía total en misión (Etot)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["Etot"] / 1000.0, 2) for p in pts_T2],
                    },
                    {
                        "nombre": "Volumen del casco (V)",
                        "unidad": "m³",
                        "eje": "y2",
                        "color": "#4ade80",
                        "valores": [round(p["V"], 2) for p in pts_T2],
                    },
                    {
                        "nombre": "Pérdida de sustentación si cae 10 K",
                        "unidad": "%",
                        "eje": "y2",
                        "color": "#facc15",
                        "dashed": True,
                        "valores": [round(p["pct_loss_10k"], 1) for p in pts_T2],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": f"B. Escalabilidad Multi-Viaje (nv × {d1_actual:.0f} m): Batería Dirigible vs. Dron Puro",
                "x_label": f"Número de viajes consecutivos nv (tramo d1 = {d1_actual:.0f} m)",
                "x_actual": round(nv_actual, 2),
                "x_optimo": 1.0,
                "x_optimo_label": "1 viaje (280 m)",
                "y1_label": "Masa de batería requerida (g)",
                "y2_label": "Combustible mgm (g) / Costo Cop (Bs)",
                "xs": [round(p["nv"], 2) for p in pts_nv],
                "series": [
                    {
                        "nombre": "Batería dirigible híbrido (mbat)",
                        "unidad": "g",
                        "eje": "y1",
                        "color": "#4ade80",
                        "valores": [round(p["mbat"] * 1000.0, 1) for p in pts_nv],
                    },
                    {
                        "nombre": "Batería dron puro equivalente",
                        "unidad": "g",
                        "eje": "y1",
                        "color": "#f87171",
                        "dashed": True,
                        "valores": [round(p["mbat_dron_g"], 1) for p in pts_nv],
                    },
                    {
                        "nombre": "Combustible térmico consumido (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(p["mgm"] * 1000.0, 2) for p in pts_nv],
                    },
                    {
                        "nombre": "Costo operativo total (Cop)",
                        "unidad": "Bs",
                        "eje": "y2",
                        "color": "#a78bfa",
                        "valores": [round(p["Cop"], 2) for p in pts_nv],
                    },
                ],
            },
        ],
    }

    return [
        grafica_esbeltez,
        grafica_sustentacion,
        grafica_distancia,
        grafica_aislante,
        grafica_propano,
        grafica_geometria,
        grafica_temp_escalabilidad,
    ]
