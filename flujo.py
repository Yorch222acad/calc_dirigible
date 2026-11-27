"""
Metadatos de flujo físico y relacional de las 13 categorías del modelo del dirigible.

Actúa como fuente única de verdad para:
  - Las explicaciones pedagógicas de cada categoría y su encadenamiento interno.
  - Los diagramas de flujo internos por categoría (nodos por ecuación, capas y lazos).
  - Las conexiones dirigidas entre categorías (entradas, salidas y lazos cerrados).
  - El Mapa de Flujo Global (C1 -> C13) del modelo completo.
"""
from __future__ import annotations

from typing import Any

import modelo


GRUPOS_TEMATICOS: list[dict[str, str]] = [
    {
        "id": "aerostatica",
        "nombre": "Aerostática y Geometría del Casco",
        "color": "#38bdf8",
        "descripcion": "Define las propiedades del aire ambiente y caliente (C1), el volumen y dimensiones del casco prolado (C2) y las áreas superficiales de membrana y película aislante (C3).",
    },
    {
        "id": "termica",
        "nombre": "Transferencia de Calor y Quemador Térmico",
        "color": "#fb923c",
        "descripcion": "Resuelve la convección natural y forzada sin aislante (C4) y con capa celular intermedia (C5), cuantifica el ahorro térmico y enfriamiento (C6) y calcula el combustible térmico requerido (C7).",
    },
    {
        "id": "aerodinamica",
        "nombre": "Vuelo, Viento en Contra y Arrastre",
        "color": "#a78bfa",
        "descripcion": "Integra la velocidad del aire, el viento en contra, la cinemática de misión (vg, tm) y la resistencia aerodinámica volumétrica de Hoerner (C8).",
    },
    {
        "id": "propulsion",
        "nombre": "Propulsión Híbrida, Energía y Lazo de Batería",
        "color": "#4ade80",
        "descripcion": "Reparte el peso entre flotabilidad y motores (C9), calcula el empuje vectorial y actitud A2212 (C10), eficiencia de hélice y potencia eléctrica (C11), balance energético (C12) y batería acoplada (C13 ↺ C9).",
    },
]

_GRUPOS_BY_ID: dict[str, dict[str, str]] = {g["id"]: g for g in GRUPOS_TEMATICOS}


# Lista maestra de conexiones dirigidas entre categorías (índices base 0: C1=0 .. C13=12)
CONEXIONES_INTER_CATEGORIAS: list[dict[str, Any]] = [
    # Aerostática y Casco (C1 -> C2 -> C3) y sus salidas hacia todo el modelo
    {
        "origen": 0,
        "destino": 1,
        "variables": ["drho", "rhocel", "F"],
        "origenes_internos": ["drho", "rhocel", "F"],
        "destinos_internos": ["F"],
        "explicacion": "Las densidades drho y rhocel junto al empuje F fijan el volumen exterior V del casco descontando el volumen periférico de las celdas aislantes.",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 0,
        "variables": ["Vnuc", "Vcel"],
        "origenes_internos": ["Vnuc", "Vcel"],
        "destinos_internos": ["F", "m", "Q"],
        "explicacion": "El volumen del núcleo Vnuc y el de celdas Vcel determinan la flotabilidad exacta F, la masa total de aire encerrado m y el calor sensible regional Q.",
        "es_lazo": True,
    },
    {
        "origen": 4,
        "destino": 0,
        "variables": ["Tm"],
        "origenes_internos": ["Tm"],
        "destinos_internos": ["rhocel"],
        "explicacion": "La temperatura media de pared Tm fija la densidad media rhocel del aire encerrado en las celdas aislantes.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 3,
        "variables": ["dT"],
        "origenes_internos": ["dT"],
        "destinos_internos": ["dTi0"],
        "explicacion": "El gradiente térmico total dT = T2 - T1 impulsa el reparto de caída térmica en el casco base sin aislante.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 4,
        "variables": ["dT"],
        "origenes_internos": ["dT"],
        "destinos_internos": ["dTi", "dTcel"],
        "explicacion": "El salto térmico total dT fija las caídas acopladas en la película interna (dTi) y en la celda aislante (dTcel).",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 5,
        "variables": ["dT", "Q"],
        "origenes_internos": ["dT", "Q"],
        "destinos_internos": ["Qp0", "Qp", "vT", "Qc", "tc"],
        "explicacion": "El salto dT determina los flujos térmicos Qp0 y Qp, mientras que el calor sensible regional Q define la capacidad calorífica efectiva C_ef = Q/dT para vT, Qc y tc.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 6,
        "variables": ["Q"],
        "origenes_internos": ["Q"],
        "destinos_internos": ["Epre"],
        "explicacion": "El calor sensible Q requerido para llevar el volumen V desde T1 hasta T2 fija la energía de precalentamiento en tierra Epre = Q/npre y su costo Cpre.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 7,
        "variables": ["rho1"],
        "origenes_internos": ["rho1"],
        "destinos_internos": ["ReL", "FD"],
        "explicacion": "La densidad del aire ambiente (rho1) interviene en el número de Reynolds ReL y en la presión dinámica de arrastre FD.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 8,
        "variables": ["F", "mflot", "m"],
        "origenes_internos": ["F", "mflot", "m"],
        "destinos_internos": ["F", "mflot", "map"],
        "explicacion": "C1 comparte F, la masa compensada mflot = F/g y la masa de gas encerrado m que contribuye a la inercia traslacional y vertical.",
        "es_lazo": False,
    },
    {
        "origen": 0,
        "destino": 10,
        "variables": ["rho1"],
        "origenes_internos": ["rho1"],
        "destinos_internos": ["Pelec"],
        "explicacion": "La densidad del aire (rho1) determina el flujo de masa en el disco de las hélices y la potencia inducida en Pelec.",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 2,
        "variables": ["D", "xf", "L", "S"],
        "origenes_internos": ["D", "xf", "L", "S"],
        "destinos_internos": ["ef", "er", "S"],
        "explicacion": "Los semiejes (cf = xf·L, cr = L - cf) y el radio R = D/2 definen las excentricidades y áreas semielipsoidales en C3.",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 3,
        "variables": ["L", "D"],
        "origenes_internos": ["L", "D"],
        "destinos_internos": ["he", "RaD0", "hi0"],
        "explicacion": "La longitud L escala el coeficiente convectivo exterior he y el diámetro D escala la convección natural interna (RaD0, hi0).",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 4,
        "variables": ["D"],
        "origenes_internos": ["D"],
        "destinos_internos": ["RaD", "hi"],
        "explicacion": "El diámetro máximo D determina el número de Rayleigh interno RaD y la convección interna hi con aislante.",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 7,
        "variables": ["L", "V", "lam"],
        "origenes_internos": ["L", "V", "lam"],
        "destinos_internos": ["ReL", "CDVc", "FD"],
        "explicacion": "L define ReL, la esbeltez lam gobierna el coeficiente volumétrico de Hoerner (CDVc) y V^(2/3) escala el arrastre FD.",
        "es_lazo": False,
    },
    {
        "origen": 2,
        "destino": 5,
        "variables": ["S"],
        "origenes_internos": ["S"],
        "destinos_internos": ["Qp0", "Qp"],
        "explicacion": "El área superficial total S del casco multiplica los coeficientes globales U0 y U para obtener las pérdidas Qp0 y Qp.",
        "es_lazo": False,
    },
    {
        "origen": 2,
        "destino": 8,
        "variables": ["mc"],
        "origenes_internos": ["mc"],
        "destinos_internos": ["mc", "mart"],
        "explicacion": "La masa de las capas celulares de Mylar (mc) se suma directamente en la masa estructural mart.",
        "es_lazo": False,
    },
    # Convección, Aislamiento y Balance Térmico (C4, C5 -> C6 -> C7 -> C12)
    {
        "origen": 3,
        "destino": 4,
        "variables": ["hetot"],
        "origenes_internos": ["hetot"],
        "destinos_internos": ["hetot", "Usup", "Uinf"],
        "explicacion": "El coeficiente externo total hetot = he + hrade se comparte entre C4 y C5 como resistencia exterior común del casco Mylar.",
        "es_lazo": False,
    },
    {
        "origen": 3,
        "destino": 5,
        "variables": ["U0"],
        "origenes_internos": ["U0"],
        "destinos_internos": ["Qp0"],
        "explicacion": "El coeficiente global base U0 fija la pérdida térmica sin capa celular (Qp0 = U0·S·dT).",
        "es_lazo": False,
    },
    {
        "origen": 4,
        "destino": 5,
        "variables": ["U"],
        "origenes_internos": ["U"],
        "destinos_internos": ["Qp"],
        "explicacion": "El coeficiente global con aislante U determina la pérdida térmica real del casco (Qp = U·S·dT).",
        "es_lazo": False,
    },
    {
        "origen": 5,
        "destino": 6,
        "variables": ["Qp0", "Qp", "dQp", "Qc"],
        "origenes_internos": ["Qp0", "Qp", "dQp", "Qc"],
        "destinos_internos": ["Em0", "Em", "Eah", "mgc"],
        "explicacion": "Las potencias térmicas Qp0, Qp, dQp se multiplican por el tiempo de vuelo tm para obtener las energías en C7, y Qc fija mgc.",
        "es_lazo": False,
    },
    {
        "origen": 6,
        "destino": 11,
        "variables": ["Eprop", "Cpre"],
        "origenes_internos": ["Eprop", "Cpre"],
        "destinos_internos": ["Eprop", "Cpre", "Etot", "Cop"],
        "explicacion": "La energía química del combustible (Eprop = Em / ncal) compone la rama térmica de Etot, y Cpre entra en el costo operativo total Cop.",
        "es_lazo": False,
    },
    # Vuelo, Viento y Arrastre (C8 -> C4, C7, C10, C12)
    {
        "origen": 7,
        "destino": 3,
        "variables": ["ReL"],
        "origenes_internos": ["ReL"],
        "destinos_internos": ["Nue"],
        "explicacion": "El número de Reynolds del flujo externo (ReL) gobierna la convección forzada exterior en Nue.",
        "es_lazo": False,
    },
    {
        "origen": 7,
        "destino": 6,
        "variables": ["dm", "tm"],
        "origenes_internos": ["tm"],
        "destinos_internos": ["dm", "Em0", "Em", "Eah"],
        "explicacion": "El tiempo de vuelo tm = dm / vg impuesto por la distancia y el viento en contra determina las pérdidas térmicas integradas en misión.",
        "es_lazo": False,
    },
    {
        "origen": 7,
        "destino": 9,
        "variables": ["FD"],
        "origenes_internos": ["FD"],
        "destinos_internos": ["FD", "FX", "thcruc"],
        "explicacion": "La fuerza de resistencia aerodinámica FD constituye la carga base horizontal tanto en maniobra (FX) como en crucero (thcruc).",
        "es_lazo": False,
    },
    {
        "origen": 7,
        "destino": 11,
        "variables": ["ED", "dm", "tm"],
        "origenes_internos": ["ED", "tm"],
        "destinos_internos": ["ED", "Ereq", "celec", "ctot"],
        "explicacion": "C8 entrega el trabajo aerodinámico ED para referencia energética, dm para los costes por metro y tm para integrar Ereq.",
        "es_lazo": False,
    },
    # Masas, Propulsión, Energía y Lazo Cerrado de Batería (C9 -> C10 -> C11 -> C12 -> C13 ↺ C9)
    {
        "origen": 8,
        "destino": 9,
        "variables": ["mres", "map"],
        "origenes_internos": ["mres", "map"],
        "destinos_internos": ["FL", "FX", "thcruc"],
        "explicacion": "La masa residual mres exige sustentación estática FL (e inclinación thcruc en crucero) y la masa aparente inercial map = fap·(mtot + m) aporta las fuerzas de ascenso y arranque.",
        "es_lazo": False,
    },
    {
        "origen": 8,
        "destino": 10,
        "variables": ["F", "mtot", "mres"],
        "origenes_internos": ["F", "mtot", "mres"],
        "destinos_internos": ["Fexc", "Tcruc"],
        "explicacion": "F y mtot·g fijan el excedente Fexc, mientras mres·g determina el empuje vertical requerido en crucero estacionario (Tcruc).",
        "es_lazo": False,
    },
    {
        "origen": 7,
        "destino": 10,
        "variables": ["FD"],
        "origenes_internos": ["FD"],
        "destinos_internos": ["Tcruc", "Pcruc"],
        "explicacion": "El arrastre aerodinámico FD fija el empuje y potencia de avance en régimen de crucero estacionario (Tcruc, Pcruc).",
        "es_lazo": False,
    },
    {
        "origen": 9,
        "destino": 10,
        "variables": ["FX", "Ttot"],
        "origenes_internos": ["FX", "Ttot"],
        "destinos_internos": ["Ttot", "FLmax", "Pelec"],
        "explicacion": "FX limita la sustentación vertical disponible FLmax y el empuje pico de maniobra Ttot fija la potencia pico Pelec.",
        "es_lazo": False,
    },
    {
        "origen": 10,
        "destino": 11,
        "variables": ["Pelec", "Pcruc"],
        "origenes_internos": ["Pelec", "Pcruc"],
        "destinos_internos": ["Pelec", "Pcruc", "Ptot", "Ereq"],
        "explicacion": "Pelec fija el pico Ptot = Pelec + Pad durante tman, mientras Pcruc + Pad gobierna el consumo energético durante el crucero estacionario.",
        "es_lazo": False,
    },
    {
        "origen": 11,
        "destino": 12,
        "variables": ["Ptot", "Ereq"],
        "origenes_internos": ["Ptot", "Ereq"],
        "destinos_internos": ["Ptot", "Ereq", "mbp", "mbe"],
        "explicacion": "La potencia total a bordo Ptot = Pelec + Pad y la energía requerida Ereq dimensionan la batería simultáneamente por potencia pico (mbp) y capacidad (mbe).",
        "es_lazo": False,
    },
    {
        "origen": 12,
        "destino": 8,
        "variables": ["mbat", "mart"],
        "origenes_internos": ["mbat", "mart"],
        "destinos_internos": ["mbat", "mart"],
        "explicacion": "LAZO CERRADO: la masa de batería mbat se suma al artefacto mart y aumenta mtot y mres, lo que a su vez eleva Pelec y mbat hasta equilibrarse.",
        "es_lazo": True,
    },
]


