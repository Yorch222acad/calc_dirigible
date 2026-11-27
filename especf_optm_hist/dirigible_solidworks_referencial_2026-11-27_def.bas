Attribute VB_Name = "DirigibleReferencial"
Option Explicit

' =============================================================================
' Modelo CAD Referencial de Dirigible Hibrido para SolidWorks
' Generado automaticamente por generar_cad_solidworks.py
' Caso: Optimo (42.0 pts | lam=3.55, T2=114.8 degC)
' Casco hueco + capas celulares simetricas: 1 sup / 1 inf (e = 29.1 mm)
' Dimensiones: L=8.083 m | D=2.274 m (cf=2.829 m, cr=5.254 m) | V=21.90 m3
' Centro flotacion X_CB = 3.738 m | Motores: 4 x dia 254 mm en +/-0.550 m
' Gondola: 600 x 300 x 250 mm (gap 135 mm)
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
    ' 1. Piel exterior del casco y capas celulares simetricas (1 sup / 1 inf)
    ' -------------------------------------------------------------------------
    ' --- Piel_Exterior_Casco (offset = 0.0 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.000000: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.003019: extPts(4) = 0.052511: extPts(5) = 0#
    extPts(6) = 0.012068: extPts(7) = 0.104909: extPts(8) = 0#
    extPts(9) = 0.027129: extPts(10) = 0.157084: extPts(11) = 0#
    extPts(12) = 0.048169: extPts(13) = 0.208923: extPts(14) = 0#
    extPts(15) = 0.075144: extPts(16) = 0.260317: extPts(17) = 0#
    extPts(18) = 0.107995: extPts(19) = 0.311155: extPts(20) = 0#
    extPts(21) = 0.146654: extPts(22) = 0.361329: extPts(23) = 0#
    extPts(24) = 0.191036: extPts(25) = 0.410732: extPts(26) = 0#
    extPts(27) = 0.241048: extPts(28) = 0.459258: extPts(29) = 0#
    extPts(30) = 0.296583: extPts(31) = 0.506805: extPts(32) = 0#
    extPts(33) = 0.357522: extPts(34) = 0.553269: extPts(35) = 0#
    extPts(36) = 0.423736: extPts(37) = 0.598553: extPts(38) = 0#
    extPts(39) = 0.495082: extPts(40) = 0.642560: extPts(41) = 0#
    extPts(42) = 0.571409: extPts(43) = 0.685196: extPts(44) = 0#
    extPts(45) = 0.652554: extPts(46) = 0.726369: extPts(47) = 0#
    extPts(48) = 0.738344: extPts(49) = 0.765992: extPts(50) = 0#
    extPts(51) = 0.828595: extPts(52) = 0.803980: extPts(53) = 0#
    extPts(54) = 0.923115: extPts(55) = 0.840253: extPts(56) = 0#
    extPts(57) = 1.021702: extPts(58) = 0.874733: extPts(59) = 0#
    extPts(60) = 1.124147: extPts(61) = 0.907346: extPts(62) = 0#
    extPts(63) = 1.230229: extPts(64) = 0.938022: extPts(65) = 0#
    extPts(66) = 1.339723: extPts(67) = 0.966697: extPts(68) = 0#
    extPts(69) = 1.452396: extPts(70) = 0.993309: extPts(71) = 0#
    extPts(72) = 1.568006: extPts(73) = 1.017801: extPts(74) = 0#
    extPts(75) = 1.686307: extPts(76) = 1.040121: extPts(77) = 0#
    extPts(78) = 1.807047: extPts(79) = 1.060221: extPts(80) = 0#
    extPts(81) = 1.929968: extPts(82) = 1.078059: extPts(83) = 0#
    extPts(84) = 2.054807: extPts(85) = 1.093596: extPts(86) = 0#
    extPts(87) = 2.181299: extPts(88) = 1.106799: extPts(89) = 0#
    extPts(90) = 2.309173: extPts(91) = 1.117640: extPts(92) = 0#
    extPts(93) = 2.438156: extPts(94) = 1.126097: extPts(95) = 0#
    extPts(96) = 2.567973: extPts(97) = 1.132150: extPts(98) = 0#
    extPts(99) = 2.698347: extPts(100) = 1.135787: extPts(101) = 0#
    extPts(102) = 2.829000: extPts(103) = 1.137000: extPts(104) = 0#
    extPts(105) = 3.025453: extPts(106) = 1.136205: extPts(107) = 0#
    extPts(108) = 3.221632: extPts(109) = 1.133821: extPts(110) = 0#
    extPts(111) = 3.417261: extPts(112) = 1.129851: extPts(113) = 0#
    extPts(114) = 3.612068: extPts(115) = 1.124301: extPts(116) = 0#
    extPts(117) = 3.805780: extPts(118) = 1.117178: extPts(119) = 0#
    extPts(120) = 3.998125: extPts(121) = 1.108493: extPts(122) = 0#
    extPts(123) = 4.188835: extPts(124) = 1.098258: extPts(125) = 0#
    extPts(126) = 4.377644: extPts(127) = 1.086486: extPts(128) = 0#
    extPts(129) = 4.564286: extPts(130) = 1.073195: extPts(131) = 0#
    extPts(132) = 4.748502: extPts(133) = 1.058403: extPts(134) = 0#
    extPts(135) = 4.930033: extPts(136) = 1.042131: extPts(137) = 0#
    extPts(138) = 5.108625: extPts(139) = 1.024402: extPts(140) = 0#
    extPts(141) = 5.284029: extPts(142) = 1.005239: extPts(143) = 0#
    extPts(144) = 5.456000: extPts(145) = 0.984671: extPts(146) = 0#
    extPts(147) = 5.624297: extPts(148) = 0.962725: extPts(149) = 0#
    extPts(150) = 5.788684: extPts(151) = 0.939433: extPts(152) = 0#
    extPts(153) = 5.948931: extPts(154) = 0.914828: extPts(155) = 0#
    extPts(156) = 6.104815: extPts(157) = 0.888942: extPts(158) = 0#
    extPts(159) = 6.256118: extPts(160) = 0.861814: extPts(161) = 0#
    extPts(162) = 6.402628: extPts(163) = 0.833480: extPts(164) = 0#
    extPts(165) = 6.544139: extPts(166) = 0.803980: extPts(167) = 0#
    extPts(168) = 6.680455: extPts(169) = 0.773356: extPts(170) = 0#
    extPts(171) = 6.811383: extPts(172) = 0.741651: extPts(173) = 0#
    extPts(174) = 6.936743: extPts(175) = 0.708908: extPts(176) = 0#
    extPts(177) = 7.056357: extPts(178) = 0.675174: extPts(179) = 0#
    extPts(180) = 7.170059: extPts(181) = 0.640495: extPts(182) = 0#
    extPts(183) = 7.277689: extPts(184) = 0.604920: extPts(185) = 0#
    extPts(186) = 7.379097: extPts(187) = 0.568500: extPts(188) = 0#
    extPts(189) = 7.474142: extPts(190) = 0.531284: extPts(191) = 0#
    extPts(192) = 7.562690: extPts(193) = 0.493326: extPts(194) = 0#
    extPts(195) = 7.644618: extPts(196) = 0.454677: extPts(197) = 0#
    extPts(198) = 7.719811: extPts(199) = 0.415393: extPts(200) = 0#
    extPts(201) = 7.788163: extPts(202) = 0.375527: extPts(203) = 0#
    extPts(204) = 7.849580: extPts(205) = 0.335137: extPts(206) = 0#
    extPts(207) = 7.903974: extPts(208) = 0.294277: extPts(209) = 0#
    extPts(210) = 7.951271: extPts(211) = 0.253006: extPts(212) = 0#
    extPts(213) = 7.991404: extPts(214) = 0.211381: extPts(215) = 0#
    extPts(216) = 8.024317: extPts(217) = 0.169461: extPts(218) = 0#
    extPts(219) = 8.049964: extPts(220) = 0.127304: extPts(221) = 0#
    extPts(222) = 8.068309: extPts(223) = 0.084968: extPts(224) = 0#
    extPts(225) = 8.079326: extPts(226) = 0.042514: extPts(227) = 0#
    extPts(228) = 8.083000: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 8.080000: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 8.076328: intPts(4) = 0.042402: intPts(5) = 0#
    intPts(6) = 8.065317: intPts(7) = 0.084744: intPts(8) = 0#
    intPts(9) = 8.046983: intPts(10) = 0.126968: intPts(11) = 0#
    intPts(12) = 8.021351: intPts(13) = 0.169014: intPts(14) = 0#
    intPts(15) = 7.988457: intPts(16) = 0.210824: intPts(17) = 0#
    intPts(18) = 7.948346: intPts(19) = 0.252339: intPts(20) = 0#
    intPts(21) = 7.901077: intPts(22) = 0.293501: intPts(23) = 0#
    intPts(24) = 7.846713: intPts(25) = 0.334252: intPts(26) = 0#
    intPts(27) = 7.785331: intPts(28) = 0.374536: intPts(29) = 0#
    intPts(30) = 7.717018: intPts(31) = 0.414297: intPts(32) = 0#
    intPts(33) = 7.641868: intPts(34) = 0.453478: intPts(35) = 0#
    intPts(36) = 7.559988: intPts(37) = 0.492024: intPts(38) = 0#
    intPts(39) = 7.471490: intPts(40) = 0.529883: intPts(41) = 0#
    intPts(42) = 7.376499: intPts(43) = 0.567000: intPts(44) = 0#
    intPts(45) = 7.275149: intPts(46) = 0.603324: intPts(47) = 0#
    intPts(48) = 7.167580: intPts(49) = 0.638805: intPts(50) = 0#
    intPts(51) = 7.053943: intPts(52) = 0.673392: intPts(53) = 0#
    intPts(54) = 6.934397: intPts(55) = 0.707037: intPts(56) = 0#
    intPts(57) = 6.809110: intPts(58) = 0.739694: intPts(59) = 0#
    intPts(60) = 6.678255: intPts(61) = 0.771316: intPts(62) = 0#
    intPts(63) = 6.542018: intPts(64) = 0.801859: intPts(65) = 0#
    intPts(66) = 6.400587: intPts(67) = 0.831281: intPts(68) = 0#
    intPts(69) = 6.254161: intPts(70) = 0.859540: intPts(71) = 0#
    intPts(72) = 6.102945: intPts(73) = 0.886597: intPts(74) = 0#
    intPts(75) = 5.947150: intPts(76) = 0.912414: intPts(77) = 0#
    intPts(78) = 5.786994: intPts(79) = 0.936955: intPts(80) = 0#
    intPts(81) = 5.622700: intPts(82) = 0.960185: intPts(83) = 0#
    intPts(84) = 5.454500: intPts(85) = 0.982073: intPts(86) = 0#
    intPts(87) = 5.282628: intPts(88) = 1.002587: intPts(89) = 0#
    intPts(90) = 5.107324: intPts(91) = 1.021699: intPts(92) = 0#
    intPts(93) = 4.928833: intPts(94) = 1.039382: intPts(95) = 0#
    intPts(96) = 4.747406: intPts(97) = 1.055611: intPts(98) = 0#
    intPts(99) = 4.563295: intPts(100) = 1.070364: intPts(101) = 0#
    intPts(102) = 4.376759: intPts(103) = 1.083620: intPts(104) = 0#
    intPts(105) = 4.188059: intPts(106) = 1.095360: intPts(107) = 0#
    intPts(108) = 3.997457: intPts(109) = 1.105568: intPts(110) = 0#
    intPts(111) = 3.805222: intPts(112) = 1.114230: intPts(113) = 0#
    intPts(114) = 3.611621: intPts(115) = 1.121334: intPts(116) = 0#
    intPts(117) = 3.416925: intPts(118) = 1.126870: intPts(119) = 0#
    intPts(120) = 3.221408: intPts(121) = 1.130829: intPts(122) = 0#
    intPts(123) = 3.025341: intPts(124) = 1.133207: intPts(125) = 0#
    intPts(126) = 2.829000: intPts(127) = 1.134000: intPts(128) = 0#
    intPts(129) = 2.698486: intPts(130) = 1.132790: intPts(131) = 0#
    intPts(132) = 2.568250: intPts(133) = 1.129163: intPts(134) = 0#
    intPts(135) = 2.438570: intPts(136) = 1.123125: intPts(137) = 0#
    intPts(138) = 2.309724: intPts(139) = 1.114691: intPts(140) = 0#
    intPts(141) = 2.181986: intPts(142) = 1.103879: intPts(143) = 0#
    intPts(144) = 2.055628: intPts(145) = 1.090710: intPts(146) = 0#
    intPts(147) = 1.930921: intPts(148) = 1.075214: intPts(149) = 0#
    intPts(150) = 1.808131: intPts(151) = 1.057424: intPts(152) = 0#
    intPts(153) = 1.687519: intPts(154) = 1.037376: intPts(155) = 0#
    intPts(156) = 1.569343: intPts(157) = 1.015115: intPts(158) = 0#
    intPts(159) = 1.453856: intPts(160) = 0.990688: intPts(161) = 0#
    intPts(162) = 1.341303: intPts(163) = 0.964146: intPts(164) = 0#
    intPts(165) = 1.231924: intPts(166) = 0.935547: intPts(167) = 0#
    intPts(168) = 1.125955: intPts(169) = 0.904952: intPts(170) = 0#
    intPts(171) = 1.023619: intPts(172) = 0.872425: intPts(173) = 0#
    intPts(174) = 0.925136: intPts(175) = 0.838036: intPts(176) = 0#
    intPts(177) = 0.830716: intPts(178) = 0.801859: intPts(179) = 0#
    intPts(180) = 0.740561: intPts(181) = 0.763971: intPts(182) = 0#
    intPts(183) = 0.654862: intPts(184) = 0.724452: intPts(185) = 0#
    intPts(186) = 0.573803: intPts(187) = 0.683388: intPts(188) = 0#
    intPts(189) = 0.497557: intPts(190) = 0.640865: intPts(191) = 0#
    intPts(192) = 0.426286: intPts(193) = 0.596974: intPts(194) = 0#
    intPts(195) = 0.360143: intPts(196) = 0.551809: intPts(197) = 0#
    intPts(198) = 0.299269: intPts(199) = 0.505467: intPts(200) = 0#
    intPts(201) = 0.243793: intPts(202) = 0.458046: intPts(203) = 0#
    intPts(204) = 0.193833: intPts(205) = 0.409648: intPts(206) = 0#
    intPts(207) = 0.149498: intPts(208) = 0.360375: intPts(209) = 0#
    intPts(210) = 0.110881: intPts(211) = 0.310334: intPts(212) = 0#
    intPts(213) = 0.078064: intPts(214) = 0.259630: intPts(215) = 0#
    intPts(216) = 0.051118: intPts(217) = 0.208372: intPts(218) = 0#
    intPts(219) = 0.030100: intPts(220) = 0.156669: intPts(221) = 0#
    intPts(222) = 0.015055: intPts(223) = 0.104632: intPts(224) = 0#
    intPts(225) = 0.006015: intPts(226) = 0.052372: intPts(227) = 0#
    intPts(228) = 0.003000: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 8.083000, 0#, 0#, 8.080000, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.003000, 0#, 0#, 0.000000, 0#, 0#

    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 6.283185307180, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Piel_Exterior_Casco"

    ' --- Capa_Aislante_1_360 (offset = 29.1 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.029100: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.032088: extPts(4) = 0.051167: extPts(5) = 0#
    extPts(6) = 0.041044: extPts(7) = 0.102224: extPts(8) = 0#
    extPts(9) = 0.055950: extPts(10) = 0.153063: extPts(11) = 0#
    extPts(12) = 0.076774: extPts(13) = 0.203576: extPts(14) = 0#
    extPts(15) = 0.103471: extPts(16) = 0.253654: extPts(17) = 0#
    extPts(18) = 0.135984: extPts(19) = 0.303191: extPts(20) = 0#
    extPts(21) = 0.174245: extPts(22) = 0.352081: extPts(23) = 0#
    extPts(24) = 0.218171: extPts(25) = 0.400220: extPts(26) = 0#
    extPts(27) = 0.267669: extPts(28) = 0.447504: extPts(29) = 0#
    extPts(30) = 0.322632: extPts(31) = 0.493834: extPts(32) = 0#
    extPts(33) = 0.382945: extPts(34) = 0.539109: extPts(35) = 0#
    extPts(36) = 0.448477: extPts(37) = 0.583234: extPts(38) = 0#
    extPts(39) = 0.519090: extPts(40) = 0.626115: extPts(41) = 0#
    extPts(42) = 0.594632: extPts(43) = 0.667659: extPts(44) = 0#
    extPts(45) = 0.674942: extPts(46) = 0.707778: extPts(47) = 0#
    extPts(48) = 0.759849: extPts(49) = 0.746387: extPts(50) = 0#
    extPts(51) = 0.849172: extPts(52) = 0.783404: extPts(53) = 0#
    extPts(54) = 0.942720: extPts(55) = 0.818748: extPts(56) = 0#
    extPts(57) = 1.040293: extPts(58) = 0.852345: extPts(59) = 0#
    extPts(60) = 1.141683: extPts(61) = 0.884123: extPts(62) = 0#
    extPts(63) = 1.246675: extPts(64) = 0.914015: extPts(65) = 0#
    extPts(66) = 1.355043: extPts(67) = 0.941956: extPts(68) = 0#
    extPts(69) = 1.466556: extPts(70) = 0.967886: extPts(71) = 0#
    extPts(72) = 1.580977: extPts(73) = 0.991751: extPts(74) = 0#
    extPts(75) = 1.698062: extPts(76) = 1.013500: extPts(77) = 0#
    extPts(78) = 1.817559: extPts(79) = 1.033086: extPts(80) = 0#
    extPts(81) = 1.939216: extPts(82) = 1.050467: extPts(83) = 0#
    extPts(84) = 2.062771: extPts(85) = 1.065607: extPts(86) = 0#
    extPts(87) = 2.187961: extPts(88) = 1.078472: extPts(89) = 0#
    extPts(90) = 2.314520: extPts(91) = 1.089036: extPts(92) = 0#
    extPts(93) = 2.442176: extPts(94) = 1.097276: extPts(95) = 0#
    extPts(96) = 2.570658: extPts(97) = 1.103174: extPts(98) = 0#
    extPts(99) = 2.699691: extPts(100) = 1.106718: extPts(101) = 0#
    extPts(102) = 2.829000: extPts(103) = 1.107900: extPts(104) = 0#
    extPts(105) = 3.024365: extPts(106) = 1.107125: extPts(107) = 0#
    extPts(108) = 3.219457: extPts(109) = 1.104802: extPts(110) = 0#
    extPts(111) = 3.414003: extPts(112) = 1.100934: extPts(113) = 0#
    extPts(114) = 3.607731: extPts(115) = 1.095526: extPts(116) = 0#
    extPts(117) = 3.800370: extPts(118) = 1.088585: extPts(119) = 0#
    extPts(120) = 3.991650: extPts(121) = 1.080123: extPts(122) = 0#
    extPts(123) = 4.181304: extPts(124) = 1.070149: extPts(125) = 0#
    extPts(126) = 4.369066: extPts(127) = 1.058679: extPts(128) = 0#
    extPts(129) = 4.554675: extPts(130) = 1.045728: extPts(131) = 0#
    extPts(132) = 4.737870: extPts(133) = 1.031315: extPts(134) = 0#
    extPts(135) = 4.918396: extPts(136) = 1.015459: extPts(137) = 0#
    extPts(138) = 5.095999: extPts(139) = 0.998183: extPts(140) = 0#
    extPts(141) = 5.270432: extPts(142) = 0.979511: extPts(143) = 0#
    extPts(144) = 5.441450: extPts(145) = 0.959470: extPts(146) = 0#
    extPts(147) = 5.608814: extPts(148) = 0.938086: extPts(149) = 0#
    extPts(150) = 5.772291: extPts(151) = 0.915390: extPts(152) = 0#
    extPts(153) = 5.931651: extPts(154) = 0.891414: extPts(155) = 0#
    extPts(156) = 6.086672: extPts(157) = 0.866191: extPts(158) = 0#
    extPts(159) = 6.237136: extPts(160) = 0.839757: extPts(161) = 0#
    extPts(162) = 6.382835: extPts(163) = 0.812148: extPts(164) = 0#
    extPts(165) = 6.523562: extPts(166) = 0.783404: extPts(167) = 0#
    extPts(168) = 6.659123: extPts(169) = 0.753563: extPts(170) = 0#
    extPts(171) = 6.789326: extPts(172) = 0.722669: extPts(173) = 0#
    extPts(174) = 6.913991: extPts(175) = 0.690764: extPts(176) = 0#
    extPts(177) = 7.032943: extPts(178) = 0.657893: extPts(179) = 0#
    extPts(180) = 7.146015: extPts(181) = 0.624102: extPts(182) = 0#
    extPts(183) = 7.253049: extPts(184) = 0.589438: extPts(185) = 0#
    extPts(186) = 7.353896: extPts(187) = 0.553950: extPts(188) = 0#
    extPts(189) = 7.448415: extPts(190) = 0.517687: extPts(191) = 0#
    extPts(192) = 7.536472: extPts(193) = 0.480700: extPts(194) = 0#
    extPts(195) = 7.617946: extPts(196) = 0.443040: extPts(197) = 0#
    extPts(198) = 7.692722: extPts(199) = 0.404761: extPts(200) = 0#
    extPts(201) = 7.760696: extPts(202) = 0.365916: extPts(203) = 0#
    extPts(204) = 7.821772: extPts(205) = 0.326559: extPts(206) = 0#
    extPts(207) = 7.875866: extPts(208) = 0.286746: extPts(209) = 0#
    extPts(210) = 7.922901: extPts(211) = 0.246531: extPts(212) = 0#
    extPts(213) = 7.962812: extPts(214) = 0.205971: extPts(215) = 0#
    extPts(216) = 7.995542: extPts(217) = 0.165124: extPts(218) = 0#
    extPts(219) = 8.021047: extPts(220) = 0.124045: extPts(221) = 0#
    extPts(222) = 8.039290: extPts(223) = 0.082793: extPts(224) = 0#
    extPts(225) = 8.050246: extPts(226) = 0.041426: extPts(227) = 0#
    extPts(228) = 8.053900: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 8.050900: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 8.047248: intPts(4) = 0.041314: intPts(5) = 0#
    intPts(6) = 8.036299: intPts(7) = 0.082569: intPts(8) = 0#
    intPts(9) = 8.018066: intPts(10) = 0.123710: intPts(11) = 0#
    intPts(12) = 7.992576: intPts(13) = 0.164677: intPts(14) = 0#
    intPts(15) = 7.959864: intPts(16) = 0.205414: intPts(17) = 0#
    intPts(18) = 7.919976: intPts(19) = 0.245863: intPts(20) = 0#
    intPts(21) = 7.872968: intPts(22) = 0.285969: intPts(23) = 0#
    intPts(24) = 7.818906: intPts(25) = 0.325675: intPts(26) = 0#
    intPts(27) = 7.757864: intPts(28) = 0.364925: intPts(29) = 0#
    intPts(30) = 7.689930: intPts(31) = 0.403665: intPts(32) = 0#
    intPts(33) = 7.615196: intPts(34) = 0.441841: intPts(35) = 0#
    intPts(36) = 7.533769: intPts(37) = 0.479398: intPts(38) = 0#
    intPts(39) = 7.445762: intPts(40) = 0.516285: intPts(41) = 0#
    intPts(42) = 7.351298: intPts(43) = 0.552450: intPts(44) = 0#
    intPts(45) = 7.250509: intPts(46) = 0.587842: intPts(47) = 0#
    intPts(48) = 7.143536: intPts(49) = 0.622412: intPts(50) = 0#
    intPts(51) = 7.030529: intPts(52) = 0.656112: intPts(53) = 0#
    intPts(54) = 6.911646: intPts(55) = 0.688894: intPts(56) = 0#
    intPts(57) = 6.787053: intPts(58) = 0.720712: intPts(59) = 0#
    intPts(60) = 6.656924: intPts(61) = 0.751523: intPts(62) = 0#
    intPts(63) = 6.521441: intPts(64) = 0.781282: intPts(65) = 0#
    intPts(66) = 6.380794: intPts(67) = 0.809949: intPts(68) = 0#
    intPts(69) = 6.235180: intPts(70) = 0.837483: intPts(71) = 0#
    intPts(72) = 6.084801: intPts(73) = 0.863846: intPts(74) = 0#
    intPts(75) = 5.929870: intPts(76) = 0.889000: intPts(77) = 0#
    intPts(78) = 5.770601: intPts(79) = 0.912911: intPts(80) = 0#
    intPts(81) = 5.607218: intPts(82) = 0.935546: intPts(83) = 0#
    intPts(84) = 5.439950: intPts(85) = 0.956871: intPts(86) = 0#
    intPts(87) = 5.269030: intPts(88) = 0.976859: intPts(89) = 0#
    intPts(90) = 5.094697: intPts(91) = 0.995481: intPts(92) = 0#
    intPts(93) = 4.917196: intPts(94) = 1.012710: intPts(95) = 0#
    intPts(96) = 4.736774: intPts(97) = 1.028522: intPts(98) = 0#
    intPts(99) = 4.553684: intPts(100) = 1.042897: intPts(101) = 0#
    intPts(102) = 4.368182: intPts(103) = 1.055812: intPts(104) = 0#
    intPts(105) = 4.180527: intPts(106) = 1.067251: intPts(107) = 0#
    intPts(108) = 3.990982: intPts(109) = 1.077198: intPts(110) = 0#
    intPts(111) = 3.799812: intPts(112) = 1.085638: intPts(113) = 0#
    intPts(114) = 3.607284: intPts(115) = 1.092559: intPts(116) = 0#
    intPts(117) = 3.413667: intPts(118) = 1.097953: intPts(119) = 0#
    intPts(120) = 3.219233: intPts(121) = 1.101810: intPts(122) = 0#
    intPts(123) = 3.024253: intPts(124) = 1.104127: intPts(125) = 0#
    intPts(126) = 2.829000: intPts(127) = 1.104900: intPts(128) = 0#
    intPts(129) = 2.699829: intPts(130) = 1.103721: intPts(131) = 0#
    intPts(132) = 2.570935: intPts(133) = 1.100187: intPts(134) = 0#
    intPts(135) = 2.442590: intPts(136) = 1.094304: intPts(137) = 0#
    intPts(138) = 2.315071: intPts(139) = 1.086087: intPts(140) = 0#
    intPts(141) = 2.188648: intPts(142) = 1.075552: intPts(143) = 0#
    intPts(144) = 2.063592: intPts(145) = 1.062721: intPts(146) = 0#
    intPts(147) = 1.940169: intPts(148) = 1.047623: intPts(149) = 0#
    intPts(150) = 1.818643: intPts(151) = 1.030289: intPts(152) = 0#
    intPts(153) = 1.699273: intPts(154) = 1.010756: intPts(155) = 0#
    intPts(156) = 1.582314: intPts(157) = 0.989066: intPts(158) = 0#
    intPts(159) = 1.468016: intPts(160) = 0.965265: intPts(161) = 0#
    intPts(162) = 1.356622: intPts(163) = 0.939405: intPts(164) = 0#
    intPts(165) = 1.248370: intPts(166) = 0.911540: intPts(167) = 0#
    intPts(168) = 1.143491: intPts(169) = 0.881729: intPts(170) = 0#
    intPts(171) = 1.042209: intPts(172) = 0.850037: intPts(173) = 0#
    intPts(174) = 0.944741: intPts(175) = 0.816531: intPts(176) = 0#
    intPts(177) = 0.851293: intPts(178) = 0.781282: intPts(179) = 0#
    intPts(180) = 0.762066: intPts(181) = 0.744366: intPts(182) = 0#
    intPts(183) = 0.677250: intPts(184) = 0.705862: intPts(185) = 0#
    intPts(186) = 0.597026: intPts(187) = 0.665851: intPts(188) = 0#
    intPts(189) = 0.521565: intPts(190) = 0.624419: intPts(191) = 0#
    intPts(192) = 0.451028: intPts(193) = 0.581655: intPts(194) = 0#
    intPts(195) = 0.385566: intPts(196) = 0.537649: intPts(197) = 0#
    intPts(198) = 0.325318: intPts(199) = 0.492496: intPts(200) = 0#
    intPts(201) = 0.270413: intPts(202) = 0.446292: intPts(203) = 0#
    intPts(204) = 0.220968: intPts(205) = 0.399136: intPts(206) = 0#
    intPts(207) = 0.177089: intPts(208) = 0.351128: intPts(209) = 0#
    intPts(210) = 0.138870: intPts(211) = 0.302370: intPts(212) = 0#
    intPts(213) = 0.106391: intPts(214) = 0.252967: intPts(215) = 0#
    intPts(216) = 0.079723: intPts(217) = 0.203025: intPts(218) = 0#
    intPts(219) = 0.058921: intPts(220) = 0.152649: intPts(221) = 0#
    intPts(222) = 0.044031: intPts(223) = 0.101947: intPts(224) = 0#
    intPts(225) = 0.035084: intPts(226) = 0.051028: intPts(227) = 0#
    intPts(228) = 0.032100: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 8.053900, 0#, 0#, 8.050900, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.032100, 0#, 0#, 0.029100, 0#, 0#

    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 6.283185307180, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Capa_Aislante_1_360"

    ' --- Anillos_Celulares_360 ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 1.290280, 0.925978, 1.296280, 0.952345)
    Call DibujarRectangulo(swSketchMgr, 2.206353, 1.080028, 2.212353, 1.106804)
    Call DibujarRectangulo(swSketchMgr, 3.122427, 1.105716, 3.128427, 1.132592)
    Call DibujarRectangulo(swSketchMgr, 4.038500, 1.077255, 4.044500, 1.103754)
    Call DibujarRectangulo(swSketchMgr, 4.954573, 1.011394, 4.960573, 1.037052)
    Call DibujarRectangulo(swSketchMgr, 5.870647, 0.899961, 5.876647, 0.924319)
    Call DibujarRectangulo(swSketchMgr, 6.786720, 0.722172, 6.792720, 0.744932)
    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        True, True, False, False, False, False, _
        0, 0, 6.283185307180, 0#, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Anillos_Celulares_360"


    ' -------------------------------------------------------------------------
    ' 2. Gondola rectangular de componentes internos (bajo X_CB, gap 135 mm)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.438375, -1.504840, 4.038375, -1.254840)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.300000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Gondola_Componentes"

    ' -------------------------------------------------------------------------
    ' 3. Dos soportes verticales de suspension (casco <-> gondola)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.503375, -1.254840, 3.533375, -1.085421)
    Call DibujarRectangulo(swSketchMgr, 3.943375, -1.254840, 3.973375, -1.085421)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.03#, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Soportes_Gondola"

    ' -------------------------------------------------------------------------
    ' 4. Brazos transversales en H alineados bajo los puntales dentro de la gondola
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.505875, -1.392340, 3.530875, -1.367340)
    Call DibujarRectangulo(swSketchMgr, 3.945875, -1.392340, 3.970875, -1.367340)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 1.125000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Brazos_Transversales_H"

    ' -------------------------------------------------------------------------
    ' 5. Tirantes diagonales triangulados (union superior gondola <-> brazos)
    ' -------------------------------------------------------------------------
    ' --- Tirantes_Triangulados_Del (en X = 3.518 m) ---
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 3.518375, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Tirantes_Del"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarPoligono4(swSketchMgr, 0.140286, -1.266135, 0.517286, -1.365135, 0.512714, -1.382545, 0.135714, -1.283545)
    Call DibujarPoligono4(swSketchMgr, -0.135714, -1.283545, -0.512714, -1.382545, -0.517286, -1.365135, -0.140286, -1.266135)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.018000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tirantes_Triangulados_Del"

    ' --- Tirantes_Triangulados_Tras (en X = 3.958 m) ---
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 3.958375, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Tirantes_Tras"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarPoligono4(swSketchMgr, 0.140286, -1.266135, 0.517286, -1.365135, 0.512714, -1.382545, 0.135714, -1.283545)
    Call DibujarPoligono4(swSketchMgr, -0.135714, -1.283545, -0.512714, -1.382545, -0.517286, -1.365135, -0.140286, -1.266135)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.018000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tirantes_Triangulados_Tras"


    ' -------------------------------------------------------------------------
    ' 6. Largueros longitudinales en H (conectan brazos transversales con los motores)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.379840, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Brazos_H"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.293375, -0.562500, 4.183375, -0.537500)
    Call DibujarRectangulo(swSketchMgr, 3.293375, 0.537500, 4.183375, 0.562500)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.025000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Largueros_H"

    ' -------------------------------------------------------------------------
    ' 7. Motores A2212 referenciales (4 motores en 2 costados)
    ' -------------------------------------------------------------------------
    Dim xsMot(0 To 1) As Double
    xsMot(0) = 3.318375
    xsMot(1) = 4.158375
    Dim i As Long

    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.367340, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Base_Motores"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    For i = 0 To 1
        swSketchMgr.CreateCircleByRadius xsMot(i), 0.550000, 0#, 0.015000
        swSketchMgr.CreateCircleByRadius xsMot(i), -0.550000, 0#, 0.015000
    Next i
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.030000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Motores_A2212"

    ' -------------------------------------------------------------------------
    ' 8. Discos referenciales de helices (dia 254 mm)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.337340, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Helices"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    For i = 0 To 1
        swSketchMgr.CreateCircleByRadius xsMot(i), 0.550000, 0#, 0.127000
        swSketchMgr.CreateCircleByRadius xsMot(i), -0.550000, 0#, 0.127000
    Next i
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_BLIND, 0.006000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Helices_Ref"

    swModel.ClearSelection2 True
    swModel.SetAddToDB False
    swModel.SetDisplayWhenAdded True
    swModel.ForceRebuild3 False
    swModel.ShowNamedView2 "*Isometric", 7
    swModel.ViewZoomtofit2

    MsgBox "Dirigible referencial generado correctamente:" & vbCrLf & _
           "Casco hueco: 8083 x 2274 mm | Capas: 1 sup / 1 inf (e=29.1 mm)" & vbCrLf & _
           "Gondola (X_CB=3738 mm): 600 x 300 x 250 mm (gap 135 mm)" & vbCrLf & _
           "Bastidor H con 4 tirantes triangulados + 4 motores dia 254 mm" & vbCrLf & _
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
