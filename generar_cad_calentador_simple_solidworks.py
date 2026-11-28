#!/usr/bin/env python3
"""
Generador de macro VBA de SolidWorks (modelo 3D referencial) para la version
simplificada del calentador aereo de etanol con ventilador externo lateral,
bandeja-esponja integrada y difusor conico superior (~175-205 g en seco).

Arquitectura de 16 solidos multicuerpo (sin fusionar):
  - Monotubo unico de aluminio con base cerrada inferior y ventilador externo
    lateral en el costado -X (alimenta aire fresco bajo la llama y alrededor
    de la pared).
  - Bandeja circular deposito-quemador con esponja de fibra ceramica
    sobresaliente (4 mm arriba del borde) para distinguirla claramente.
  - Anillo cortaviento, tapa corrediza con microservo SG90, collar ignifugo
    al casco, malla apagachispas, difusor conico ancho con plato deflector de
    3 anillos y sensor NTC de seguridad (<= 150 C).

Por defecto genera las piezas envolventes en corte expositivo de 270 grados
(CORTE_EXPOSITIVO = True). Usar --completo para revolucion cerrada de 360 deg.

Uso:
    ./venv_sus_d/bin/python generar_cad_calentador_simple_solidworks.py
    ./venv_sus_d/bin/python generar_cad_calentador_simple_solidworks.py --completo
    ./venv_sus_d/bin/python generar_cad_calentador_simple_solidworks.py --output ruta.bas
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

DEFAULT_OUTPUT = Path("especf_optm_hist/calentador_etanol_simple_solidworks.bas")


def generar_vba(corte_expositivo: bool = True) -> str:
    """Genera el codigo VBA completo de SolidWorks en ASCII puro con LF."""
    corte_str = "True" if corte_expositivo else "False"
    ang_270 = f"{1.5 * math.pi:.12f}"
    ang_360 = f"{2.0 * math.pi:.12f}"

    return f'''Attribute VB_Name = "CalentadorEtanolSimple"
Option Explicit

' =============================================================================
' CALENTADOR AEREO DE ETANOL SIMPLIFICADO (VENTILADOR EXTERNO + DIFUSOR)
' Generado por generar_cad_calentador_simple_solidworks.py
' Geometria multicuerpo didactica (unidades del API en metros, vista en mm)
' Orientacion: Eje +Y vertical (salida hacia arriba al interior del casco)
'   - Y = -0.003..0.215 m : Base cerrada, ventilador externo (-X) y bandeja
'   - Y =  0.215..0.220 m : Collar ignifugo de paso por la tela del casco
'   - Y =  0.220..0.478 m : Apagachispas, difusor conico, plato deflector y NTC
' =============================================================================

' Cambiar a False para carcasa cerrada de 360 deg (True = corte de 270 deg)
Private Const CORTE_EXPOSITIVO As Boolean = {corte_str}

Private Const SW_DEFAULT_TEMPLATE_PART As Long = 8
Private Const SW_END_MIDPLANE As Long = 6
Private Const SW_REFPLANE_DIST As Long = 8
Private Const SW_REFPLANE_FLIP As Long = 256
Private Const SW_UNITS_LINEAR As Long = 0
Private Const SW_MM As Long = 0

Sub main()
    Dim swApp As Object
    Dim swModel As Object
    Dim swFeatMgr As Object
    Dim swSketchMgr As Object
    Dim swSelMgr As Object
    Dim swSelData As Object
    Dim swFeat As Object
    Dim swAxisFeat As Object
    Dim swPlaneTmp As Object
    Dim plFront As Object
    Dim plTop As Object
    Dim plRight As Object
    Dim plantilla As String
    Dim angExt As Double
    Dim ang360 As Double

    On Error GoTo ErrHandler
    Set swApp = Application.SldWorks
    plantilla = swApp.GetUserPreferenceStringValue(SW_DEFAULT_TEMPLATE_PART)
    If Len(plantilla) > 0 Then
        Set swModel = swApp.NewDocument(plantilla, 0, 0, 0)
    End If
    If swModel Is Nothing Then
        Set swModel = swApp.ActiveDoc
    End If
    If swModel Is Nothing Then
        MsgBox "No se pudo crear una nueva Pieza. Abre una Pieza vacia en SolidWorks y vuelve a ejecutar la macro.", vbExclamation, "Calentador Etanol Simple"
        Exit Sub
    End If

    swModel.SetUserPreferenceIntegerValue SW_UNITS_LINEAR, SW_MM
    Set swFeatMgr = swModel.FeatureManager
    Set swSketchMgr = swModel.SketchManager
    Set swSelMgr = swModel.SelectionManager
    Set swSelData = swSelMgr.CreateSelectData

    ang360 = {ang_360}#
    If CORTE_EXPOSITIVO Then
        angExt = {ang_270}#
    Else
        angExt = ang360
    End If

    ObtenerPlanosBase swModel, plFront, plTop, plRight
    If plFront Is Nothing Or plTop Is Nothing Or plRight Is Nothing Then
        MsgBox "No se encontraron los planos base de SolidWorks.", vbCritical, "Calentador Etanol Simple"
        Exit Sub
    End If

    swModel.SetAddToDB True
    swModel.SetDisplayWhenAdded False

    ' Eje vertical central (+Y) por interseccion de Plano Alzado y Vista Lateral
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    plRight.Select2 True, 0
    swModel.InsertAxis2 True
    Set swAxisFeat = swModel.FeatureByPositionReverse(0)
    If Not swAxisFeat Is Nothing Then swAxisFeat.Name = "Eje_Vertical_Y"

    ' =========================================================================
    ' 1. MONOTUBO EXTERIOR, BASE CERRADA Y VENTILADOR EXTERNO LATERAL (-X)
    ' =========================================================================

    ' 1.1 Base inferior cerrada del monotubo (obliga a subir todo el aire)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, -0.003, 0.106, 0#
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Base_Inferior_Tubo"

    ' 1.2 Tubo unico de aluminio (r = 104..106 mm, h = 340 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.104, 0#, 0.106, 0.34
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tubo_Unico_Aluminio"

    ' 1.3 Ducto del ventilador externo lateral (lado -X, Y = 62 mm, bajo la bandeja)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.145, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Ventilador_Externo"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.062, 0#, 0.048
    swSketchMgr.CreateCircleByRadius 0#, 0.062, 0#, 0.044
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.086, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Ducto_Ventilador_Externo"

    ' 1.4 Motor brushless del ventilador externo
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.166, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Motor_Externo"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.062, 0#, 0.014
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.026, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Motor_Ventilador_Externo"

    ' 1.5 Helice de 4 aspas dentro del ducto externo (contornos disjuntos)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.146, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Helice_Externa"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.015, 0.058, 0.041, 0.066
    DibujarRectangulo swSketchMgr, -0.041, 0.058, -0.015, 0.066
    DibujarRectangulo swSketchMgr, -0.004, 0.077, 0.004, 0.103
    DibujarRectangulo swSketchMgr, -0.004, 0.021, 0.004, 0.047
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.005, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Helice_Ventilador_Externo"

    ' =========================================================================
    ' 2. BANDEJA-DEPOSITO INTEGRADA CON ESPONJA SOBRESALIENTE Y APAGADO
    ' =========================================================================

    ' 2.1 Soportes de la bandeja (dejan paso anular de 29 mm para el aire)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.073, 0.112, 0.104, 0.116
    DibujarRectangulo swSketchMgr, -0.104, 0.112, -0.073, 0.116
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.008, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Soportes_Bandeja_Quemador"

    ' 2.2 Bandeja circular deposito-quemador (r = 75 mm, y = 115..142 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0#, 0.115, _
        0.075, 0.115, _
        0.075, 0.142, _
        0.073, 0.142, _
        0.073, 0.117, _
        0#, 0.117)
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Bandeja_Deposito_Etanol"

    ' 2.3 Esponja de fibra ceramica / vidrio (sobresale 4 mm sobre la bandeja)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, 0.1175, 0.071, 0.146
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Esponja_Fibra_Ceramica"

    ' 2.4 Anillo cortaviento perimetral (protege la llama del chorro lateral)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.075, 0.135, 0.077, 0.19
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Anillo_Cortaviento_Llama"

    ' 2.5 Tapa corrediza de apagado / control de llama sobre la bandeja
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.015, 0.15, 0.128, 0.153
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.11, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tapa_Apagado_Llama"

    ' 2.6 Microservo SG90 exterior de accionamiento de la tapa (lado +X)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.114, 0.14, 0.136, 0.163
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.012, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Microservo_SG90_Apagado"

    ' =========================================================================
    ' 3. INTERFAZ AL CASCO, APAGACHISPAS, DIFUSOR CONICO Y SENSOR NTC
    ' =========================================================================

    ' 3.1 Collar ignifugo de fijacion a la tela del casco (Y = 215..220 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.106, 0.215, 0.21, 0.22
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Collar_Ignifugo_Casco"

    ' 3.2 Malla apagachispas inoxidable en la boca del monotubo
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, 0.336, 0.104, 0.338
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, ang360, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Malla_Apagachispas_Inox"

    ' 3.3 Difusor conico de salida (expande y homogeniza <= 150 C)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.104, 0.34, _
        0.106, 0.34, _
        0.187, 0.445, _
        0.185, 0.445)
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Difusor_Conico_Salida"

    ' 3.4 Plato deflector ranurado de 3 anillos dentro del difusor
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, 0.422, 0.055, 0.426
    DibujarRectangulo swSketchMgr, 0.072, 0.422, 0.115, 0.426
    DibujarRectangulo swSketchMgr, 0.132, 0.422, 0.165, 0.426
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, ang360, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Plato_Deflector_Difusor"

    ' 3.5 Sonda termica NTC de seguridad sobre la boca del difusor
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.181, 0.445, _
        0.185, 0.445, _
        0.185, 0.478, _
        0.02, 0.478, _
        0.02, 0.473, _
        0.181, 0.473)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.005, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Sensor_NTC_Salida"

    swModel.ClearSelection2 True
    swModel.SetAddToDB False
    swModel.SetDisplayWhenAdded True
    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "*Isometric", 7
    swModel.ViewZoomtofit2

    MsgBox "Calentador simplificado con ventilador externo y difusor generado correctamente.", vbInformation, "Calentador Etanol Simple"
    Exit Sub

ErrHandler:
    On Error Resume Next
    If Not swModel Is Nothing Then
        swModel.SetAddToDB False
        swModel.SetDisplayWhenAdded True
    End If
    MsgBox "Error en macro (" & Err.Number & "): " & Err.Description, vbCritical, "Calentador Etanol Simple"
End Sub

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

Private Sub DibujarPoligonoCerrado(ByVal swSketchMgr As Object, ByVal pts As Variant)
    Dim i As Long
    Dim n As Long
    Dim xA As Double
    Dim yA As Double
    Dim xB As Double
    Dim yB As Double
    n = (UBound(pts) - LBound(pts) + 1) \\ 2
    For i = 0 To n - 1
        xA = CDbl(pts(LBound(pts) + 2 * i))
        yA = CDbl(pts(LBound(pts) + 2 * i + 1))
        If i = n - 1 Then
            xB = CDbl(pts(LBound(pts)))
            yB = CDbl(pts(LBound(pts) + 1))
        Else
            xB = CDbl(pts(LBound(pts) + 2 * (i + 1)))
            yB = CDbl(pts(LBound(pts) + 2 * (i + 1) + 1))
        End If
        swSketchMgr.CreateLine xA, yA, 0#, xB, yB, 0#
    Next i
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

Private Function RevolverPerfil(ByVal swModel As Object, ByVal swFeatMgr As Object, ByVal swSelData As Object, ByVal swAxisFeat As Object, ByVal angulo As Double, ByVal fusionar As Boolean) As Object
    Dim swSketchFeat As Object
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set RevolverPerfil = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, angulo, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        fusionar, True, True)
End Function
'''


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genera la macro VBA referencial de SolidWorks para el calentador simplificado de etanol."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"Ruta de salida del archivo .bas (por defecto: {DEFAULT_OUTPUT})",
    )
    parser.add_argument(
        "--completo",
        action="store_true",
        help="Genera carcasas cerradas de 360 grados (CORTE_EXPOSITIVO = False).",
    )
    args = parser.parse_args()

    macro = generar_vba(corte_expositivo=not args.completo)
    macro_crlf = macro.replace("\r\n", "\n").replace("\n", "\r\n")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(macro_crlf.encode("ascii"))
    modo = "360 grados completo" if args.completo else "corte expositivo 270 grados"
    print(f"Macro generada ({modo}): {args.output} ({len(macro_crlf)} bytes ASCII)")


if __name__ == "__main__":
    main()
