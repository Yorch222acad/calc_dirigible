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

import formateo
import modelo


def _area_semielipsoide(R: float, c: float) -> float:
    """Calcula el área superficial lateral de un semielipsoide de radio R y semieje axial c."""
    if c <= 0 or R <= 0:
        return 0.0
    if abs(c - R) < 1e-9:
        return 2.0 * math.pi * R * R
    if c > R:
        # Prolado
        e_val = math.sqrt(max(0.0, 1.0 - (R * R) / (c * c)))
        return math.pi * R * c * math.asin(e_val) / e_val
    # Oblado (por si en un barrido extremo c < R)
    e_val = math.sqrt(max(0.0, 1.0 - (c * c) / (R * R)))
    return math.pi * R * R + (math.pi * c * c / e_val) * math.atanh(min(0.999999, e_val))


def simular_punto(base: dict[str, float], **overrides: float) -> dict[str, float] | None:
    """
    Evalúa en ~15 microsegundos el punto de equilibrio físico a partir del estado `base`
    aplicando las variaciones `overrides` (p. ej. lam=..., mflot=..., dm=..., v=..., e=...).
    """
    p = dict(base)
    p.update(overrides)

    try:
        P1, T1, R1 = p["P1"], p["T1"], p["R1"]
        P2, T2, R2 = p["P2"], p["T2"], p["R2"]
        rho1 = P1 / (R1 * (T1 + 273.15))
        rho2 = P2 / (R2 * (T2 + 273.15))
        drho = rho1 - rho2
        dT = T2 - T1
        if drho <= 0 or dT <= 0:
            return None

        g = p["g"]
        lam = p["lam"]
        xf = p["xf"]
        mflot = p["mflot"]
        if lam <= 0.4 or mflot <= 0.05:
            return None

        F = mflot * g
        V = F / (drho * g)
        # V = (2/3) * pi * R^2 * L = (4/3) * pi * lam * R^3
        R = ((3.0 * V) / (4.0 * math.pi * lam)) ** (1.0 / 3.0)
        D = 2.0 * R
        L = lam * D
        cf = xf * L
        cr = L - cf

        Sf = _area_semielipsoide(R, cf)
        Sr = _area_semielipsoide(R, cr)
        S = Sf + Sr

        m = rho2 * V
        cp = p["cp"]
        Q = m * cp * dT

        v = max(0.2, p["v"])
        if "tm" in overrides and "dm" not in overrides and "v" not in overrides:
            tm = max(1.0, overrides["tm"])
            dm = v * tm
        else:
            dm = max(1.0, p["dm"])
            tm = dm / v

        mu, kp = p["mu"], p["kp"]
        ReL = (rho1 * v * L) / mu
        if ReL <= 10.0:
            return None
        Cf = 0.455 / ((math.log10(ReL)) ** 2.58)
        CDVc = Cf * (4.0 * (lam ** (1.0 / 3.0)) + 6.0 * (lam ** -1.2) + 24.0 * (lam ** -2.7))
        CDV = kp * CDVc
        FD = 0.5 * rho1 * (v ** 2) * CDV * (V ** (2.0 / 3.0))

        e = max(1e-5, p["e"])
        W = p["W"]
        ep, ke, fcal = p["ep"], p["ke"], p["fcal"]
        beta, nu, alpha = p["beta"], p["nu"], p["alpha"]
        Rac, ka, sigma = p["Rac"], p["ka"], p["sigma"]

        Pr = nu / alpha
        Nue = 0.037 * (ReL ** 0.8) * (Pr ** (1.0 / 3.0))
        he = (Nue * ka) / L

        # Caso 1 (Independiente): Casco sin capa celular (dTi0, RaD0, Nui0, hi0, U0)
        dTi0 = max(1.0, base.get("dTi0", 0.65 * dT))
        for _ in range(10):
            RaD0 = (g * beta * max(1e-4, dTi0) * (D ** 3)) / (nu * alpha)
            Nui0 = 0.13 * (RaD0 ** (1.0 / 3.0))
            hi0 = fcal * (Nui0 * ka) / D
            U0 = 1.0 / ((1.0 / hi0) + (ep / ke) + (1.0 / he))
            nuevo_dTi0 = (U0 / hi0) * dT
            if abs(nuevo_dTi0 - dTi0) < 1e-7:
                dTi0 = nuevo_dTi0
                break
            dTi0 = nuevo_dTi0

        # Caso 2 (Independiente): Casco con capa celular (dTi, RaD, Nui, hi, dTcel, Rae, Nuc, U)
        dTi = max(1.0, base.get("dTi", 0.35 * dT))
        dTcel = max(1.0, base.get("dTcel", 0.45 * dT))
        for _ in range(12):
            RaD = (g * beta * max(1e-4, dTi) * (D ** 3)) / (nu * alpha)
            Nui = 0.13 * (RaD ** (1.0 / 3.0))
            hi = fcal * (Nui * ka) / D
            Rae = (g * beta * max(1e-4, dTcel) * (e ** 3)) / (nu * alpha)
            Nuc = 1.0 + ((Rae / Rac) ** 0.25) + (e / W) * ((Rae / Rac) ** 0.75)
            U = 1.0 / ((1.0 / hi) + (2.0 * ep / ke) + (e / (ka * Nuc)) + (1.0 / he))
            nuevo_dTi = (U / hi) * dT
            nuevo_dTcel = max(1e-4, ((U * e) / (ka * Nuc)) * dT)
            if abs(nuevo_dTi - dTi) < 1e-7 and abs(nuevo_dTcel - dTcel) < 1e-7:
                dTi, dTcel = nuevo_dTi, nuevo_dTcel
                break
            dTi, dTcel = nuevo_dTi, nuevo_dTcel

        Qp0 = U0 * S * dT
        Qp = U * S * dT
        dQp = Qp0 - Qp
        fais = dQp / Qp0 if Qp0 > 0 else 0.0
        Sc = S * (1.0 + 2.0 * e / W)
        mc = Sc * sigma

        dTc = p["dTc"]
        PC = p["PC"]
        ncal = p["ncal"]
        vT = Qp / (m * cp)
        Qc = m * cp * dTc
        tc = Qc / Qp
        mgc = Qc / (ncal * PC)

        Em0 = Qp0 * tm
        Em = Qp * tm
        Eah = dQp * tm
        mgm = Em / (ncal * PC)

        N, mmot, mp, mad, mcarga, fap = p["N"], p["mmot"], p["mp"], p["mad"], p["mcarga"], p["fap"]
        vz, vx, ta = p["vz"], p["vx"], p["ta"]
        az = vz / ta
        ax = vx / ta
        dp = p["dp"]
        Ap = math.pi * (dp ** 2) / 4.0
        ntot = p["nprop"] * p["nm"] * p["nESC"]
        km = p["km"]
        ebat, DoD, ntemp = p["ebat"], p["DoD"], p["ntemp"]
        Tmax1 = p["Tmax1"]

        # Iteración de punto fijo para el lazo cerrado masa <-> batería <-> propulsión
        mbat = max(0.005, base.get("mbat", 0.02))
        for _ in range(12):
            mart = mc + N * mmot + mp + mad + mbat
            mtot = mart + mcarga
            mres = mtot - mflot
            map_val = fap * mtot
            FL = mres * g + mtot * az
            FX = FD + map_val * ax
            Ttot = math.hypot(FL, FX)
            Pelec = (km / ntot) * (
                (Ttot ** 1.5) / math.sqrt(2.0 * rho1 * N * Ap) + FX * v
            )
            Ereq = (Pelec * tm) / 3600.0
            nuevo_mbat = Ereq / (ebat * DoD * ntemp)
            if abs(nuevo_mbat - mbat) < 1e-9:
                mbat = nuevo_mbat
                break
            mbat = nuevo_mbat

        if not math.isfinite(mbat) or mbat < 0 or mbat > 25.0:
            return None

        celec = Ereq / dm
        Etot = Em + 3600.0 * Ereq
        ctot = Etot / dm
        theta = math.degrees(math.atan2(FX, FL)) if FL > 0 else 90.0
        cap_sq = (N * Tmax1) ** 2 - FX ** 2
        FLmax = math.sqrt(cap_sq) if cap_sq > 0 else 0.0
        Fexc = F + FLmax - mtot * g

        return {
            "lam": lam,
            "R": R,
            "D": D,
            "L": L,
            "cf": cf,
            "cr": cr,
            "V": V,
            "S": S,
            "F": F,
            "e": e,
            "Rae": Rae,
            "U": U,
            "Qp0": Qp0,
            "Qp": Qp,
            "dQp": dQp,
            "fais": fais,
            "mc": mc,
            "Qc": Qc,
            "mgc": mgc,
            "v": v,
            "dm": dm,
            "tm": tm,
            "Em0": Em0,
            "Em": Em,
            "Eah": Eah,
            "mgm": mgm,
            "FD": FD,
            "mart": mart,
            "mtot": mtot,
            "mflot": mflot,
            "mres": mres,
            "FL": FL,
            "FX": FX,
            "Ttot": Ttot,
            "theta": theta,
            "FLmax": FLmax,
            "Fexc": Fexc,
            "Pelec": Pelec,
            "Ereq": Ereq,
            "Eelec_J": 3600.0 * Ereq,
            "Etot": Etot,
            "ctot": ctot,
            "mbat": mbat,
        }
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


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

    # Encontrar el punto de mínima energía total en el barrido de esbeltez
    opt_lam = min(pts_lam, key=lambda d: d["Etot"]) if pts_lam else None

    grafica_esbeltez = {
        "id": "esbeltez",
        "indice": 1,
        "titulo": "Esbeltez (λ) vs. Energía Total y Dimensiones (L, D)",
        "titulo_corto": "Esbeltez vs. Energía y Casco",
        "subtitulo": (
            "Cómo varía la Energía Total Consumida (térmica + eléctrica), la Masa Total y "
            "la Geometría del Dirigible (Longitud L y Diámetro máximo D) respecto a la Relación de Esbeltez (λ = L/D)."
        ),
        "variables": vars_meta(["lam", "L", "D", "R", "Etot", "mtot", "Em", "Ereq", "FD"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Relación de Esbeltez (λ) vs. Energía Consumida Total y Masa Total",
                "x_label": "Relación de esbeltez λ = L/D (adim)",
                "x_actual": lam_actual,
                "x_optimo": opt_lam["lam"] if opt_lam else None,
                "x_optimo_label": f"Mín. Etot (λ={opt_lam['lam']:.2f})" if opt_lam else "",
                "y1_label": "Energía en misión (kJ)",
                "y2_label": "Energía eléctrica (kJ) / Masa total (kg)",
                "xs": [round(p["lam"], 4) for p in pts_lam],
                "series": [
                    {
                        "nombre": "Energía total consumida (Etot)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#38bdf8",
                        "valores": [round(p["Etot"] / 1000.0, 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Energía térmica perdida (Em)",
                        "unidad": "kJ",
                        "eje": "y1",
                        "color": "#f97316",
                        "dashed": True,
                        "valores": [round(p["Em"] / 1000.0, 3) for p in pts_lam],
                    },
                    {
                        "nombre": "Energía eléctrica motores (3600·Ereq)",
                        "unidad": "kJ",
                        "eje": "y2",
                        "color": "#facc15",
                        "valores": [round(p["Eelec_J"] / 1000.0, 3) for p in pts_lam],
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
            {
                "tipo": "lineas_doble_eje",
                "titulo": "B. Relación de Esbeltez (λ) vs. Longitud (L), Diámetro Máximo (D) y Arrastre (FD)",
                "x_label": "Relación de esbeltez λ = L/D (adim)",
                "x_actual": lam_actual,
                "y1_label": "Dimensiones del casco: L y D (m)",
                "y2_label": "Resistencia aerodinámica FD (N)",
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
                        "nombre": "Fuerza de arrastre aerodinámico (FD)",
                        "unidad": "N",
                        "eje": "y2",
                        "color": "#f87171",
                        "valores": [round(p["FD"], 3) for p in pts_lam],
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
        "variables": vars_meta(["mflot", "mres", "mtot", "F", "FL", "FLmax", "Fexc", "Etot"]),
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
                "titulo": "B. Variación de Fuerzas (F, FL), Carga de Motores (mres) y Masa Total (mtot) según mflot",
                "x_label": "Carga de sustentación destinada al aire caliente mflot (kg)",
                "x_actual": mflot_actual,
                "y1_label": "Fuerza vertical de sustentación (N)",
                "y2_label": "Masas: mres y mtot (kg)",
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
    # 3. DISTANCIA (dm) Y TIEMPO DE VUELO (tm) vs. ENERGÍA TOTAL Y PROPANO
    # =========================================================
    dm_actual = valores["dm"]
    dm_min = max(40.0, min(60.0, dm_actual * 0.25))
    dm_max = max(750.0, dm_actual * 2.5)
    xs_dm = _linspace(dm_min, dm_max, 42, incluir=dm_actual)
    pts_dm = [p for x in xs_dm if (p := simular_punto(valores, dm=x)) is not None]

    v_actual = valores["v"]
    xs_v = _linspace(1.5, 9.0, 42, incluir=v_actual)
    pts_v = [p for x in xs_v if (p := simular_punto(valores, v=x)) is not None]
    opt_v = min(pts_v, key=lambda d: d["Etot"]) if pts_v else None

    grafica_distancia = {
        "id": "distancia_tiempo",
        "indice": 3,
        "titulo": "Distancia (dm) y Tiempo de Vuelo (tm) vs. Energía Total y Propano",
        "titulo_corto": "Distancia y Tiempo de Vuelo",
        "subtitulo": (
            "Cómo escalan el Tiempo de Vuelo (tm), la Energía Consumida en Total (Etot) y la Masa de Propano "
            "necesaria (mgm) con la Distancia (dm), y el compromiso velocidad/tiempo para cubrir la distancia fija."
        ),
        "variables": vars_meta(["dm", "tm", "v", "Etot", "mgm", "mtot", "ctot", "Em", "Ereq"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Distancia a Recorrer (dm) vs. Tiempo de Vuelo (tm), Energía Total (Etot) y Propano (mgm)",
                "x_label": "Distancia de misión dm (m)",
                "x_actual": dm_actual,
                "x_optimo": 240.0,
                "x_optimo_label": "Base 240 m",
                "y1_label": "Energía total Etot (kJ) / Tiempo tm (s)",
                "y2_label": "Masa de propano mgm (g) / Masa total mtot (kg)",
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
                        "nombre": "Masa de propano necesaria (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(p["mgm"] * 1000.0, 3) for p in pts_dm],
                    },
                    {
                        "nombre": "Masa total del dirigible (mtot)",
                        "unidad": "kg",
                        "eje": "y2",
                        "color": "#4ade80",
                        "valores": [round(p["mtot"], 4) for p in pts_dm],
                    },
                ],
            },
            {
                "tipo": "lineas_doble_eje",
                "titulo": f"B. Efecto de la Velocidad (v) y Tiempo de Vuelo (tm = dm/v) para recorrer dm = {dm_actual:.0f} m",
                "x_label": "Velocidad de crucero v (m/s)  [← más tiempo tm | menos tiempo tm →]",
                "x_actual": v_actual,
                "x_optimo": opt_v["v"] if opt_v else None,
                "x_optimo_label": f"Mín. Etot (v={opt_v['v']:.2f} m/s)" if opt_v else "",
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
    # 4. ESPESOR DEL AISLANTE CELULAR (e) vs. ENERGÍA AHORRADA Y PERDIDA
    # =========================================================
    e_actual_mm = valores["e"] * 1000.0
    xs_e_mm = _linspace(1.5, 65.0, 48, incluir=e_actual_mm)
    pts_e = [p for x_mm in xs_e_mm if (p := simular_punto(valores, e=x_mm / 1000.0)) is not None]

    # Espesor óptimo donde la pérdida térmica Em es mínima (y el ahorro Eah es máximo)
    opt_e = min(pts_e, key=lambda d: d["Em"]) if pts_e else None
    opt_e_mm = round(opt_e["e"] * 1000.0, 2) if opt_e else None

    grafica_aislante = {
        "id": "aislante",
        "indice": 4,
        "titulo": "Espesor del Aislante Celular (e) vs. Energía Ahorrada y Perdida",
        "titulo_corto": "Aislante: Ahorro vs. Pérdida",
        "subtitulo": (
            "Cómo influye el Espesor de la Capa Celular (e) en la Energía Ahorrada (Eah), la Energía Perdida (Em), "
            "el Número de Nusselt celular (Nuc), la Masa de Propano necesaria (mgm) y la Masa Total (mtot)."
        ),
        "variables": vars_meta(["e", "dTi0", "hi0", "U0", "dTi", "hi", "dTcel", "Nuc", "U", "he", "Eah", "Em", "Em0", "mc", "mtot", "mgm"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": "A. Espesor del Aislante (e) vs. Energía Ahorrada (Eah), Energía Perdida (Em) y Propano (mgm)",
                "x_label": "Espesor del aislante celular e (mm)",
                "x_actual": round(e_actual_mm, 2),
                "x_optimo": opt_e_mm,
                "x_optimo_label": f"Óptimo térmico ({opt_e_mm:.1f} mm)" if opt_e_mm else "",
                "y1_label": "Energía térmica en misión (kJ)",
                "y2_label": "Masa de propano necesaria mgm (g)",
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
                        "nombre": "Masa de propano necesaria (mgm)",
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
    # 5. BALANCE TÉRMICO, ENERGÍA PERDIDA/AHORRADA Y PROPANO EN EL VUELO
    # =========================================================
    tm_actual = valores["tm"]
    ts_vuelo = _linspace(0.0, tm_actual, 36)
    qp0_w = valores["Qp0"]
    qp_w = valores["Qp"]
    dqp_w = valores["dQp"]
    pelec_w = valores["Pelec"]
    pc_ef = valores["ncal"] * valores["PC"]

    grafica_propano = {
        "id": "propano_energia",
        "indice": 5,
        "titulo": "Energía Perdida, Energía Ahorrada y Propano (mgm) en el Vuelo",
        "titulo_corto": "Propano y Balance Térmico",
        "subtitulo": (
            "Evolución acumulada a lo largo del Tiempo de Vuelo (tm) de la Energía Perdida, la Energía Ahorrada "
            "gracias al aislante, la Energía Total Consumida y la Masa de Propano necesaria (con eficiencia ncal)."
        ),
        "variables": vars_meta(["mgm", "ncal", "fcal", "Em", "Eah", "Em0", "Etot", "Qc", "mgc", "mp", "tm", "dm"]),
        "paneles": [
            {
                "tipo": "lineas_doble_eje",
                "titulo": f"A. Evolución Temporal Acumulada durante el Vuelo (0 → {tm_actual:.1f} s / {valores['dm']:.0f} m)",
                "x_label": "Tiempo transcurrido de vuelo t (s)",
                "x_actual": round(tm_actual, 2),
                "y1_label": "Energía acumulada (kJ)",
                "y2_label": "Masa de propano consumida mgm (g)",
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
                        "valores": [round(((qp_w + pelec_w) * t) / 1000.0, 3) for t in ts_vuelo],
                    },
                    {
                        "nombre": "Masa de propano consumida (mgm)",
                        "unidad": "g",
                        "eje": "y2",
                        "color": "#f97316",
                        "valores": [round(((qp_w * t) / pc_ef) * 1000.0, 3) for t in ts_vuelo],
                    },
                ],
            },
            {
                "tipo": "barras_comparativas",
                "titulo": "B. Resumen Comparativo de Energías de Misión (kJ) y Masa de Propano (g)",
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
                                "etiqueta": "Total Consumida (Etot)",
                                "codigo": "Etot",
                                "valor": round(valores["Etot"] / 1000.0, 3),
                                "color": "#38bdf8",
                                "detalle": f"Em + {valores['Ereq']:.2f} Wh eléc.",
                            },
                        ],
                    },
                    {
                        "subtitulo": "Masa de Propano Requerida vs. Disponible (g)",
                        "unidad": "g",
                        "barras": [
                            {
                                "etiqueta": "Propano para terminar el vuelo (mgm)",
                                "codigo": "mgm",
                                "valor": round(valores["mgm"] * 1000.0, 3),
                                "color": "#f97316",
                                "detalle": f"Misión de {valores['dm']:.0f} m ({valores['tm']:.1f} s)",
                            },
                            {
                                "etiqueta": "Propano para recuperar caída dTc (mgc)",
                                "codigo": "mgc",
                                "valor": round(valores["mgc"] * 1000.0, 3),
                                "color": "#facc15",
                                "detalle": f"Caída dTc = {valores['dTc']:.0f} K",
                            },
                            {
                                "etiqueta": "Propano total a bordo (mp)",
                                "codigo": "mp",
                                "valor": round(valores["mp"] * 1000.0, 3),
                                "color": "#4ade80",
                                "detalle": f"Autonomía térmica x{(valores['mp'] / max(1e-9, valores['mgm'])):.1f} vuelos",
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
                        "etiqueta": "Cuadrícula aislante celular (mc)",
                        "codigo": "mc",
                        "valor_g": round(valores["mc"] * 1000.0, 2),
                        "color": "#4ade80",
                    },
                    {
                        "etiqueta": "Propano a bordo (mp)",
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

    return [
        grafica_esbeltez,
        grafica_sustentacion,
        grafica_distancia,
        grafica_aislante,
        grafica_propano,
        grafica_geometria,
    ]
