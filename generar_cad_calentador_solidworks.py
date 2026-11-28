#!/usr/bin/env python3
"""
Generador de macro VBA de SolidWorks (modelo 3D referencial) para el calentador
aereo de etanol de 3 etapas concentricas del dirigible hibrido.

El modelo se construye en modo multicuerpo (sin fusionar los solidos) para
que cada componente sea distinguible en el arbol de operaciones de SolidWorks y
se entienda claramente el funcionamiento termico y mecanico:
  1. Etapa de combustion anular (copa, mecha ceramica, cortavientos,
     obturador de apagado con servo, malla apagachispas y sistema de etanol).
  2. Etapa de doble pared e inyeccion de aire frio (chimenea interna caliente,
     camisa externa de dilucion y ventilador brushless lateral).
  3. Etapa de mezcla turbulenta, difusor ancho con deflector, collar ignifugo
     de interfaz al casco y sensor termico NTC de seguridad (<= 150 C).

Por defecto genera la carcasa exterior en corte expositivo de 270 grados
(CORTE_EXPOSITIVO = True) para ver inmediatamente el interior. Usar --completo
para revolucion cerrada de 360 grados.

Uso:
    ./venv_sus_d/bin/python generar_cad_calentador_solidworks.py
    ./venv_sus_d/bin/python generar_cad_calentador_solidworks.py --completo
    ./venv_sus_d/bin/python generar_cad_calentador_solidworks.py --output ruta.bas
"""

from __future__ import annotations

import argparse
import math
from pathlib import Path

DEFAULT_OUTPUT = Path("especf_optm_hist/calentador_etanol_solidworks_referencial.bas")


