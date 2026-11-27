Attribute VB_Name = "DirigibleReferencial"
Option Explicit

' =============================================================================
' Modelo CAD Referencial de Dirigible Hibrido para SolidWorks
' Generado automaticamente por generar_cad_solidworks.py
' Caso: ptimo (50.0 pts  lam==2.94, T2=93.3 degC)
' Casco hueco + capas celulares asimetricas: 4 sup / 2 inf (e = 31.8 mm)
' Dimensiones: L=7.082 m | D=2.408 m (cf=2.479 m, cr=4.603 m) | V=21.51 m3
' Centro flotacion X_CB = 3.276 m | Motores: 4 x dia 254 mm en +/-0.550 m
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
    ' 1. Piel exterior del casco y capas celulares asimetricas (4 sup / 2 inf)
    ' -------------------------------------------------------------------------
    ' --- Piel_Exterior_Casco (offset = 0.0 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.000000: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.002645: extPts(4) = 0.055605: extPts(5) = 0#
    extPts(6) = 0.010575: extPts(7) = 0.111091: extPts(8) = 0#
    extPts(9) = 0.023773: extPts(10) = 0.166340: extPts(11) = 0#
    extPts(12) = 0.042210: extPts(13) = 0.221234: extPts(14) = 0#
    extPts(15) = 0.065847: extPts(16) = 0.275656: extPts(17) = 0#
    extPts(18) = 0.094634: extPts(19) = 0.329490: extPts(20) = 0#
    extPts(21) = 0.128510: extPts(22) = 0.382621: extPts(23) = 0#
    extPts(24) = 0.167401: extPts(25) = 0.434935: extPts(26) = 0#
    extPts(27) = 0.211226: extPts(28) = 0.486321: extPts(29) = 0#
    extPts(30) = 0.259890: extPts(31) = 0.536669: extPts(32) = 0#
    extPts(33) = 0.313290: extPts(34) = 0.585872: extPts(35) = 0#
    extPts(36) = 0.371312: extPts(37) = 0.633824: extPts(38) = 0#
    extPts(39) = 0.433831: extPts(40) = 0.680424: extPts(41) = 0#
    extPts(42) = 0.500715: extPts(43) = 0.725572: extPts(44) = 0#
    extPts(45) = 0.571821: extPts(46) = 0.769172: extPts(47) = 0#
    extPts(48) = 0.646997: extPts(49) = 0.811130: extPts(50) = 0#
    extPts(51) = 0.726082: extPts(52) = 0.851357: extPts(53) = 0#
    extPts(54) = 0.808908: extPts(55) = 0.889767: extPts(56) = 0#
    extPts(57) = 0.895299: extPts(58) = 0.926278: extPts(59) = 0#
    extPts(60) = 0.985069: extPts(61) = 0.960813: extPts(62) = 0#
    extPts(63) = 1.078027: extPts(64) = 0.993297: extPts(65) = 0#
    extPts(66) = 1.173975: extPts(67) = 1.023661: extPts(68) = 0#
    extPts(69) = 1.272707: extPts(70) = 1.051841: extPts(71) = 0#
    extPts(72) = 1.374015: extPts(73) = 1.077777: extPts(74) = 0#
    extPts(75) = 1.477680: extPts(76) = 1.101412: extPts(77) = 0#
    extPts(78) = 1.583482: extPts(79) = 1.122697: extPts(80) = 0#
    extPts(81) = 1.691195: extPts(82) = 1.141585: extPts(83) = 0#
    extPts(84) = 1.800589: extPts(85) = 1.158038: extPts(86) = 0#
    extPts(87) = 1.911432: extPts(88) = 1.172019: extPts(89) = 0#
    extPts(90) = 2.023485: extPts(91) = 1.183500: extPts(92) = 0#
    extPts(93) = 2.136510: extPts(94) = 1.192454: extPts(95) = 0#
    extPts(96) = 2.250267: extPts(97) = 1.198864: extPts(98) = 0#
    extPts(99) = 2.364511: extPts(100) = 1.202715: extPts(101) = 0#
    extPts(102) = 2.479000: extPts(103) = 1.204000: extPts(104) = 0#
    extPts(105) = 2.651112: extPts(106) = 1.203158: extPts(107) = 0#
    extPts(108) = 2.822983: extPts(109) = 1.200633: extPts(110) = 0#
    extPts(111) = 2.994372: extPts(112) = 1.196430: extPts(113) = 0#
    extPts(114) = 3.165042: extPts(115) = 1.190552: extPts(116) = 0#
    extPts(117) = 3.334751: extPts(118) = 1.183010: extPts(119) = 0#
    extPts(120) = 3.503264: extPts(121) = 1.173813: extPts(122) = 0#
    extPts(123) = 3.670344: extPts(124) = 1.162975: extPts(125) = 0#
    extPts(126) = 3.835758: extPts(127) = 1.150510: extPts(128) = 0#
    extPts(129) = 3.999275: extPts(130) = 1.136436: extPts(131) = 0#
    extPts(132) = 4.160665: extPts(133) = 1.120772: extPts(134) = 0#
    extPts(135) = 4.319703: extPts(136) = 1.103541: extPts(137) = 0#
    extPts(138) = 4.476167: extPts(139) = 1.084767: extPts(140) = 0#
    extPts(141) = 4.629837: extPts(142) = 1.064475: extPts(143) = 0#
    extPts(144) = 4.780500: extPts(145) = 1.042695: extPts(146) = 0#
    extPts(147) = 4.927944: extPts(148) = 1.019456: extPts(149) = 0#
    extPts(150) = 5.071962: extPts(151) = 0.994791: extPts(152) = 0#
    extPts(153) = 5.212354: extPts(154) = 0.968736: extPts(155) = 0#
    extPts(156) = 5.348924: extPts(157) = 0.941325: extPts(158) = 0#
    extPts(159) = 5.481479: extPts(160) = 0.912598: extPts(161) = 0#
    extPts(162) = 5.609835: extPts(163) = 0.882594: extPts(164) = 0#
    extPts(165) = 5.733813: extPts(166) = 0.851357: extPts(167) = 0#
    extPts(168) = 5.853238: extPts(169) = 0.818928: extPts(170) = 0#
    extPts(171) = 5.967944: extPts(172) = 0.785354: extPts(173) = 0#
    extPts(174) = 6.077770: extPts(175) = 0.750682: extPts(176) = 0#
    extPts(177) = 6.182564: extPts(178) = 0.714960: extPts(179) = 0#
    extPts(180) = 6.282177: extPts(181) = 0.678237: extPts(182) = 0#
    extPts(183) = 6.376471: extPts(184) = 0.640567: extPts(185) = 0#
    extPts(186) = 6.465315: extPts(187) = 0.602000: extPts(188) = 0#
    extPts(189) = 6.548583: extPts(190) = 0.562591: extPts(191) = 0#
    extPts(192) = 6.626160: extPts(193) = 0.522396: extPts(194) = 0#
    extPts(195) = 6.697936: extPts(196) = 0.481470: extPts(197) = 0#
    extPts(198) = 6.763812: extPts(199) = 0.439871: extPts(200) = 0#
    extPts(201) = 6.823695: extPts(202) = 0.397656: extPts(203) = 0#
    extPts(204) = 6.877502: extPts(205) = 0.354885: extPts(206) = 0#
    extPts(207) = 6.925157: extPts(208) = 0.311618: extPts(209) = 0#
    extPts(210) = 6.966593: extPts(211) = 0.267915: extPts(212) = 0#
    extPts(213) = 7.001753: extPts(214) = 0.223838: extPts(215) = 0#
    extPts(216) = 7.030588: extPts(217) = 0.179447: extPts(218) = 0#
    extPts(219) = 7.053057: extPts(220) = 0.134805: extPts(221) = 0#
    extPts(222) = 7.069129: extPts(223) = 0.089975: extPts(224) = 0#
    extPts(225) = 7.078781: extPts(226) = 0.045019: extPts(227) = 0#
    extPts(228) = 7.082000: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 7.079000: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 7.075783: intPts(4) = 0.044907: intPts(5) = 0#
    intPts(6) = 7.066137: intPts(7) = 0.089751: intPts(8) = 0#
    intPts(9) = 7.050076: intPts(10) = 0.134469: intPts(11) = 0#
    intPts(12) = 7.027622: intPts(13) = 0.179000: intPts(14) = 0#
    intPts(15) = 6.998806: intPts(16) = 0.223280: intPts(17) = 0#
    intPts(18) = 6.963668: intPts(19) = 0.267248: intPts(20) = 0#
    intPts(21) = 6.922259: intPts(22) = 0.310842: intPts(23) = 0#
    intPts(24) = 6.874635: intPts(25) = 0.354001: intPts(26) = 0#
    intPts(27) = 6.820863: intPts(28) = 0.396665: intPts(29) = 0#
    intPts(30) = 6.761019: intPts(31) = 0.438775: intPts(32) = 0#
    intPts(33) = 6.695186: intPts(34) = 0.480270: intPts(35) = 0#
    intPts(36) = 6.623457: intPts(37) = 0.521094: intPts(38) = 0#
    intPts(39) = 6.545931: intPts(40) = 0.561190: intPts(41) = 0#
    intPts(42) = 6.462717: intPts(43) = 0.600500: intPts(44) = 0#
    intPts(45) = 6.373931: intPts(46) = 0.638971: intPts(47) = 0#
    intPts(48) = 6.279698: intPts(49) = 0.676547: intPts(50) = 0#
    intPts(51) = 6.180150: intPts(52) = 0.713178: intPts(53) = 0#
    intPts(54) = 6.075425: intPts(55) = 0.748811: intPts(56) = 0#
    intPts(57) = 5.965670: intPts(58) = 0.783397: intPts(59) = 0#
    intPts(60) = 5.851039: intPts(61) = 0.816887: intPts(62) = 0#
    intPts(63) = 5.731691: intPts(64) = 0.849235: intPts(65) = 0#
    intPts(66) = 5.607795: intPts(67) = 0.880395: intPts(68) = 0#
    intPts(69) = 5.479522: intPts(70) = 0.910324: intPts(71) = 0#
    intPts(72) = 5.347053: intPts(73) = 0.938980: intPts(74) = 0#
    intPts(75) = 5.210573: intPts(76) = 0.966322: intPts(77) = 0#
    intPts(78) = 5.070272: intPts(79) = 0.992313: intPts(80) = 0#
    intPts(81) = 4.926348: intPts(82) = 1.016916: intPts(83) = 0#
    intPts(84) = 4.779000: intPts(85) = 1.040097: intPts(86) = 0#
    intPts(87) = 4.628436: intPts(88) = 1.061823: intPts(89) = 0#
    intPts(90) = 4.474865: intPts(91) = 1.082064: intPts(92) = 0#
    intPts(93) = 4.318503: intPts(94) = 1.100791: intPts(95) = 0#
    intPts(96) = 4.159569: intPts(97) = 1.117979: intPts(98) = 0#
    intPts(99) = 3.998284: intPts(100) = 1.133604: intPts(101) = 0#
    intPts(102) = 3.834874: intPts(103) = 1.147643: intPts(104) = 0#
    intPts(105) = 3.669568: intPts(106) = 1.160077: intPts(107) = 0#
    intPts(108) = 3.502596: intPts(109) = 1.170888: intPts(110) = 0#
    intPts(111) = 3.334193: intPts(112) = 1.180062: intPts(113) = 0#
    intPts(114) = 3.164594: intPts(115) = 1.187586: intPts(116) = 0#
    intPts(117) = 2.994037: intPts(118) = 1.193448: intPts(119) = 0#
    intPts(120) = 2.822758: intPts(121) = 1.197642: intPts(122) = 0#
    intPts(123) = 2.650999: intPts(124) = 1.200160: intPts(125) = 0#
    intPts(126) = 2.479000: intPts(127) = 1.201000: intPts(128) = 0#
    intPts(129) = 2.364650: intPts(130) = 1.199719: intPts(131) = 0#
    intPts(132) = 2.250544: intPts(133) = 1.195877: intPts(134) = 0#
    intPts(135) = 2.136925: intPts(136) = 1.189483: intPts(137) = 0#
    intPts(138) = 2.024036: intPts(139) = 1.180551: intPts(140) = 0#
    intPts(141) = 1.912118: intPts(142) = 1.169099: intPts(143) = 0#
    intPts(144) = 1.801410: intPts(145) = 1.155153: intPts(146) = 0#
    intPts(147) = 1.692148: intPts(148) = 1.138741: intPts(149) = 0#
    intPts(150) = 1.584566: intPts(151) = 1.119899: intPts(152) = 0#
    intPts(153) = 1.478892: intPts(154) = 1.098667: intPts(155) = 0#
    intPts(156) = 1.375352: intPts(157) = 1.075091: intPts(158) = 0#
    intPts(159) = 1.274167: intPts(160) = 1.049220: intPts(161) = 0#
    intPts(162) = 1.175554: intPts(163) = 1.021111: intPts(164) = 0#
    intPts(165) = 1.079722: intPts(166) = 0.990822: intPts(167) = 0#
    intPts(168) = 0.986877: intPts(169) = 0.958419: intPts(170) = 0#
    intPts(171) = 0.897215: intPts(172) = 0.923970: intPts(173) = 0#
    intPts(174) = 0.810930: intPts(175) = 0.887550: intPts(176) = 0#
    intPts(177) = 0.728204: intPts(178) = 0.849235: intPts(179) = 0#
    intPts(180) = 0.649214: intPts(181) = 0.809108: intPts(182) = 0#
    intPts(183) = 0.574129: intPts(184) = 0.767255: intPts(185) = 0#
    intPts(186) = 0.503109: intPts(187) = 0.723764: intPts(188) = 0#
    intPts(189) = 0.436306: intPts(190) = 0.678729: intPts(191) = 0#
    intPts(192) = 0.373862: intPts(193) = 0.632245: intPts(194) = 0#
    intPts(195) = 0.315911: intPts(196) = 0.584412: intPts(197) = 0#
    intPts(198) = 0.262576: intPts(199) = 0.535332: intPts(200) = 0#
    intPts(201) = 0.213970: intPts(202) = 0.485109: intPts(203) = 0#
    intPts(204) = 0.170199: intPts(205) = 0.433851: intPts(206) = 0#
    intPts(207) = 0.131354: intPts(208) = 0.381667: intPts(209) = 0#
    intPts(210) = 0.097520: intPts(211) = 0.328669: intPts(212) = 0#
    intPts(213) = 0.068767: intPts(214) = 0.274970: intPts(215) = 0#
    intPts(216) = 0.045159: intPts(217) = 0.220683: intPts(218) = 0#
    intPts(219) = 0.026744: intPts(220) = 0.165926: intPts(221) = 0#
    intPts(222) = 0.013562: intPts(223) = 0.110814: intPts(224) = 0#
    intPts(225) = 0.005642: intPts(226) = 0.055466: intPts(227) = 0#
    intPts(228) = 0.003000: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 7.082000, 0#, 0#, 7.079000, 0#, 0#
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

    ' --- Capa_Aislante_1_360 (offset = 31.8 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.031800: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.034411: extPts(4) = 0.054136: extPts(5) = 0#
    extPts(6) = 0.042239: extPts(7) = 0.108157: extPts(8) = 0#
    extPts(9) = 0.055268: extPts(10) = 0.161947: extPts(11) = 0#
    extPts(12) = 0.073468: extPts(13) = 0.215391: extPts(14) = 0#
    extPts(15) = 0.096802: extPts(16) = 0.268376: extPts(17) = 0#
    extPts(18) = 0.125220: extPts(19) = 0.320788: extPts(20) = 0#
    extPts(21) = 0.158661: extPts(22) = 0.372515: extPts(23) = 0#
    extPts(24) = 0.197054: extPts(25) = 0.423447: extPts(26) = 0#
    extPts(27) = 0.240316: extPts(28) = 0.473476: extPts(29) = 0#
    extPts(30) = 0.288356: extPts(31) = 0.522495: extPts(32) = 0#
    extPts(33) = 0.341071: extPts(34) = 0.570398: extPts(35) = 0#
    extPts(36) = 0.398349: extPts(37) = 0.617084: extPts(38) = 0#
    extPts(39) = 0.460066: extPts(40) = 0.662453: extPts(41) = 0#
    extPts(42) = 0.526092: extPts(43) = 0.706408: extPts(44) = 0#
    extPts(45) = 0.596286: extPts(46) = 0.748856: extPts(47) = 0#
    extPts(48) = 0.670497: extPts(49) = 0.789706: extPts(50) = 0#
    extPts(51) = 0.748568: extPts(52) = 0.828871: extPts(53) = 0#
    extPts(54) = 0.830332: extPts(55) = 0.866266: extPts(56) = 0#
    extPts(57) = 0.915614: extPts(58) = 0.901813: extPts(59) = 0#
    extPts(60) = 1.004233: extPts(61) = 0.935436: extPts(62) = 0#
    extPts(63) = 1.095998: extPts(64) = 0.967062: extPts(65) = 0#
    extPts(66) = 1.190715: extPts(67) = 0.996625: extPts(68) = 0#
    extPts(69) = 1.288182: extPts(70) = 1.024060: extPts(71) = 0#
    extPts(72) = 1.388189: extPts(73) = 1.049310: extPts(74) = 0#
    extPts(75) = 1.490525: extPts(76) = 1.072321: extPts(77) = 0#
    extPts(78) = 1.594969: extPts(79) = 1.093044: extPts(80) = 0#
    extPts(81) = 1.701301: extPts(82) = 1.111434: extPts(83) = 0#
    extPts(84) = 1.809292: extPts(85) = 1.127452: extPts(86) = 0#
    extPts(87) = 1.918712: extPts(88) = 1.141064: extPts(89) = 0#
    extPts(90) = 2.029328: extPts(91) = 1.152241: extPts(92) = 0#
    extPts(93) = 2.140904: extPts(94) = 1.160959: extPts(95) = 0#
    extPts(96) = 2.253201: extPts(97) = 1.167200: extPts(98) = 0#
    extPts(99) = 2.365980: extPts(100) = 1.170949: extPts(101) = 0#
    extPts(102) = 2.479000: extPts(103) = 1.172200: extPts(104) = 0#
    extPts(105) = 2.649923: extPts(106) = 1.171380: extPts(107) = 0#
    extPts(108) = 2.820606: extPts(109) = 1.168922: extPts(110) = 0#
    extPts(111) = 2.990812: extPts(112) = 1.164829: extPts(113) = 0#
    extPts(114) = 3.160302: extPts(115) = 1.159107: extPts(116) = 0#
    extPts(117) = 3.328839: extPts(118) = 1.151764: extPts(119) = 0#
    extPts(120) = 3.496188: extPts(121) = 1.142810: extPts(122) = 0#
    extPts(123) = 3.662114: extPts(124) = 1.132258: extPts(125) = 0#
    extPts(126) = 3.826385: extPts(127) = 1.120122: extPts(128) = 0#
    extPts(129) = 3.988772: extPts(130) = 1.106420: extPts(131) = 0#
    extPts(132) = 4.149047: extPts(133) = 1.091170: extPts(134) = 0#
    extPts(135) = 4.306986: extPts(136) = 1.074394: extPts(137) = 0#
    extPts(138) = 4.462369: extPts(139) = 1.056116: extPts(140) = 0#
    extPts(141) = 4.614978: extPts(142) = 1.036360: extPts(143) = 0#
    extPts(144) = 4.764600: extPts(145) = 1.015155: extPts(146) = 0#
    extPts(147) = 4.911025: extPts(148) = 0.992530: extPts(149) = 0#
    extPts(150) = 5.054049: extPts(151) = 0.968517: extPts(152) = 0#
    extPts(153) = 5.193471: extPts(154) = 0.943150: extPts(155) = 0#
    extPts(156) = 5.329097: extPts(157) = 0.916463: extPts(158) = 0#
    extPts(159) = 5.460736: extPts(160) = 0.888494: extPts(161) = 0#
    extPts(162) = 5.588206: extPts(163) = 0.859283: extPts(164) = 0#
    extPts(165) = 5.711327: extPts(166) = 0.828871: extPts(167) = 0#
    extPts(168) = 5.829927: extPts(169) = 0.797298: extPts(170) = 0#
    extPts(171) = 5.943840: extPts(172) = 0.764611: extPts(173) = 0#
    extPts(174) = 6.052908: extPts(175) = 0.730855: extPts(176) = 0#
    extPts(177) = 6.156977: extPts(178) = 0.696076: extPts(179) = 0#
    extPts(180) = 6.255903: extPts(181) = 0.660324: extPts(182) = 0#
    extPts(183) = 6.349546: extPts(184) = 0.623648: extPts(185) = 0#
    extPts(186) = 6.437775: extPts(187) = 0.586100: extPts(188) = 0#
    extPts(189) = 6.520468: extPts(190) = 0.547732: extPts(191) = 0#
    extPts(192) = 6.597509: extPts(193) = 0.508599: extPts(194) = 0#
    extPts(195) = 6.668789: extPts(196) = 0.468753: extPts(197) = 0#
    extPts(198) = 6.734210: extPts(199) = 0.428253: extPts(200) = 0#
    extPts(201) = 6.793679: extPts(202) = 0.387153: extPts(203) = 0#
    extPts(204) = 6.847114: extPts(205) = 0.345512: extPts(206) = 0#
    extPts(207) = 6.894440: extPts(208) = 0.303388: extPts(209) = 0#
    extPts(210) = 6.935590: extPts(211) = 0.260839: extPts(212) = 0#
    extPts(213) = 6.970508: extPts(214) = 0.217926: extPts(215) = 0#
    extPts(216) = 6.999143: extPts(217) = 0.174707: extPts(218) = 0#
    extPts(219) = 7.021457: extPts(220) = 0.131245: extPts(221) = 0#
    extPts(222) = 7.037418: extPts(223) = 0.087599: extPts(224) = 0#
    extPts(225) = 7.047003: extPts(226) = 0.043830: extPts(227) = 0#
    extPts(228) = 7.050200: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 7.047200: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 7.044005: intPts(4) = 0.043718: intPts(5) = 0#
    intPts(6) = 7.034426: intPts(7) = 0.087374: intPts(8) = 0#
    intPts(9) = 7.018476: intPts(10) = 0.130909: intPts(11) = 0#
    intPts(12) = 6.996177: intPts(13) = 0.174260: intPts(14) = 0#
    intPts(15) = 6.967560: intPts(16) = 0.217368: intPts(17) = 0#
    intPts(18) = 6.932666: intPts(19) = 0.260171: intPts(20) = 0#
    intPts(21) = 6.891542: intPts(22) = 0.302611: intPts(23) = 0#
    intPts(24) = 6.844248: intPts(25) = 0.344628: intPts(26) = 0#
    intPts(27) = 6.790848: intPts(28) = 0.386162: intPts(29) = 0#
    intPts(30) = 6.731417: intPts(31) = 0.427157: intPts(32) = 0#
    intPts(33) = 6.666040: intPts(34) = 0.467554: intPts(35) = 0#
    intPts(36) = 6.594806: intPts(37) = 0.507297: intPts(38) = 0#
    intPts(39) = 6.517816: intPts(40) = 0.546330: intPts(41) = 0#
    intPts(42) = 6.435177: intPts(43) = 0.584600: intPts(44) = 0#
    intPts(45) = 6.347005: intPts(46) = 0.622052: intPts(47) = 0#
    intPts(48) = 6.253424: intPts(49) = 0.658634: intPts(50) = 0#
    intPts(51) = 6.154564: intPts(52) = 0.694295: intPts(53) = 0#
    intPts(54) = 6.050563: intPts(55) = 0.728984: intPts(56) = 0#
    intPts(57) = 5.941566: intPts(58) = 0.762654: intPts(59) = 0#
    intPts(60) = 5.827728: intPts(61) = 0.795258: intPts(62) = 0#
    intPts(63) = 5.709205: intPts(64) = 0.826749: intPts(65) = 0#
    intPts(66) = 5.586165: intPts(67) = 0.857084: intPts(68) = 0#
    intPts(69) = 5.458779: intPts(70) = 0.886221: intPts(71) = 0#
    intPts(72) = 5.327226: intPts(73) = 0.914117: intPts(74) = 0#
    intPts(75) = 5.191689: intPts(76) = 0.940736: intPts(77) = 0#
    intPts(78) = 5.052359: intPts(79) = 0.966038: intPts(80) = 0#
    intPts(81) = 4.909429: intPts(82) = 0.989990: intPts(83) = 0#
    intPts(84) = 4.763100: intPts(85) = 1.012557: intPts(86) = 0#
    intPts(87) = 4.613577: intPts(88) = 1.033708: intPts(89) = 0#
    intPts(90) = 4.461068: intPts(91) = 1.053413: intPts(92) = 0#
    intPts(93) = 4.305787: intPts(94) = 1.071645: intPts(95) = 0#
    intPts(96) = 4.147951: intPts(97) = 1.088378: intPts(98) = 0#
    intPts(99) = 3.987781: intPts(100) = 1.103588: intPts(101) = 0#
    intPts(102) = 3.825501: intPts(103) = 1.117256: intPts(104) = 0#
    intPts(105) = 3.661337: intPts(106) = 1.129360: intPts(107) = 0#
    intPts(108) = 3.495520: intPts(109) = 1.139886: intPts(110) = 0#
    intPts(111) = 3.328281: intPts(112) = 1.148817: intPts(113) = 0#
    intPts(114) = 3.159855: intPts(115) = 1.156141: intPts(116) = 0#
    intPts(117) = 2.990476: intPts(118) = 1.161848: intPts(119) = 0#
    intPts(120) = 2.820382: intPts(121) = 1.165931: intPts(122) = 0#
    intPts(123) = 2.649810: intPts(124) = 1.168382: intPts(125) = 0#
    intPts(126) = 2.479000: intPts(127) = 1.169200: intPts(128) = 0#
    intPts(129) = 2.366118: intPts(130) = 1.167952: intPts(131) = 0#
    intPts(132) = 2.253478: intPts(133) = 1.164212: intPts(134) = 0#
    intPts(135) = 2.141318: intPts(136) = 1.157988: intPts(137) = 0#
    intPts(138) = 2.029879: intPts(139) = 1.149292: intPts(140) = 0#
    intPts(141) = 1.919399: intPts(142) = 1.138144: intPts(143) = 0#
    intPts(144) = 1.810113: intPts(145) = 1.124567: intPts(146) = 0#
    intPts(147) = 1.702254: intPts(148) = 1.108589: intPts(149) = 0#
    intPts(150) = 1.596053: intPts(151) = 1.090247: intPts(152) = 0#
    intPts(153) = 1.491736: intPts(154) = 1.069577: intPts(155) = 0#
    intPts(156) = 1.389526: intPts(157) = 1.046625: intPts(158) = 0#
    intPts(159) = 1.289641: intPts(160) = 1.021439: intPts(161) = 0#
    intPts(162) = 1.192295: intPts(163) = 0.994074: intPts(164) = 0#
    intPts(165) = 1.097694: intPts(166) = 0.964587: intPts(167) = 0#
    intPts(168) = 1.006040: intPts(169) = 0.933042: intPts(170) = 0#
    intPts(171) = 0.917531: intPts(172) = 0.899505: intPts(173) = 0#
    intPts(174) = 0.832353: intPts(175) = 0.864049: intPts(176) = 0#
    intPts(177) = 0.750690: intPts(178) = 0.826749: intPts(179) = 0#
    intPts(180) = 0.672714: intPts(181) = 0.787685: intPts(182) = 0#
    intPts(183) = 0.598594: intPts(184) = 0.746940: intPts(185) = 0#
    intPts(186) = 0.528486: intPts(187) = 0.704600: intPts(188) = 0#
    intPts(189) = 0.462541: intPts(190) = 0.660757: intPts(191) = 0#
    intPts(192) = 0.400899: intPts(193) = 0.615504: intPts(194) = 0#
    intPts(195) = 0.343692: intPts(196) = 0.568938: intPts(197) = 0#
    intPts(198) = 0.291042: intPts(199) = 0.521157: intPts(200) = 0#
    intPts(201) = 0.243061: intPts(202) = 0.472264: intPts(203) = 0#
    intPts(204) = 0.199851: intPts(205) = 0.422364: intPts(206) = 0#
    intPts(207) = 0.161506: intPts(208) = 0.371562: intPts(209) = 0#
    intPts(210) = 0.128106: intPts(211) = 0.319967: intPts(212) = 0#
    intPts(213) = 0.099723: intPts(214) = 0.267689: intPts(215) = 0#
    intPts(216) = 0.076417: intPts(217) = 0.214840: intPts(218) = 0#
    intPts(219) = 0.058239: intPts(220) = 0.161532: intPts(221) = 0#
    intPts(222) = 0.045227: intPts(223) = 0.107880: intPts(224) = 0#
    intPts(225) = 0.037408: intPts(226) = 0.053998: intPts(227) = 0#
    intPts(228) = 0.034800: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 7.050200, 0#, 0#, 7.047200, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.034800, 0#, 0#, 0.031800, 0#, 0#

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

    ' --- Capa_Aislante_2_360 (offset = 63.6 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.063600: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.066177: extPts(4) = 0.052668: extPts(5) = 0#
    extPts(6) = 0.073904: extPts(7) = 0.105223: extPts(8) = 0#
    extPts(9) = 0.086763: extPts(10) = 0.157554: extPts(11) = 0#
    extPts(12) = 0.104727: extPts(13) = 0.209548: extPts(14) = 0#
    extPts(15) = 0.127758: extPts(16) = 0.261095: extPts(17) = 0#
    extPts(18) = 0.155806: extPts(19) = 0.312085: extPts(20) = 0#
    extPts(21) = 0.188813: extPts(22) = 0.362409: extPts(23) = 0#
    extPts(24) = 0.226707: extPts(25) = 0.411960: extPts(26) = 0#
    extPts(27) = 0.269407: extPts(28) = 0.460632: extPts(29) = 0#
    extPts(30) = 0.316823: extPts(31) = 0.508320: extPts(32) = 0#
    extPts(33) = 0.368852: extPts(34) = 0.554924: extPts(35) = 0#
    extPts(36) = 0.425386: extPts(37) = 0.600343: extPts(38) = 0#
    extPts(39) = 0.486301: extPts(40) = 0.644482: extPts(41) = 0#
    extPts(42) = 0.551469: extPts(43) = 0.687245: extPts(44) = 0#
    extPts(45) = 0.620751: extPts(46) = 0.728541: extPts(47) = 0#
    extPts(48) = 0.693998: extPts(49) = 0.768283: extPts(50) = 0#
    extPts(51) = 0.771054: extPts(52) = 0.806385: extPts(53) = 0#
    extPts(54) = 0.851756: extPts(55) = 0.842766: extPts(56) = 0#
    extPts(57) = 0.935929: extPts(58) = 0.877348: extPts(59) = 0#
    extPts(60) = 1.023396: extPts(61) = 0.910059: extPts(62) = 0#
    extPts(63) = 1.113970: extPts(64) = 0.940827: extPts(65) = 0#
    extPts(66) = 1.207456: extPts(67) = 0.969588: extPts(68) = 0#
    extPts(69) = 1.303656: extPts(70) = 0.996279: extPts(71) = 0#
    extPts(72) = 1.402364: extPts(73) = 1.020844: extPts(74) = 0#
    extPts(75) = 1.503369: extPts(76) = 1.043231: extPts(77) = 0#
    extPts(78) = 1.606457: extPts(79) = 1.063391: extPts(80) = 0#
    extPts(81) = 1.711407: extPts(82) = 1.081282: extPts(83) = 0#
    extPts(84) = 1.817994: extPts(85) = 1.096866: extPts(86) = 0#
    extPts(87) = 1.925993: extPts(88) = 1.110109: extPts(89) = 0#
    extPts(90) = 2.035171: extPts(91) = 1.120983: extPts(92) = 0#
    extPts(93) = 2.145297: extPts(94) = 1.129464: extPts(95) = 0#
    extPts(96) = 2.256135: extPts(97) = 1.135535: extPts(98) = 0#
    extPts(99) = 2.367448: extPts(100) = 1.139183: extPts(101) = 0#
    extPts(102) = 2.479000: extPts(103) = 1.140400: extPts(104) = 0#
    extPts(105) = 2.648734: extPts(106) = 1.139603: extPts(107) = 0#
    extPts(108) = 2.818230: extPts(109) = 1.137211: extPts(110) = 0#
    extPts(111) = 2.987252: extPts(112) = 1.133229: extPts(113) = 0#
    extPts(114) = 3.155562: extPts(115) = 1.127663: extPts(116) = 0#
    extPts(117) = 3.322927: extPts(118) = 1.120519: extPts(119) = 0#
    extPts(120) = 3.489112: extPts(121) = 1.111808: extPts(122) = 0#
    extPts(123) = 3.653883: extPts(124) = 1.101542: extPts(125) = 0#
    extPts(126) = 3.817012: extPts(127) = 1.089735: extPts(128) = 0#
    extPts(129) = 3.978269: extPts(130) = 1.076405: extPts(131) = 0#
    extPts(132) = 4.137429: extPts(133) = 1.061568: extPts(134) = 0#
    extPts(135) = 4.294270: extPts(136) = 1.045248: extPts(137) = 0#
    extPts(138) = 4.448572: extPts(139) = 1.027465: extPts(140) = 0#
    extPts(141) = 4.600119: extPts(142) = 1.008245: extPts(143) = 0#
    extPts(144) = 4.748700: extPts(145) = 0.987615: extPts(146) = 0#
    extPts(147) = 4.894106: extPts(148) = 0.965604: extPts(149) = 0#
    extPts(150) = 5.036135: extPts(151) = 0.942243: extPts(152) = 0#
    extPts(153) = 5.174587: extPts(154) = 0.917563: extPts(155) = 0#
    extPts(156) = 5.309270: extPts(157) = 0.891601: extPts(158) = 0#
    extPts(159) = 5.439993: extPts(160) = 0.864391: extPts(161) = 0#
    extPts(162) = 5.566576: extPts(163) = 0.835972: extPts(164) = 0#
    extPts(165) = 5.688841: extPts(166) = 0.806385: extPts(167) = 0#
    extPts(168) = 5.806616: extPts(169) = 0.775669: extPts(170) = 0#
    extPts(171) = 5.919737: extPts(172) = 0.743869: extPts(173) = 0#
    extPts(174) = 6.028046: extPts(175) = 0.711028: extPts(176) = 0#
    extPts(177) = 6.131391: extPts(178) = 0.677193: extPts(179) = 0#
    extPts(180) = 6.229628: extPts(181) = 0.642410: extPts(182) = 0#
    extPts(183) = 6.322620: extPts(184) = 0.606729: extPts(185) = 0#
    extPts(186) = 6.410236: extPts(187) = 0.570200: extPts(188) = 0#
    extPts(189) = 6.492353: extPts(190) = 0.532873: extPts(191) = 0#
    extPts(192) = 6.568858: extPts(193) = 0.494801: extPts(194) = 0#
    extPts(195) = 6.639643: extPts(196) = 0.456037: extPts(197) = 0#
    extPts(198) = 6.704608: extPts(199) = 0.416635: extPts(200) = 0#
    extPts(201) = 6.763664: extPts(202) = 0.376650: extPts(203) = 0#
    extPts(204) = 6.816727: extPts(205) = 0.336139: extPts(206) = 0#
    extPts(207) = 6.863724: extPts(208) = 0.295157: extPts(209) = 0#
    extPts(210) = 6.904588: extPts(211) = 0.253763: extPts(212) = 0#
    extPts(213) = 6.939262: extPts(214) = 0.212014: extPts(215) = 0#
    extPts(216) = 6.967699: extPts(217) = 0.169968: extPts(218) = 0#
    extPts(219) = 6.989857: extPts(220) = 0.127684: extPts(221) = 0#
    extPts(222) = 7.005707: extPts(223) = 0.085222: extPts(224) = 0#
    extPts(225) = 7.015226: extPts(226) = 0.042641: extPts(227) = 0#
    extPts(228) = 7.018400: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 7.015400: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 7.012228: intPts(4) = 0.042529: intPts(5) = 0#
    intPts(6) = 7.002715: intPts(7) = 0.084998: intPts(8) = 0#
    intPts(9) = 6.986876: intPts(10) = 0.127348: intPts(11) = 0#
    intPts(12) = 6.964732: intPts(13) = 0.169521: intPts(14) = 0#
    intPts(15) = 6.936315: intPts(16) = 0.211456: intPts(17) = 0#
    intPts(18) = 6.901663: intPts(19) = 0.253095: intPts(20) = 0#
    intPts(21) = 6.860826: intPts(22) = 0.294381: intPts(23) = 0#
    intPts(24) = 6.813860: intPts(25) = 0.335255: intPts(26) = 0#
    intPts(27) = 6.760832: intPts(28) = 0.375659: intPts(29) = 0#
    intPts(30) = 6.701816: intPts(31) = 0.415539: intPts(32) = 0#
    intPts(33) = 6.636893: intPts(34) = 0.454837: intPts(35) = 0#
    intPts(36) = 6.566155: intPts(37) = 0.493499: intPts(38) = 0#
    intPts(39) = 6.489701: intPts(40) = 0.531471: intPts(41) = 0#
    intPts(42) = 6.407638: intPts(43) = 0.568700: intPts(44) = 0#
    intPts(45) = 6.320080: intPts(46) = 0.605133: intPts(47) = 0#
    intPts(48) = 6.227150: intPts(49) = 0.640720: intPts(50) = 0#
    intPts(51) = 6.128977: intPts(52) = 0.675411: intPts(53) = 0#
    intPts(54) = 6.025700: intPts(55) = 0.709157: intPts(56) = 0#
    intPts(57) = 5.917463: intPts(58) = 0.741912: intPts(59) = 0#
    intPts(60) = 5.804417: intPts(61) = 0.773628: intPts(62) = 0#
    intPts(63) = 5.686719: intPts(64) = 0.804263: intPts(65) = 0#
    intPts(66) = 5.564536: intPts(67) = 0.833773: intPts(68) = 0#
    intPts(69) = 5.438037: intPts(70) = 0.862117: intPts(71) = 0#
    intPts(72) = 5.307399: intPts(73) = 0.889255: intPts(74) = 0#
    intPts(75) = 5.172806: intPts(76) = 0.915150: intPts(77) = 0#
    intPts(78) = 5.034445: intPts(79) = 0.939764: intPts(80) = 0#
    intPts(81) = 4.892510: intPts(82) = 0.963064: intPts(83) = 0#
    intPts(84) = 4.747200: intPts(85) = 0.985017: intPts(86) = 0#
    intPts(87) = 4.598717: intPts(88) = 1.005593: intPts(89) = 0#
    intPts(90) = 4.447270: intPts(91) = 1.024762: intPts(92) = 0#
    intPts(93) = 4.293070: intPts(94) = 1.042498: intPts(95) = 0#
    intPts(96) = 4.136333: intPts(97) = 1.058776: intPts(98) = 0#
    intPts(99) = 3.977278: intPts(100) = 1.073573: intPts(101) = 0#
    intPts(102) = 3.816127: intPts(103) = 1.086869: intPts(104) = 0#
    intPts(105) = 3.653107: intPts(106) = 1.098644: intPts(107) = 0#
    intPts(108) = 3.488444: intPts(109) = 1.108883: intPts(110) = 0#
    intPts(111) = 3.322369: intPts(112) = 1.117571: intPts(113) = 0#
    intPts(114) = 3.155115: intPts(115) = 1.124696: intPts(116) = 0#
    intPts(117) = 2.986916: intPts(118) = 1.130248: intPts(119) = 0#
    intPts(120) = 2.818006: intPts(121) = 1.134220: intPts(122) = 0#
    intPts(123) = 2.648621: intPts(124) = 1.136605: intPts(125) = 0#
    intPts(126) = 2.479000: intPts(127) = 1.137400: intPts(128) = 0#
    intPts(129) = 2.367587: intPts(130) = 1.136186: intPts(131) = 0#
    intPts(132) = 2.256412: intPts(133) = 1.132548: intPts(134) = 0#
    intPts(135) = 2.145712: intPts(136) = 1.126493: intPts(137) = 0#
    intPts(138) = 2.035723: intPts(139) = 1.118034: intPts(140) = 0#
    intPts(141) = 1.926680: intPts(142) = 1.107188: intPts(143) = 0#
    intPts(144) = 1.818815: intPts(145) = 1.093980: intPts(146) = 0#
    intPts(147) = 1.712360: intPts(148) = 1.078438: intPts(149) = 0#
    intPts(150) = 1.607541: intPts(151) = 1.060594: intPts(152) = 0#
    intPts(153) = 1.504581: intPts(154) = 1.040487: intPts(155) = 0#
    intPts(156) = 1.403701: intPts(157) = 1.018159: intPts(158) = 0#
    intPts(159) = 1.305115: intPts(160) = 0.993658: intPts(161) = 0#
    intPts(162) = 1.209035: intPts(163) = 0.967037: intPts(164) = 0#
    intPts(165) = 1.115665: intPts(166) = 0.938352: intPts(167) = 0#
    intPts(168) = 1.025204: intPts(169) = 0.907665: intPts(170) = 0#
    intPts(171) = 0.937846: intPts(172) = 0.875040: intPts(173) = 0#
    intPts(174) = 0.853777: intPts(175) = 0.840549: intPts(176) = 0#
    intPts(177) = 0.773176: intPts(178) = 0.804263: intPts(179) = 0#
    intPts(180) = 0.696215: intPts(181) = 0.766261: intPts(182) = 0#
    intPts(183) = 0.623059: intPts(184) = 0.726624: intPts(185) = 0#
    intPts(186) = 0.553863: intPts(187) = 0.685437: intPts(188) = 0#
    intPts(189) = 0.488776: intPts(190) = 0.642786: intPts(191) = 0#
    intPts(192) = 0.427936: intPts(193) = 0.598764: intPts(194) = 0#
    intPts(195) = 0.371473: intPts(196) = 0.553464: intPts(197) = 0#
    intPts(198) = 0.319508: intPts(199) = 0.506983: intPts(200) = 0#
    intPts(201) = 0.272151: intPts(202) = 0.459420: intPts(203) = 0#
    intPts(204) = 0.229504: intPts(205) = 0.410876: intPts(206) = 0#
    intPts(207) = 0.191657: intPts(208) = 0.361456: intPts(209) = 0#
    intPts(210) = 0.158692: intPts(211) = 0.311264: intPts(212) = 0#
    intPts(213) = 0.130678: intPts(214) = 0.260408: intPts(215) = 0#
    intPts(216) = 0.107676: intPts(217) = 0.208997: intPts(218) = 0#
    intPts(219) = 0.089734: intPts(220) = 0.157139: intPts(221) = 0#
    intPts(222) = 0.076891: intPts(223) = 0.104946: intPts(224) = 0#
    intPts(225) = 0.069174: intPts(226) = 0.052529: intPts(227) = 0#
    intPts(228) = 0.066600: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 7.018400, 0#, 0#, 7.015400, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.066600, 0#, 0#, 0.063600, 0#, 0#

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
    If Not swFeat Is Nothing Then swFeat.Name = "Capa_Aislante_2_360"

    ' --- Capa_Aislante_3_Sup (offset = 95.4 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.095400: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.097943: extPts(4) = 0.051199: extPts(5) = 0#
    extPts(6) = 0.105568: extPts(7) = 0.102289: extPts(8) = 0#
    extPts(9) = 0.118258: extPts(10) = 0.153160: extPts(11) = 0#
    extPts(12) = 0.135985: extPts(13) = 0.203705: extPts(14) = 0#
    extPts(15) = 0.158713: extPts(16) = 0.253815: extPts(17) = 0#
    extPts(18) = 0.186392: extPts(19) = 0.303383: extPts(20) = 0#
    extPts(21) = 0.218964: extPts(22) = 0.352304: extPts(23) = 0#
    extPts(24) = 0.256359: extPts(25) = 0.400473: extPts(26) = 0#
    extPts(27) = 0.298497: extPts(28) = 0.447787: extPts(29) = 0#
    extPts(30) = 0.345289: extPts(31) = 0.494146: extPts(32) = 0#
    extPts(33) = 0.396634: extPts(34) = 0.539450: extPts(35) = 0#
    extPts(36) = 0.452422: extPts(37) = 0.583603: extPts(38) = 0#
    extPts(39) = 0.512536: extPts(40) = 0.626510: extPts(41) = 0#
    extPts(42) = 0.576846: extPts(43) = 0.668081: extPts(44) = 0#
    extPts(45) = 0.645216: extPts(46) = 0.708226: extPts(47) = 0#
    extPts(48) = 0.717498: extPts(49) = 0.746859: extPts(50) = 0#
    extPts(51) = 0.793540: extPts(52) = 0.783899: extPts(53) = 0#
    extPts(54) = 0.873179: extPts(55) = 0.819265: extPts(56) = 0#
    extPts(57) = 0.956245: extPts(58) = 0.852884: extPts(59) = 0#
    extPts(60) = 1.042560: extPts(61) = 0.884682: extPts(62) = 0#
    extPts(63) = 1.131941: extPts(64) = 0.914592: extPts(65) = 0#
    extPts(66) = 1.224196: extPts(67) = 0.942551: extPts(68) = 0#
    extPts(69) = 1.319130: extPts(70) = 0.968498: extPts(71) = 0#
    extPts(72) = 1.416538: extPts(73) = 0.992378: extPts(74) = 0#
    extPts(75) = 1.516214: extPts(76) = 1.014140: extPts(77) = 0#
    extPts(78) = 1.617944: extPts(79) = 1.033739: extPts(80) = 0#
    extPts(81) = 1.721512: extPts(82) = 1.051131: extPts(83) = 0#
    extPts(84) = 1.826697: extPts(85) = 1.066280: extPts(86) = 0#
    extPts(87) = 1.933273: extPts(88) = 1.079153: extPts(89) = 0#
    extPts(90) = 2.041015: extPts(91) = 1.089724: extPts(92) = 0#
    extPts(93) = 2.149691: extPts(94) = 1.097969: extPts(95) = 0#
    extPts(96) = 2.259069: extPts(97) = 1.103871: extPts(98) = 0#
    extPts(99) = 2.368917: extPts(100) = 1.107417: extPts(101) = 0#
    extPts(102) = 2.479000: extPts(103) = 1.108600: extPts(104) = 0#
    extPts(105) = 2.647545: extPts(106) = 1.107825: extPts(107) = 0#
    extPts(108) = 2.815853: extPts(109) = 1.105500: extPts(110) = 0#
    extPts(111) = 2.983691: extPts(112) = 1.101629: extPts(113) = 0#
    extPts(114) = 3.150823: extPts(115) = 1.096218: extPts(116) = 0#
    extPts(117) = 3.317015: extPts(118) = 1.089273: extPts(119) = 0#
    extPts(120) = 3.482035: extPts(121) = 1.080805: extPts(122) = 0#
    extPts(123) = 3.645653: extPts(124) = 1.070825: extPts(125) = 0#
    extPts(126) = 3.807638: extPts(127) = 1.059348: extPts(128) = 0#
    extPts(129) = 3.967766: extPts(130) = 1.046389: extPts(131) = 0#
    extPts(132) = 4.125811: extPts(133) = 1.031967: extPts(134) = 0#
    extPts(135) = 4.281553: extPts(136) = 1.016101: extPts(137) = 0#
    extPts(138) = 4.434774: extPts(139) = 0.998814: extPts(140) = 0#
    extPts(141) = 4.585260: extPts(142) = 0.980130: extPts(143) = 0#
    extPts(144) = 4.732800: extPts(145) = 0.960076: extPts(146) = 0#
    extPts(147) = 4.877188: extPts(148) = 0.938678: extPts(149) = 0#
    extPts(150) = 5.018221: extPts(151) = 0.915968: extPts(152) = 0#
    extPts(153) = 5.155704: extPts(154) = 0.891977: extPts(155) = 0#
    extPts(156) = 5.289443: extPts(157) = 0.866738: extPts(158) = 0#
    extPts(159) = 5.419251: extPts(160) = 0.840287: extPts(161) = 0#
    extPts(162) = 5.544947: extPts(163) = 0.812661: extPts(164) = 0#
    extPts(165) = 5.666355: extPts(166) = 0.783899: extPts(167) = 0#
    extPts(168) = 5.783305: extPts(169) = 0.754039: extPts(170) = 0#
    extPts(171) = 5.895633: extPts(172) = 0.723126: extPts(173) = 0#
    extPts(174) = 6.003184: extPts(175) = 0.691201: extPts(176) = 0#
    extPts(177) = 6.105805: extPts(178) = 0.658309: extPts(179) = 0#
    extPts(180) = 6.203354: extPts(181) = 0.624497: extPts(182) = 0#
    extPts(183) = 6.295694: extPts(184) = 0.589811: extPts(185) = 0#
    extPts(186) = 6.382696: extPts(187) = 0.554300: extPts(188) = 0#
    extPts(189) = 6.464239: extPts(190) = 0.518014: extPts(191) = 0#
    extPts(192) = 6.540207: extPts(193) = 0.481004: extPts(194) = 0#
    extPts(195) = 6.610496: extPts(196) = 0.443320: extPts(197) = 0#
    extPts(198) = 6.675007: extPts(199) = 0.405017: extPts(200) = 0#
    extPts(201) = 6.733648: extPts(202) = 0.366147: extPts(203) = 0#
    extPts(204) = 6.786340: extPts(205) = 0.326766: extPts(206) = 0#
    extPts(207) = 6.833007: extPts(208) = 0.286927: extPts(209) = 0#
    extPts(210) = 6.873585: extPts(211) = 0.246687: extPts(212) = 0#
    extPts(213) = 6.908017: extPts(214) = 0.206102: extPts(215) = 0#
    extPts(216) = 6.936254: extPts(217) = 0.165228: extPts(218) = 0#
    extPts(219) = 6.958257: extPts(220) = 0.124124: extPts(221) = 0#
    extPts(222) = 6.973996: extPts(223) = 0.082846: extPts(224) = 0#
    extPts(225) = 6.983448: extPts(226) = 0.041452: extPts(227) = 0#
    extPts(228) = 6.986600: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 6.983600: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 6.980450: intPts(4) = 0.041340: intPts(5) = 0#
    intPts(6) = 6.971004: intPts(7) = 0.082622: intPts(8) = 0#
    intPts(9) = 6.955276: intPts(10) = 0.123788: intPts(11) = 0#
    intPts(12) = 6.933287: intPts(13) = 0.164781: intPts(14) = 0#
    intPts(15) = 6.905069: intPts(16) = 0.205544: intPts(17) = 0#
    intPts(18) = 6.870660: intPts(19) = 0.246019: intPts(20) = 0#
    intPts(21) = 6.830109: intPts(22) = 0.286150: intPts(23) = 0#
    intPts(24) = 6.783473: intPts(25) = 0.325881: intPts(26) = 0#
    intPts(27) = 6.730817: intPts(28) = 0.365157: intPts(29) = 0#
    intPts(30) = 6.672214: intPts(31) = 0.403921: intPts(32) = 0#
    intPts(33) = 6.607746: intPts(34) = 0.442121: intPts(35) = 0#
    intPts(36) = 6.537504: intPts(37) = 0.479702: intPts(38) = 0#
    intPts(39) = 6.461586: intPts(40) = 0.516612: intPts(41) = 0#
    intPts(42) = 6.380098: intPts(43) = 0.552800: intPts(44) = 0#
    intPts(45) = 6.293154: intPts(46) = 0.588215: intPts(47) = 0#
    intPts(48) = 6.200875: intPts(49) = 0.622807: intPts(50) = 0#
    intPts(51) = 6.103391: intPts(52) = 0.656528: intPts(53) = 0#
    intPts(54) = 6.000838: intPts(55) = 0.689330: intPts(56) = 0#
    intPts(57) = 5.893359: intPts(58) = 0.721169: intPts(59) = 0#
    intPts(60) = 5.781105: intPts(61) = 0.751999: intPts(62) = 0#
    intPts(63) = 5.664233: intPts(64) = 0.781777: intPts(65) = 0#
    intPts(66) = 5.542906: intPts(67) = 0.810462: intPts(68) = 0#
    intPts(69) = 5.417294: intPts(70) = 0.838014: intPts(71) = 0#
    intPts(72) = 5.287572: intPts(73) = 0.864393: intPts(74) = 0#
    intPts(75) = 5.153922: intPts(76) = 0.889563: intPts(77) = 0#
    intPts(78) = 5.016532: intPts(79) = 0.913490: intPts(80) = 0#
    intPts(81) = 4.875592: intPts(82) = 0.936138: intPts(83) = 0#
    intPts(84) = 4.731300: intPts(85) = 0.957478: intPts(86) = 0#
    intPts(87) = 4.583858: intPts(88) = 0.977478: intPts(89) = 0#
    intPts(90) = 4.433473: intPts(91) = 0.996111: intPts(92) = 0#
    intPts(93) = 4.280354: intPts(94) = 1.013351: intPts(95) = 0#
    intPts(96) = 4.124715: intPts(97) = 1.029174: intPts(98) = 0#
    intPts(99) = 3.966775: intPts(100) = 1.043557: intPts(101) = 0#
    intPts(102) = 3.806754: intPts(103) = 1.056481: intPts(104) = 0#
    intPts(105) = 3.644876: intPts(106) = 1.067928: intPts(107) = 0#
    intPts(108) = 3.481368: intPts(109) = 1.077880: intPts(110) = 0#
    intPts(111) = 3.316457: intPts(112) = 1.086325: intPts(113) = 0#
    intPts(114) = 3.150376: intPts(115) = 1.093251: intPts(116) = 0#
    intPts(117) = 2.983355: intPts(118) = 1.098648: intPts(119) = 0#
    intPts(120) = 2.815629: intPts(121) = 1.102509: intPts(122) = 0#
    intPts(123) = 2.647432: intPts(124) = 1.104827: intPts(125) = 0#
    intPts(126) = 2.479000: intPts(127) = 1.105600: intPts(128) = 0#
    intPts(129) = 2.369056: intPts(130) = 1.104420: intPts(131) = 0#
    intPts(132) = 2.259346: intPts(133) = 1.100884: intPts(134) = 0#
    intPts(135) = 2.150105: intPts(136) = 1.094998: intPts(137) = 0#
    intPts(138) = 2.041566: intPts(139) = 1.086775: intPts(140) = 0#
    intPts(141) = 1.933960: intPts(142) = 1.076233: intPts(143) = 0#
    intPts(144) = 1.827518: intPts(145) = 1.063394: intPts(146) = 0#
    intPts(147) = 1.722466: intPts(148) = 1.048286: intPts(149) = 0#
    intPts(150) = 1.619028: intPts(151) = 1.030941: intPts(152) = 0#
    intPts(153) = 1.517426: intPts(154) = 1.011396: intPts(155) = 0#
    intPts(156) = 1.417875: intPts(157) = 0.989693: intPts(158) = 0#
    intPts(159) = 1.320589: intPts(160) = 0.965877: intPts(161) = 0#
    intPts(162) = 1.225776: intPts(163) = 0.940000: intPts(164) = 0#
    intPts(165) = 1.133636: intPts(166) = 0.912117: intPts(167) = 0#
    intPts(168) = 1.044368: intPts(169) = 0.882288: intPts(170) = 0#
    intPts(171) = 0.958161: intPts(172) = 0.850576: intPts(173) = 0#
    intPts(174) = 0.875200: intPts(175) = 0.817048: intPts(176) = 0#
    intPts(177) = 0.795662: intPts(178) = 0.781777: intPts(179) = 0#
    intPts(180) = 0.719715: intPts(181) = 0.744838: intPts(182) = 0#
    intPts(183) = 0.647524: intPts(184) = 0.706309: intPts(185) = 0#
    intPts(186) = 0.579240: intPts(187) = 0.666273: intPts(188) = 0#
    intPts(189) = 0.515011: intPts(190) = 0.624815: intPts(191) = 0#
    intPts(192) = 0.454973: intPts(193) = 0.582023: intPts(194) = 0#
    intPts(195) = 0.399255: intPts(196) = 0.537990: intPts(197) = 0#
    intPts(198) = 0.347974: intPts(199) = 0.492808: intPts(200) = 0#
    intPts(201) = 0.301242: intPts(202) = 0.446575: intPts(203) = 0#
    intPts(204) = 0.259157: intPts(205) = 0.399389: intPts(206) = 0#
    intPts(207) = 0.221809: intPts(208) = 0.351350: intPts(209) = 0#
    intPts(210) = 0.189278: intPts(211) = 0.302562: intPts(212) = 0#
    intPts(213) = 0.161633: intPts(214) = 0.253128: intPts(215) = 0#
    intPts(216) = 0.138934: intPts(217) = 0.203153: intPts(218) = 0#
    intPts(219) = 0.121229: intPts(220) = 0.152746: intPts(221) = 0#
    intPts(222) = 0.108555: intPts(223) = 0.102012: intPts(224) = 0#
    intPts(225) = 0.100940: intPts(226) = 0.051060: intPts(227) = 0#
    intPts(228) = 0.098400: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 6.986600, 0#, 0#, 6.983600, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.098400, 0#, 0#, 0.095400, 0#, 0#

    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        False, True, False, False, False, False, _
        0, 0, 1.570796326795, 1.570796326795, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Capa_Aislante_3_Sup"

    ' --- Capa_Aislante_4_Sup (offset = 127.2 mm, espesor visual = 3.0 mm) ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True

    ReDim extPts(0 To 230) As Double
    ReDim intPts(0 To 230) As Double
    extPts(0) = 0.127200: extPts(1) = 0.000000: extPts(2) = 0#
    extPts(3) = 0.129709: extPts(4) = 0.049730: extPts(5) = 0#
    extPts(6) = 0.137232: extPts(7) = 0.099355: extPts(8) = 0#
    extPts(9) = 0.149753: extPts(10) = 0.148767: extPts(11) = 0#
    extPts(12) = 0.167244: extPts(13) = 0.197861: extPts(14) = 0#
    extPts(15) = 0.189668: extPts(16) = 0.246534: extPts(17) = 0#
    extPts(18) = 0.216978: extPts(19) = 0.294680: extPts(20) = 0#
    extPts(21) = 0.249116: extPts(22) = 0.342198: extPts(23) = 0#
    extPts(24) = 0.286012: extPts(25) = 0.388985: extPts(26) = 0#
    extPts(27) = 0.327588: extPts(28) = 0.434942: extPts(29) = 0#
    extPts(30) = 0.373755: extPts(31) = 0.479971: extPts(32) = 0#
    extPts(33) = 0.424415: extPts(34) = 0.523976: extPts(35) = 0#
    extPts(36) = 0.479459: extPts(37) = 0.566862: extPts(38) = 0#
    extPts(39) = 0.538771: extPts(40) = 0.608539: extPts(41) = 0#
    extPts(42) = 0.602223: extPts(43) = 0.648917: extPts(44) = 0#
    extPts(45) = 0.669680: extPts(46) = 0.687910: extPts(47) = 0#
    extPts(48) = 0.740999: extPts(49) = 0.725435: extPts(50) = 0#
    extPts(51) = 0.816026: extPts(52) = 0.761413: extPts(53) = 0#
    extPts(54) = 0.894603: extPts(55) = 0.795765: extPts(56) = 0#
    extPts(57) = 0.976560: extPts(58) = 0.828419: extPts(59) = 0#
    extPts(60) = 1.061724: extPts(61) = 0.859305: extPts(62) = 0#
    extPts(63) = 1.149912: extPts(64) = 0.888357: extPts(65) = 0#
    extPts(66) = 1.240937: extPts(67) = 0.915514: extPts(68) = 0#
    extPts(69) = 1.334604: extPts(70) = 0.940717: extPts(71) = 0#
    extPts(72) = 1.430713: extPts(73) = 0.963912: extPts(74) = 0#
    extPts(75) = 1.529059: extPts(76) = 0.985050: extPts(77) = 0#
    extPts(78) = 1.629432: extPts(79) = 1.004086: extPts(80) = 0#
    extPts(81) = 1.731618: extPts(82) = 1.020979: extPts(83) = 0#
    extPts(84) = 1.835399: extPts(85) = 1.035694: extPts(86) = 0#
    extPts(87) = 1.940554: extPts(88) = 1.048198: extPts(89) = 0#
    extPts(90) = 2.046858: extPts(91) = 1.058465: extPts(92) = 0#
    extPts(93) = 2.154084: extPts(94) = 1.066474: extPts(95) = 0#
    extPts(96) = 2.262003: extPts(97) = 1.072207: extPts(98) = 0#
    extPts(99) = 2.370386: extPts(100) = 1.075651: extPts(101) = 0#
    extPts(102) = 2.479000: extPts(103) = 1.076800: extPts(104) = 0#
    extPts(105) = 2.646356: extPts(106) = 1.076047: extPts(107) = 0#
    extPts(108) = 2.813477: extPts(109) = 1.073789: extPts(110) = 0#
    extPts(111) = 2.980131: extPts(112) = 1.070029: extPts(113) = 0#
    extPts(114) = 3.146083: extPts(115) = 1.064773: extPts(116) = 0#
    extPts(117) = 3.311103: extPts(118) = 1.058028: extPts(119) = 0#
    extPts(120) = 3.474959: extPts(121) = 1.049802: extPts(122) = 0#
    extPts(123) = 3.637422: extPts(124) = 1.040109: extPts(125) = 0#
    extPts(126) = 3.798265: extPts(127) = 1.028961: extPts(128) = 0#
    extPts(129) = 3.957263: extPts(130) = 1.016374: extPts(131) = 0#
    extPts(132) = 4.114193: extPts(133) = 1.002365: extPts(134) = 0#
    extPts(135) = 4.268837: extPts(136) = 0.986954: extPts(137) = 0#
    extPts(138) = 4.420977: extPts(139) = 0.970163: extPts(140) = 0#
    extPts(141) = 4.570401: extPts(142) = 0.952015: extPts(143) = 0#
    extPts(144) = 4.716900: extPts(145) = 0.932536: extPts(146) = 0#
    extPts(147) = 4.860269: extPts(148) = 0.911753: extPts(149) = 0#
    extPts(150) = 5.000308: extPts(151) = 0.889694: extPts(152) = 0#
    extPts(153) = 5.136820: extPts(154) = 0.866391: extPts(155) = 0#
    extPts(156) = 5.269616: extPts(157) = 0.841876: extPts(158) = 0#
    extPts(159) = 5.398508: extPts(160) = 0.816184: extPts(161) = 0#
    extPts(162) = 5.523317: extPts(163) = 0.789350: extPts(164) = 0#
    extPts(165) = 5.643869: extPts(166) = 0.761413: extPts(167) = 0#
    extPts(168) = 5.759994: extPts(169) = 0.732410: extPts(170) = 0#
    extPts(171) = 5.871530: extPts(172) = 0.702383: extPts(173) = 0#
    extPts(174) = 5.978321: extPts(175) = 0.671374: extPts(176) = 0#
    extPts(177) = 6.080219: extPts(178) = 0.639426: extPts(179) = 0#
    extPts(180) = 6.177080: extPts(181) = 0.606583: extPts(182) = 0#
    extPts(183) = 6.268768: extPts(184) = 0.572892: extPts(185) = 0#
    extPts(186) = 6.355157: extPts(187) = 0.538400: extPts(188) = 0#
    extPts(189) = 6.436124: extPts(190) = 0.503155: extPts(191) = 0#
    extPts(192) = 6.511556: extPts(193) = 0.467206: extPts(194) = 0#
    extPts(195) = 6.581349: extPts(196) = 0.430604: extPts(197) = 0#
    extPts(198) = 6.645405: extPts(199) = 0.393399: extPts(200) = 0#
    extPts(201) = 6.703633: extPts(202) = 0.355644: extPts(203) = 0#
    extPts(204) = 6.755953: extPts(205) = 0.317392: extPts(206) = 0#
    extPts(207) = 6.802291: extPts(208) = 0.278696: extPts(209) = 0#
    extPts(210) = 6.842582: extPts(211) = 0.239611: extPts(212) = 0#
    extPts(213) = 6.876771: extPts(214) = 0.200190: extPts(215) = 0#
    extPts(216) = 6.904809: extPts(217) = 0.160489: extPts(218) = 0#
    extPts(219) = 6.926657: extPts(220) = 0.120563: extPts(221) = 0#
    extPts(222) = 6.942285: extPts(223) = 0.080469: extPts(224) = 0#
    extPts(225) = 6.951670: extPts(226) = 0.040263: extPts(227) = 0#
    extPts(228) = 6.954800: extPts(229) = 0.000000: extPts(230) = 0#
    intPts(0) = 6.951800: intPts(1) = 0.000000: intPts(2) = 0#
    intPts(3) = 6.948672: intPts(4) = 0.040151: intPts(5) = 0#
    intPts(6) = 6.939293: intPts(7) = 0.080245: intPts(8) = 0#
    intPts(9) = 6.923676: intPts(10) = 0.120227: intPts(11) = 0#
    intPts(12) = 6.901843: intPts(13) = 0.160042: intPts(14) = 0#
    intPts(15) = 6.873823: intPts(16) = 0.199632: intPts(17) = 0#
    intPts(18) = 6.839658: intPts(19) = 0.238943: intPts(20) = 0#
    intPts(21) = 6.799393: intPts(22) = 0.277920: intPts(23) = 0#
    intPts(24) = 6.753086: intPts(25) = 0.316508: intPts(26) = 0#
    intPts(27) = 6.700801: intPts(28) = 0.354654: intPts(29) = 0#
    intPts(30) = 6.642612: intPts(31) = 0.392303: intPts(32) = 0#
    intPts(33) = 6.578600: intPts(34) = 0.429404: intPts(35) = 0#
    intPts(36) = 6.508854: intPts(37) = 0.465904: intPts(38) = 0#
    intPts(39) = 6.433471: intPts(40) = 0.501753: intPts(41) = 0#
    intPts(42) = 6.352558: intPts(43) = 0.536900: intPts(44) = 0#
    intPts(45) = 6.266228: intPts(46) = 0.571296: intPts(47) = 0#
    intPts(48) = 6.174601: intPts(49) = 0.604893: intPts(50) = 0#
    intPts(51) = 6.077805: intPts(52) = 0.637644: intPts(53) = 0#
    intPts(54) = 5.975976: intPts(55) = 0.669503: intPts(56) = 0#
    intPts(57) = 5.869256: intPts(58) = 0.700426: intPts(59) = 0#
    intPts(60) = 5.757794: intPts(61) = 0.730369: intPts(62) = 0#
    intPts(63) = 5.641747: intPts(64) = 0.759291: intPts(65) = 0#
    intPts(66) = 5.521277: intPts(67) = 0.787151: intPts(68) = 0#
    intPts(69) = 5.396551: intPts(70) = 0.813910: intPts(71) = 0#
    intPts(72) = 5.267745: intPts(73) = 0.839531: intPts(74) = 0#
    intPts(75) = 5.135039: intPts(76) = 0.863977: intPts(77) = 0#
    intPts(78) = 4.998618: intPts(79) = 0.887215: intPts(80) = 0#
    intPts(81) = 4.858673: intPts(82) = 0.909212: intPts(83) = 0#
    intPts(84) = 4.715400: intPts(85) = 0.929938: intPts(86) = 0#
    intPts(87) = 4.568999: intPts(88) = 0.949363: intPts(89) = 0#
    intPts(90) = 4.419675: intPts(91) = 0.967460: intPts(92) = 0#
    intPts(93) = 4.267637: intPts(94) = 0.984205: intPts(95) = 0#
    intPts(96) = 4.113097: intPts(97) = 0.999572: intPts(98) = 0#
    intPts(99) = 3.956272: intPts(100) = 1.013542: intPts(101) = 0#
    intPts(102) = 3.797381: intPts(103) = 1.026094: intPts(104) = 0#
    intPts(105) = 3.636646: intPts(106) = 1.037211: intPts(107) = 0#
    intPts(108) = 3.474292: intPts(109) = 1.046878: intPts(110) = 0#
    intPts(111) = 3.310545: intPts(112) = 1.055080: intPts(113) = 0#
    intPts(114) = 3.145636: intPts(115) = 1.061807: intPts(116) = 0#
    intPts(117) = 2.979795: intPts(118) = 1.067048: intPts(119) = 0#
    intPts(120) = 2.813253: intPts(121) = 1.070797: intPts(122) = 0#
    intPts(123) = 2.646243: intPts(124) = 1.073049: intPts(125) = 0#
    intPts(126) = 2.479000: intPts(127) = 1.073800: intPts(128) = 0#
    intPts(129) = 2.370524: intPts(130) = 1.072654: intPts(131) = 0#
    intPts(132) = 2.262280: intPts(133) = 1.069219: intPts(134) = 0#
    intPts(135) = 2.154498: intPts(136) = 1.063503: intPts(137) = 0#
    intPts(138) = 2.047409: intPts(139) = 1.055517: intPts(140) = 0#
    intPts(141) = 1.941241: intPts(142) = 1.045278: intPts(143) = 0#
    intPts(144) = 1.836220: intPts(145) = 1.032808: intPts(146) = 0#
    intPts(147) = 1.732572: intPts(148) = 1.018135: intPts(149) = 0#
    intPts(150) = 1.630516: intPts(151) = 1.001289: intPts(152) = 0#
    intPts(153) = 1.530270: intPts(154) = 0.982306: intPts(155) = 0#
    intPts(156) = 1.432050: intPts(157) = 0.961226: intPts(158) = 0#
    intPts(159) = 1.336063: intPts(160) = 0.938096: intPts(161) = 0#
    intPts(162) = 1.242516: intPts(163) = 0.912963: intPts(164) = 0#
    intPts(165) = 1.151608: intPts(166) = 0.885882: intPts(167) = 0#
    intPts(168) = 1.063532: intPts(169) = 0.856911: intPts(170) = 0#
    intPts(171) = 0.978477: intPts(172) = 0.826111: intPts(173) = 0#
    intPts(174) = 0.896624: intPts(175) = 0.793548: intPts(176) = 0#
    intPts(177) = 0.818148: intPts(178) = 0.759291: intPts(179) = 0#
    intPts(180) = 0.743216: intPts(181) = 0.723414: intPts(182) = 0#
    intPts(183) = 0.671988: intPts(184) = 0.685994: intPts(185) = 0#
    intPts(186) = 0.604617: intPts(187) = 0.647109: intPts(188) = 0#
    intPts(189) = 0.541246: intPts(190) = 0.606843: intPts(191) = 0#
    intPts(192) = 0.482010: intPts(193) = 0.565283: intPts(194) = 0#
    intPts(195) = 0.427036: intPts(196) = 0.522516: intPts(197) = 0#
    intPts(198) = 0.376440: intPts(199) = 0.478634: intPts(200) = 0#
    intPts(201) = 0.330332: intPts(202) = 0.433730: intPts(203) = 0#
    intPts(204) = 0.288809: intPts(205) = 0.387901: intPts(206) = 0#
    intPts(207) = 0.251960: intPts(208) = 0.341244: intPts(209) = 0#
    intPts(210) = 0.219864: intPts(211) = 0.293859: intPts(212) = 0#
    intPts(213) = 0.192589: intPts(214) = 0.245847: intPts(215) = 0#
    intPts(216) = 0.170193: intPts(217) = 0.197310: intPts(218) = 0#
    intPts(219) = 0.152724: intPts(220) = 0.148352: intPts(221) = 0#
    intPts(222) = 0.140220: intPts(223) = 0.099078: intPts(224) = 0#
    intPts(225) = 0.132706: intPts(226) = 0.049592: intPts(227) = 0#
    intPts(228) = 0.130200: intPts(229) = 0.000000: intPts(230) = 0#
    extArr = extPts
    intArr = intPts
    swSketchMgr.CreateSpline2 (extArr), True
    swSketchMgr.CreateLine 6.954800, 0#, 0#, 6.951800, 0#, 0#
    swSketchMgr.CreateSpline2 (intArr), True
    swSketchMgr.CreateLine 0.130200, 0#, 0#, 0.127200, 0#, 0#

    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        False, True, False, False, False, False, _
        0, 0, 1.570796326795, 1.570796326795, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Capa_Aislante_4_Sup"

    ' --- Anillos_Celulares_360 ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 1.130120, 0.946557, 1.136120, 1.008476)
    Call DibujarRectangulo(swSketchMgr, 1.932747, 1.110782, 1.938747, 1.172136)
    Call DibujarRectangulo(swSketchMgr, 2.735373, 1.138137, 2.741373, 1.199489)
    Call DibujarRectangulo(swSketchMgr, 3.538000, 1.108352, 3.544000, 1.168955)
    Call DibujarRectangulo(swSketchMgr, 4.340627, 1.039350, 4.346627, 1.098306)
    Call DibujarRectangulo(swSketchMgr, 5.143253, 0.922374, 5.149253, 0.978893)
    Call DibujarRectangulo(swSketchMgr, 5.945880, 0.734875, 5.951880, 0.788862)
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

    ' --- Anillos_Celulares_Sup ---
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 1.130120, 0.882641, 1.136120, 0.944337)
    Call DibujarRectangulo(swSketchMgr, 1.932747, 1.047278, 1.938747, 1.108585)
    Call DibujarRectangulo(swSketchMgr, 2.735373, 1.074590, 2.741373, 1.135939)
    Call DibujarRectangulo(swSketchMgr, 3.538000, 1.045649, 3.544000, 1.106193)
    Call DibujarRectangulo(swSketchMgr, 4.340627, 0.978507, 4.346627, 1.037275)
    Call DibujarRectangulo(swSketchMgr, 5.143253, 0.864311, 5.149253, 0.920426)
    Call DibujarRectangulo(swSketchMgr, 5.945880, 0.679761, 5.951880, 0.733059)
    swSketchMgr.InsertSketch True
    Set swSketchFeat = swModel.FeatureByPositionReverse(0)

    swModel.ClearSelection2 True
    swSelData.Mark = 0
    swSketchFeat.Select4 False, swSelData
    swSelData.Mark = 4
    swAxisFeat.Select4 True, swSelData

    Set swFeat = swFeatMgr.FeatureRevolve2( _
        False, True, False, False, False, False, _
        0, 0, 1.570796326795, 1.570796326795, _
        False, False, 0.01, 0.01, _
        0, 0#, 0#, _
        False, True, True)
    If Not swFeat Is Nothing Then swFeat.Name = "Anillos_Celulares_Sup"


    ' -------------------------------------------------------------------------
    ' 2. Gondola rectangular de componentes internos (bajo X_CB, gap 135 mm)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 2.975500, -1.570838, 3.575500, -1.320838)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.300000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Gondola_Componentes"

    ' -------------------------------------------------------------------------
    ' 3. Dos soportes verticales de suspension (casco <-> gondola)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.040500, -1.320838, 3.070500, -1.149275)
    Call DibujarRectangulo(swSketchMgr, 3.480500, -1.320838, 3.510500, -1.149275)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.03#, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Soportes_Gondola"

    ' -------------------------------------------------------------------------
    ' 4. Brazos transversales en H alineados bajo los puntales dentro de la gondola
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plFront.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 3.043000, -1.458338, 3.068000, -1.433338)
    Call DibujarRectangulo(swSketchMgr, 3.483000, -1.458338, 3.508000, -1.433338)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 1.125000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Brazos_Transversales_H"

    ' -------------------------------------------------------------------------
    ' 5. Tirantes diagonales triangulados (union superior gondola <-> brazos)
    ' -------------------------------------------------------------------------
    ' --- Tirantes_Triangulados_Del (en X = 3.056 m) ---
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 3.055500, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Tirantes_Del"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarPoligono4(swSketchMgr, 0.140286, -1.332133, 0.517286, -1.431133, 0.512714, -1.448542, 0.135714, -1.349542)
    Call DibujarPoligono4(swSketchMgr, -0.135714, -1.349542, -0.512714, -1.448542, -0.517286, -1.431133, -0.140286, -1.332133)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.018000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tirantes_Triangulados_Del"

    ' --- Tirantes_Triangulados_Tras (en X = 3.495 m) ---
    swModel.ClearSelection2 True
    plRight.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST, 3.495500, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Tirantes_Tras"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarPoligono4(swSketchMgr, 0.140286, -1.332133, 0.517286, -1.431133, 0.512714, -1.448542, 0.135714, -1.349542)
    Call DibujarPoligono4(swSketchMgr, -0.135714, -1.349542, -0.512714, -1.448542, -0.517286, -1.431133, -0.140286, -1.332133)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.018000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Tirantes_Triangulados_Tras"


    ' -------------------------------------------------------------------------
    ' 6. Largueros longitudinales en H (conectan brazos transversales con los motores)
    ' -------------------------------------------------------------------------
    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.445838, 0, 0, 0, 0)
    Set swFeat = swModel.FeatureByPositionReverse(0)
    If Not swFeat Is Nothing Then swFeat.Name = "Plano_Brazos_H"

    swModel.ClearSelection2 True
    swFeat.Select2 False, 0
    swSketchMgr.InsertSketch True
    Call DibujarRectangulo(swSketchMgr, 2.830500, -0.562500, 3.720500, -0.537500)
    Call DibujarRectangulo(swSketchMgr, 2.830500, 0.537500, 3.720500, 0.562500)
    swSketchMgr.InsertSketch True

    Set swFeat = ExtruirSolido(swFeatMgr, SW_END_MIDPLANE, 0.025000, False, False)
    If Not swFeat Is Nothing Then swFeat.Name = "Largueros_H"

    ' -------------------------------------------------------------------------
    ' 7. Motores A2212 referenciales (4 motores en 2 costados)
    ' -------------------------------------------------------------------------
    Dim xsMot(0 To 1) As Double
    xsMot(0) = 2.855500
    xsMot(1) = 3.695500
    Dim i As Long

    swModel.ClearSelection2 True
    plTop.Select2 False, 0
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.433338, 0, 0, 0, 0)
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
    Set swPlaneTmp = swFeatMgr.InsertRefPlane(SW_REFPLANE_DIST + SW_REFPLANE_FLIP, 1.403338, 0, 0, 0, 0)
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
           "Casco hueco: 7082 x 2408 mm | Capas: 4 sup / 2 inf (e=31.8 mm)" & vbCrLf & _
           "Gondola (X_CB=3276 mm): 600 x 300 x 250 mm (gap 135 mm)" & vbCrLf & _
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
