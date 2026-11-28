Attribute VB_Name = "CalentadorTierraRef"
Option Explicit

' =============================================================================
' Modelo CAD Referencial del Calentador en Tierra (Compacto + Recirculacion)
' Tipo: Calentador electrico de aire en tierra (100% aire limpio, sin GLP)
' Medidas carcasa: 420 x 220 x 220 mm (portatil, con 2 bocas superiores)
' Funcionamiento:
'   1. Inicio desinflado: compuerta trasera abierta toma aire fresco del exterior,
'      el ventilador interno lo impulsa por las resistencias y lo envia por la
'      valvula de entrada al dirigible.
'   2. Recirculacion: parte del aire del dirigible regresa por la segunda valvula
'      al retorno del calentador, se mezcla y vuelve a pasar por las resistencias
'      hasta alcanzar volumen y temperatura sin desperdiciar energia.
' Nota: Modelo multicuerpo (Merge=False). Oculta '1_Pared_Lateral_Visor' o usa
'       'Vista de seccion' (Alzado/Front) para ver todo el recorrido interno.
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

Private Function CrearPlanoOffset(ByVal swModel As Object, ByVal swFeatMgr As Object, ByVal basePlane As Object, ByVal flags As Long, ByVal dist As Double, ByVal planeName As String) As Object
    Dim swPlaneTmp As Object
    Dim swFeat As Object
    swModel.ClearSelection2 True
    basePlane.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(flags, dist, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = planeName
    Set CrearPlanoOffset = swFeat
End Function

Sub main()
    Dim swApp As Object
    Dim swModel As Object
    Dim swFeatMgr As Object
    Dim swSketchMgr As Object
    Dim plFront As Object, plTop As Object, plRight As Object
    Dim swFeat As Object
    Dim swPlane As Object
    Dim swPlaneTapa As Object
    Dim swPlaneMangas As Object
    Dim swPlaneValvulas As Object
    Dim tplPath As String

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
        MsgBox "No se pudo crear una nueva Pieza. Abre una Pieza vacia en SolidWorks y vuelve a ejecutar la macro.", vbExclamation, "Calentador Tierra CAD"
        Exit Sub
    End If

    swModel.SetUserPreferenceIntegerValue SW_UNITS_LINEAR, SW_MM
    Set swFeatMgr = swModel.FeatureManager
    Set swSketchMgr = swModel.SketchManager

    Call ObtenerPlanosBase(swModel, plFront, plTop, plRight)
    If plFront Is Nothing Or plTop Is Nothing Or plRight Is Nothing Then
        MsgBox "No se encontraron los tres planos base en la pieza.", vbCritical, "Calentador Tierra CAD"
        Exit Sub
    End If

    swModel.SetAddToDB True
    swModel.SetDisplayWhenAdded False

    ' -------------------------------------------------------------------------
    ' 1. Carcasa portatil (420 x 220 x 220 mm, paredes 4 mm separadas)
    ' -------------------------------------------------------------------------
    ' 1a. Base inferior (Y = 20 .. 24 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0#, 0.02, 0.42, 0.024)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.22, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Base_Carcasa"

    ' 1b. Tapa superior con 2 orificios (retorno en X=65 mm, impulsion en X=355 mm)
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plTop, SW_REFPLANE_DIST, 0.236, "Plano_Tapa_Inf")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0#, -0.11, 0.42, 0.11)
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.051
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.051
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.004, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Tapa_Superior"

    ' 1c. Pared trasera con orificio de admision de aire fresco (X = 0 .. 4 mm)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.11, 0.024, 0.11, 0.236)
    swSketchMgr.CreateCircleByRadius 0#, 0.13, 0#, 0.051
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.004, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Pared_Trasera"

    ' 1d. Pared frontal cerrada (X = 416 .. 420 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0.416, 0.024, 0.42, 0.236)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.22, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Pared_Frontal"

    ' 1e. Pared lateral frontal (visor: ocultar o dar transparencia para ver interior)
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plFront, SW_REFPLANE_DIST, 0.108, "Plano_Pared_Visor")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0.004, 0.024, 0.416, 0.236)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.004, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Pared_Lateral_Visor"

    ' 1f. Pared lateral trasera de fondo
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plFront, SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.108, "Plano_Pared_Fondo")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0.004, 0.024, 0.416, 0.236)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.004, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Pared_Lateral_Fondo"

    ' 1g. 4 patas de apoyo (Y = 0 .. 20 mm)
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0.025, -0.095, 0.055, -0.065)
    Call DibujarRectangulo(swSketchMgr, 0.025, 0.065, 0.055, 0.095)
    Call DibujarRectangulo(swSketchMgr, 0.365, -0.095, 0.395, -0.065)
    Call DibujarRectangulo(swSketchMgr, 0.365, 0.065, 0.395, 0.095)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.02, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "1_Patas_Apoyo"

    ' -------------------------------------------------------------------------
    ' Planos horizontales comunes sobre la tapa para bocas, mangas y valvulas
    ' -------------------------------------------------------------------------
    Set swPlaneTapa = CrearPlanoOffset(swModel, swFeatMgr, plTop, SW_REFPLANE_DIST, 0.24, "Plano_Tapa_Sup")
    Set swPlaneMangas = CrearPlanoOffset(swModel, swFeatMgr, plTop, SW_REFPLANE_DIST, 0.295, "Plano_Mangas")
    Set swPlaneValvulas = CrearPlanoOffset(swModel, swFeatMgr, plTop, SW_REFPLANE_DIST, 0.415, "Plano_Valvulas")

    ' -------------------------------------------------------------------------
    ' 2. Admision de aire fresco (inflado inicial) + Retorno desde el dirigible
    ' -------------------------------------------------------------------------
    ' 2a. Boca trasera de aire fresco (D = 110 mm ext / 102 mm int)
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.13, 0#, 0.055
    swSketchMgr.CreateCircleByRadius 0#, 0.13, 0#, 0.051
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.045, True, False)
    If Not swFeat Is Nothing Then swFeat.Name = "2_Boca_Aire_Fresco"

    ' 2b. Compuerta reguladora de aire fresco (abierta para inflado, se cierra en recirculacion)
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plRight, SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 0.048, "Plano_Compuerta_Aire")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.065, 0.07, 0.015, 0.215)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.004, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "2_Compuerta_Aire_Fresco"

    ' 2c. Boca superior de retorno desde el dirigible (X = 65 mm)
    swModel.ClearSelection2 True
    swPlaneTapa.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.055
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.051
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.055, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "2_Boca_Retorno_Dirigible"

    ' 2d. Manga flexible de retorno desde el dirigible (tramo referencial)
    swModel.ClearSelection2 True
    swPlaneMangas.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.053
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.049
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.145, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "2_Manga_Retorno_Ref"

    ' 2e. Valvula de retorno en el dirigible (acople referencial)
    swModel.ClearSelection2 True
    swPlaneValvulas.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.065
    swSketchMgr.CreateCircleByRadius 0.065, 0#, 0#, 0.053
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.025, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "2_Valvula_Retorno_Ref"

    ' -------------------------------------------------------------------------
    ' 3. Ventilador interno de circulacion (X = 145 mm)
    ' -------------------------------------------------------------------------
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plRight, SW_REFPLANE_DIST, 0.145, "Plano_Ventilador_Int")

    ' 3a. Marco divisor que obliga al aire a pasar por el rotor
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.105, 0.025, 0.105, 0.235)
    swSketchMgr.CreateCircleByRadius 0#, 0.13, 0#, 0.085
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.036, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "3_Marco_Ventilador"

    ' 3b. Cubo / motor del ventilador
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0#, 0.13, 0#, 0.026
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.046, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "3_Motor_Ventilador"

    ' 3c. 4 aspas disjuntas del ventilador
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.01, 0.158, 0.01, 0.212)
    Call DibujarRectangulo(swSketchMgr, -0.01, 0.048, 0.01, 0.102)
    Call DibujarRectangulo(swSketchMgr, 0.028, 0.12, 0.082, 0.14)
    Call DibujarRectangulo(swSketchMgr, -0.082, 0.12, -0.028, 0.14)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.01, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "3_Aspas_Ventilador"

    ' -------------------------------------------------------------------------
    ' 4. Banco de resistencias electricas y rejilla difusora (aire limpio)
    ' -------------------------------------------------------------------------
    ' 4a. 9 elementos calefactores electricos (malla 3 x 3 entre X = 215 y 295 mm)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.215, 0.075, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.255, 0.075, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.295, 0.075, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.215, 0.13, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.255, 0.13, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.295, 0.13, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.215, 0.185, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.255, 0.185, 0#, 0.008
    swSketchMgr.CreateCircleByRadius 0.295, 0.185, 0#, 0.008
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.195, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "4_Resistencias_Electricas"

    ' 4b. Rejilla difusora y protectora (X = 325 mm)
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plRight, SW_REFPLANE_DIST, 0.325, "Plano_Rejilla_Difusora")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.063, 0.03, -0.057, 0.23)
    Call DibujarRectangulo(swSketchMgr, -0.023, 0.03, -0.017, 0.23)
    Call DibujarRectangulo(swSketchMgr, 0.017, 0.03, 0.023, 0.23)
    Call DibujarRectangulo(swSketchMgr, 0.057, 0.03, 0.063, 0.23)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.006, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "4_Rejilla_Difusora"

    ' -------------------------------------------------------------------------
    ' 5. Impulsion caliente hacia el dirigible, sensor de T y panel electrico
    ' -------------------------------------------------------------------------
    ' 5a. Boca superior de impulsion de aire caliente (X = 355 mm)
    swModel.ClearSelection2 True
    swPlaneTapa.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.055
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.051
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.055, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Boca_Impulsion_Caliente"

    ' 5b. Manga flexible de impulsion caliente hacia el dirigible
    swModel.ClearSelection2 True
    swPlaneMangas.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.053
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.049
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.145, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Manga_Impulsion_Ref"

    ' 5c. Valvula de entrada en el dirigible (acople referencial)
    swModel.ClearSelection2 True
    swPlaneValvulas.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.065
    swSketchMgr.CreateCircleByRadius 0.355, 0#, 0#, 0.053
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.025, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Valvula_Entrada_Dirigible_Ref"

    ' 5d. Sonda de control termico en camara de salida (evita superar limite del Mylar)
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 0.355, 0.162, 0.445, 0.168)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.006, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Sensor_Temperatura"

    ' 5e. Caja de control electrico frontal y perillas (potencia + ventilador)
    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plRight, SW_REFPLANE_DIST, 0.42, "Plano_Panel_Control")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, -0.075, 0.045, 0.075, 0.115)
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.025, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Panel_Control_Electrico"

    Set swPlane = CrearPlanoOffset(swModel, swFeatMgr, plRight, SW_REFPLANE_DIST, 0.445, "Plano_Perillas_Control")
    swModel.ClearSelection2 True
    swPlane.Select2 False, 0
    swSketchMgr.InsertSketch True
    swSketchMgr.CreateCircleByRadius -0.035, 0.08, 0#, 0.015
    swSketchMgr.CreateCircleByRadius 0.035, 0.08, 0#, 0.015
    swSketchMgr.InsertSketch True
    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.015, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "5_Perillas_Control"

    ' -------------------------------------------------------------------------
    ' Reconstruccion final y vista isometrica
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    swModel.SetAddToDB False
    swModel.SetDisplayWhenAdded True
    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "*Isometric", 7
    swModel.ViewZoomtofit2

    MsgBox "Calentador electrico compacto con recirculacion generado (420 x 220 x 220 mm):" & vbCrLf & _
           "1. Carcasa portatil (oculta '1_Pared_Lateral_Visor' para ver todo el interior)." & vbCrLf & _
           "2. Atras: '2_Boca_Aire_Fresco' + compuerta para inflar desde desinflado." & vbCrLf & _
           "   Arriba izq.: '2_Valvula_Retorno_Ref' recibe aire tibio desde el dirigible." & vbCrLf & _
           "3. Centro: '3_Aspas_Ventilador' succiona retorno + aire fresco hacia el banco." & vbCrLf & _
           "4. Derecha: '4_Resistencias_Electricas' recalientan el aire (100% limpio, sin GLP)." & vbCrLf & _
           "5. Arriba der.: '5_Valvula_Entrada_Dirigible_Ref' inyecta aire controlado por sensor.", vbInformation, "Calentador Tierra SolidWorks"
    Exit Sub

ErrHandler:
    On Error Resume Next
    If Not swModel Is Nothing Then
        swModel.SetAddToDB False
        swModel.SetDisplayWhenAdded True
    End If
    MsgBox "Error en macro (" & Err.Number & "): " & Err.Description, vbCritical, "Calentador Tierra CAD"
End Sub