def generar_vba(corte_expositivo: bool = True) -> str:
    """Genera el codigo VBA completo de SolidWorks en ASCII puro con LF."""
    corte_str = "True" if corte_expositivo else "False"
    ang_270 = f"{1.5 * math.pi:.12f}"
    ang_360 = f"{2.0 * math.pi:.12f}"

    return f'''Attribute VB_Name = "CalentadorEtanol3Etapas"
Option Explicit

' =============================================================================
' CALENTADOR AEREO DE ETANOL (3 ETAPAS CONCENTRICAS) - MODELO REFERENCIAL
' Generado por generar_cad_calentador_solidworks.py
' Geometria multicuerpo didactica (unidades del API en metros, vista en mm)
' Orientacion: Eje +Y vertical (salida hacia arriba al interior del casco)
'   - Y < 0.295 m : Zona fria / exterior (quemador, combustible, ventilador)
'   - Y = 0.295 m : Collar ignifugo de paso por la tela inferior del casco
'   - Y > 0.301 m : Zona interior del dirigible (mezcla y difusor <= 150 C)
' =============================================================================

' Cambiar a False para carcasa cerrada de 360 deg (True = corte de 270 deg)
Private Const CORTE_EXPOSITIVO As Boolean = {corte_str}

Private Const SW_DEFAULT_TEMPLATE_PART As Long = 8
Private Const SW_END_BLIND As Long = 0
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
        MsgBox "No se pudo crear una nueva Pieza. Abre una Pieza vacia en SolidWorks y vuelve a ejecutar la macro.", vbExclamation, "Calentador Etanol 3 Etapas"
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
        MsgBox "No se encontraron los planos base de SolidWorks.", vbCritical, "Calentador Etanol 3 Etapas"
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
    ' ETAPA 1: COMBUSTION ANULAR DE ETANOL Y SEGURIDAD DE LLAMA
    ' =========================================================================

    ' 1.1 Base metalica inferior (disco macizo r = 88 mm, y = -4..0 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, -0.004, 0.088, 0#
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Base_Soporte_Quemador"

    ' 1.2 Cuatro pilares perimetrales (dejan ranura inferior de aire primario)
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.082, 0#, 0#, 0.004
    swSketchMgr.CreateCircleByRadius -0.082, 0#, 0#, 0.004
    swSketchMgr.CreateCircleByRadius 0#, 0.082, 0#, 0.004
    swSketchMgr.CreateCircleByRadius 0#, -0.082, 0#, 0.004
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.022, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Pilares_Aire_Primario"

    ' 1.3 Copa anular del quemador (perfil en U: r_in=28 mm, r_out=78 mm)
    '     Permite aire primario tanto por el centro (r<28) como por el borde
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.028, 0#, _
        0.078, 0#, _
        0.078, 0.03, _
        0.075, 0.03, _
        0.075, 0.003, _
        0.031, 0.003, _
        0.031, 0.03, _
        0.028, 0.03)
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Copa_Quemador_Anular"

    ' 1.4 Mecha absorbente de fibra ceramica dentro de la copa
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.0315, 0.0035, 0.0745, 0.026
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Mecha_Fibra_Ceramica"

    ' 1.5 Malla de retencion superior de la mecha
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.0315, 0.026, 0.0745, 0.028
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Malla_Retencion_Mecha"

    ' 1.6 Camisa cortaviento de la base con brida superior hacia chimenea
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.084, 0.02, _
        0.087, 0.02, _
        0.087, 0.11, _
        0.056, 0.11, _
        0.056, 0.106, _
        0.084, 0.106)
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Camisa_Cortaviento_Base"

    ' 1.7 Malla apagachispas inoxidable a la entrada de la chimenea
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, 0.106, 0.056, 0.108
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, ang360, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Malla_Apagachispas_Inox"

    ' 1.8 Obturador deslizante de apagado / control de llama (sobre la copa)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.01, 0.036, 0.12, 0.039
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.09, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Obturador_Control_Llama"

    ' 1.9 Servomotor MG90S de accionamiento del obturador (lado +X)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.11, 0.028, 0.133, 0.055
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.013, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Servo_Apagado_MG90S"

    ' =========================================================================
    ' SISTEMA DE COMBUSTIBLE REMOTO (LADO +X, ZONA FRIA)
    ' =========================================================================

    ' 1.10 Deposito de etanol 96% (250 mL PEAD, X = 215 mm)
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.215, 0#, 0#, 0.031
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.1, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tanque_Etanol_250mL"

    ' 1.11 Tubo metalico de alimentacion desde tanque hasta la copa (Y = 15 mm)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 0.13, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Tubo_Etanol"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.015, 0#, 0.003
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.114, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tubo_Alimentacion_Etanol"

    ' 1.12 Valvula de corte en linea sobre el tubo de alimentacion
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 0.155, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Valvula_Combustible"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, -0.01, 0.005, 0.01, 0.025
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.022, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Valvula_Corte_Combustible"

    ' =========================================================================
    ' ETAPA 2: CHIMENEA DE DOBLE PARED Y VENTILACION FORZADA (LADO -X)
    ' =========================================================================

    ' 2.1 Tubo interno de combustion (inox, r = 56..59 mm, y = 110..380 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.056, 0.11, 0.059, 0.38
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, ang360, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tubo_Interno_Combustion"

    ' 2.2 Camisa externa de dilucion con anillo de cierre inferior (r = 94..97 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.059, 0.12, _
        0.097, 0.12, _
        0.097, 0.48, _
        0.094, 0.48, _
        0.094, 0.124, _
        0.059, 0.124)
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Camisa_Externa_Dilucion"

    ' 2.3 Separadores radiales de centrado entre tubo interno y camisa externa
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.059, 0.158, 0.094, 0.162
    DibujarRectangulo swSketchMgr, -0.094, 0.158, -0.059, 0.162
    DibujarRectangulo swSketchMgr, 0.059, 0.348, 0.094, 0.352
    DibujarRectangulo swSketchMgr, -0.094, 0.348, -0.059, 0.352
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.008, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Separadores_Centrado_Tubos"

    ' 2.4 Ducto lateral del ventilador de dilucion (lado -X, Y = 215 mm)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.136, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Ducto_Ventilador"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.215, 0#, 0.056
    swSketchMgr.CreateCircleByRadius 0#, 0.215, 0#, 0.052
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.088, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Ducto_Entrada_Ventilador"

    ' 2.5 Motor brushless del ventilador
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.158, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Motor_Ventilador"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.215, 0#, 0.015
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.028, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Motor_Ventilador_Brushless"

    ' 2.6 Helice de 4 aspas dentro del ducto (contornos disjuntos alrededor del buje)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.136, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Helice_Ventilador"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.016, 0.21, 0.049, 0.22
    DibujarRectangulo swSketchMgr, -0.049, 0.21, -0.016, 0.22
    DibujarRectangulo swSketchMgr, -0.005, 0.231, 0.005, 0.264
    DibujarRectangulo swSketchMgr, -0.005, 0.166, 0.005, 0.199
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.005, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Helice_Dilucion"

    ' =========================================================================
    ' ETAPA 3: MEZCLA TURBULENTA, DIFUSOR ANCHO, COLLAR CASCO Y SENSOR NTC
    ' =========================================================================

    ' 3.1 Aletas deflectoras inclinadas en la salida del tubo interno (y = 380 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligono4 swSketchMgr, 0.038, 0.382, 0.086, 0.418, 0.084, 0.422, 0.036, 0.386
    DibujarPoligono4 swSketchMgr, -0.038, 0.418, -0.086, 0.382, -0.084, 0.378, -0.036, 0.414
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.028, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Aletas_Mezcla_Turbulenta"

    ' 3.2 Difusor conico ancho (reduce velocidad de salida y homogeniza <= 150 C)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligono4 swSketchMgr, 0.094, 0.48, 0.097, 0.48, 0.188, 0.585, 0.185, 0.585
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Difusor_Conico_Ancho"

    ' 3.3 Plato deflector ranurado en la boca del difusor (distribucion radial)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0#, 0.562, 0.055, 0.566
    DibujarRectangulo swSketchMgr, 0.072, 0.562, 0.115, 0.566
    DibujarRectangulo swSketchMgr, 0.132, 0.562, 0.165, 0.566
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, ang360, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Plato_Deflector_Difusor"

    ' 3.4 Collar ignifugo de fijacion a la tela del casco (Y = 295..301 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarRectangulo swSketchMgr, 0.097, 0.295, 0.21, 0.301
    swSketchMgr.InsertSketch True
    Set swFeat = RevolverPerfil(swModel, swFeatMgr, swSelData, swAxisFeat, angExt, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Collar_Ignifugo_Casco"

    ' 3.5 Sonda de temperatura NTC sobre la boca del difusor (corte si T > 150 C)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    DibujarPoligonoCerrado swSketchMgr, Array( _
        0.18, 0.585, _
        0.184, 0.585, _
        0.184, 0.618, _
        0.015, 0.618, _
        0.015, 0.613, _
        0.18, 0.613)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.006, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Sensor_NTC_Difusor"

    swModel.ClearSelection2 True
    swModel.SetAddToDB False
    swModel.SetDisplayWhenAdded True
    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "*Isometric", 7
    swModel.ViewZoomtofit2

    MsgBox "Calentador de etanol de 3 etapas concentricas generado correctamente.", vbInformation, "Calentador Etanol 3 Etapas"
    Exit Sub

ErrHandler:
    On Error Resume Next
    If Not swModel Is Nothing Then
        swModel.SetAddToDB False
        swModel.SetDisplayWhenAdded True
    End If
    MsgBox "Error en macro (" & Err.Number & "): " & Err.Description, vbCritical, "Calentador Etanol 3 Etapas"
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

Private Sub DibujarPoligono4(ByVal swSketchMgr As Object, ByVal x1 As Double, ByVal y1 As Double, ByVal x2 As Double, ByVal y2 As Double, ByVal x3 As Double, ByVal y3 As Double, ByVal x4 As Double, ByVal y4 As Double)
    swSketchMgr.CreateLine x1, y1, 0#, x2, y2, 0#
    swSketchMgr.CreateLine x2, y2, 0#, x3, y3, 0#
    swSketchMgr.CreateLine x3, y3, 0#, x4, y4, 0#
    swSketchMgr.CreateLine x4, y4, 0#, x1, y1, 0#
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
        description="Genera la macro VBA referencial de SolidWorks para el calentador de etanol."
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
