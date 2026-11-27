"""
Generador de macro VBA nativa para SolidWorks (.bas) a partir de cualquier archivo JSON
exportado desde el histórico de la Calculadora de Sustentación de Dirigibles.

Construye un modelo sólido multicuerpo referencial con:
  1. Casco bi-semielipsoidal hueco + capas celulares asimétricas simples (ncapS arriba /
     ncapI abajo, separadas por e) y anillos separadores simples visibles en vista de corte.
  2. Góndola rectangular de componentes internos centrada en el centro de flotación (x_cb).
  3. Dos soportes verticales de suspensión entre el casco y la góndola.
  4. Bastidor en "H" conectado estructuralmente debajo de los puntales dentro de la góndola
     y reforzado con 4 tirantes diagonales triangulados hacia las esquinas de la góndola.
  5. N motores cilíndricos referenciales y discos de hélice de diámetro dp.

Uso:
  python generar_cad_solidworks.py
  python generar_cad_solidworks.py --input especf_optm_hist/historico_dirigible_2026-11-25.json
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def radio_casco(x: float, r_max: float, cf: float, cr: float) -> float:
    """Radio transversal r(x) del casco bi-semielipsoidal prolado en la estación axial x."""
    if x <= 0.0 or x >= cf + cr:
        return 0.0
    if x <= cf:
        u = (cf - x) / max(1e-9, cf)
        return r_max * math.sqrt(max(0.0, 1.0 - u * u))
    u = (x - cf) / max(1e-9, cr)
    return r_max * math.sqrt(max(0.0, 1.0 - u * u))


def radio_capa(x: float, r_max: float, cf: float, cr: float, offset_r: float) -> float:
    """Radio transversal de una lámina concéntrica desplazada `offset_r` hacia el interior."""
    r_k = r_max - offset_r
    cf_k = cf - offset_r
    cr_k = cr - offset_r
    if r_k <= 0.01 or cf_k <= 0.01 or cr_k <= 0.01:
        return 0.0
    return radio_casco(x - offset_r, r_k, cf_k, cr_k)


def _puntos_semielipse(
    x_ini: float,
    r_max: float,
    cf: float,
    cr: float,
    n_nose: int = 34,
    n_tail: int = 42,
    invertir: bool = False,
) -> list[tuple[float, float]]:
    pts: list[tuple[float, float]] = []
    for i in range(n_nose + 1):
        ang = math.pi * 0.5 * (i / n_nose)
        x = x_ini + cf * (1.0 - math.cos(ang))
        y = r_max * math.sin(ang)
        pts.append((x, y))
    for i in range(1, n_tail + 1):
        ang = math.pi * 0.5 * (i / n_tail)
        x = x_ini + cf + cr * math.sin(ang)
        y = r_max * math.cos(ang)
        pts.append((x, y))
    pts[0] = (x_ini, 0.0)
    pts[-1] = (x_ini + cf + cr, 0.0)
    if invertir:
        pts.reverse()
    return pts


def _puntos_barra_inclinada(
    u1: float,
    v1: float,
    u2: float,
    v2: float,
    grosor: float,
) -> tuple[tuple[float, float], tuple[float, float], tuple[float, float], tuple[float, float]]:
    """Devuelve los 4 vértices de una barra rectangular de espesor `grosor` entre (u1, v1) y (u2, v2)."""
    du = u2 - u1
    dv = v2 - v1
    norm = math.hypot(du, dv)
    if norm < 1e-9:
        raise ValueError("Longitud nula en barra inclinada.")
    nu = -dv / norm * (0.5 * grosor)
    nv = du / norm * (0.5 * grosor)
    return (
        (u1 + nu, v1 + nv),
        (u2 + nu, v2 + nv),
        (u2 - nu, v2 - nv),
        (u1 - nu, v1 - nv),
    )


def cargar_registro(ruta_json: Path, indice: int = 0) -> dict[str, Any]:
    data = json.loads(ruta_json.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        if "registros" in data and isinstance(data["registros"], list):
            data = data["registros"]
        elif "especificaciones" in data:
            return data
    if not isinstance(data, list) or not data:
        raise ValueError(f"El archivo '{ruta_json}' no contiene registros válidos.")
    if indice < 0 or indice >= len(data):
        raise IndexError(f"Índice {indice} fuera de rango (0..{len(data) - 1}).")
    return data[indice]


def extraer_parametros_cad(
    reg: dict[str, Any],
    gond_l: float,
    gond_w: float,
    gond_h: float,
    gap: float,
    z_mot: float | None,
    dx_mot: float,
) -> dict[str, Any]:
    esp = reg.get("especificaciones", {})
    ent = reg.get("entradas", {})

    r_max = float(esp["R"])
    cf = float(esp["cf"])
    cr = float(esp["cr"])
    length = float(esp.get("L", cf + cr))
    vol = float(esp.get("V", (2.0 / 3.0) * math.pi * r_max * r_max * length))
    n_mot = max(2, int(round(float(ent.get("N", 4)))))
    dp = float(ent.get("dp", 0.254))

    # Centro de flotación volumétrico exacto del bi-semielipsoide: x_cb = cf + (3/8)*(cr - cf)
    x_cb = cf + 0.375 * (cr - cf)
    r_belly = radio_casco(x_cb, r_max, cf, cr)

    y_gond_top = -(r_belly + gap)
    y_gond_bot = y_gond_top - gond_h
    y_arm = 0.5 * (y_gond_top + y_gond_bot)

    dx_strut = max(0.08, gond_l * 0.5 - 0.08)
    x_s1 = x_cb - dx_strut
    x_s2 = x_cb + dx_strut
    r_s1 = radio_casco(x_s1, r_max, cf, cr)
    r_s2 = radio_casco(x_s2, r_max, cf, cr)
    y_strut_top = -(min(r_s1, r_s2) - 0.025)

    # Separación lateral y longitudinal de motores garantizando holgura frente a la góndola
    z_mot_calc = z_mot if z_mot is not None else max(0.55, gond_w * 0.5 + dp * 0.5 + 0.27)
    n_pares = max(1, n_mot // 2)
    if n_pares == 1:
        xs_pares = [x_cb]
    else:
        xs_pares = [
            x_cb - dx_mot + (2.0 * dx_mot) * i / (n_pares - 1)
            for i in range(n_pares)
        ]

    # Altura de montaje encima del brazo en H (brazo 25 mm -> base motor -> hélice 30 mm arriba)
    h_arm = 0.025
    h_mot = 0.030
    h_prop = 0.006
    y_mot_base = y_arm + 0.5 * h_arm
    y_prop_base = y_mot_base + h_mot
    y_prop_top = y_prop_base + h_prop

    # Verificación de holguras de hélice respecto al casco y a la góndola
    min_holgura_casco = float("inf")
    z_borde_int = max(0.0, z_mot_calc - 0.5 * dp)
    for xp in xs_pares:
        for sx in (xp - 0.5 * dp, xp, xp + 0.5 * dp):
            rx = radio_casco(sx, r_max, cf, cr)
            if rx > z_borde_int:
                y_casco_local = -math.sqrt(max(0.0, rx * rx - z_borde_int * z_borde_int))
                holgura = y_casco_local - y_prop_top
                min_holgura_casco = min(min_holgura_casco, holgura)
    if math.isinf(min_holgura_casco):
        min_holgura_casco = abs(y_prop_top)

    holgura_lat_gondola = z_borde_int - 0.5 * gond_w

    return {
        "nombre": str(reg.get("nombre", "Dirigible referencial")),
        "L": length,
        "D": 2.0 * r_max,
        "R": r_max,
        "cf": cf,
        "cr": cr,
        "V": vol,
        "ncapS": float(esp.get("ncapS", 4.0)),
        "ncapI": float(esp.get("ncapI", 2.0)),
        "e_mm": float(esp.get("e_mm", 14.0)),
        "mbat_g": float(esp.get("mbat_g", 0.0)),
        "mp_g": float(esp.get("mp_g", 0.0)),
        "mcarga": float(esp.get("mcarga", 1.0)),
        "x_cb": x_cb,
        "r_belly": r_belly,
        "gond_l": gond_l,
        "gond_w": gond_w,
        "gond_h": gond_h,
        "gap": gap,
        "y_gond_top": y_gond_top,
        "y_gond_bot": y_gond_bot,
        "y_arm": y_arm,
        "x_s1": x_s1,
        "x_s2": x_s2,
        "y_strut_top": y_strut_top,
        "N": n_mot,
        "dp": dp,
        "z_mot": z_mot_calc,
        "dx_mot": dx_mot,
        "xs_pares": xs_pares,
        "h_arm": h_arm,
        "h_mot": h_mot,
        "h_prop": h_prop,
        "y_mot_base": y_mot_base,
        "y_prop_base": y_prop_base,
        "min_holgura_casco": min_holgura_casco,
        "holgura_lat_gondola": holgura_lat_gondola,
    }


def _bloque_capa_revolucion(
    feat_name: str,
    offset_r: float,
    t_film: float,
    r_max: float,
    cf: float,
    cr: float,
    sym_180: bool,
) -> str:
    """Genera el bloque VBA para una lámina cerrada (piel exterior o capa aislante)."""
    r_o = r_max - offset_r
    cf_o = cf - offset_r
    cr_o = cr - offset_r
    r_i = r_o - t_film
    cf_i = cf_o - t_film
    cr_i = cr_o - t_film

    pts_ext = _puntos_semielipse(offset_r, r_o, cf_o, cr_o, invertir=False)
    pts_int = _puntos_semielipse(offset_r + t_film, r_i, cf_i, cr_i, invertir=True)

    n_e = len(pts_ext)
    n_i = len(pts_int)
    asig_ext = "\n".join(
        f"    extPts({idx*3}) = {x:.6f}: extPts({idx*3+1}) = {y:.6f}: extPts({idx*3+2}) = 0#"
        for idx, (x, y) in enumerate(pts_ext)
    )
    asig_int = "\n".join(
        f"    intPts({idx*3}) = {x:.6f}: intPts({idx*3+1}) = {y:.6f}: intPts({idx*3+2}) = 0#"
        for idx, (x, y) in enumerate(pts_int)
    )

    x_nose_ext = pts_ext[0][0]
    x_tail_ext = pts_ext[-1][0]
    x_tail_int = pts_int[0][0]
    x_nose_int = pts_int[-1][0]

    if sym_180:
        rev_call = f'''    Set swFeat = swFeatMgr.FeatureRevolve2( _
        False, True, False, False, False, False, _
        0, 0, {0.5 * math.pi:.12f}, {0.5 * math.pi:.12f}, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)'''
    else:
        rev_call = f'''    Set swFeat = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, {2.0 * math.pi:.12f}, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)'''

    return f'''    ' --- {feat_name} (offset = {offset_r*1000:.1f} mm, espesor visual = {t_film*1000:.1f} mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To {n_e * 3 - 1}) As Double
    ReDim intPts(0 To {n_i * 3 - 1}) As Double
{asig_ext}
{asig_int}
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine {x_tail_ext:.6f}, 0#, 0#, {x_tail_int:.6f}, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine {x_nose_int:.6f}, 0#, 0#, {x_nose_ext:.6f}, 0#, 0#

    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

{rev_call}
    If Not swFeat Is Nothing Then swFeat.Name = "{feat_name}"
'''


def _bloque_anillos_celulares(
    feat_name: str,
    estaciones_x: list[float],
    offset_ext: float,
    offset_int: float,
    t_film: float,
    r_max: float,
    cf: float,
    cr: float,
    sym_180: bool,
) -> str:
    """Genera anillos separadores radiales simples entre las capas celulares."""
    rects: list[str] = []
    for xc in estaciones_x:
        r_out = radio_capa(xc, r_max, cf, cr, offset_ext + t_film)
        r_in = radio_capa(xc, r_max, cf, cr, offset_int)
        if r_in > 0.08 and r_out > r_in + 0.008:
            rects.append(
                f"    Call DibujarRectangulo(swSketchMgr, {xc - 0.003:.6f}, {r_in - 0.0004:.6f}, {xc + 0.003:.6f}, {r_out + 0.0004:.6f})"
            )
    if not rects:
        return ""

    if sym_180:
        rev_call = f'''    Set swFeat = swFeatMgr.FeatureRevolve2( _
        False, True, False, False, False, False, _
        0, 0, {0.5 * math.pi:.12f}, {0.5 * math.pi:.12f}, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)'''
    else:
        rev_call = f'''    Set swFeat = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, {2.0 * math.pi:.12f}, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)'''

    return f'''    ' --- {feat_name} ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
{chr(10).join(rects)}
    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

{rev_call}
    If Not swFeat Is Nothing Then swFeat.Name = "{feat_name}"
'''


def _bloque_tirantes_plano(
    plane_name: str,
    feat_name: str,
    x_pos: float,
    gond_w: float,
    y_gond_top: float,
    y_arm: float,
    z_mot: float,
) -> str:
    """Genera 2 tirantes diagonales triangulados (en +Z y -Z) sobre un plano transversal en X."""
    z_g = max(0.04, 0.5 * gond_w - 0.012)
    y_g = y_gond_top - 0.020
    z_b = max(z_g + 0.05, z_mot - 0.035)
    y_b = y_arm + 0.006
    grosor = 0.018

    b1 = _puntos_barra_inclinada(z_g, y_g, z_b, y_b, grosor)
    b2 = _puntos_barra_inclinada(-z_g, y_g, -z_b, y_b, grosor)

    return f'''    ' --- {feat_name} (en X = {x_pos:.3f} m) ---
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, {x_pos:.6f}, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "{plane_name}"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarPoligono4(swSketchMgr, {b1[0][0]:.6f}, {b1[0][1]:.6f}, {b1[1][0]:.6f}, {b1[1][1]:.6f}, {b1[2][0]:.6f}, {b1[2][1]:.6f}, {b1[3][0]:.6f}, {b1[3][1]:.6f})
    Call DibujarPoligono4(swSketchMgr, {b2[0][0]:.6f}, {b2[0][1]:.6f}, {b2[1][0]:.6f}, {b2[1][1]:.6f}, {b2[2][0]:.6f}, {b2[2][1]:.6f}, {b2[3][0]:.6f}, {b2[3][1]:.6f})
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, {grosor:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "{feat_name}"
'''


def generar_macro_vba(p: dict[str, Any]) -> str:
    t_film = 0.003  # 3 mm espesor visual para corte limpio en SolidWorks
    e_capa = max(0.008, p["e_mm"] / 1000.0)
    n_inf = max(0, int(round(p["ncapI"])))
    n_sup = max(n_inf, int(round(p["ncapS"])))

    # Construccion de capas concentricas simples
    bloques_capas: list[str] = [
        _bloque_capa_revolucion(
            "Piel_Exterior_Casco", 0.0, t_film, p["R"], p["cf"], p["cr"], sym_180=False
        )
    ]
    for k in range(1, n_inf + 1):
        bloques_capas.append(
            _bloque_capa_revolucion(
                f"Capa_Aislante_{k}_360",
                k * e_capa,
                t_film,
                p["R"],
                p["cf"],
                p["cr"],
                sym_180=False,
            )
        )
    for k in range(n_inf + 1, n_sup + 1):
        bloques_capas.append(
            _bloque_capa_revolucion(
                f"Capa_Aislante_{k}_Sup",
                k * e_capa,
                t_film,
                p["R"],
                p["cf"],
                p["cr"],
                sym_180=True,
            )
        )

    # Anillos separadores celulares simples visibles en Vista de Seccion
    estaciones_anillos = [p["L"] * (0.16 + 0.68 * i / 6.0) for i in range(7)]
    if n_inf >= 1:
        bloques_capas.append(
            _bloque_anillos_celulares(
                "Anillos_Celulares_360",
                estaciones_anillos,
                0.0,
                n_inf * e_capa,
                t_film,
                p["R"],
                p["cf"],
                p["cr"],
                sym_180=False,
            )
        )
    if n_sup > n_inf:
        bloques_capas.append(
            _bloque_anillos_celulares(
                "Anillos_Celulares_Sup",
                estaciones_anillos,
                n_inf * e_capa,
                n_sup * e_capa,
                t_film,
                p["R"],
                p["cf"],
                p["cr"],
                sym_180=True,
            )
        )

    x_g1 = p["x_cb"] - 0.5 * p["gond_l"]
    x_g2 = p["x_cb"] + 0.5 * p["gond_l"]
    x_rail1 = min(p["x_s1"], min(p["xs_pares"])) - 0.025
    x_rail2 = max(p["x_s2"], max(p["xs_pares"])) + 0.025
    span_z = 2.0 * p["z_mot"] + p["h_arm"]
    r_mot = 0.015  # 30 mm dia referencial para A2212
    r_prop = 0.5 * p["dp"]

    xs_mot_code = "\n".join(
        [f"    xsMot({i}) = {xv:.6f}" for i, xv in enumerate(p["xs_pares"])]
    )

    tirantes_del = _bloque_tirantes_plano(
        "Plano_Tirantes_Del",
        "Tirantes_Triangulados_Del",
        p["x_s1"],
        p["gond_w"],
        p["y_gond_top"],
        p["y_arm"],
        p["z_mot"],
    )
    tirantes_tras = _bloque_tirantes_plano(
        "Plano_Tirantes_Tras",
        "Tirantes_Triangulados_Tras",
        p["x_s2"],
        p["gond_w"],
        p["y_gond_top"],
        p["y_arm"],
        p["z_mot"],
    )

    nombre_limpio = (
        p["nombre"]
        .replace("Ó", "O")
        .replace("ó", "o")
        .replace("·", "|")
        .replace("λ", "lam")
        .replace("₂", "2")
        .replace("°", " deg")
        .encode("ascii", "ignore")
        .decode("ascii")
    )
    tipo_capas = "simetricas" if n_sup == n_inf else "asimetricas"

    vba = f'''Attribute VB_Name = "DirigibleReferencial"
Option Explicit

' =============================================================================
' Modelo CAD Referencial de Dirigible Hibrido para SolidWorks
' Generado automaticamente por generar_cad_solidworks.py
' Caso: {nombre_limpio}
' Casco hueco + capas celulares {tipo_capas}: {n_sup} sup / {n_inf} inf (e = {p["e_mm"]:.1f} mm)
' Dimensiones: L={p["L"]:.3f} m | D={p["D"]:.3f} m (cf={p["cf"]:.3f} m, cr={p["cr"]:.3f} m) | V={p["V"]:.2f} m3
' Centro flotacion X_CB = {p["x_cb"]:.3f} m | Motores: {p["N"]} x dia {p["dp"]*1000:.0f} mm en +/-{p["z_mot"]:.3f} m
' Gondola: {p["gond_l"]*1000:.0f} x {p["gond_w"]*1000:.0f} x {p["gond_h"]*1000:.0f} mm (gap {p["gap"]*1000:.0f} mm)
' =============================================================================

Private Const SW_DEFAULT_TEMPLATE_PART As Long = 8
Private Const SW_END_BLIND As Long = 0
Private Const SW_END_MIDPLANE As Long = 6
Private Const SW_REFPLANE_DIST As Long = 8
Private Const SW_REFPLANE_FLIP As Long = 256
Private Const SW_UNITS_LINEAR As Long = 0
Private Const SW_MM As Long = 0

Private Sub ObtenerPlanosBase(ByVal swModel As Object, ByRef plFront As Object, ByRef plTop As Object, ByRef plRight As Object)
    Dim swFeat As Object
    Dim encontrados As Long
    Set swFeat = swModel.FirstFeature
    encontrados = 0
    Do While Not swFeat Is Nothing
        If swFeat.GetTypeName2 = "RefPlane" Then
            encontrados = encontrados + 1
            If encontrados = 1 Then
                Set plFront = swFeat
            ElseIf encontrados = 2 Then
                Set plTop = swFeat
            ElseIf encontrados = 3 Then
                Set plRight = swFeat
                Exit Do
            End If
        End If
        Set swFeat = swFeat.GetNextFeature
    Loop
End Sub

Private Sub DibujarRectangulo(ByVal swSketchMgr As Object, ByVal x1 As Double, ByVal y1 As Double, ByVal x2 As Double, ByVal y2 As Double)
    swSketchMgr.CreateLine x1, y1, 0#, x2, y1, 0#
    swSketchMgr.CreateLine x2, y1, 0#, x2, y2, 0#
    swSketchMgr.CreateLine x2, y2, 0#, x1, y2, 0#
    swSketchMgr.CreateLine x1, y2, 0#, x1, y1, 0#
End Sub

Private Sub DibujarPoligono4(ByVal swSketchMgr As Object, ByVal x1 As Double, ByVal y1 As Double, ByVal x2 As Double, ByVal y2 As Double, ByVal x3 As Double, ByVal y3 As Double, ByVal x4 As Double, ByVal y4 As Double)
    swSketchMgr.CreateLine x1, y1, 0#, x2, y2, 0#
    swSketchMgr.CreateLine x2, y2, 0#, x3, y3, 0#
    swSketchMgr.CreateLine x3, y3, 0#, x4, y4, 0#
    swSketchMgr.CreateLine x4, y4, 0#, x1, y1, 0#
End Sub

Private Function ExtruirSolido(ByVal swFeatMgr As Object, ByVal condFin As Long, ByVal prof As Double, ByVal invertirDir As Boolean, ByVal fusionar As Boolean) As Object
    Set ExtruirSolido = swFeatMgr.FeatureExtrusion2( _
        True, False, invertirDir, _
        condFin, condFin, _
        prof, 0#, _
        False, False, False, False, _
        0#, 0#, _
        False, False, False, False, _
        fusionar, True, True, _
        0, 0#, False)
End Function

Sub main()
    Dim swApp As Object
    Dim swModel As Object
    Dim swFeatMgr As Object
    Dim swSketchMgr As Object
    Dim swSelMgr As Object
    Dim swSelData As Object
    Dim plFront As Object, plTop As Object, plRight As Object
    Dim swAxisFeat As Object
    Dim swSketchFeat As Object
    Dim swFeat As Object
    Dim swPlaneTmp As Object
    Dim tplPath As String
    Dim extPts() As Double
    Dim intPts() As Double
    Dim extArr As Variant
    Dim intArr As Variant

    On Error GoTo ErrHandler
    Set swApp = Application.SldWorks
    tplPath = swApp.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_PART)
    If Len(tplPath) > 0 Then
        Set swModel = swApp.NewDocument(tplPath, 0, 0, 0)
    End If
    If swModel Is Nothing Then
        Set swModel = swApp.ActiveDoc
    End If
    If swModel Is Nothing Then
        MsgBox "No se pudo crear una nueva Pieza. Abre una Pieza vacia en SolidWorks y vuelve a ejecutar la macro.", vbExclamation, "Dirigible CAD"
        Exit Sub
    End If

    swModel.SetUserPreferenceIntegerValue SW_UNITS_LINEAR, SW_MM
    Set swFeatMgr = swModel.FeatureManager
    Set swSketchMgr = swModel.SketchManager
    Set swSelMgr = swModel.SelectionManager
    Set swSelData = swSelMgr.CreateSelectData

    Call ObtenerPlanosBase(swModel, plFront, plTop, plRight)
    If plFront Is Nothing Or plTop Is Nothing Or plRight Is Nothing Then
        MsgBox "No se encontraron los tres planos base en la pieza.", vbCritical, "Dirigible CAD"
        Exit Sub
    End If

    swModel.SetAddToDB True
    swModel.SetDisplayWhenAdded False

    ' -------------------------------------------------------------------------
    ' 0. Eje X de referencia (interseccion de Alzado/Front y Planta/Top)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    plTop.Select2 True, 0
    swModel.InsertAxis2 True
    Set swAxisFeat = swModel.FeatureByPositionReverse(0)
    If Not swAxisFeat Is Nothing Then swAxisFeat.Name = "Eje_Casco_X"

    ' -------------------------------------------------------------------------
    ' 1. Piel exterior del casco y capas celulares {tipo_capas} ({n_sup} sup / {n_inf} inf)
    ' -------------------------------------------------------------------------
{chr(10).join(bloques_capas)}

    ' -------------------------------------------------------------------------
    ' 2. Gondola rectangular de componentes internos (bajo X_CB, gap {p["gap"]*1000:.0f} mm)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, {x_g1:.6f}, {p["y_gond_bot"]:.6f}, {x_g2:.6f}, {p["y_gond_top"]:.6f})
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, {p["gond_w"]:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Gondola_Componentes"

    ' -------------------------------------------------------------------------
    ' 3. Dos soportes verticales de suspension (casco <-> gondola)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, {p["x_s1"] - 0.015:.6f}, {p["y_gond_top"]:.6f}, {p["x_s1"] + 0.015:.6f}, {p["y_strut_top"]:.6f})
    Call DibujarRectangulo(swSketchMgr, {p["x_s2"] - 0.015:.6f}, {p["y_gond_top"]:.6f}, {p["x_s2"] + 0.015:.6f}, {p["y_strut_top"]:.6f})
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.03#, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Soportes_Gondola"

    ' -------------------------------------------------------------------------
    ' 4. Brazos transversales en H alineados bajo los puntales dentro de la gondola
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, {p["x_s1"] - 0.0125:.6f}, {p["y_arm"] - 0.5 * p["h_arm"]:.6f}, {p["x_s1"] + 0.0125:.6f}, {p["y_arm"] + 0.5 * p["h_arm"]:.6f})
    Call DibujarRectangulo(swSketchMgr, {p["x_s2"] - 0.0125:.6f}, {p["y_arm"] - 0.5 * p["h_arm"]:.6f}, {p["x_s2"] + 0.0125:.6f}, {p["y_arm"] + 0.5 * p["h_arm"]:.6f})
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, {span_z:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Brazos_Transversales_H"

    ' -------------------------------------------------------------------------
    ' 5. Tirantes diagonales triangulados (union superior gondola <-> brazos)
    ' -------------------------------------------------------------------------
{tirantes_del}
{tirantes_tras}

    ' -------------------------------------------------------------------------
    ' 6. Largueros longitudinales en H (conectan brazos transversales con los motores)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, {abs(p["y_arm"]):.6f}, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Brazos_H"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, {x_rail1:.6f}, {-p["z_mot"] - 0.5 * p["h_arm"]:.6f}, {x_rail2:.6f}, {-p["z_mot"] + 0.5 * p["h_arm"]:.6f})
    Call DibujarRectangulo(swSketchMgr, {x_rail1:.6f}, {p["z_mot"] - 0.5 * p["h_arm"]:.6f}, {x_rail2:.6f}, {p["z_mot"] + 0.5 * p["h_arm"]:.6f})
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, {p["h_arm"]:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Largueros_H"

    ' -------------------------------------------------------------------------
    ' 7. Motores A2212 referenciales ({p["N"]} motores en 2 costados)
    ' -------------------------------------------------------------------------
    Dim xsMot(0 To {len(p["xs_pares"]) - 1}) As Double
{xs_mot_code}
    Dim i As Long

    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, {abs(p["y_mot_base"]):.6f}, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Base_Motores"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    For i = 0 To {len(p["xs_pares"]) - 1}
        swSketchMgr.CreateCircleByRadius xsMot(i), {p["z_mot"]:.6f}, 0#, {r_mot:.6f}
        swSketchMgr.CreateCircleByRadius xsMot(i), {-p["z_mot"]:.6f}, 0#, {r_mot:.6f}
    Next i
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, {p["h_mot"]:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Motores_A2212"

    ' -------------------------------------------------------------------------
    ' 8. Discos referenciales de helices (dia {p["dp"]*1000:.0f} mm)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, {abs(p["y_prop_base"]):.6f}, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Helices"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    For i = 0 To {len(p["xs_pares"]) - 1}
        swSketchMgr.CreateCircleByRadius xsMot(i), {p["z_mot"]:.6f}, 0#, {r_prop:.6f}
        swSketchMgr.CreateCircleByRadius xsMot(i), {-p["z_mot"]:.6f}, 0#, {r_prop:.6f}
    Next i
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, {p["h_prop"]:.6f}, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Helices_Ref"

    swModel.ClearSelection2 True
    swModel.SetAddToDB False
    swModel.SetDisplayWhenAdded True
    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "*Isometric", 7
    swModel.ViewZoomtofit2

    MsgBox "Dirigible referencial generado correctamente:" & vbCrLf & _
           "Casco hueco: {p["L"]*1000:.0f} x {p["D"]*1000:.0f} mm | Capas: {n_sup} sup / {n_inf} inf (e={p["e_mm"]:.1f} mm)" & vbCrLf & _
           "Gondola (X_CB={p["x_cb"]*1000:.0f} mm): {p["gond_l"]*1000:.0f} x {p["gond_w"]*1000:.0f} x {p["gond_h"]*1000:.0f} mm (gap {p["gap"]*1000:.0f} mm)" & vbCrLf & _
           "Bastidor H con 4 tirantes triangulados + {p["N"]} motores dia {p["dp"]*1000:.0f} mm" & vbCrLf & _
           "Tip: usa 'Vista de seccion' o transparencia en Piel_Exterior_Casco para ver las capas internas.", vbInformation, "Dirigible CAD SolidWorks"
    Exit Sub

ErrHandler:
    On Error Resume Next
    If Not swModel Is Nothing Then
        swModel.SetAddToDB False
        swModel.SetDisplayWhenAdded True
    End If
    MsgBox "Error en macro (" & Err.Number & "): " & Err.Description, vbCritical, "Dirigible CAD"
End Sub
'''
    return vba.replace("\r\n", "\n").replace("\n", "\r\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera una macro VBA de SolidWorks (.bas) desde un JSON exportado del dirigible."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("especf_optm_hist/historico_dirigible_2026-11-25.json"),
        help="Ruta al archivo JSON exportado del histórico.",
    )
    parser.add_argument(
        "--index",
        type=int,
        default=0,
        help="Índice del diseño dentro del JSON (0 por defecto).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("especf_optm_hist/dirigible_solidworks_referencial.bas"),
        help="Ruta del archivo macro VBA (.bas) de salida.",
    )
    parser.add_argument("--gond-l", type=float, default=0.60, help="Largo de góndola (m).")
    parser.add_argument("--gond-w", type=float, default=0.30, help="Ancho de góndola (m).")
    parser.add_argument("--gond-h", type=float, default=0.25, help="Alto de góndola (m).")
    parser.add_argument("--gap", type=float, default=0.135, help="Separación vertical casco-góndola (m).")
    parser.add_argument("--z-mot", type=float, default=None, help="Separación lateral de motores desde eje (m).")
    parser.add_argument("--dx-mot", type=float, default=0.42, help="Semiseparación longitudinal entre pares (m).")
    args = parser.parse_args()

    reg = cargar_registro(args.input, args.index)
    params = extraer_parametros_cad(
        reg,
        gond_l=args.gond_l,
        gond_w=args.gond_w,
        gond_h=args.gond_h,
        gap=args.gap,
        z_mot=args.z_mot,
        dx_mot=args.dx_mot,
    )
    macro = generar_macro_vba(params)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(macro.encode("ascii"))

    print(f"Macro SolidWorks generada: {args.output}")
    print(f"  Caso: {params['nombre']}")
    print(f"  Casco hueco + capas: L={params['L']:.3f} m, D={params['D']:.3f} m | ncapS={int(round(params['ncapS']))}, ncapI={int(round(params['ncapI']))}, e={params['e_mm']:.1f} mm")
    print(f"  Centro de flotacion X_CB = {params['x_cb']:.3f} m (radio panza = {params['r_belly']:.3f} m)")
    print(f"  Gondola: {params['gond_l']*1000:.0f} x {params['gond_w']*1000:.0f} x {params['gond_h']*1000:.0f} mm (gap {params['gap']*1000:.0f} mm)")
    print(f"  Brazos H anclados en puntales X={[round(params['x_s1']*1000), round(params['x_s2']*1000)]} mm + 4 tirantes triangulados")
    print(f"  Motores ({params['N']}x, dp={params['dp']*1000:.0f} mm): +/-Z={params['z_mot']*1000:.0f} mm, X={[round(x*1000) for x in params['xs_pares']]} mm")
    print(f"  Holgura min. helice -> casco = {params['min_holgura_casco']*1000:.1f} mm | lateral gondola = {params['holgura_lat_gondola']*1000:.1f} mm")


if __name__ == "__main__":
    main()