FLUJO_CATEGORIAS: list[dict[str, Any]] = [
    {
        "titulo_corto": "Gases y Flotabilidad",
        "grupo": "aerostatica",
        "pos_global": {"fila": 0, "col": 0},
        "resumen": (
            "Modela las propiedades termodinámicas del aire frío exterior y del aire caliente interior "
            "mediante la ley de gases ideales, cuantificando el empuje hidrostático disponible por unidad de volumen."
        ),
        "flujo_interno": (
            "Las ecuaciones de gas ideal calculan las densidades rho1 y rho2, cuyo contraste define drho y dT. "
            "En calibración directa, la carga asignada mflot fija F = mflot·g; una vez calculado V en C2, "
            "regresa para determinar la masa de aire caliente m = rho2·V y su calor sensible Q."
        ),
        "nodos": [
            {"eq": "Gas ideal (caso 1 - ambiente)", "var": "rho1", "etiqueta": "Densidad aire exterior", "capa": 0},
            {"eq": "Gas ideal (caso 2 - caliente)", "var": "rho2", "etiqueta": "Densidad núcleo caliente", "capa": 0},
            {"eq": "Densidad media del aire en celdas aislantes", "var": "rhocel", "etiqueta": "Densidad celdas rhocel", "capa": 0},
            {"eq": "Gradiente térmico", "var": "dT", "etiqueta": "Salto térmico T2 - T1", "capa": 0},
            {"eq": "Masa compensada por aire caliente (mflot)", "var": "mflot", "etiqueta": "Carga asignada al globo", "capa": 0},
            {"eq": "Diferencia de densidades", "var": "drho", "etiqueta": "Contraste rho1 - rho2", "capa": 1},
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Empuje de Arquímedes", "capa": 1},
            {"eq": "Masa de aire caliente", "var": "m", "etiqueta": "Gas núcleo + celdas", "capa": 1},
            {"eq": "Calor sensible", "var": "Q", "etiqueta": "Calor regional Q", "capa": 2},
        ],
        "aristas_internas": [
            {"origen": "rho1", "destino": "drho", "etiqueta": "rho1 - rho2", "lazo": False},
            {"origen": "rho2", "destino": "drho", "etiqueta": "rho1 - rho2", "lazo": False},
            {"origen": "mflot", "destino": "F", "etiqueta": "F = mflot·g", "lazo": False},
            {"origen": "drho", "destino": "F", "etiqueta": "núcleo Vnuc", "lazo": False},
            {"origen": "rhocel", "destino": "F", "etiqueta": "celdas Vcel", "lazo": False},
            {"origen": "rho2", "destino": "m", "etiqueta": "rho2 · Vnuc", "lazo": False},
            {"origen": "rhocel", "destino": "m", "etiqueta": "rhocel · Vcel", "lazo": False},
            {"origen": "rho2", "destino": "Q", "etiqueta": "núcleo ΔT", "lazo": False},
            {"origen": "rhocel", "destino": "Q", "etiqueta": "celdas ΔT/2", "lazo": False},
            {"origen": "dT", "destino": "Q", "etiqueta": "cp · ΔT", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Dimensiones y Volumen",
        "grupo": "aerostatica",
        "pos_global": {"fila": 0, "col": 1},
        "resumen": (
            "Convierte la fuerza aerostática F en volumen de casco y deduce las dimensiones principales "
            "(R, D, λ, L, cf, cr), además de separar el núcleo caliente Vnuc del volumen periférico de celdas Vcel."
        ),
        "flujo_interno": (
            "Partiendo de F, drho y rhocel se despeja el volumen exterior V y su reparto en núcleo Vnuc y celdas Vcel. "
            "Junto con lam = L/D determina R, D y L; la fracción xf parte el casco en cf y cr hacia el área S."
        ),
        "nodos": [
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Empuje aerostático", "capa": 0},
            {"eq": "Volumen total del casco", "var": "V", "etiqueta": "Volumen V = (2/3)πR²L", "capa": 1},
            {"eq": "Diámetro máximo transversal (2R)", "var": "D", "etiqueta": "Diámetro D = 2R", "capa": 2},
            {"eq": "Relación de esbeltez (L/D)", "var": "lam", "etiqueta": "Esbeltez λ = L/D", "capa": 2},
            {"eq": "Longitud total del casco", "var": "L", "etiqueta": "Longitud L = cf + cr", "capa": 3},
            {"eq": "Fracción de nariz (cf/L)", "var": "xf", "etiqueta": "Partición nariz cf/L", "capa": 3},
            {"eq": "Volumen del núcleo interior caliente", "var": "Vnuc", "etiqueta": "Núcleo caliente Vnuc", "capa": 4},
            {"eq": "Área superficial total", "var": "S", "etiqueta": "Área envolvente S", "capa": 4},
            {"eq": "Volumen ocupado por celdas aislantes", "var": "Vcel", "etiqueta": "Celdas V - Vnuc", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "F", "destino": "V", "etiqueta": "arquímedes", "lazo": False},
            {"origen": "V", "destino": "D", "etiqueta": "R ∝ (V/λ)^(1/3)", "lazo": False},
            {"origen": "V", "destino": "lam", "etiqueta": "geometría", "lazo": False},
            {"origen": "D", "destino": "L", "etiqueta": "L = λ·D", "lazo": False},
            {"origen": "lam", "destino": "L", "etiqueta": "λ", "lazo": False},
            {"origen": "L", "destino": "xf", "etiqueta": "cf = xf·L", "lazo": False},
            {"origen": "D", "destino": "S", "etiqueta": "R en Sf, Sr", "lazo": False},
            {"origen": "xf", "destino": "S", "etiqueta": "cf, cr en C3", "lazo": False},
            {"origen": "D", "destino": "Vnuc", "etiqueta": "R - ncap·e", "lazo": False},
            {"origen": "L", "destino": "Vnuc", "etiqueta": "L - 2ncap·e", "lazo": False},
            {"origen": "V", "destino": "Vcel", "etiqueta": "+V", "lazo": False},
            {"origen": "Vnuc", "destino": "Vcel", "etiqueta": "-Vnuc", "lazo": False},
            {"origen": "Vnuc", "destino": "F", "etiqueta": "↺ núcleo", "lazo": True},
            {"origen": "Vcel", "destino": "F", "etiqueta": "↺ celdas", "lazo": True},
        ],
    },
    {
        "titulo_corto": "Superficies y Mylar",
        "grupo": "aerostatica",
        "pos_global": {"fila": 0, "col": 2},
        "resumen": (
            "Calcula el área curva exacta de los dos semielipsoides prolados, el promedio asimétrico "
            "de capas Mylar (ncapS/ncapI), la piel exterior y la masa total de película mc."
        ),
        "flujo_interno": (
            "Con R, cf y cr se obtienen ef, er, Sf, Sr y S. El promedio ncap = (ncapS + ncapI)/2 escala la "
            "superficie multicapa con piel exterior Sc = S·(1 + ncap·(1+2e/W)) y su masa mc = Sc·σ."
        ),
        "nodos": [
            {"eq": "Excentricidad frontal (cf > R)", "var": "ef", "etiqueta": "Excentricidad nariz", "capa": 0},
            {"eq": "Excentricidad trasera (cr > R)", "var": "er", "etiqueta": "Excentricidad cola", "capa": 0},
            {"eq": "Número promedio de capas celulares (ncap)", "var": "ncap", "etiqueta": "Promedio (ncapS+ncapI)/2", "capa": 0},
            {"eq": "Área superficial frontal", "var": "Sf", "etiqueta": "Área nariz Sf", "capa": 1},
            {"eq": "Área superficial trasera", "var": "Sr", "etiqueta": "Área cola Sr", "capa": 1},
            {"eq": "Área superficial total", "var": "S", "etiqueta": "Área casco S = Sf + Sr", "capa": 2},
            {"eq": "Área total de película celular", "var": "Sc", "etiqueta": "Piel + ncap·(1+2e/W)", "capa": 3},
            {"eq": "Masa de la cuadrícula celular", "var": "mc", "etiqueta": "Masa Mylar mc = Sc·σ", "capa": 4},
        ],
        "aristas_internas": [
            {"origen": "ef", "destino": "Sf", "etiqueta": "πR²+arcsin(ef)", "lazo": False},
            {"origen": "er", "destino": "Sr", "etiqueta": "πR²+arcsin(er)", "lazo": False},
            {"origen": "Sf", "destino": "S", "etiqueta": "suma", "lazo": False},
            {"origen": "Sr", "destino": "S", "etiqueta": "suma", "lazo": False},
            {"origen": "S", "destino": "Sc", "etiqueta": "1+ncap·(1+2e/W)", "lazo": False},
            {"origen": "ncap", "destino": "Sc", "etiqueta": "ncap", "lazo": False},
            {"origen": "Sc", "destino": "mc", "etiqueta": "Sc · σ", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Convección y Base (U0)",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 0},
        "resumen": (
            "Determina el coeficiente global base U0 del casco simple sin capa aislante, "
            "combinando convección forzada externa, radiación exterior (hrade) y convección natural interna."
        ),
        "flujo_interno": (
            "La rama externa calcula Pr, Nue, he y hrade para obtener hetot = he + hrade. "
            "La rama interna resuelve el lazo acoplado base (dTi0 → RaD0 → Nui0 → hi0 → U0), completamente aislado de C5."
        ),
        "nodos": [
            {"eq": "Número de Prandtl del aire (Pr)", "var": "Pr", "etiqueta": "Pr = ν / α", "capa": 0},
            {"eq": "Coeficiente radiativo externo del casco (hrade)", "var": "hrade", "etiqueta": "Radiación ext. Mylar", "capa": 0},
            {"eq": "Número de Nusselt externo por viento (Nue)", "var": "Nue", "etiqueta": "Convección externa Nue", "capa": 1},
            {"eq": "Caída térmica interna sin capa celular (dTi0)", "var": "dTi0", "etiqueta": "Salto interno dTi0", "capa": 1},
            {"eq": "Coeficiente convectivo externo del casco (he)", "var": "he", "etiqueta": "Coef. convectivo he", "capa": 2},
            {"eq": "Número de Rayleigh interno sin capa celular (RaD0)", "var": "RaD0", "etiqueta": "Rayleigh base RaD0", "capa": 2},
            {"eq": "Coeficiente externo total del casco (hetot)", "var": "hetot", "etiqueta": "hetot = he + hrade", "capa": 3},
            {"eq": "Número de Nusselt interno sin capa celular (Nui0)", "var": "Nui0", "etiqueta": "Nusselt base Nui0", "capa": 3},
            {"eq": "Coeficiente convectivo interno sin capa celular (hi0)", "var": "hi0", "etiqueta": "Coef. interno hi0", "capa": 4},
            {"eq": "Coeficiente global sin capa celular (U0)", "var": "U0", "etiqueta": "Global base U0", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "Pr", "destino": "Nue", "etiqueta": "Pr^(1/3)", "lazo": False},
            {"origen": "Nue", "destino": "he", "etiqueta": "Nue·ka/L", "lazo": False},
            {"origen": "he", "destino": "hetot", "etiqueta": "+ he", "lazo": False},
            {"origen": "hrade", "destino": "hetot", "etiqueta": "+ hrade", "lazo": False},
            {"origen": "hetot", "destino": "U0", "etiqueta": "1/hetot", "lazo": False},
            {"origen": "dTi0", "destino": "RaD0", "etiqueta": "flotabilidad", "lazo": False},
            {"origen": "RaD0", "destino": "Nui0", "etiqueta": "0.13·Ra^(1/3)", "lazo": False},
            {"origen": "Nui0", "destino": "hi0", "etiqueta": "fcal·ka/D", "lazo": False},
            {"origen": "hi0", "destino": "U0", "etiqueta": "1/hi0", "lazo": False},
            {"origen": "U0", "destino": "dTi0", "etiqueta": "↺ (U0/hi0)·dT", "lazo": True},
        ],
    },
    {
        "titulo_corto": "Mylar Asimétrico (U)",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 1},
        "resumen": (
            "Resuelve la transferencia de calor por capas Mylar asimétricas (ncapS arriba con Hollands y ncapI abajo "
            "estratificada Nu=1), radiación interna entre láminas (hrad) y convección natural interna (hi)."
        ),
        "flujo_interno": (
            "Tm y epsef fijan la conductancia radiativa hrad entre láminas Mylar. El lazo interno (dTi → RaD → Nui → hi con fcal) "
            "y el lazo superior celular (dTcel → Rae → Nuc de Hollands) determinan Usup y Uinf, promediados en U."
        ),
        "nodos": [
            {"eq": "Coeficiente externo total del casco (hetot)", "var": "hetot", "etiqueta": "Externo hetot", "capa": 0},
            {"eq": "Temperatura media absoluta de pared (Tm)", "var": "Tm", "etiqueta": "Temp. media Tm (K)", "capa": 0},
            {"eq": "Emisividad efectiva entre láminas (epsef)", "var": "epsef", "etiqueta": "Emisividad epsef", "capa": 0},
            {"eq": "Caída térmica interna con capa celular (dTi)", "var": "dTi", "etiqueta": "Salto interno dTi", "capa": 0},
            {"eq": "Caída térmica en la celda aislante (dTcel)", "var": "dTcel", "etiqueta": "Salto celda dTcel", "capa": 0},
            {"eq": "Coeficiente radiativo interno de cavidad (hrad)", "var": "hrad", "etiqueta": "Radiación hrad", "capa": 1},
            {"eq": "Número de Rayleigh interno con capa celular (RaD)", "var": "RaD", "etiqueta": "Rayleigh casco RaD", "capa": 1},
            {"eq": "Número de Rayleigh en cavidad celular (Rae)", "var": "Rae", "etiqueta": "Rayleigh celda Rae", "capa": 1},
            {"eq": "Número de Nusselt interno con capa celular (Nui)", "var": "Nui", "etiqueta": "Nusselt casco Nui", "capa": 2},
            {"eq": "Número de Nusselt efectivo en celda (Nuc)", "var": "Nuc", "etiqueta": "Hollands Nuc ≥ 1", "capa": 2},
            {"eq": "Coeficiente convectivo interno con capa celular (hi)", "var": "hi", "etiqueta": "Convección int. hi", "capa": 3},
            {"eq": "Coeficiente global mitad superior (Usup)", "var": "Usup", "etiqueta": "Superior ncapS", "capa": 4},
            {"eq": "Coeficiente global mitad inferior (Uinf)", "var": "Uinf", "etiqueta": "Inferior ncapI", "capa": 4},
            {"eq": "Coeficiente global con capa celular (U)", "var": "U", "etiqueta": "(Usup + Uinf)/2", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "Tm", "destino": "hrad", "etiqueta": "4·σ·Tm³", "lazo": False},
            {"origen": "epsef", "destino": "hrad", "etiqueta": "× epsef", "lazo": False},
            {"origen": "hrad", "destino": "Usup", "etiqueta": "+hrad", "lazo": False},
            {"origen": "hrad", "destino": "Uinf", "etiqueta": "+hrad", "lazo": False},
            {"origen": "hetot", "destino": "Usup", "etiqueta": "1/hetot", "lazo": False},
            {"origen": "hetot", "destino": "Uinf", "etiqueta": "1/hetot", "lazo": False},
            {"origen": "dTi", "destino": "RaD", "etiqueta": "dTi", "lazo": False},
            {"origen": "RaD", "destino": "Nui", "etiqueta": "RaD^(1/3)", "lazo": False},
            {"origen": "Nui", "destino": "hi", "etiqueta": "fcal·ka/D", "lazo": False},
            {"origen": "hi", "destino": "Usup", "etiqueta": "1/hi", "lazo": False},
            {"origen": "hi", "destino": "Uinf", "etiqueta": "1/hi", "lazo": False},
            {"origen": "dTcel", "destino": "Rae", "etiqueta": "e³", "lazo": False},
            {"origen": "Rae", "destino": "Nuc", "etiqueta": "Hollands", "lazo": False},
            {"origen": "Nuc", "destino": "Usup", "etiqueta": "ncapS/hc", "lazo": False},
            {"origen": "Usup", "destino": "U", "etiqueta": "½ Usup", "lazo": False},
            {"origen": "Uinf", "destino": "U", "etiqueta": "½ Uinf", "lazo": False},
            {"origen": "Usup", "destino": "dTcel", "etiqueta": "↺ dTcel(Usup)", "lazo": True},
            {"origen": "U", "destino": "dTi", "etiqueta": "↺ (U/hi)·dT", "lazo": True},
        ],
    },
    {
        "titulo_corto": "Pérdidas y Enfriamiento",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 2},
        "resumen": (
            "Compara la potencia calorífica perdida sin aislante (Qp0) frente a la del casco con aislante (Qp), "
            "evalúa la fracción de ahorro térmico (fais) y la dinámica de enfriamiento pasivo sin quemador."
        ),
        "flujo_interno": (
            "Multiplicando U0 y U por S·dT se obtienen las potencias térmicas Qp0 y Qp; su diferencia define el ahorro "
            "instantáneo dQp y el porcentaje fais. En paralelo, Qp y la capacidad calorífica efectiva regional Q/dT dan la tasa de "
            "enfriamiento vT, la energía Qc y el tiempo tc para agotar la caída admisible dTc."
        ),
        "nodos": [
            {"eq": "Potencia perdida sin capa celular (Qp0)", "var": "Qp0", "etiqueta": "Potencia base Qp0", "capa": 0},
            {"eq": "Potencia perdida con capa celular (Qp)", "var": "Qp", "etiqueta": "Potencia aislada Qp", "capa": 0},
            {"eq": "Energía cedida en caída admisible", "var": "Qc", "etiqueta": "Reserva térmica Qc", "capa": 0},
            {"eq": "Potencia ahorrada por capa celular (dQp)", "var": "dQp", "etiqueta": "Ahorro Qp0 - Qp", "capa": 1},
            {"eq": "Velocidad de enfriamiento (dT/dt)", "var": "vT", "etiqueta": "Tasa dT/dt", "capa": 1},
            {"eq": "Fracción de ahorro térmico celular (fais)", "var": "fais", "etiqueta": "Fracción fais", "capa": 2},
            {"eq": "Tiempo de enfriamiento sin aporte", "var": "tc", "etiqueta": "Enfriamiento log. tc", "capa": 2},
        ],
        "aristas_internas": [
            {"origen": "Qp0", "destino": "dQp", "etiqueta": "Qp0 - Qp", "lazo": False},
            {"origen": "Qp", "destino": "dQp", "etiqueta": "resta", "lazo": False},
            {"origen": "dQp", "destino": "fais", "etiqueta": "dQp / Qp0", "lazo": False},
            {"origen": "Qp0", "destino": "fais", "etiqueta": "base", "lazo": False},
            {"origen": "Qp", "destino": "vT", "etiqueta": "Qp / (Q/dT)", "lazo": False},
            {"origen": "Qp", "destino": "tc", "etiqueta": "ln(ΔT/(ΔT-dTc))", "lazo": False},
            {"origen": "Qc", "destino": "tc", "etiqueta": "C_ef = Q/ΔT", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Precalentamiento y Quemador",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 3},
        "resumen": (
            "Cuantifica la energía y el bajo costo del precalentamiento inicial en tierra (Epre, Cpre) y "
            "calcula las pérdidas térmicas integradas en vuelo y el consumo de combustible térmico."
        ),
        "flujo_interno": (
            "En tierra se calcula Epre = Q/npre y su costo Cpre. En vuelo, el tiempo tm = dm/vg integra Em0, Em y Eah; "
            "Em/ncal define Eprop y el consumo mgm = Eprop/PC para mantener T2 durante los nv viajes."
        ),
        "nodos": [
            {"eq": "Distancia recorrida en misión (dm)", "var": "dm", "etiqueta": "Misión dm = vg·tm", "capa": 0},
            {"eq": "Energía de precalentamiento en tierra (Epre)", "var": "Epre", "etiqueta": "Tierra Epre = Q/npre", "capa": 0},
            {"eq": "Costo de precalentamiento en tierra (Cpre)", "var": "Cpre", "etiqueta": "Costo tierra Cpre", "capa": 1},
            {"eq": "Energía perdida sin aislante en misión", "var": "Em0", "etiqueta": "Pérdida base Em0", "capa": 1},
            {"eq": "Energía perdida con aislante en misión", "var": "Em", "etiqueta": "Pérdida real Em", "capa": 1},
            {"eq": "Energía ahorrada gracias al aislante", "var": "Eah", "etiqueta": "Ahorro térmico Eah", "capa": 1},
            {"eq": "Masa de combustible térmico para recuperar caída dTc", "var": "mgc", "etiqueta": "Comb. caída dTc", "capa": 1},
            {"eq": "Energía suministrada por combustible térmico en misión (Eprop)", "var": "Eprop", "etiqueta": "Energía comb. Em/ncal", "capa": 2},
            {"eq": "Masa de combustible térmico para mantener T en misión", "var": "mgm", "etiqueta": "Consumo vuelo mgm", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "Epre", "destino": "Cpre", "etiqueta": "× cpre", "lazo": False},
            {"origen": "dm", "destino": "Em0", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "dm", "destino": "Em", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "dm", "destino": "Eah", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "Em", "destino": "Eprop", "etiqueta": "Em / ncal", "lazo": False},
            {"origen": "Eprop", "destino": "mgm", "etiqueta": "Eprop / PC", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Multi-Viaje, Viento y Arrastre",
        "grupo": "aerodinamica",
        "pos_global": {"fila": 2, "col": 0},
        "resumen": (
            "Integra la distancia multi-viaje dm = nv·d1 con la velocidad efectiva vg = v - vv para fijar tm, "
            "y calcula la resistencia aerodinámica volumétrica de Hoerner FD y el trabajo ED."
        ),
        "flujo_interno": (
            "dm = nv·d1 y vg = v - vv determinan el tiempo total de misión tm = dm/vg. En paralelo, v fija ReL, "
            "la fricción turbulenta Cf, el coeficiente CDVc(lam), el total CDV = kp·CDVc, la fuerza FD y ED."
        ),
        "nodos": [
            {"eq": "Velocidad neta de avance respecto al suelo (vg)", "var": "vg", "etiqueta": "Velocidad suelo v - vv", "capa": 0},
            {"eq": "Distancia total por viajes (nv·d1)", "var": "dm", "etiqueta": "Distancia dm = nv·d1", "capa": 0},
            {"eq": "Número de Reynolds longitudinal (ReL)", "var": "ReL", "etiqueta": "Reynolds ReL", "capa": 0},
            {"eq": "Distancia recorrida en misión (dm)", "var": "tm", "etiqueta": "Tiempo total dm/vg", "capa": 1},
            {"eq": "Coeficiente de fricción superficial (Cf)", "var": "Cf", "etiqueta": "Fricción piel Cf", "capa": 1},
            {"eq": "Coeficiente volumétrico del casco (CDVc - Hoerner)", "var": "CDVc", "etiqueta": "Casco Hoerner CDVc", "capa": 2},
            {"eq": "Coeficiente de resistencia volumétrico total (CDV)", "var": "CDV", "etiqueta": "Total CDV = kp·CDVc", "capa": 3},
            {"eq": "Fuerza de resistencia aerodinámica (FD)", "var": "FD", "etiqueta": "Arrastre FD", "capa": 4},
            {"eq": "Energía perdida por resistencia aerodinámica (ED)", "var": "ED", "etiqueta": "Trabajo arrastre ED", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "vg", "destino": "tm", "etiqueta": "dm / vg", "lazo": False},
            {"origen": "dm", "destino": "tm", "etiqueta": "dm / vg", "lazo": False},
            {"origen": "ReL", "destino": "Cf", "etiqueta": "log10(ReL)", "lazo": False},
            {"origen": "Cf", "destino": "CDVc", "etiqueta": "f(λ)", "lazo": False},
            {"origen": "CDVc", "destino": "CDV", "etiqueta": "× kp", "lazo": False},
            {"origen": "CDV", "destino": "FD", "etiqueta": "½ρ₁v²·CDV", "lazo": False},
            {"origen": "FD", "destino": "ED", "etiqueta": "FD · v · tm", "lazo": False},
            {"origen": "tm", "destino": "ED", "etiqueta": "v · tm", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Masas y Sustentación",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 0},
        "resumen": (
            "Consolida la masa del artefacto (capas Mylar mc, motores, combustible, batería), añade "
            "la carga útil en mtot y determina la masa residual mres y la inercia aparente map = fap·(mtot + m)."
        ),
        "flujo_interno": (
            "Suma mc (C3) y mbat (lazo C13) con motores, combustible y componentes para hallar mart y mtot. "
            "Luego calcula map = fap·(mtot + m) incluyendo el gas interior y la carga residual mres = mtot - mflot."
        ),
        "nodos": [
            {"eq": "Masa de la cuadrícula celular", "var": "mc", "etiqueta": "Masa Mylar mc", "capa": 0},
            {"eq": "Masa de batería requerida (mbat)", "var": "mbat", "etiqueta": "Masa batería mbat", "capa": 0},
            {"eq": "Masa del artefacto con sus componentes (mart)", "var": "mart", "etiqueta": "Artefacto mart", "capa": 1},
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Fuerza globo F", "capa": 1},
            {"eq": "Masa total del dirigible con carga útil (mtot)", "var": "mtot", "etiqueta": "Masa total mtot", "capa": 2},
            {"eq": "Masa compensada por aire caliente (mflot)", "var": "mflot", "etiqueta": "Flotabilidad mflot", "capa": 2},
            {"eq": "Masa aparente traslacional (map)", "var": "map", "etiqueta": "Inercia fap·(mtot+m)", "capa": 3},
            {"eq": "Masa residual a compensar por motores (mres)", "var": "mres", "etiqueta": "Carga rotores mres", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "mc", "destino": "mart", "etiqueta": "+mc", "lazo": False},
            {"origen": "mbat", "destino": "mart", "etiqueta": "+mbat", "lazo": False},
            {"origen": "mart", "destino": "mtot", "etiqueta": "+mcarga", "lazo": False},
            {"origen": "mtot", "destino": "map", "etiqueta": "fap·(mtot+m)", "lazo": False},
            {"origen": "mtot", "destino": "mres", "etiqueta": "mtot - mflot", "lazo": False},
            {"origen": "F", "destino": "mflot", "etiqueta": "F / g", "lazo": False},
            {"origen": "mflot", "destino": "mres", "etiqueta": "-mflot", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Dinámica Vectorial",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 1},
        "resumen": (
            "Descompone las fuerzas de maniobra vertical (sustentación residual + ascenso) y horizontal (arrastre + inercia aparente) "
            "para hallar el empuje pico Ttot y el ángulo de inclinación theta frente a sus límites."
        ),
        "flujo_interno": (
            "Calcula las aceleraciones az y ax de maniobra. Con mres y map determina el empuje vertical FL; con FD (C8) "
            "y map determina la fuerza de avance FX. Su suma vectorial fija Ttot = √(FL² + FX²) y el ángulo de "
            "inclinación theta = atan(FX/FL), evaluando los márgenes de empuje dTtot y ángulo dth."
        ),
        "nodos": [
            {"eq": "Aceleración vertical de ascenso (az)", "var": "az", "etiqueta": "Aceleración az", "capa": 0},
            {"eq": "Aceleración horizontal de traslación (ax)", "var": "ax", "etiqueta": "Aceleración ax", "capa": 0},
            {"eq": "Fuerza de resistencia aerodinámica (FD)", "var": "FD", "etiqueta": "Arrastre FD", "capa": 0},
            {"eq": "Componente vertical de sustentación de motores (FL)", "var": "FL", "etiqueta": "Empuje vertical FL", "capa": 1},
            {"eq": "Componente horizontal de avance de motores (FX)", "var": "FX", "etiqueta": "Empuje avance FX", "capa": 1},
            {"eq": "Empuje vectorial total de los 4 motores (Ttot)", "var": "Ttot", "etiqueta": "Empuje pico Ttot", "capa": 2},
            {"eq": "Ángulo de rotación respecto a la vertical (theta)", "var": "theta", "etiqueta": "Inclinación maniobra θ", "capa": 2},
            {"eq": "Ángulo de rotación en crucero estacionario (thcruc)", "var": "thcruc", "etiqueta": "Inclinación crucero θcruc", "capa": 2},
            {"eq": "Margen de empuje disponible de los 4 motores (dTtot)", "var": "dTtot", "etiqueta": "Margen dTtot", "capa": 3},
            {"eq": "Margen respecto al ángulo máximo de rotación (dth)", "var": "dth", "etiqueta": "Margen angular dth", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "az", "destino": "FL", "etiqueta": "map·az", "lazo": False},
            {"origen": "ax", "destino": "FX", "etiqueta": "map·ax", "lazo": False},
            {"origen": "FD", "destino": "FX", "etiqueta": "+map·ax", "lazo": False},
            {"origen": "FD", "destino": "thcruc", "etiqueta": "atan(FD/mres·g)", "lazo": False},
            {"origen": "FL", "destino": "Ttot", "etiqueta": "√(FL²+FX²)", "lazo": False},
            {"origen": "FX", "destino": "Ttot", "etiqueta": "√(FL²+FX²)", "lazo": False},
            {"origen": "FL", "destino": "theta", "etiqueta": "atan(FX/FL)", "lazo": False},
            {"origen": "FX", "destino": "theta", "etiqueta": "atan(FX/FL)", "lazo": False},
            {"origen": "Ttot", "destino": "dTtot", "etiqueta": "N·Tmax1-Ttot", "lazo": False},
            {"origen": "theta", "destino": "dth", "etiqueta": "thmax-max(θ)", "lazo": False},
            {"origen": "thcruc", "destino": "dth", "etiqueta": "thmax-max(θ)", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Eficiencia y Potencia",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 2},
        "resumen": (
            "Evalúa la reserva de sustentación vertical (FLmax, Fexc), la caída cuadrática de eficiencia de la hélice "
            "con la velocidad v hacia vpitch, la potencia eléctrica pico de maniobra (Pelec) y la de crucero (Pcruc)."
        ),
        "flujo_interno": (
            "La capacidad de los rotores menos el avance FX deja FLmax y el excedente Fexc. Por otro lado, "
            "dp fija Ap y la velocidad v degrada nprop hasta ntot = nprop·nm·nESC. "
            "Ttot fija el pico Pelec frente a Pmax = N·Pmax1, mientras Tcruc y FD fijan la potencia continua de crucero Pcruc."
        ),
        "nodos": [
            {"eq": "Empuje vectorial total de los 4 motores (Ttot)", "var": "Ttot", "etiqueta": "Empuje pico Ttot", "capa": 0},
            {"eq": "Área de disco barrida por cada hélice (Ap)", "var": "Ap", "etiqueta": "Área disco Ap", "capa": 0},
            {"eq": "Eficiencia aerodinámica de hélice según velocidad (nprop)", "var": "nprop", "etiqueta": "Eficiencia nprop(v)", "capa": 0},
            {"eq": "Sustentación vertical máxima de los 4 motores (FLmax)", "var": "FLmax", "etiqueta": "Máx. vertical FLmax", "capa": 1},
            {"eq": "Empuje vectorial en crucero estacionario (Tcruc)", "var": "Tcruc", "etiqueta": "Empuje crucero Tcruc", "capa": 1},
            {"eq": "Eficiencia propulsiva global (ntot)", "var": "ntot", "etiqueta": "Eficiencia ntot", "capa": 1},
            {"eq": "Potencia eléctrica máxima continua de 4 motores (Pmax)", "var": "Pmax", "etiqueta": "Límite Pmax", "capa": 1},
            {"eq": "Excedente de sustentación total (Fexc)", "var": "Fexc", "etiqueta": "Excedente Fexc", "capa": 2},
            {"eq": "Potencia eléctrica demandada por los 4 motores (Pelec)", "var": "Pelec", "etiqueta": "Potencia pico Pelec", "capa": 2},
            {"eq": "Potencia eléctrica motriz en crucero estacionario (Pcruc)", "var": "Pcruc", "etiqueta": "Potencia crucero Pcruc", "capa": 2},
            {"eq": "Margen de potencia eléctrica de los motores (dPelec)", "var": "dPelec", "etiqueta": "Margen dPelec", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "FLmax", "destino": "Fexc", "etiqueta": "F+FLmax-mg", "lazo": False},
            {"origen": "nprop", "destino": "ntot", "etiqueta": "× nm·nESC", "lazo": False},
            {"origen": "Ttot", "destino": "Pelec", "etiqueta": "Ttot^(3/2)", "lazo": False},
            {"origen": "Ap", "destino": "Pelec", "etiqueta": "disco N·Ap", "lazo": False},
            {"origen": "ntot", "destino": "Pelec", "etiqueta": "km / ntot", "lazo": False},
            {"origen": "Tcruc", "destino": "Pcruc", "etiqueta": "Tcruc^(3/2)", "lazo": False},
            {"origen": "Ap", "destino": "Pcruc", "etiqueta": "disco N·Ap", "lazo": False},
            {"origen": "ntot", "destino": "Pcruc", "etiqueta": "km / ntot", "lazo": False},
            {"origen": "Pelec", "destino": "dPelec", "etiqueta": "Pmax-Pelec", "lazo": False},
            {"origen": "Pmax", "destino": "dPelec", "etiqueta": "Pmax", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Balance Energético y Costos",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 3},
        "resumen": (
            "Integra la energía eléctrica diferenciando maniobras pico (Ptot durante tman) y crucero estacionario "
            "(Pcruc + Pad durante tm - tman), suma Eprop en Etot y consolida el costo operativo total Cop."
        ),
        "flujo_interno": (
            "Ptot = Pelec + Pad actúa durante el tiempo acumulado de maniobras tman = min(tm, nv·ta), y Pcruc + Pad "
            "durante el crucero restante para obtener Ereq (Wh), Eelec (J) y Celec. Sumando Eelec + Eprop resulta Etot."
        ),
        "nodos": [
            {"eq": "Potencia eléctrica demandada por los 4 motores (Pelec)", "var": "Pelec", "etiqueta": "Potencia pico Pelec", "capa": 0},
            {"eq": "Potencia eléctrica motriz en crucero estacionario (Pcruc)", "var": "Pcruc", "etiqueta": "Potencia crucero Pcruc", "capa": 0},
            {"eq": "Costo de precalentamiento en tierra (Cpre)", "var": "Cpre", "etiqueta": "Costo tierra Cpre", "capa": 0},
            {"eq": "Potencia eléctrica total a bordo (Ptot)", "var": "Ptot", "etiqueta": "Pico Pelec + Pad", "capa": 1},
            {"eq": "Tiempo acumulado de maniobras en misión (tman)", "var": "tman", "etiqueta": "Maniobras min(tm,nv·ta)", "capa": 1},
            {"eq": "Energía suministrada por combustible térmico en misión (Eprop)", "var": "Eprop", "etiqueta": "Energía comb. Eprop", "capa": 1},
            {"eq": "Energía perdida por resistencia aerodinámica (ED)", "var": "ED", "etiqueta": "Arrastre ED", "capa": 1},
            {"eq": "Energía eléctrica requerida en misión (Ereq)", "var": "Ereq", "etiqueta": "Energía (Wh) Ereq", "capa": 2},
            {"eq": "Energía eléctrica total usada en misión (Eelec)", "var": "Eelec", "etiqueta": "Eléctrica (J) Eelec", "capa": 3},
            {"eq": "Coste energético eléctrico por distancia (celec)", "var": "celec", "etiqueta": "Coste celec", "capa": 3},
            {"eq": "Costo de recarga eléctrica de batería (Celec)", "var": "Celec", "etiqueta": "Costo batería Celec", "capa": 3},
            {"eq": "Energía total consumida en misión (Etot)", "var": "Etot", "etiqueta": "Global Etot", "capa": 4},
            {"eq": "Costo de combustible térmico en vuelo (Ccomb)", "var": "Ccomb", "etiqueta": "Costo comb. Ccomb", "capa": 4},
            {"eq": "Coste energético total por distancia (ctot)", "var": "ctot", "etiqueta": "Coste total ctot", "capa": 5},
            {"eq": "Costo operativo total de misión (Cop)", "var": "Cop", "etiqueta": "Total Cop (Bs)", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "Pelec", "destino": "Ptot", "etiqueta": "+ Pad", "lazo": False},
            {"origen": "Ptot", "destino": "Ereq", "etiqueta": "× tman/3600", "lazo": False},
            {"origen": "Pcruc", "destino": "Ereq", "etiqueta": "× (tm-tman)", "lazo": False},
            {"origen": "tman", "destino": "Ereq", "etiqueta": "peso fase", "lazo": False},
            {"origen": "Ereq", "destino": "Eelec", "etiqueta": "× 3600", "lazo": False},
            {"origen": "Ereq", "destino": "celec", "etiqueta": "Ereq / dm", "lazo": False},
            {"origen": "Ereq", "destino": "Celec", "etiqueta": "× celecU", "lazo": False},
            {"origen": "Eelec", "destino": "Etot", "etiqueta": "+Eelec", "lazo": False},
            {"origen": "Eprop", "destino": "Etot", "etiqueta": "+Eprop", "lazo": False},
            {"origen": "Etot", "destino": "ctot", "etiqueta": "Etot / dm", "lazo": False},
            {"origen": "Cpre", "destino": "Cop", "etiqueta": "+Cpre", "lazo": False},
            {"origen": "Ccomb", "destino": "Cop", "etiqueta": "+Ccomb", "lazo": False},
            {"origen": "Celec", "destino": "Cop", "etiqueta": "+Celec", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Batería y Lazo Cerrado",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 4},
        "resumen": (
            "Dimensiona la batería por doble criterio exacto —energía de misión (mbe) y potencia pico total "
            "(mbp)— tomando mbat = max(mbe, mbp), verifica el margen dmbat y retroalimenta mart en C9."
        ),
        "flujo_interno": (
            "Ereq (Wh) exige una masa por energía mbe considerando DoD; Ptot (W) exige una masa por descarga "
            "continua mbp según Cmax. El valor exacto max(mbe, mbp) fija mbat, verificado frente a mbmax en dmbat, "
            "y entra en mart (C9) cerrando el lazo acoplado masa ↔ empuje ↔ potencia ↔ batería."
        ),
        "nodos": [
            {"eq": "Potencia eléctrica total a bordo (Ptot)", "var": "Ptot", "etiqueta": "Total Pelec + Pad", "capa": 0},
            {"eq": "Energía eléctrica requerida en misión (Ereq)", "var": "Ereq", "etiqueta": "Energía Ereq", "capa": 0},
            {"eq": "Masa de batería por potencia pico (mbp)", "var": "mbp", "etiqueta": "Criterio potencia mbp", "capa": 1},
            {"eq": "Masa de batería por energía de misión (mbe)", "var": "mbe", "etiqueta": "Criterio energía mbe", "capa": 1},
            {"eq": "Masa de batería requerida (mbat)", "var": "mbat", "etiqueta": "Batería max(mbe, mbp)", "capa": 2},
            {"eq": "Margen respecto al peso máximo de batería (dmbat)", "var": "dmbat", "etiqueta": "Margen dmbat", "capa": 3},
            {"eq": "Masa del artefacto con sus componentes (mart)", "var": "mart", "etiqueta": "Retroalimenta mart", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "Ptot", "destino": "mbp", "etiqueta": "÷(ebat·Cmax)", "lazo": False},
            {"origen": "Ereq", "destino": "mbe", "etiqueta": "÷(ebat·DoD)", "lazo": False},
            {"origen": "mbp", "destino": "mbat", "etiqueta": "max(e,p)", "lazo": False},
            {"origen": "mbe", "destino": "mbat", "etiqueta": "max(e,p)", "lazo": False},
            {"origen": "mbat", "destino": "dmbat", "etiqueta": "mbmax-mbat", "lazo": False},
            {"origen": "mbat", "destino": "mart", "etiqueta": "+mbat", "lazo": False},
            {"origen": "mart", "destino": "Ptot", "etiqueta": "↺ C9→C12", "lazo": True},
        ],
    },
]


TIPOS_BLOQUES_NOTA: list[tuple[str, str]] = [
    ("ecuacion", "Ecuación"),
    ("variables", "Variables"),
    ("coeficientes", "Coeficientes"),
    ("criterio", "Criterio / Alcance"),
]
_TIPOS_VALIDOS_NOTA = {k for k, _ in TIPOS_BLOQUES_NOTA}


NOTAS_ECUACIONES: dict[str, dict[str, str]] = {
    # --- C1: Gases ideales, aire caliente y flotabilidad ---
    "Gas ideal (caso 1 - ambiente)": {
        "ecuacion": (
            "Aplica la ley de los gases ideales para determinar la densidad del aire frío exterior ρ₁ a la presión atmosférica P₁ "
            "y temperatura ambiente T₁."
        ),
        "variables": (
            "R₁ representa la constante específica del aire seco (Rair = 287.058 J/(kg·K)), obtenida al dividir la constante universal "
            "de los gases (8.3145 J/(mol·K)) entre la masa molar media del aire (0.028965 kg/mol)."
        ),
        "coeficientes": (
            "273.15 K convierte la temperatura de °C a escala absoluta Kelvin, requisito obligatorio de la ecuación de estado."
        ),
    },
    "Gas ideal (caso 2 - caliente)": {
        "ecuacion": (
            "Calcula la densidad del aire caliente interior ρ₂ cuando el gas se calienta a T₂. Al ser un casco no rígido, "
            "la presión interior P₂ iguala prácticamente a la atmosférica P₁ y la densidad cae."
        ),
    },
    "Densidad media del aire en celdas aislantes": {
        "ecuacion": (
            "Calcula la densidad media rhocel del aire encerrado en las capas celulares aislantes a temperatura media Tm."
        ),
        "criterio": (
            "Como las celdas están entre la cavidad caliente T₂ y el exterior T₁, su aire es más frío y denso que el núcleo ρ₂."
        ),
    },
    "Diferencia de densidades": {
        "ecuacion": (
            "Cuantifica el contraste de densidad Δρ = ρ₁ − ρ₂ entre el aire exterior frío y el aire interior caliente, "
            "que es la fuente física de flotabilidad aerostática por cada metro cúbico de casco."
        ),
    },
    "Masa de aire caliente": {
        "ecuacion": (
            "Calcula la masa total m del aire contenido dentro del dirigible sumando el núcleo caliente (ρ₂·Vnuc) y el aire periférico "
            "en las celdas aislantes (rhocel·Vcel)."
        ),
    },
    "Calor sensible": {
        "ecuacion": (
            "Calcula la energía térmica almacenada por regiones en el aire interior respecto a T₁: el núcleo Vnuc se calienta todo ΔT = T₂ − T₁, "
            "mientras el aire en las celdas Vcel a temperatura media (T₁ + T₂)/2 aporta ΔT/2."
        ),
        "variables": (
            "cp (1005 J/(kg·K)) es el calor específico a presión constante del aire; ρ₂·Vnuc y rhocel·Vcel son las masas regionales a masas finales."
        ),
    },
    "Fuerza de sustentación aerostática": {
        "ecuacion": (
            "Empuje hidrostático de Arquímedes por regiones: F = g·[(ρ₁ − ρ₂)·Vnuc + (ρ₁ − rhocel)·Vcel]."
        ),
        "criterio": (
            "Descuenta la menor flotabilidad de la corona de celdas aislantes (a densidad media rhocel > ρ₂), evitando sobreestimar "
            "la sustentación cuando aumentan el espesor e o el número de capas."
        ),
    },
    "Masa compensada por aire caliente (mflot)": {
        "ecuacion": (
            "Convierte el empuje aerostático F en kilogramos de masa sostenidos gratuitamente por el aire caliente (mflot = F/g). "
            "El peso restante (mres = mtot − mflot) lo sostienen los rotores."
        ),
    },
    # --- C2: Dimensiones principales y volumen ---
    "Relación de esbeltez (L/D)": {
        "ecuacion": (
            "Define la esbeltez geométrica λ = L/D del dirigible."
        ),
        "criterio": (
            "Valores bajos (λ ≈ 2–3) minimizan el área superficial S para un mismo volumen V (reduciendo pérdidas de calor); "
            "valores más altos reducen el arrastre de forma aerodinámico a mayor velocidad."
        ),
    },
    "Fracción de nariz (cf/L)": {
        "ecuacion": (
            "Reparte la longitud total L entre el semielipsoide frontal de nariz (cf = xf·L) y el trasero de popa (cr = (1 − xf)·L) "
            "sin alterar el volumen total V."
        ),
    },
    "Volumen total del casco": {
        "ecuacion": (
            "Calcula el volumen exterior total V desplazado por dos semielipsoides prolados de revolución unidos por su círculo máximo de radio R."
        ),
        "coeficientes": (
            "El factor 2/3·π proviene de sumar los volúmenes de ambos semielipsoides: (2/3)·π·R²·cf + (2/3)·π·R²·cr = (2/3)·π·R²·(cf + cr) = (2/3)·π·R²·L."
        ),
    },
    "Volumen del núcleo interior caliente": {
        "ecuacion": (
            "Calcula el volumen interno Vnuc que queda libre a temperatura plena T₂ tras restar radial y axialmente los espesores asimétricos "
            "ncapS·e (mitad superior) y ncapI·e (mitad inferior)."
        ),
    },
    "Volumen ocupado por celdas aislantes": {
        "ecuacion": (
            "Obtiene por diferencia geométrica el volumen periférico Vcel = V − Vnuc ocupado por el aire estratificado en las celdas Mylar."
        ),
    },
    # --- C3: Superficies del casco y capas Mylar ---
    "Excentricidad frontal (cf > R)": {
        "ecuacion": (
            "Mide el alargamiento geométrico del semielipsoide de proa respecto a una semiesfera (ef = 0)."
        ),
        "criterio": (
            "Exige estrictamente cf > R (esbeltez prolada) para que √(1 − R²/cf²) tome un valor real positivo."
        ),
    },
    "Excentricidad trasera (cr > R)": {
        "ecuacion": (
            "Mide el alargamiento del semielipsoide de popa respecto a una semiesfera (er = 0); requiere cr > R."
        ),
    },
    "Área superficial frontal": {
        "ecuacion": (
            "Calcula el área curva exacta del semielipsoide prolado de nariz: π·R² + π·R·cf·arcsin(ef)/ef."
        ),
        "coeficientes": (
            "Al integrar la superficie curva de revolución aparecen dos términos (ambos corresponden solo a la cáscara exterior, sin disco ecuatorial); "
            "cuando cf → R (semiesfera, ef → 0), el área converge exactamente a π·R² + π·R² = 2·π·R²."
        ),
    },
    "Área superficial trasera": {
        "ecuacion": (
            "Calcula el área curva exacta del semielipsoide prolado de popa mediante π·R² + π·R·cr·arcsin(er)/er; sumada a Sf da la envolvente exterior S."
        ),
    },
    "Número promedio de capas celulares (ncap)": {
        "ecuacion": (
            "Promedia el número de capas superiores ncapS y el de capas inferiores ncapI para obtener el espesor medio equivalente del "
            "aislamiento asimétrico y dimensionar la superficie total de película."
        ),
    },
    "Área total de película celular": {
        "ecuacion": (
            "Calcula la superficie real de película Mylar sumando la piel exterior (1·S) más todas las láminas y tabiques celulares internos: "
            "Sc = S·[1 + ncap·(1 + 2·e/W)]."
        ),
        "coeficientes": (
            "Incluir la piel exterior mantiene coherencia exacta con las ncap + 1 películas del modelo térmico y con el caso base sin aislamiento (0/0 → Sc = S). "
            "Cada celda de paso W y altura e aporta dos tabiques ortogonales de fracción 2·e/W."
        ),
    },
    "Masa de la cuadrícula celular": {
        "ecuacion": (
            "Calcula el peso total de la envolvente multicapa multiplicando el área real desarrollada Sc por el gramaje superficial σ del Mylar."
        ),
    },
    # --- C4: Convección externa, radiación y modelo térmico base (U0) ---
    "Número de Prandtl del aire (Pr)": {
        "ecuacion": (
            "Calcula el número adimensional de Prandtl del aire: Pr = ν/α."
        ),
        "variables": (
            "ν es la viscosidad cinemática (difusión de movimiento) y α es la difusividad térmica (difusión de calor). "
            "Para el aire vale ~0.70–0.72 y acopla la capa límite hidrodinámica con la térmica."
        ),
    },
    "Número de Nusselt externo por viento (Nue)": {
        "ecuacion": (
            "Evalúa la transferencia convectiva forzada causada por el viento relativo v a lo largo de la envolvente exterior en régimen turbulento."
        ),
        "variables": (
            "Nue = he·L/ka es el número de Nusselt externo: mide cuántas veces más calor transfiere el viento respecto a conducción pura "
            "a través de una capa de aire quieto de espesor L (~5.9 m). Un valor de ~2000–3000 significa que la capa límite turbulenta "
            "equivale térmicamente a una película inmóvil de solo L/Nue ≈ 2–3 mm. ReL mide inercia frente a viscosidad y Pr el acoplamiento del aire."
        ),
        "coeficientes": (
            "0.037 proviene de integrar sobre toda la longitud L la correlación turbulenta local sobre placa plana (Nu_x = 0.0296·Re_x^(4/5)·Pr^(1/3)): "
            "al integrar x^(−1/5) entre 0 y L aparece el factor 5/4, y (5/4) × 0.0296 = 0.037. Los exponentes 4/5 y 1/3 reflejan capa límite turbulenta "
            "y analogía de Chilton–Colburn."
        ),
    },
    "Coeficiente convectivo externo del casco (he)": {
        "ecuacion": (
            "Convierte el número adimensional externo Nue en coeficiente convectivo físico he = Nue·ka/L."
        ),
        "variables": (
            "he representa la potencia térmica disipada al aire exterior por cada m² de superficie y por cada Kelvin de salto térmico; "
            "ka es la conductividad térmica del aire."
        ),
    },
    "Coeficiente radiativo externo del casco (hrade)": {
        "ecuacion": (
            "Calcula la conductancia linealizada de pérdida por radiación infrarroja desde la piel exterior del casco hacia el entorno a T₁."
        ),
        "variables": (
            "eps (ε) es la emisividad infrarroja de la piel exterior y (T₁ + 273.15) es la temperatura ambiente absoluta en Kelvin."
        ),
        "coeficientes": (
            "El factor 4 proviene de linealizar la ley de Stefan–Boltzmann q_rad = ε·σ_SB·(Ts⁴ − T₁⁴) usando d(T⁴)/dT = 4·T³; "
            "σ_SB = 5.6704×10⁻⁸ W/(m²·K⁴) es la constante física universal de radiación térmica."
        ),
        "criterio": (
            "Con Mylar aluminizado (ε = 0.04) resulta muy bajo (~0.22 W/(m²·K)) frente a un plástico opaco (ε ≈ 0.90 → ~5 W/(m²·K))."
        ),
    },
    "Coeficiente externo total del casco (hetot)": {
        "ecuacion": (
            "Suma la convección forzada externa he y la radiación externa hrade porque ambos mecanismos actúan en paralelo desde la superficie exterior."
        ),
    },
    "Caída térmica interna sin capa celular (dTi0)": {
        "ecuacion": (
            "Por continuidad de flujo térmico en serie, el salto de temperatura dTi0 en la capa límite interior es proporcional "
            "a la fracción que representa la resistencia interna 1/hi0 dentro de la resistencia total 1/U0."
        ),
    },
    "Número de Rayleigh interno sin capa celular (RaD0)": {
        "ecuacion": (
            "RaD0 = g·β·dTi0·D³/(ν·α) mide la intensidad de la convección natural interna en el casco sin aislar."
        ),
        "variables": (
            "Compara el empuje térmico de flotabilidad (g·β·dTi0·D³) frente al frenado viscoso (ν) y térmico (α) del aire caliente."
        ),
        "criterio": (
            "Al depender de D³ y superar 10⁹ en cascos de escala métrica, confirma que el flujo convectivo interno es completamente turbulento."
        ),
    },
    "Número de Nusselt interno sin capa celular (Nui0)": {
        "ecuacion": (
            "Calcula el número de Nusselt interno sin aislante mediante la correlación turbulenta natural Nui0 = 0.13·RaD0^(1/3)."
        ),
        "variables": (
            "Nui0 indica cuántas veces mayor es el intercambio térmico convectivo interno frente a la conducción pura en un espesor D."
        ),
        "coeficientes": (
            "La constante empírica 0.13 y el exponente 1/3 corresponden a convección natural turbulenta en recintos grandes (Ra > 10⁹); "
            "con ese exponente D³^(1/3) = D, cancelando el diámetro en hi0 porque la transferencia pasa a depender de la flotabilidad local."
        ),
    },
    "Coeficiente convectivo interno sin capa celular (hi0)": {
        "ecuacion": (
            "Convierte Nui0 en el coeficiente convectivo interno físico hi0 = fcal·Nui0·ka/D para el casco sin aislar."
        ),
        "coeficientes": (
            "El factor fcal (~1.275) recoge la agitación adicional generada por la cámara mezcladora y difusor suave del quemador de etanol."
        ),
    },
    "Coeficiente global sin capa celular (U0)": {
        "ecuacion": (
            "Transmitancia térmica total en serie del casco simple de referencia: 1/U0 = 1/hi0 + ep/ke + 1/hetot."
        ),
        "criterio": (
            "Se mantiene estrictamente independiente de las variables de aislamiento (e, W, ncapS, ncapI, Nuc, hrad) "
            "para que la comparación del ahorro térmico frente a U sea siempre exacta."
        ),
    },
    # --- C5: Aislamiento Mylar multicapa asimétrico y radiación interna (U) ---
    "Caída térmica interna con capa celular (dTi)": {
        "ecuacion": (
            "Calcula qué porción del salto térmico total ΔT cae en la capa límite interna del casco aislado: dTi = (U/hi)·ΔT."
        ),
        "criterio": (
            "Al caer drásticamente la transmitancia global U gracias al Mylar multicapa, se reduce el flujo térmico que cruza la pared y baja dTi."
        ),
    },
    "Número de Rayleigh interno con capa celular (RaD)": {
        "ecuacion": (
            "Evalúa la fuerza de la convección natural dentro de la cavidad principal del dirigible cuando ya cuenta con aislamiento Mylar."
        ),
        "variables": (
            "RaD es el número de Rayleigh interno referido al diámetro D: compara las fuerzas de flotabilidad térmica (g·β·dTi·D³) "
            "frente a la viscosidad cinemática ν y la difusividad térmica α del aire, utilizando la caída interna amortiguada dTi."
        ),
        "criterio": (
            "Aunque dTi disminuye respecto al casco sin aislar, RaD sigue estando por encima de 10⁹ en diámetros de ~2.5 m (régimen turbulento)."
        ),
    },
    "Número de Nusselt interno con capa celular (Nui)": {
        "ecuacion": (
            "Calcula la intensidad adimensional de la convección natural dentro del casco aislado."
        ),
        "variables": (
            "Nui es el número de Nusselt interno: expresa cuántas veces supera la transferencia convectiva interna "
            "a la conducción térmica pura a través de un diámetro D de aire inmóvil."
        ),
        "coeficientes": (
            "El multiplicador empírico 0.13 y el exponente 1/3 corresponden al régimen turbulento de convección natural en grandes cavidades "
            "(Ra > 10⁹); como RaD^(1/3) ∝ D, el tamaño global D se cancela al pasar a hi porque la capa límite depende de la flotabilidad local."
        ),
    },
    "Coeficiente convectivo interno con capa celular (hi)": {
        "ecuacion": (
            "Traduce el Nusselt interno Nui a coeficiente convectivo físico hi = fcal·Nui·ka/D sobre la lámina interior del casco aislado."
        ),
        "coeficientes": (
            "fcal (~1.275) contempla la agitación moderada introducida por el sistema de recirculación y difusor del quemador de etanol."
        ),
    },
    "Temperatura media absoluta de pared (Tm)": {
        "ecuacion": (
            "Calcula la temperatura absoluta media (en Kelvin) entre el interior caliente T₂ y el exterior T₁ para linealizar la radiación intracelular."
        ),
        "coeficientes": (
            "Divide entre 2 la suma (T₁ + T₂) y suma 273.15 K para pasar a escala Kelvin."
        ),
    },
    "Emisividad efectiva entre láminas (epsef)": {
        "ecuacion": (
            "Calcula la emisividad efectiva del intercambio radiativo infrarrojo entre dos láminas planas paralelas enfrentadas de igual emisividad ε."
        ),
        "coeficientes": (
            "Al considerar las reflexiones múltiples entre ambas caras (cada superficie refleja 1 − ε), la resistencia radiativa combinada da "
            "epsef = ε/(2 − ε). Para Mylar aluminizado (ε = 0.04) resulta ≈ 0.0204 (casi la mitad de ε)."
        ),
    },
    "Coeficiente radiativo interno de cavidad (hrad)": {
        "ecuacion": (
            "Calcula la conductancia térmica por radiación infrarroja entre dos láminas vecinas de una celda aislante."
        ),
        "variables": (
            "epsef es la emisividad efectiva entre láminas enfrentadas y Tm es la temperatura media absoluta de la pared."
        ),
        "coeficientes": (
            "El coeficiente 4 surge de linealizar la diferencia de cuartas potencias en la ley de Stefan–Boltzmann, multiplicado por "
            "σ_SB = 5.6704×10⁻⁸ W/(m²·K⁴)."
        ),
        "criterio": (
            "Cada capa adicional de Mylar actúa como pantalla reflectora independiente en serie, y su baja emisividad reduce hrad ~40× frente a plástico opaco."
        ),
    },
    "Caída térmica en la celda aislante (dTcel)": {
        "ecuacion": (
            "Calcula la caída de temperatura individual ΔTcel que soporta cada una de las ncapS celdas superiores."
        ),
        "variables": (
            "Usup·ΔT es el flujo de calor constante que atraviesa toda la pared superior en serie; al dividirlo entre la conductancia de una sola celda "
            "(ka·Nuc/e + hrad), se obtiene exactamente la caída térmica de una celda individual."
        ),
        "criterio": (
            "Al aumentar ncapS disminuye Usup y se reparte el salto ΔT entre más celdas: pasar de 1 a 3 capas reduce ΔTcel a ~18.5 K, evitando que conveccione."
        ),
    },
    "Número de Rayleigh en cavidad celular (Rae)": {
        "ecuacion": (
            "Evalúa si el aire encerrado dentro de cada micro-celda superior tiende a moverse por flotabilidad térmica o permanece inmóvil."
        ),
        "variables": (
            "Rae es el número de Rayleigh local de la celda: depende del cubo del espesor de celda (e³) y de la caída individual dTcel."
        ),
        "criterio": (
            "Con capas finas (~14 mm), caída fraccionada en 3 celdas y la menor densidad del aire en altura (ν·α mayor en La Paz), "
            "Rae cae debajo de Rac = 1708 y suprime la convección intracelular."
        ),
    },
    "Número de Nusselt efectivo en celda (Nuc)": {
        "ecuacion": (
            "Correlación física de Hollands (1976) para cavidades cerradas calentadas desde abajo, determinando cuánta convección ocurre dentro de cada celda superior."
        ),
        "coeficientes": (
            "Los parámetros 1.44, Rac = 1708 (umbral crítico de Rayleigh–Bénard) y 5830 (transición turbulenta celular) ajustan los datos experimentales de Hollands; "
            "los términos max(0, ...) garantizan que, cuando Rae ≤ Rac, Nuc sea exactamente 1.000 (conducción pura, nunca menor a 1)."
        ),
    },
    "Coeficiente global mitad superior (Usup)": {
        "ecuacion": (
            "Transmitancia térmica en serie de la mitad superior del casco con ncapS capas de Mylar."
        ),
        "criterio": (
            "Integra en serie convección interior (1/hi), las ncapS + 1 láminas de película, ncapS celdas con convección (Nuc) y radiación interna (hrad) en paralelo, "
            "y el exterior (1/hetot). No hay doble conteo con hetot porque hrad actúa entre láminas internas y hrade solo en la piel exterior."
        ),
    },
    "Coeficiente global mitad inferior (Uinf)": {
        "ecuacion": (
            "Transmitancia térmica de la mitad inferior del casco con ncapI capas de Mylar."
        ),
        "criterio": (
            "Como el lado caliente está arriba y el frío abajo, el aire dentro de las celdas inferiores queda estratificado de forma estable sin convección (Nu = 1 exacto), "
            "manteniendo solo conducción pura ka/e y radiación interna hrad en paralelo."
        ),
    },
    "Coeficiente global con capa celular (U)": {
        "ecuacion": (
            "Promedia la transmitancia de la cúpula superior Usup y la mitad inferior Uinf para caracterizar la pérdida media global del dirigible."
        ),
        "criterio": (
            "Al invertir U para despejar el espesor e, pueden existir dos raíces físicas a ambos lados de Rac = 1708: una fina en conducción "
            "pura (Nuc = 1) y otra más gruesa con convección intracelular (Nuc > 1)."
        ),
    },
    # --- C6: Pérdidas de calor, ahorro del aislante y enfriamiento ---
    "Potencia perdida sin capa celular (Qp0)": {
        "ecuacion": (
            "Calcula la pérdida instantánea de calor (en W) que tendría el mismo casco si estuviera cubierto por una sola lámina de Mylar sin celdas aislantes."
        ),
    },
    "Potencia perdida con capa celular (Qp)": {
        "ecuacion": (
            "Calcula la potencia térmica real perdida hacia el ambiente (en W) con el aislamiento multicapa asimétrico instalado."
        ),
    },
    "Fracción de ahorro térmico celular (fais)": {
        "ecuacion": (
            "Mide la eficiencia relativa del aislamiento multicapa como fracción del calor ahorrado frente al casco simple (1 − U/U0)."
        ),
    },
    "Velocidad de enfriamiento (dT/dt)": {
        "ecuacion": (
            "Ritmo instantáneo de enfriamiento pasivo vT = Qp / C_ef = (Qp·ΔT)/Q si se apagara el quemador; usa la capacidad térmica efectiva regional C_ef = Q/ΔT."
        ),
    },
    "Tiempo de enfriamiento sin aporte": {
        "ecuacion": (
            "Integra analíticamente el decaimiento exponencial de temperatura desde ΔT hasta ΔT − dTc manteniendo el perfil lineal en la capa celular (C_ef = Q/ΔT): "
            "tc = (Q/Qp)·ln(ΔT/(ΔT − dTc))."
        ),
        "criterio": (
            "Coherente con el balance energético regional del calentamiento Q e impone el dominio físico dTc < ΔT."
        ),
    },
    # --- C7: Precalentamiento en tierra y quemador térmico ---
    "Energía de precalentamiento en tierra (Epre)": {
        "ecuacion": (
            "Calcula la energía primaria consumida en la estación de tierra para llevar el volumen V desde T₁ hasta T₂ antes del despegue."
        ),
        "variables": (
            "Q es el calor sensible útil que retiene el aire caliente y npre (~0.65) es el rendimiento del soplador/calentador externo con recirculación."
        ),
    },
    "Costo de precalentamiento en tierra (Cpre)": {
        "ecuacion": (
            "Traduce la energía de precalentamiento Epre a costo económico en tierra."
        ),
        "coeficientes": (
            "10⁶ convierte Joules a MegaJoules para multiplicar directamente por la tarifa en tierra cpre (Bs/MJ)."
        ),
    },
    "Masa de combustible térmico para recuperar caída dTc": {
        "ecuacion": (
            "Calcula la masa de combustible térmico requerida para reponer una caída térmica admisible dTc mediante la reserva energética Qc."
        ),
        "variables": (
            "PC es el poder calorífico inferior del combustible (25 MJ/kg calibrado para etanol al 96 %) y ncal (~0.75) el rendimiento del quemador."
        ),
    },
    "Energía suministrada por combustible térmico en misión (Eprop)": {
        "ecuacion": (
            "Divide la pérdida térmica neta en vuelo Em entre el rendimiento del quemador ncal para incluir pérdidas térmicas de mezcla y escape."
        ),
    },
    "Masa de combustible térmico para mantener T en misión": {
        "ecuacion": (
            "Calcula la masa total de combustible consumida en vuelo mgm = Eprop/PC para sostener T₂ constante durante toda la misión."
        ),
    },
    # --- C8: Cinemática multi-viaje, viento y arrastre aerodinámico ---
    "Velocidad neta de avance respecto al suelo (vg)": {
        "ecuacion": (
            "Calcula la velocidad efectiva sobre el terreno vg = v − vv descontando el viento frontal en contra vv a la velocidad aerodinámica v."
        ),
    },
    "Distancia total por viajes (nv·d1)": {
        "ecuacion": (
            "Define la distancia total recorrida dm multiplicando nv viajes consecutivos por el tramo unitario d1 (3 × 280 m = 840 m por defecto) para evaluar escalabilidad."
        ),
    },
    "Distancia recorrida en misión (dm)": {
        "ecuacion": (
            "Relaciona distancia total dm, velocidad neta sobre el suelo vg y duración total de vuelo tm."
        ),
        "criterio": (
            "Con viento en contra (vv > 0), avanzar más lento respecto al suelo eleva tm y penaliza el consumo energético en vuelo."
        ),
    },
    "Número de Reynolds longitudinal (ReL)": {
        "ecuacion": (
            "ReL = ρ₁·v·L/μ mide la razón entre fuerzas inerciales y viscosas del aire exterior que fluye alrededor del casco de longitud L."
        ),
        "variables": (
            "Usa la velocidad aerodinámica v (y no vg) porque la fricción y capa límite dependen del aire incidente relativo."
        ),
        "criterio": (
            "En el rango típico ReL ~ 10⁵–10⁶ el flujo exterior es turbulento y fija tanto Cf como Nue."
        ),
    },
    "Coeficiente de fricción superficial (Cf)": {
        "ecuacion": (
            "Calcula el coeficiente medio de fricción viscosa sobre la piel lisa del casco mediante la correlación de Prandtl–Schlichting."
        ),
        "coeficientes": (
            "Las constantes empíricas 0.455 y el exponente 2.58 sobre log10(ReL) corresponden específicamente al régimen de capa límite turbulenta sobre pared lisa."
        ),
    },
    "Coeficiente volumétrico del casco (CDVc - Hoerner)": {
        "ecuacion": (
            "Correlación clásica de Hoerner referida al área volumétrica V^(2/3), combinando resistencia por fricción superficial y arrastre de presión por forma."
        ),
        "coeficientes": (
            "Los términos 4·λ^(1/3), 6·λ^(−1.2) y 24·λ^(−2.7) capturan respectivamente el área mojada, la interacción del espesor y la separación de presión trasera en función de la esbeltez λ = L/D."
        ),
    },
    "Coeficiente de resistencia volumétrico total (CDV)": {
        "ecuacion": (
            "Multiplica el casco limpio CDVc por el factor de resistencia parásita kp (~1.45) para incluir góndola, brazos motores, cables, quemador e irregularidades."
        ),
    },
    "Fuerza de resistencia aerodinámica (FD)": {
        "ecuacion": (
            "Calcula la fuerza total de arrastre aerodinámico FD que frena el avance horizontal del dirigible."
        ),
        "variables": (
            "Se evalúa siempre con la velocidad aerodinámica v = vg + vv y el área de referencia volumétrica V^(2/3)."
        ),
        "coeficientes": (
            "El factor 1/2 proviene de la definición de presión dinámica ½·ρ₁·v²."
        ),
    },
    "Energía perdida por resistencia aerodinámica (ED)": {
        "ecuacion": (
            "Calcula la energía disipada contra la masa de aire circundante durante el vuelo: ED = FD·v·tm."
        ),
        "criterio": (
            "Emplea el recorrido aerodinámico v·tm (y no el desplazamiento sobre el suelo dm), por lo que permanece consistente con el trabajo útil FD·v en potencia cuando hay viento frontal."
        ),
    },
    # --- C9: Masas del dirigible y reparto híbrido ---
    "Masa del artefacto con sus componentes (mart)": {
        "ecuacion": (
            "Suma la masa de todas las partes propias de la aeronave: cuadrícula Mylar mc, N motores, depósito/quemador térmico mp, "
            "estructura/electrónica adicional mad y batería requerida mbat."
        ),
    },
    "Masa residual a compensar por motores (mres)": {
        "ecuacion": (
            "Determina el peso neto residual mres = mtot − mflot que excede al empuje del aire caliente y debe ser cargado verticalmente por los rotores."
        ),
    },
    "Masa aparente traslacional (map)": {
        "ecuacion": (
            "Calcula la inercia efectiva completa map = fap·(mtot + m) durante aceleraciones verticales u horizontales."
        ),
        "coeficientes": (
            "Incluye explícitamente la masa de gas encerrado m (aunque su peso se compense estáticamente en Arquímedes, debe acelerarse junto al casco) multiplicada por el factor de masa añadida del aire desplazado fap (~1.15)."
        ),
    },
    # --- C10: Dinámica vectorial, empuje y actitud ---
    "Aceleración vertical de ascenso (az)": {
        "ecuacion": (
            "Estima la aceleración vertical de maniobra az = vz/ta en el arranque (en crucero estacionario vale 0)."
        ),
    },
    "Aceleración horizontal de traslación (ax)": {
        "ecuacion": (
            "Estima la aceleración horizontal de arranque ax = vx/ta aplicada sobre la masa aparente map (en crucero constante vale 0)."
        ),
    },
    "Componente vertical de sustentación de motores (FL)": {
        "ecuacion": (
            "Empuje vertical pico de maniobra necesario para sostener la masa residual mres·g y acelerar en ascenso la masa inercial map·az."
        ),
    },
    "Componente horizontal de avance de motores (FX)": {
        "ecuacion": (
            "Empuje horizontal total necesario para vencer la resistencia aerodinámica FD y aportar la fuerza de aceleración horizontal map·ax."
        ),
    },
    "Empuje vectorial total de los 4 motores (Ttot)": {
        "ecuacion": (
            "Calcula la magnitud del empuje vectorial pico de maniobra Ttot = √(FL² + FX²) combinando sustentación vertical y avance horizontal."
        ),
    },
    "Ángulo de rotación respecto a la vertical (theta)": {
        "ecuacion": (
            "Calcula el ángulo de inclinación vectorial de maniobra θ = arctan(FX/FL) respecto a la vertical."
        ),
        "coeficientes": (
            "El factor 180/π convierte radianes a grados sexagesimales para compararlo con el límite mecánico thmax."
        ),
    },
    "Ángulo de rotación en crucero estacionario (thcruc)": {
        "ecuacion": (
            "Calcula la inclinación de los motores durante el crucero horizontal estacionario (sin aceleraciones az ni ax): "
            "thcruc = arctan(FD / (mres·g))."
        ),
        "criterio": (
            "Cuando la flotabilidad mflot es muy alta (mres pequeño), el ángulo en crucero puede superar al de maniobra y volverse limitante frente a thmax."
        ),
    },
    "Margen respecto al ángulo máximo de rotación (dth)": {
        "ecuacion": (
            "Calcula el margen angular restante frente al límite mecánico thmax usando el peor régimen entre maniobra y crucero: "
            "dth = thmax − max(theta, thcruc)."
        ),
    },
    # --- C11: Capacidad vertical, eficiencia y potencia eléctrica ---
    "Sustentación vertical máxima de los 4 motores (FLmax)": {
        "ecuacion": (
            "Calcula el empuje vertical máximo disponible FLmax = √((N·Tmax1)² − FX²) tras reservar la componente horizontal FX requerida para avanzar."
        ),
    },
    "Empuje vectorial en crucero estacionario (Tcruc)": {
        "ecuacion": (
            "Calcula el empuje vectorial continuo en vuelo estacionario (az = 0, ax = 0): Tcruc = √((mres·g)² + FD²)."
        ),
    },
    "Potencia eléctrica motriz en crucero estacionario (Pcruc)": {
        "ecuacion": (
            "Evalúa la potencia eléctrica continua de los rotores durante la fase de crucero sin aceleraciones (empuje Tcruc y avance FD·v)."
        ),
    },
    "Área de disco barrida por cada hélice (Ap)": {
        "ecuacion": (
            "Calcula el área circular barrida por cada rotor Ap = π·dp²/4, determinante en el empuje inducido de la teoría de disco actuador."
        ),
    },
    "Eficiencia aerodinámica de hélice según velocidad (nprop)": {
        "ecuacion": (
            "Modela la caída cuadrática de eficiencia propulsiva nprop = nprop0·(1 − (v/vpitch)²) cuando la velocidad de avance v se acerca a la velocidad de paso nulo vpitch."
        ),
    },
    "Eficiencia propulsiva global (ntot)": {
        "ecuacion": (
            "Multiplica en cascada el rendimiento aerodinámico de hélice (nprop), la eficiencia electromecánica del motor (nm) y la de los ESC (nESC)."
        ),
    },
    "Potencia eléctrica demandada por los 4 motores (Pelec)": {
        "ecuacion": (
            "Calcula la potencia eléctrica pico de maniobra exigida a los rotores para dimensionar ESC/motores (Pmax) y corriente pico de batería (mbp)."
        ),
        "variables": (
            "El término Ttot^(3/2)/√(2·ρ₁·N·Ap) es la potencia inducida y FX·v el trabajo útil horizontal de maniobra, divididos entre ntot."
        ),
        "coeficientes": (
            "km (~1.20) es el factor de figura de mérito/margen que incorpora pérdidas de punta de pala, perfil, interferencia con el casco y control."
        ),
    },
    # --- C12: Balance energético global y costos operativos ---
    "Potencia eléctrica total a bordo (Ptot)": {
        "ecuacion": (
            "Suma la potencia eléctrica motriz pico Pelec más la carga base Pad de electrónica, telemetría y micro-ventilador mezclador del quemador."
        ),
    },
    "Tiempo acumulado de maniobras en misión (tman)": {
        "ecuacion": (
            "Determina el tiempo total dedicado a maniobras de arranque/ascenso durante los nv viajes: tman = min(tm, nv·ta)."
        ),
    },
    "Energía eléctrica requerida en misión (Ereq)": {
        "ecuacion": (
            "Integra por fases reales el consumo eléctrico total en Watt-hora: potencia pico Ptot durante tman más potencia estacionaria (Pcruc + Pad) durante el crucero tm − tman."
        ),
        "coeficientes": (
            "Se divide entre 3600 s/h para obtener la energía en Wh y compararla directamente con la capacidad específica ebat (Wh/kg) en mbe."
        ),
    },
    "Energía eléctrica total usada en misión (Eelec)": {
        "ecuacion": (
            "Convierte la energía eléctrica de misión Ereq (en Wh) a Joules multiplicando por 3600 s/h para sumarla homogéneamente con Eprop en Etot."
        ),
    },
    "Costo de combustible térmico en vuelo (Ccomb)": {
        "ecuacion": (
            "Calcula el gasto económico del combustible térmico consumido en vuelo multiplicando la masa mgm (kg) por su precio unitario ccomb (Bs/kg)."
        ),
    },
    "Costo de recarga eléctrica de batería (Celec)": {
        "ecuacion": (
            "Calcula el costo económico de recargar la energía eléctrica consumida en la misión."
        ),
        "coeficientes": (
            "Divide Ereq entre 1000 para convertir Wh a kWh antes de multiplicar por la tarifa eléctrica celecU (Bs/kWh)."
        ),
    },
    "Costo operativo total de misión (Cop)": {
        "ecuacion": (
            "Consolida el costo operativo completo del ciclo combinando precalentamiento en tierra (Cpre), combustible en vuelo (Ccomb) y recarga eléctrica (Celec)."
        ),
    },
    # --- C13: Dimensionamiento y límites de la batería ---
    "Masa de batería por energía de misión (mbe)": {
        "ecuacion": (
            "Calcula la masa mínima de batería exigida por autonomía energética mbe = Ereq/(ebat·DoD·ntemp)."
        ),
        "coeficientes": (
            "DoD (~0.80) limita la profundidad de descarga para no dañar las celdas LiPo, y ntemp (~0.92) compensa pérdidas internas/térmicas."
        ),
    },
    "Masa de batería por potencia pico (mbp)": {
        "ecuacion": (
            "Calcula la masa mínima de batería exigida por capacidad de entrega instantánea de corriente mbp = Ptot/(ebat·Cmax·ntemp)."
        ),
        "variables": (
            "Cmax (h⁻¹) es la tasa máxima de descarga continua segura de la batería."
        ),
    },
    "Masa de batería requerida (mbat)": {
        "ecuacion": (
            "Selecciona el criterio más exigente entre energía y potencia pico: mbat = max(mbe, mbp) mediante sp.Max."
        ),
        "criterio": (
            "El resultado cierra el lazo acoplado regresando a mart en C9, porque una batería más pesada exige más sustentación y potencia."
        ),
    },
}


def bloques_nota_ecuacion(nombre_eq: str) -> list[dict[str, str]]:
    """Devuelve la lista ordenada de bloques explicativos `{tipo, titulo, texto}` de una ecuación."""
    data = NOTAS_ECUACIONES.get(nombre_eq)
    if not data:
        return []
    return [
        {"tipo": tipo, "titulo": titulo, "texto": data[tipo]}
        for tipo, titulo in TIPOS_BLOQUES_NOTA
        if data.get(tipo)
    ]


def nota_ecuacion(nombre_eq: str) -> str:
    """Devuelve la explicación física unificada como texto plano, o cadena vacía."""
    bloques = bloques_nota_ecuacion(nombre_eq)
    if not bloques:
        return ""
    return " ".join(
        f"{b['titulo']}: {b['texto']}" if b["tipo"] != "ecuacion" else b["texto"]
        for b in bloques
    )


def validar_integridad_flujo() -> None:
    """Verifica consistencia exacta entre `modelo.CATEGORIAS`, `FLUJO_CATEGORIAS` y `CONEXIONES_INTER_CATEGORIAS`."""
    cats = list(modelo.CATEGORIAS.items())
    assert len(FLUJO_CATEGORIAS) == len(cats), (
        f"FLUJO_CATEGORIAS ({len(FLUJO_CATEGORIAS)}) no coincide con CATEGORIAS ({len(cats)})"
    )
    eqs_totales = {nom_eq for _, eqs_cat in cats for nom_eq in eqs_cat}
    faltantes_notas = set(NOTAS_ECUACIONES) - eqs_totales
    assert not faltantes_notas, f"NOTAS_ECUACIONES referencia ecuaciones inexistentes: {faltantes_notas}"
    for nom_eq, bloques_dict in NOTAS_ECUACIONES.items():
        invalidos = set(bloques_dict) - _TIPOS_VALIDOS_NOTA
        assert not invalidos, f"NOTAS_ECUACIONES['{nom_eq}'] tiene tipos inválidos: {invalidos}"

    vars_por_cat: list[set[str]] = []
    for idx, ((_, eqs_cat), flujo_cat) in enumerate(zip(cats, FLUJO_CATEGORIAS)):
        assert flujo_cat["grupo"] in _GRUPOS_BY_ID, f"Grupo desconocido en C{idx + 1}: {flujo_cat['grupo']}"
        nodos = flujo_cat["nodos"]
        eqs_nodos = [n["eq"] for n in nodos]
        assert len(eqs_nodos) == len(set(eqs_nodos)), f"Nodos con ecuación repetida en C{idx + 1}"
        assert set(eqs_nodos) == set(eqs_cat.keys()), (
            f"C{idx + 1}: los nodos no cubren exactamente las ecuaciones de la categoría. "
            f"Faltan={set(eqs_cat.keys()) - set(eqs_nodos)}, Sobran={set(eqs_nodos) - set(eqs_cat.keys())}"
        )

        vars_nodos = {n["var"] for n in nodos}
        assert len(vars_nodos) == len(nodos), f"Variable principal repetida en nodos de C{idx + 1}"
        for n in nodos:
            assert n["var"] in modelo.VARIABLES, f"Variable desconocida en nodo C{idx + 1}: {n['var']}"
            assert n["var"] in {s.name for s in eqs_cat[n["eq"]].free_symbols}, (
                f"La variable destacada '{n['var']}' no aparece en '{n['eq']}'"
            )

        for ar in flujo_cat["aristas_internas"]:
            assert ar["origen"] in vars_nodos, f"Arista interna en C{idx + 1}: origen inválido '{ar['origen']}'"
            assert ar["destino"] in vars_nodos, f"Arista interna en C{idx + 1}: destino inválido '{ar['destino']}'"

        vars_por_cat.append(vars_nodos)

    pares_vistos: set[tuple[int, int]] = set()
    for con in CONEXIONES_INTER_CATEGORIAS:
        o, d = con["origen"], con["destino"]
        assert 0 <= o < len(cats) and 0 <= d < len(cats) and o != d, f"Conexión inválida {o}->{d}"
        assert (o, d) not in pares_vistos, f"Conexión duplicada {o}->{d}"
        pares_vistos.add((o, d))
        for v in con["variables"]:
            assert v in modelo.VARIABLES, f"Variable desconocida en conexión C{o+1}->C{d+1}: {v}"
        for v in con["origenes_internos"]:
            assert v in vars_por_cat[o], f"origen_interno '{v}' no existe en nodos de C{o+1}"
        for v in con["destinos_internos"]:
            assert v in vars_por_cat[d], f"destino_interno '{v}' no existe en nodos de C{d+1}"


validar_integridad_flujo()


def _item_conexion(con: dict[str, Any], cat_ext_id: int, nodos_clave: list[str]) -> dict[str, Any]:
    cats_nombres = list(modelo.CATEGORIAS.keys())
    flujo_ext = FLUJO_CATEGORIAS[cat_ext_id]
    grupo = _GRUPOS_BY_ID[flujo_ext["grupo"]]
    return {
        "categoria_id": cat_ext_id,
        "categoria_codigo": f"C{cat_ext_id + 1}",
        "categoria_nombre": cats_nombres[cat_ext_id],
        "categoria_corto": flujo_ext["titulo_corto"],
        "grupo": grupo["id"],
        "color": grupo["color"],
        "variables": list(con["variables"]),
        "nodos_conectados": list(nodos_clave),
        "explicacion": con["explicacion"],
        "es_lazo": bool(con["es_lazo"]),
    }


def construir_flujo_categoria(cat_id: int) -> dict[str, Any]:
    """Construye los datos completos del diagrama de flujo y relaciones para la categoría `cat_id`."""
    cats_nombres = list(modelo.CATEGORIAS.keys())
    flujo_cat = FLUJO_CATEGORIAS[cat_id]
    grupo = _GRUPOS_BY_ID[flujo_cat["grupo"]]

    nodos_enriquecidos = []
    for nodo in flujo_cat["nodos"]:
        cats_eq = modelo.categorias_numeradas_de_ecuacion(nodo["eq"])
        eq_num = modelo.numero_ecuacion_en_categoria(cat_id, nodo["eq"])
        nodos_enriquecidos.append({
            **nodo,
            "ecuacion_num": eq_num,
            "ecuacion_codigo": f"(C{cat_id + 1}, E{eq_num})",
            "es_compartida": len(cats_eq) > 1,
            "categorias_codigo_str": ", ".join(cod for _, cod, _, _, _ in cats_eq),
            "categorias_eq_codigo_str": ", ".join(eq_cod for _, _, _, _, eq_cod in cats_eq),
        })

    entradas = [
        _item_conexion(con, con["origen"], con["destinos_internos"])
        for con in CONEXIONES_INTER_CATEGORIAS
        if con["destino"] == cat_id
    ]
    salidas = [
        _item_conexion(con, con["destino"], con["origenes_internos"])
        for con in CONEXIONES_INTER_CATEGORIAS
        if con["origen"] == cat_id
    ]

    return {
        "categoria_id": cat_id,
        "categoria_codigo": f"C{cat_id + 1}",
        "categoria_nombre": cats_nombres[cat_id],
        "titulo_corto": flujo_cat["titulo_corto"],
        "grupo": dict(grupo),
        "resumen": flujo_cat["resumen"],
        "flujo_interno": flujo_cat["flujo_interno"],
        "nodos": nodos_enriquecidos,
        "aristas_internas": [dict(a) for a in flujo_cat["aristas_internas"]],
        "entradas_externas": entradas,
        "salidas_externas": salidas,
    }


def construir_mapa_global() -> dict[str, Any]:
    """Construye la estructura completa para el Mapa de Flujo Global (C1 -> C13)."""
    cats_items = list(modelo.CATEGORIAS.items())
    nodos_globales = []

    for idx, (cat_nombre, eqs_cat) in enumerate(cats_items):
        flujo_cat = FLUJO_CATEGORIAS[idx]
        grupo = _GRUPOS_BY_ID[flujo_cat["grupo"]]
        num_comp = sum(1 for nom_eq in eqs_cat if len(modelo.categorias_de_ecuacion(nom_eq)) > 1)
        entradas_cod = [
            f"C{con['origen'] + 1}"
            for con in CONEXIONES_INTER_CATEGORIAS
            if con["destino"] == idx
        ]
        salidas_cod = [
            f"C{con['destino'] + 1}"
            for con in CONEXIONES_INTER_CATEGORIAS
            if con["origen"] == idx
        ]
        vars_clave: list[str] = []
        for con in CONEXIONES_INTER_CATEGORIAS:
            if con["origen"] == idx or con["destino"] == idx:
                for v in con["variables"]:
                    if v not in vars_clave:
                        vars_clave.append(v)

        nodos_globales.append({
            "id": idx,
            "codigo": f"C{idx + 1}",
            "nombre": cat_nombre,
            "titulo_corto": flujo_cat["titulo_corto"],
            "grupo": flujo_cat["grupo"],
            "color": grupo["color"],
            "pos_global": dict(flujo_cat["pos_global"]),
            "num_ecuaciones": len(eqs_cat),
            "num_compartidas": num_comp,
            "resumen": flujo_cat["resumen"],
            "variables_clave": vars_clave[:6],
            "entradas_codigos": entradas_cod,
            "salidas_codigos": salidas_cod,
        })

    aristas_globales = [
        {
            "origen_id": con["origen"],
            "origen_codigo": f"C{con['origen'] + 1}",
            "destino_id": con["destino"],
            "destino_codigo": f"C{con['destino'] + 1}",
            "variables": list(con["variables"]),
            "explicacion": con["explicacion"],
            "es_lazo": bool(con["es_lazo"]),
        }
        for con in CONEXIONES_INTER_CATEGORIAS
    ]

    return {
        "grupos": [dict(g) for g in GRUPOS_TEMATICOS],
        "nodos": nodos_globales,
        "aristas": aristas_globales,
    }
