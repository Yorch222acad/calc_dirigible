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
        "nombre": "Transferencia de Calor y Quemador GLP",
        "color": "#fb923c",
        "descripcion": "Resuelve la convección natural y forzada sin aislante (C4) y con capa celular intermedia (C5), cuantifica el ahorro térmico y enfriamiento (C6) y calcula el propano requerido (C7).",
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
        "variables": ["drho", "F"],
        "origenes_internos": ["drho", "F"],
        "destinos_internos": ["F", "V"],
        "explicacion": "La diferencia de densidades (drho) y la fuerza de flotación (F) fijan el volumen necesario del globo V = F / (drho·g).",
        "es_lazo": False,
    },
    {
        "origen": 1,
        "destino": 0,
        "variables": ["V"],
        "origenes_internos": ["V"],
        "destinos_internos": ["m"],
        "explicacion": "El volumen geométrico V obtenido del casco determina la masa de aire caliente encerrada m = rho2·V y su calor sensible Q.",
        "es_lazo": True,
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
        "variables": ["dT", "m"],
        "origenes_internos": ["dT", "m"],
        "destinos_internos": ["Qp0", "Qp", "vT", "Qc"],
        "explicacion": "El salto dT determina los flujos térmicos Qp0 y Qp, mientras que la masa m de aire caliente define la capacidad calorífica (vT y Qc).",
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
        "variables": ["F", "mflot"],
        "origenes_internos": ["F", "mflot"],
        "destinos_internos": ["F", "mflot"],
        "explicacion": "C1 comparte directamente la fuerza F y la masa compensada mflot = F/g que descarga peso de los motores.",
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
        "explicacion": "La masa de la película celular aislante (mc) se suma directamente en la masa estructural del artefacto mart.",
        "es_lazo": False,
    },
    # Convección, Aislamiento y Balance Térmico (C4, C5 -> C6 -> C7 -> C12)
    {
        "origen": 3,
        "destino": 4,
        "variables": ["he"],
        "origenes_internos": ["he"],
        "destinos_internos": ["he", "U"],
        "explicacion": "La ecuación de convección externa he se comparte entre C4 y C5 como resistencia exterior común del casco.",
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
        "variables": ["Eprop"],
        "origenes_internos": ["Eprop"],
        "destinos_internos": ["Eprop", "Etot"],
        "explicacion": "La energía química suministrada por el propano (Eprop = Em / ncal) compone la rama térmica del consumo total Etot.",
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
        "destinos_internos": ["FD", "FX"],
        "explicacion": "La fuerza de resistencia aerodinámica FD constituye la carga base que deben vencer los motores en la componente horizontal FX.",
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
        "variables": ["mres", "mtot", "map"],
        "origenes_internos": ["mres", "mtot", "map"],
        "destinos_internos": ["FL", "FX"],
        "explicacion": "La masa residual mres exige empuje vertical FL; mtot y la masa aparente map añaden las fuerzas inerciales de ascenso/avance.",
        "es_lazo": False,
    },
    {
        "origen": 8,
        "destino": 10,
        "variables": ["F", "mtot"],
        "origenes_internos": ["F", "mtot"],
        "destinos_internos": ["Fexc"],
        "explicacion": "El empuje hidrostático F y el peso total mtot·g se combinan con FLmax para evaluar el excedente de sustentación Fexc.",
        "es_lazo": False,
    },
    {
        "origen": 9,
        "destino": 10,
        "variables": ["FX", "Ttot"],
        "origenes_internos": ["FX", "Ttot"],
        "destinos_internos": ["Ttot", "FLmax", "Pelec"],
        "explicacion": "FX limita la sustentación vertical disponible FLmax y el empuje vectorial total Ttot fija la potencia inducida y de avance Pelec.",
        "es_lazo": False,
    },
    {
        "origen": 10,
        "destino": 11,
        "variables": ["Pelec"],
        "origenes_internos": ["Pelec"],
        "destinos_internos": ["Pelec", "Ptot"],
        "explicacion": "La potencia eléctrica demandada por los motores Pelec se suma al consumo adicional Pad en Ptot = Pelec + Pad para integrar la energía de misión.",
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
            {"eq": "Gas ideal (caso 2 - caliente)", "var": "rho2", "etiqueta": "Densidad aire caliente", "capa": 0},
            {"eq": "Gradiente térmico", "var": "dT", "etiqueta": "Salto térmico T2 - T1", "capa": 0},
            {"eq": "Masa compensada por aire caliente (mflot)", "var": "mflot", "etiqueta": "Carga asignada al globo", "capa": 0},
            {"eq": "Diferencia de densidades", "var": "drho", "etiqueta": "Contraste rho1 - rho2", "capa": 1},
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Empuje de Arquímedes", "capa": 1},
            {"eq": "Masa de aire caliente", "var": "m", "etiqueta": "Masa interna rho2·V", "capa": 1},
            {"eq": "Calor sensible", "var": "Q", "etiqueta": "Contenido térmico m·cp·dT", "capa": 2},
        ],
        "aristas_internas": [
            {"origen": "rho1", "destino": "drho", "etiqueta": "rho1 - rho2", "lazo": False},
            {"origen": "rho2", "destino": "drho", "etiqueta": "rho1 - rho2", "lazo": False},
            {"origen": "mflot", "destino": "F", "etiqueta": "F = mflot·g", "lazo": False},
            {"origen": "drho", "destino": "F", "etiqueta": "escala V en C2", "lazo": False},
            {"origen": "rho2", "destino": "m", "etiqueta": "rho2 · V", "lazo": False},
            {"origen": "m", "destino": "Q", "etiqueta": "m · cp · dT", "lazo": False},
            {"origen": "dT", "destino": "Q", "etiqueta": "ΔT", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Dimensiones y Volumen",
        "grupo": "aerostatica",
        "pos_global": {"fila": 0, "col": 1},
        "resumen": (
            "Convierte la fuerza aerostática F en volumen de casco y deduce las dimensiones principales "
            "(radio R, diámetro D, esbeltez λ, longitud L y partición proa/popa cf y cr) del dirigible prolado."
        ),
        "flujo_interno": (
            "Partiendo de F y drho se despeja el volumen V = F/(drho·g). Junto con la relación de esbeltez lam = L/D, "
            "el bloque acoplado {L, R} determina el radio R, el diámetro D = 2R y la longitud total L; la fracción xf "
            "parte el casco en cf y cr, sirviendo de entrada para el área total S."
        ),
        "nodos": [
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Empuje aerostático", "capa": 0},
            {"eq": "Volumen total del casco", "var": "V", "etiqueta": "Volumen V = (2/3)πR²L", "capa": 1},
            {"eq": "Diámetro máximo transversal (2R)", "var": "D", "etiqueta": "Diámetro D = 2R", "capa": 2},
            {"eq": "Relación de esbeltez (L/D)", "var": "lam", "etiqueta": "Esbeltez λ = L/D", "capa": 2},
            {"eq": "Longitud total del casco", "var": "L", "etiqueta": "Longitud L = cf + cr", "capa": 3},
            {"eq": "Fracción de nariz (cf/L)", "var": "xf", "etiqueta": "Partición nariz cf/L", "capa": 3},
            {"eq": "Área superficial total", "var": "S", "etiqueta": "Área envolvente S", "capa": 4},
        ],
        "aristas_internas": [
            {"origen": "F", "destino": "V", "etiqueta": "F / (drho·g)", "lazo": False},
            {"origen": "V", "destino": "D", "etiqueta": "R ∝ (V/λ)^(1/3)", "lazo": False},
            {"origen": "V", "destino": "lam", "etiqueta": "geometría", "lazo": False},
            {"origen": "D", "destino": "L", "etiqueta": "L = λ·D", "lazo": False},
            {"origen": "lam", "destino": "L", "etiqueta": "λ", "lazo": False},
            {"origen": "L", "destino": "xf", "etiqueta": "cf = xf·L", "lazo": False},
            {"origen": "D", "destino": "S", "etiqueta": "R en Sf, Sr", "lazo": False},
            {"origen": "xf", "destino": "S", "etiqueta": "cf, cr en C3", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Superficies y Película",
        "grupo": "aerostatica",
        "pos_global": {"fila": 0, "col": 2},
        "resumen": (
            "Calcula el área superficial exacta de los dos semielipsoides prolados (proa y popa), "
            "su suma S y el área y masa de la película plástica celular aislante."
        ),
        "flujo_interno": (
            "Con R, cf y cr (donde cf > R y cr > R) se obtienen las excentricidades ef y er, luego las áreas "
            "laterales analíticas Sf y Sr que suman la superficie S del globo. Sobre S, el factor geométrico de las "
            "paredes celulares amplifica la superficie Sc y fija la masa estructural mc de la capa aislante."
        ),
        "nodos": [
            {"eq": "Excentricidad frontal (cf > R)", "var": "ef", "etiqueta": "Excentricidad nariz", "capa": 0},
            {"eq": "Excentricidad trasera (cr > R)", "var": "er", "etiqueta": "Excentricidad cola", "capa": 0},
            {"eq": "Área superficial frontal", "var": "Sf", "etiqueta": "Área nariz Sf", "capa": 1},
            {"eq": "Área superficial trasera", "var": "Sr", "etiqueta": "Área cola Sr", "capa": 1},
            {"eq": "Área superficial total", "var": "S", "etiqueta": "Área casco S = Sf + Sr", "capa": 2},
            {"eq": "Área total de película celular", "var": "Sc", "etiqueta": "Película S·(1+2e/W)", "capa": 3},
            {"eq": "Masa de la cuadrícula celular", "var": "mc", "etiqueta": "Masa film mc = Sc·σ", "capa": 4},
        ],
        "aristas_internas": [
            {"origen": "ef", "destino": "Sf", "etiqueta": "arcsin(ef)", "lazo": False},
            {"origen": "er", "destino": "Sr", "etiqueta": "arcsin(er)", "lazo": False},
            {"origen": "Sf", "destino": "S", "etiqueta": "suma", "lazo": False},
            {"origen": "Sr", "destino": "S", "etiqueta": "suma", "lazo": False},
            {"origen": "S", "destino": "Sc", "etiqueta": "1 + 2e/W", "lazo": False},
            {"origen": "Sc", "destino": "mc", "etiqueta": "Sc · σ", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Convección Base (U0)",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 0},
        "resumen": (
            "Determina el coeficiente global de transferencia de calor U0 del casco simple sin capa aislante, "
            "combinando convección forzada externa por el viento y convección natural interna."
        ),
        "flujo_interno": (
            "La rama externa calcula Pr, el Nusselt forzado Nue (con ReL de C8) y el coeficiente exterior he. "
            "La rama interna forma un bloque acoplado no lineal de 5 ecuaciones: la caída interna dTi0 fija "
            "RaD0 → Nui0 → hi0, que junto a he y ep/ke define U0, retroalimentando dTi0 = (U0/hi0)·dT."
        ),
        "nodos": [
            {"eq": "Número de Prandtl del aire (Pr)", "var": "Pr", "etiqueta": "Pr = ν / α", "capa": 0},
            {"eq": "Número de Nusselt externo por viento (Nue)", "var": "Nue", "etiqueta": "Convección externa Nue", "capa": 1},
            {"eq": "Coeficiente convectivo externo del casco (he)", "var": "he", "etiqueta": "Coef. externo he", "capa": 2},
            {"eq": "Caída térmica interna sin capa celular (dTi0)", "var": "dTi0", "etiqueta": "Salto interno dTi0", "capa": 1},
            {"eq": "Número de Rayleigh interno sin capa celular (RaD0)", "var": "RaD0", "etiqueta": "Rayleigh interno RaD0", "capa": 2},
            {"eq": "Número de Nusselt interno sin capa celular (Nui0)", "var": "Nui0", "etiqueta": "Nusselt interno Nui0", "capa": 3},
            {"eq": "Coeficiente convectivo interno sin capa celular (hi0)", "var": "hi0", "etiqueta": "Coef. interno hi0", "capa": 4},
            {"eq": "Coeficiente global sin capa celular (U0)", "var": "U0", "etiqueta": "Global base U0", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "Pr", "destino": "Nue", "etiqueta": "Pr^(1/3)", "lazo": False},
            {"origen": "Nue", "destino": "he", "etiqueta": "Nue·ka/L", "lazo": False},
            {"origen": "he", "destino": "U0", "etiqueta": "1/he", "lazo": False},
            {"origen": "dTi0", "destino": "RaD0", "etiqueta": "flotabilidad", "lazo": False},
            {"origen": "RaD0", "destino": "Nui0", "etiqueta": "0.13·Ra^(1/3)", "lazo": False},
            {"origen": "Nui0", "destino": "hi0", "etiqueta": "fcal·ka/D", "lazo": False},
            {"origen": "hi0", "destino": "U0", "etiqueta": "1/hi0", "lazo": False},
            {"origen": "U0", "destino": "dTi0", "etiqueta": "↺ (U0/hi0)·dT", "lazo": True},
        ],
    },
    {
        "titulo_corto": "Aislante Celular (U)",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 1},
        "resumen": (
            "Resuelve la transferencia de calor a través de la doble pared con cavidad celular de espesor e y ancho W, "
            "reduciendo el coeficiente global hasta el valor U con aislante."
        ),
        "flujo_interno": (
            "Forma un bloque acoplado de 8 ecuaciones que reutiliza he de C4 y resuelve simultáneamente dos lazos: "
            "la convección interna (dTi → RaD → Nui → hi) y la convección confinado en la celda aislante "
            "(dTcel → Rae → Nuc). Ambas resistencias junto a 2·ep/ke y 1/he fijan U, que realimenta dTi y dTcel."
        ),
        "nodos": [
            {"eq": "Coeficiente convectivo externo del casco (he)", "var": "he", "etiqueta": "Coef. externo he", "capa": 0},
            {"eq": "Caída térmica interna con capa celular (dTi)", "var": "dTi", "etiqueta": "Salto interno dTi", "capa": 0},
            {"eq": "Caída térmica en la celda aislante (dTcel)", "var": "dTcel", "etiqueta": "Salto en celda dTcel", "capa": 0},
            {"eq": "Número de Rayleigh interno con capa celular (RaD)", "var": "RaD", "etiqueta": "Rayleigh casco RaD", "capa": 1},
            {"eq": "Número de Rayleigh en cavidad celular (Rae)", "var": "Rae", "etiqueta": "Rayleigh celda Rae", "capa": 1},
            {"eq": "Número de Nusselt interno con capa celular (Nui)", "var": "Nui", "etiqueta": "Nusselt casco Nui", "capa": 2},
            {"eq": "Número de Nusselt efectivo en celda (Nuc)", "var": "Nuc", "etiqueta": "Nusselt celda Nuc", "capa": 2},
            {"eq": "Coeficiente convectivo interno con capa celular (hi)", "var": "hi", "etiqueta": "Coef. interno hi", "capa": 3},
            {"eq": "Coeficiente global con capa celular (U)", "var": "U", "etiqueta": "Global aislado U", "capa": 4},
        ],
        "aristas_internas": [
            {"origen": "he", "destino": "U", "etiqueta": "1/he", "lazo": False},
            {"origen": "dTi", "destino": "RaD", "etiqueta": "dTi", "lazo": False},
            {"origen": "RaD", "destino": "Nui", "etiqueta": "RaD^(1/3)", "lazo": False},
            {"origen": "Nui", "destino": "hi", "etiqueta": "hi", "lazo": False},
            {"origen": "hi", "destino": "U", "etiqueta": "1/hi", "lazo": False},
            {"origen": "dTcel", "destino": "Rae", "etiqueta": "e³", "lazo": False},
            {"origen": "Rae", "destino": "Nuc", "etiqueta": "Rae/Rac", "lazo": False},
            {"origen": "Nuc", "destino": "U", "etiqueta": "e/(ka·Nuc)", "lazo": False},
            {"origen": "U", "destino": "dTi", "etiqueta": "↺ (U/hi)·dT", "lazo": True},
            {"origen": "U", "destino": "dTcel", "etiqueta": "↺ dTcel(U)", "lazo": True},
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
            "instantáneo dQp y el porcentaje fais. En paralelo, Qp y la capacidad calorífica m·cp dan la tasa de "
            "enfriamiento vT y el tiempo tc para agotar la caída admisible Qc."
        ),
        "nodos": [
            {"eq": "Potencia perdida sin capa celular (Qp0)", "var": "Qp0", "etiqueta": "Potencia base Qp0", "capa": 0},
            {"eq": "Potencia perdida con capa celular (Qp)", "var": "Qp", "etiqueta": "Potencia aislada Qp", "capa": 0},
            {"eq": "Energía cedida en caída admisible", "var": "Qc", "etiqueta": "Reserva térmica Qc", "capa": 0},
            {"eq": "Potencia ahorrada por capa celular (dQp)", "var": "dQp", "etiqueta": "Ahorro Qp0 - Qp", "capa": 1},
            {"eq": "Velocidad de enfriamiento (dT/dt)", "var": "vT", "etiqueta": "Tasa dT/dt", "capa": 1},
            {"eq": "Fracción de ahorro térmico celular (fais)", "var": "fais", "etiqueta": "Fracción fais", "capa": 2},
            {"eq": "Tiempo de enfriamiento sin aporte", "var": "tc", "etiqueta": "Autonomía Qc / Qp", "capa": 2},
        ],
        "aristas_internas": [
            {"origen": "Qp0", "destino": "dQp", "etiqueta": "Qp0 - Qp", "lazo": False},
            {"origen": "Qp", "destino": "dQp", "etiqueta": "resta", "lazo": False},
            {"origen": "dQp", "destino": "fais", "etiqueta": "dQp / Qp0", "lazo": False},
            {"origen": "Qp0", "destino": "fais", "etiqueta": "base", "lazo": False},
            {"origen": "Qp", "destino": "vT", "etiqueta": "Qp / (m·cp)", "lazo": False},
            {"origen": "Qp", "destino": "tc", "etiqueta": "Qc / Qp", "lazo": False},
            {"origen": "Qc", "destino": "tc", "etiqueta": "Qc", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Energía Térmica y GLP",
        "grupo": "termica",
        "pos_global": {"fila": 1, "col": 3},
        "resumen": (
            "Integra las potencias térmicas durante el tiempo de misión tm = dm/vg y traduce el calor necesario "
            "en masa de propano/butano requerida considerando la eficiencia térmica del quemador (ncal)."
        ),
        "flujo_interno": (
            "El tiempo de vuelo tm fijado por dm y vg en C8 integra las pérdidas térmicas en Em0, Em y el ahorro Eah. "
            "Dividiendo Em entre la eficiencia del quemador ncal resulta la energía química Eprop, cuyo cociente con "
            "el poder calorífico PC da la masa de gas de crucero mgm (además de mgc para recuperar caídas dTc)."
        ),
        "nodos": [
            {"eq": "Distancia recorrida en misión (dm)", "var": "dm", "etiqueta": "Misión dm = vg·tm", "capa": 0},
            {"eq": "Energía perdida sin aislante en misión", "var": "Em0", "etiqueta": "Pérdida base Em0", "capa": 1},
            {"eq": "Energía perdida con aislante en misión", "var": "Em", "etiqueta": "Pérdida real Em", "capa": 1},
            {"eq": "Energía ahorrada gracias al aislante", "var": "Eah", "etiqueta": "Ahorro térmico Eah", "capa": 1},
            {"eq": "Masa de gas para recuperar caída dTc", "var": "mgc", "etiqueta": "GLP caída dTc", "capa": 1},
            {"eq": "Energía suministrada por propano en misión (Eprop)", "var": "Eprop", "etiqueta": "Energía GLP Em/ncal", "capa": 2},
            {"eq": "Masa de gas para mantener T en misión", "var": "mgm", "etiqueta": "GLP crucero mgm", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "dm", "destino": "Em0", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "dm", "destino": "Em", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "dm", "destino": "Eah", "etiqueta": "tm = dm/vg", "lazo": False},
            {"origen": "Em", "destino": "Eprop", "etiqueta": "Em / ncal", "lazo": False},
            {"origen": "Eprop", "destino": "mgm", "etiqueta": "Eprop / PC", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Vuelo, Viento y Arrastre",
        "grupo": "aerodinamica",
        "pos_global": {"fila": 2, "col": 0},
        "resumen": (
            "Relaciona la velocidad aerodinámica v con el viento en contra vv para fijar la velocidad efectiva vg y "
            "el tiempo de misión tm, y calcula el arrastre aerodinámico FD de Hoerner y el trabajo resistente ED."
        ),
        "flujo_interno": (
            "La rama cinemática resta el viento en contra (vg = v - vv) y determina tm = dm/vg. En paralelo, la rama "
            "aerodinámica usa la velocidad relativa v para calcular ReL, el factor de fricción turbulenta Cf, el "
            "coeficiente volumétrico CDVc(lam), el total CDV y la fuerza FD, integrando el trabajo ED = FD·dm."
        ),
        "nodos": [
            {"eq": "Velocidad neta de avance respecto al suelo (vg)", "var": "vg", "etiqueta": "Velocidad suelo v - vv", "capa": 0},
            {"eq": "Número de Reynolds longitudinal (ReL)", "var": "ReL", "etiqueta": "Reynolds ReL", "capa": 0},
            {"eq": "Distancia recorrida en misión (dm)", "var": "tm", "etiqueta": "Tiempo de vuelo dm/vg", "capa": 1},
            {"eq": "Coeficiente de fricción superficial (Cf)", "var": "Cf", "etiqueta": "Fricción piel Cf", "capa": 1},
            {"eq": "Coeficiente volumétrico del casco (CDVc - Hoerner)", "var": "CDVc", "etiqueta": "Casco Hoerner CDVc", "capa": 2},
            {"eq": "Coeficiente de resistencia volumétrico total (CDV)", "var": "CDV", "etiqueta": "Total CDV = kp·CDVc", "capa": 3},
            {"eq": "Fuerza de resistencia aerodinámica (FD)", "var": "FD", "etiqueta": "Arrastre FD", "capa": 4},
            {"eq": "Energía perdida por resistencia aerodinámica (ED)", "var": "ED", "etiqueta": "Trabajo arrastre ED", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "vg", "destino": "tm", "etiqueta": "dm / vg", "lazo": False},
            {"origen": "ReL", "destino": "Cf", "etiqueta": "log10(ReL)", "lazo": False},
            {"origen": "Cf", "destino": "CDVc", "etiqueta": "f(λ)", "lazo": False},
            {"origen": "CDVc", "destino": "CDV", "etiqueta": "× kp", "lazo": False},
            {"origen": "CDV", "destino": "FD", "etiqueta": "½ρ₁v²·CDV", "lazo": False},
            {"origen": "FD", "destino": "ED", "etiqueta": "FD · dm", "lazo": False},
            {"origen": "tm", "destino": "ED", "etiqueta": "vg · tm", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Masas y Sustentación",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 0},
        "resumen": (
            "Consolida la masa estructural del artefacto (película aislante, motores, propano, batería), añade la carga "
            "útil para obtener mtot y determina la masa residual mres que deben sostener los rotores."
        ),
        "flujo_interno": (
            "Suma mc (C3) y mbat (lazo cerrado con C13) con las masas fijas de motores, GLP y aditamentos para hallar "
            "mart y mtot = mart + mcarga. Luego escala la masa aparente map = fap·mtot y calcula el peso residual "
            "mres = mtot - mflot que define cuánto trabajan verticalmente los motores."
        ),
        "nodos": [
            {"eq": "Masa de la cuadrícula celular", "var": "mc", "etiqueta": "Masa aislante mc", "capa": 0},
            {"eq": "Masa de batería requerida (mbat)", "var": "mbat", "etiqueta": "Masa batería mbat", "capa": 0},
            {"eq": "Masa del artefacto con sus componentes (mart)", "var": "mart", "etiqueta": "Artefacto mart", "capa": 1},
            {"eq": "Fuerza de sustentación aerostática", "var": "F", "etiqueta": "Fuerza globo F", "capa": 1},
            {"eq": "Masa total del dirigible con carga útil (mtot)", "var": "mtot", "etiqueta": "Masa total mtot", "capa": 2},
            {"eq": "Masa compensada por aire caliente (mflot)", "var": "mflot", "etiqueta": "Flotabilidad mflot", "capa": 2},
            {"eq": "Masa aparente traslacional (map)", "var": "map", "etiqueta": "Masa aparente map", "capa": 3},
            {"eq": "Masa residual a compensar por motores (mres)", "var": "mres", "etiqueta": "Carga rotores mres", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "mc", "destino": "mart", "etiqueta": "+mc", "lazo": False},
            {"origen": "mbat", "destino": "mart", "etiqueta": "+mbat", "lazo": False},
            {"origen": "mart", "destino": "mtot", "etiqueta": "+mcarga", "lazo": False},
            {"origen": "mtot", "destino": "map", "etiqueta": "fap·mtot", "lazo": False},
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
            "Descompone las fuerzas vertical (sustentación residual + ascenso) y horizontal (arrastre + inercia aparente) "
            "para hallar el empuje vectorial total Ttot y el ángulo de inclinación theta frente a sus límites."
        ),
        "flujo_interno": (
            "Calcula las aceleraciones az y ax de maniobra. Con mres y mtot determina el empuje vertical FL; con FD (C8) "
            "y map determina la fuerza de avance FX. Su suma vectorial fija Ttot = √(FL² + FX²) y el ángulo de "
            "inclinación theta = atan(FX/FL), evaluando los márgenes de empuje dTtot y ángulo dth."
        ),
        "nodos": [
            {"eq": "Aceleración vertical de ascenso (az)", "var": "az", "etiqueta": "Aceleración az", "capa": 0},
            {"eq": "Aceleración horizontal de traslación (ax)", "var": "ax", "etiqueta": "Aceleración ax", "capa": 0},
            {"eq": "Fuerza de resistencia aerodinámica (FD)", "var": "FD", "etiqueta": "Arrastre FD", "capa": 0},
            {"eq": "Componente vertical de sustentación de motores (FL)", "var": "FL", "etiqueta": "Empuje vertical FL", "capa": 1},
            {"eq": "Componente horizontal de avance de motores (FX)", "var": "FX", "etiqueta": "Empuje avance FX", "capa": 1},
            {"eq": "Empuje vectorial total de los 4 motores (Ttot)", "var": "Ttot", "etiqueta": "Empuje Ttot", "capa": 2},
            {"eq": "Ángulo de rotación respecto a la vertical (theta)", "var": "theta", "etiqueta": "Inclinación theta", "capa": 2},
            {"eq": "Margen de empuje disponible de los 4 motores (dTtot)", "var": "dTtot", "etiqueta": "Margen dTtot", "capa": 3},
            {"eq": "Margen respecto al ángulo máximo de rotación (dth)", "var": "dth", "etiqueta": "Margen angular dth", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "az", "destino": "FL", "etiqueta": "mtot·az", "lazo": False},
            {"origen": "ax", "destino": "FX", "etiqueta": "map·ax", "lazo": False},
            {"origen": "FD", "destino": "FX", "etiqueta": "+map·ax", "lazo": False},
            {"origen": "FL", "destino": "Ttot", "etiqueta": "√(FL²+FX²)", "lazo": False},
            {"origen": "FX", "destino": "Ttot", "etiqueta": "√(FL²+FX²)", "lazo": False},
            {"origen": "FL", "destino": "theta", "etiqueta": "atan(FX/FL)", "lazo": False},
            {"origen": "FX", "destino": "theta", "etiqueta": "atan(FX/FL)", "lazo": False},
            {"origen": "Ttot", "destino": "dTtot", "etiqueta": "N·Tmax1-Ttot", "lazo": False},
            {"origen": "theta", "destino": "dth", "etiqueta": "thmax-theta", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Eficiencia y Potencia",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 2},
        "resumen": (
            "Evalúa la reserva de sustentación vertical (FLmax, Fexc), la caída cuadrática de eficiencia de la hélice "
            "con la velocidad v hacia vpitch y la potencia eléctrica continua demandada Pelec respecto a Pmax."
        ),
        "flujo_interno": (
            "Por un lado, la capacidad de los rotores menos el avance FX deja FLmax y el excedente Fexc. Por otro, "
            "el diámetro dp fija el disco Ap y la velocidad v degrada nprop hasta obtener ntot = nprop·nm·nESC. "
            "Ttot, FX, Ap y ntot fijan Pelec, comparada finalmente contra Pmax = N·Pmax1 en dPelec."
        ),
        "nodos": [
            {"eq": "Empuje vectorial total de los 4 motores (Ttot)", "var": "Ttot", "etiqueta": "Empuje total Ttot", "capa": 0},
            {"eq": "Área de disco barrida por cada hélice (Ap)", "var": "Ap", "etiqueta": "Área disco Ap", "capa": 0},
            {"eq": "Eficiencia aerodinámica de hélice según velocidad (nprop)", "var": "nprop", "etiqueta": "Eficiencia nprop(v)", "capa": 0},
            {"eq": "Sustentación vertical máxima de los 4 motores (FLmax)", "var": "FLmax", "etiqueta": "Máx. vertical FLmax", "capa": 1},
            {"eq": "Eficiencia propulsiva global (ntot)", "var": "ntot", "etiqueta": "Eficiencia ntot", "capa": 1},
            {"eq": "Potencia eléctrica máxima continua de 4 motores (Pmax)", "var": "Pmax", "etiqueta": "Límite Pmax", "capa": 1},
            {"eq": "Excedente de sustentación total (Fexc)", "var": "Fexc", "etiqueta": "Excedente Fexc", "capa": 2},
            {"eq": "Potencia eléctrica demandada por los 4 motores (Pelec)", "var": "Pelec", "etiqueta": "Potencia Pelec", "capa": 2},
            {"eq": "Margen de potencia eléctrica de los motores (dPelec)", "var": "dPelec", "etiqueta": "Margen dPelec", "capa": 3},
        ],
        "aristas_internas": [
            {"origen": "FLmax", "destino": "Fexc", "etiqueta": "F+FLmax-mg", "lazo": False},
            {"origen": "nprop", "destino": "ntot", "etiqueta": "× nm·nESC", "lazo": False},
            {"origen": "Ttot", "destino": "Pelec", "etiqueta": "Ttot^(3/2)", "lazo": False},
            {"origen": "Ap", "destino": "Pelec", "etiqueta": "disco N·Ap", "lazo": False},
            {"origen": "ntot", "destino": "Pelec", "etiqueta": "km / ntot", "lazo": False},
            {"origen": "Pelec", "destino": "dPelec", "etiqueta": "Pmax-Pelec", "lazo": False},
            {"origen": "Pmax", "destino": "dPelec", "etiqueta": "Pmax", "lazo": False},
        ],
    },
    {
        "titulo_corto": "Balance Energético",
        "grupo": "propulsion",
        "pos_global": {"fila": 3, "col": 3},
        "resumen": (
            "Suma la potencia eléctrica de los motores Pelec y el consumo adicional a bordo Pad (placa, cámara, "
            "antena y pérdidas base) en Ptot, integra el consumo eléctrico (Ereq, Eelec) y lo combina con Eprop."
        ),
        "flujo_interno": (
            "Ptot = Pelec + Pad integrada durante tm da Ereq (Wh), Eelec (J) y el coste eléctrico celec = Ereq/dm. "
            "Sumando Eelec con la energía química del quemador Eprop (C7) resulta la energía global Etot y el "
            "indicador por metro recorrido ctot (junto a la referencia mecánica ED de C8)."
        ),
        "nodos": [
            {"eq": "Potencia eléctrica demandada por los 4 motores (Pelec)", "var": "Pelec", "etiqueta": "Potencia motores Pelec", "capa": 0},
            {"eq": "Potencia eléctrica total a bordo (Ptot)", "var": "Ptot", "etiqueta": "Total Pelec + Pad", "capa": 1},
            {"eq": "Energía suministrada por propano en misión (Eprop)", "var": "Eprop", "etiqueta": "Energía GLP Eprop", "capa": 1},
            {"eq": "Energía perdida por resistencia aerodinámica (ED)", "var": "ED", "etiqueta": "Arrastre ED", "capa": 1},
            {"eq": "Energía eléctrica requerida en misión (Ereq)", "var": "Ereq", "etiqueta": "Energía (Wh) Ereq", "capa": 2},
            {"eq": "Energía eléctrica total usada en misión (Eelec)", "var": "Eelec", "etiqueta": "Eléctrica (J) Eelec", "capa": 3},
            {"eq": "Coste energético eléctrico por distancia (celec)", "var": "celec", "etiqueta": "Coste celec", "capa": 3},
            {"eq": "Energía total consumida en misión (Etot)", "var": "Etot", "etiqueta": "Global Etot", "capa": 4},
            {"eq": "Coste energético total por distancia (ctot)", "var": "ctot", "etiqueta": "Coste total ctot", "capa": 5},
        ],
        "aristas_internas": [
            {"origen": "Pelec", "destino": "Ptot", "etiqueta": "+ Pad", "lazo": False},
            {"origen": "Ptot", "destino": "Ereq", "etiqueta": "Ptot·tm/3600", "lazo": False},
            {"origen": "Ereq", "destino": "Eelec", "etiqueta": "× 3600", "lazo": False},
            {"origen": "Ereq", "destino": "celec", "etiqueta": "Ereq / dm", "lazo": False},
            {"origen": "Eelec", "destino": "Etot", "etiqueta": "+Eelec", "lazo": False},
            {"origen": "Eprop", "destino": "Etot", "etiqueta": "+Eprop", "lazo": False},
            {"origen": "Etot", "destino": "ctot", "etiqueta": "Etot / dm", "lazo": False},
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


NOTAS_ECUACIONES: dict[str, str] = {
    "Gas ideal (caso 1 - ambiente)": (
        "Relaciona presión atmosférica P y temperatura exterior T1 mediante Rair (287.058 J/(kg·K)) para fijar la densidad del aire ambiente ρ₁."
    ),
    "Fuerza de sustentación aerostática": (
        "Empuje de Arquímedes F = (ρ₁ − ρ₂)·g·V. Solo cuenta el volumen caliente interior V; la fina cámara de la capa celular no entra aquí como volumen sustentador."
    ),
    "Masa compensada por aire caliente (mflot)": (
        "Fracción de la masa total sostenida exclusivamente por el aire caliente (mflot = F/g). El resto (mres = mtot − mflot) lo cargan los rotores."
    ),
    "Relación de esbeltez (L/D)": (
        "Esbeltez geométrica λ = L/D. Valores bajos (λ ~ 2–3) minimizan el área superficial para un volumen dado; valores más altos reducen el arrastre de forma a alta velocidad."
    ),
    "Fracción de nariz (cf/L)": (
        "Reparte la longitud total L entre el semielipsoide frontal (cf = xf·L) y el trasero (cr = (1 − xf)·L) sin cambiar el volumen total V."
    ),
    "Volumen total del casco": (
        "Casco formado por dos semielipsoides prolados de revolución unidos en su diámetro máximo D = 2R, cuyo volumen total es V = (2/3)·π·R²·L."
    ),
    "Excentricidad frontal (cf > R)": (
        "Mide el alargamiento del semielipsoide de proa respecto a una semiesfera (ef = 0). Requiere estrictamente cf > R para que √(1 − R²/cf²) sea real."
    ),
    "Excentricidad trasera (cr > R)": (
        "Mide el alargamiento del semielipsoide de popa respecto a una semiesfera (er = 0). Exige cr > R para evitar raíces imaginarias."
    ),
    "Área superficial frontal": (
        "Área curva exacta del semielipsoide de proa. El factor arcsin(ef)/ef corrige la curvatura axial entre la sección media y el extremo alargado."
    ),
    "Área superficial trasera": (
        "Área curva exacta del semielipsoide de popa mediante arcsin(er)/er; sumada a Sf da la envolvente exterior S."
    ),
    "Área total de película celular": (
        "El factor (1 + 2·e/W) añade al área exterior S la superficie extra de los tabiques internos de la cuadrícula celular de altura e y paso W."
    ),
    "Número de Prandtl del aire (Pr)": (
        "Número adimensional Pr = ν/α (razón entre difusividad viscosa ν y térmica α). Para el aire vale ~0.70–0.72 y acopla hidrodinámica y transporte de calor."
    ),
    "Número de Nusselt externo por viento (Nue)": (
        "Nue = he·L/ka indica cuánto acelera el viento la transferencia de calor frente a aire estancado. El coeficiente 0.037 y el exponente ReL^(4/5) corresponden a capa límite turbulenta sobre superficie larga; en flujo laminar serían 0.664 y ReL^(1/2)."
    ),
    "Coeficiente convectivo externo del casco (he)": (
        "Traduce el Nusselt adimensional a flujo térmico exterior por metro cuadrado y kelvin: he = Nue·ka/L."
    ),
    "Caída térmica interna sin capa celular (dTi0)": (
        "Por continuidad térmica en serie, la caída de temperatura en la capa límite interior es proporcional a la fracción de resistencia térmica interna: dTi0 = (U0/hi0)·ΔT."
    ),
    "Número de Rayleigh interno sin capa celular (RaD0)": (
        "RaD0 = g·β·dTi0·D³/(ν·α) compara la flotabilidad térmica interna frente al frenado viscoso y térmico. Su magnitud (> 10⁹ en cascos de metro) determina que la convección natural interna es turbulenta."
    ),
    "Número de Nusselt interno sin capa celular (Nui0)": (
        "La ley 0.13·RaD0^(1/3) describe convección natural turbulenta en cavidades grandes (Ra > 10⁹). Al escalar con el cubo del diámetro (Ra^(1/3) ∝ D), el tamaño D se cancela al pasar a hi0."
    ),
    "Coeficiente convectivo interno sin capa celular (hi0)": (
        "Convierte Nui0 en coeficiente convectivo interno hi0 = fcal·Nui0·ka/D. El factor empírico fcal (~1.15) recoge la geometría curva y el mezclado interno por el quemador."
    ),
    "Coeficiente global sin capa celular (U0)": (
        "Transmitancia térmica total en serie sin aislante: 1/U0 = 1/hi0 + ep/ke + 1/he. La resistencia dominante suele ser la convección interna (1/hi0)."
    ),
    "Caída térmica interna con capa celular (dTi)": (
        "Reparto interno del salto térmico total ΔT cuando ya existe capa aislante (dTi = U·ΔT/hi). Al reducirse U por el aislante, disminuye el gradiente interno dTi."
    ),
    "Número de Rayleigh interno con capa celular (RaD)": (
        "Balance flotabilidad–viscosidad del aire interior evaluado con la caída interna amortiguada dTi."
    ),
    "Número de Nusselt interno con capa celular (Nui)": (
        "Usa la correlación turbulenta natural 0.13·RaD^(1/3) para Ra > 10⁹; en régimen laminar (Ra bajo) cambiaría a coeficiente ~0.59 y exponente 1/4."
    ),
    "Coeficiente convectivo interno con capa celular (hi)": (
        "Incluye el factor empírico de calibración fcal que corrige la convección interior considerando curvatura y convección forzada residual del quemador."
    ),
    "Caída térmica en la celda aislante (dTcel)": (
        "Diferencia de temperatura entre la lámina interna y externa de la celda aislante de espesor e (dTcel = U·e·ΔT/(ka·Nuc))."
    ),
    "Número de Rayleigh en cavidad celular (Rae)": (
        "Gobierna la convección dentro de la micro-celda aislante. Al depender de e³, mantener celdas delgadas mantiene Rae por debajo o cerca del umbral crítico Rac."
    ),
    "Número de Nusselt efectivo en celda (Nuc)": (
        "Representa la amplificación convectiva dentro de la celda frente a aire quieto (Nuc = 1). Si Rae ≤ Rac (Rac = 2000), el aire queda estratificado sin recirculación (Nuc ≈ 1); si lo supera, crece como (Rae/Rac)^0.25."
    ),
    "Coeficiente global con capa celular (U)": (
        "Resistencias en serie con doble lámina y aire confinado: 1/U = 1/hi + 2·ep/ke + e/(ka·Nuc) + 1/he."
    ),
    "Fracción de ahorro térmico celular (fais)": (
        "Fracción de calor salvada por la celda aislante frente al casco simple (1 − U/U0)."
    ),
    "Velocidad de enfriamiento (dT/dt)": (
        "Ritmo de enfriamiento pasivo vT = Qp/(m·cp) sin quemador encendido; relaciona pérdidas instantáneas con la capacidad térmica del gas caliente."
    ),
    "Tiempo de enfriamiento sin aporte": (
        "Tiempo estimado tc = Qc/Qp hasta agotar la caída de temperatura admisible dTc antes de requerir un nuevo pulso térmico."
    ),
    "Energía suministrada por propano en misión (Eprop)": (
        "Divide el calor neto perdido Em entre el rendimiento del quemador ncal para incluir pérdidas de escape y radiación de la llama."
    ),
    "Número de Reynolds longitudinal (ReL)": (
        "ReL = v·L/ν mide la razón entre fuerzas inerciales y viscosas a velocidad aerodinámica v. Para cascos aeronáuticos (ReL ~ 10⁵–10⁶) marca la transición a capa límite turbulenta y fija tanto Cf como Nue."
    ),
    "Coeficiente de fricción superficial (Cf)": (
        "Fórmula de Prandtl–Schlichting para capa límite turbulenta sobre pared lisa: 0.455/(log10(ReL))^2.58. Las constantes 0.455 y 2.58 corresponden exclusivamente al régimen turbulento."
    ),
    "Coeficiente volumétrico del casco (CDVc - Hoerner)": (
        "Correlación de Hoerner referida a V^(2/3): combina fricción viscosa Cf con el factor de forma por esbeltez (λ = L/D), capturando el compromiso entre área mojada y arrastre de presión."
    ),
    "Coeficiente de resistencia volumétrico total (CDV)": (
        "Aplica el factor parásito kp al casco limpio CDVc para añadir el arrastre de soportes, góndola, hélices paradas y cableado."
    ),
    "Fuerza de resistencia aerodinámica (FD)": (
        "Calculada siempre con la velocidad aerodinámica v = vg + vv, pues el viento incidente es el que genera presión dinámica ½·ρ₁·v² sobre el casco."
    ),
    "Masa aparente traslacional (map)": (
        "map = fap·mtot. Un cuerpo ligero y voluminoso debe acelerar parte del aire circundante (masa añadida), representada mediante el factor fap (> 1)."
    ),
    "Masa residual a compensar por motores (mres)": (
        "Fracción de mtot que no equilibra el aire caliente (mtot − mflot) y obliga a los rotores a aportar sustentación vertical continua."
    ),
    "Aceleración vertical de ascenso (az)": (
        "Margen de aceleración vertical de maniobra que sobrecarga FL frente al vuelo estacionario (en crucero puro az = 0)."
    ),
    "Aceleración horizontal de traslación (ax)": (
        "Aceleración longitudinal de maniobra que multiplica a la masa aparente map; en crucero constante vale 0."
    ),
    "Componente vertical de sustentación de motores (FL)": (
        "Empuje vertical continuo FL = mres·g + mtot·az necesario para sostener el peso residual y acelerar verticalmente."
    ),
    "Componente horizontal de avance de motores (FX)": (
        "Empuje hacia adelante FX = FD + map·ax requerido para vencer la resistencia del viento y acelerar horizontalmente."
    ),
    "Ángulo de rotación respecto a la vertical (theta)": (
        "Inclinación del eje de los rotores atan(FX/FL). Si mres baja mucho respecto a FD, el ángulo theta crece y exige verificar el límite mecánico thmax."
    ),
    "Sustentación vertical máxima de los 4 motores (FLmax)": (
        "Empuje vertical disponible √((N·Tmax1)² − FX²) tras descontar la componente horizontal FX consumida en avance."
    ),
    "Eficiencia aerodinámica de hélice según velocidad (nprop)": (
        "Degradación cuadrática nprop = nprop0·(1 − (v/vpitch)²) al aproximarse la velocidad de vuelo v a la velocidad de paso teórico vpitch de la hélice."
    ),
    "Eficiencia propulsiva global (ntot)": (
        "Rendimiento eléctrico-a-aerodinámico conjunto de los 4 brazos: nprop·nm·nESC."
    ),
    "Potencia eléctrica demandada por los 4 motores (Pelec)": (
        "Combina teoría de disco actuador inducido km·Ttot^(3/2)/(ntot·√(2·ρ₁·N·Ap)) con la potencia útil de traslación FX·v/ntot. km (> 1) compensa pérdidas de punta de pala, estela e interferencia."
    ),
    "Potencia eléctrica total a bordo (Ptot)": (
        "Suma la potencia eléctrica motriz Pelec más la carga base Pad de electrónica (controladora, cámara de video, enlace/antena y pérdidas de perfil en vacío)."
    ),
    "Masa de batería por energía de misión (mbe)": (
        "Masa mínima requerida por autonomía de misión Ereq/(ebat·DoD·ntemp), protegiendo la vida de la celda mediante DoD (~0.80) y derrateo térmico ntemp."
    ),
    "Masa de batería por potencia pico (mbp)": (
        "Masa mínima exigida por descarga continua Ptot/(ebat·Cmax·ntemp) para no superar la tasa segura de corriente Cmax de las celdas."
    ),
    "Masa de batería requerida (mbat)": (
        "Elige el criterio más restrictivo entre energía y potencia (max(mbe, mbp) mediante sp.Max), cerrando el bucle hacia la masa del artefacto mart."
    ),
}


def nota_ecuacion(nombre_eq: str) -> str:
    """Devuelve la explicación física breve asociada a una ecuación no trivial, o cadena vacía."""
    return NOTAS_ECUACIONES.get(nombre_eq, "")


def validar_integridad_flujo() -> None:
    """Verifica consistencia exacta entre `modelo.CATEGORIAS`, `FLUJO_CATEGORIAS` y `CONEXIONES_INTER_CATEGORIAS`."""
    cats = list(modelo.CATEGORIAS.items())
    assert len(FLUJO_CATEGORIAS) == len(cats), (
        f"FLUJO_CATEGORIAS ({len(FLUJO_CATEGORIAS)}) no coincide con CATEGORIAS ({len(cats)})"
    )
    eqs_totales = {nom_eq for _, eqs_cat in cats for nom_eq in eqs_cat}
    faltantes_notas = set(NOTAS_ECUACIONES) - eqs_totales
    assert not faltantes_notas, f"NOTAS_ECUACIONES referencia ecuaciones inexistentes: {faltantes_notas}"

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
        cats_eq = modelo.categorias_de_ecuacion(nodo["eq"])
        nodos_enriquecidos.append({
            **nodo,
            "es_compartida": len(cats_eq) > 1,
            "categorias_codigo_str": ", ".join(cod for _, cod, _ in cats_eq),
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
