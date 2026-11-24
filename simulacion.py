"""
Capa 2 (Simulación temporal por fases y enfriamiento pasivo) y Capa 3 (Optimizador
automático multidimensional) construidas encima del evaluador rápido con tearing (`evaluador.py`).
"""
from __future__ import annotations

import math
import time
from typing import Any

import evaluador


_OBJETIVOS_VALIDOS = ("Etot", "mtot", "mbat", "mgm")
_VARS_OPTIMIZABLES = ("lam", "v", "mflot", "e")
_PRIMOS_HALTON = (2, 3, 5, 7)


def _halton(indice: int, base: int) -> float:
    """Secuencia cuasialeatoria determinista de Halton en (0, 1)."""
    f = 1.0
    r = 0.0
    i = indice
    while i > 0:
        f /= base
        r += f * (i % base)
        i //= base
    return r


def simular_mision_fases(valores: dict[str, float]) -> dict[str, Any]:
    """
    Capa 2: Descompone la misión en:
      - Fase 1: Arranque y aceleración de maniobra (0 -> t_man, con az y ax activos)
      - Fase 2: Crucero estacionario (t_man -> tm, con az=0, ax=0)
    Además integra paso a paso (RK2) el enfriamiento pasivo no lineal T2(t) sin quemador.
    """
    tm = max(1e-3, float(valores["tm"]))
    dm = float(valores["dm"])
    vg = float(valores["vg"])
    ta = float(valores["ta"])
    t_man = min(ta, tm * 0.45)
    t_cruc = max(0.0, tm - t_man)

    # Fase 1: Maniobra inicial (con az, ax del modelo CAS)
    FL_man = float(valores["FL"])
    FX_man = float(valores["FX"])
    Ttot_man = float(valores["Ttot"])
    theta_man = float(valores["theta"])
    Pelec_man = float(valores["Pelec"])
    Pad = float(valores["Pad"])
    Ptot_man = Pelec_man + Pad

    # Fase 2: Crucero estacionario (az = 0, ax = 0)
    FL_cruc = float(valores["mres"]) * float(valores["g"])
    FX_cruc = float(valores["FD"])
    Ttot_cruc = math.hypot(FL_cruc, FX_cruc)
    theta_cruc = math.degrees(math.atan2(FX_cruc, FL_cruc)) if FL_cruc > 0.0 else 90.0
    Pelec_cruc = (float(valores["km"]) / float(valores["ntot"])) * (
        (Ttot_cruc ** 1.5) / math.sqrt(2.0 * float(valores["rho1"]) * float(valores["N"]) * float(valores["Ap"]))
        + FX_cruc * float(valores["v"])
    )
    Ptot_cruc = Pelec_cruc + Pad

    # Energías integradas por fases reales vs. CAS conservador
    Eelec_fases_j = Ptot_man * t_man + Ptot_cruc * t_cruc
    Ereq_fases_wh = Eelec_fases_j / 3600.0
    Eprop_j = float(valores["Eprop"])
    Etot_fases_j = Eprop_j + Eelec_fases_j
    Pprop_equiv_w = Eprop_j / tm

    ebat = float(valores["ebat"])
    DoD = float(valores["DoD"])
    ntemp = float(valores["ntemp"])
    Cmax = float(valores["Cmax"])

    mbe_fases = Ereq_fases_wh / (ebat * DoD * ntemp)
    mbp_pico = Ptot_man / (ebat * Cmax * ntemp)
    mbat_fases = max(mbe_fases, mbp_pico)

    Eelec_cas_j = float(valores["Eelec"])
    Etot_cas_j = float(valores["Etot"])
    ahorro_elec_pct = 100.0 * (Eelec_cas_j - Eelec_fases_j) / max(1e-9, Eelec_cas_j)
    ahorro_tot_pct = 100.0 * (Etot_cas_j - Etot_fases_j) / max(1e-9, Etot_cas_j)

    # Perfil temporal muestreado (asegurando el instante de transición t_man)
    n_cruc = 52
    n_man = 14
    ts_raw: list[float] = []
    for i in range(n_man):
        ts_raw.append((t_man * i) / max(1, n_man - 1))
    eps_t = max(1e-4, tm * 1e-4)
    if t_cruc > 2.0 * eps_t:
        for i in range(n_cruc):
            t_val = (t_man + eps_t) + ((tm - (t_man + eps_t)) * i) / max(1, n_cruc - 1)
            ts_raw.append(min(tm, t_val))

    ts: list[float] = []
    xs_dist: list[float] = []
    ptot_w: list[float] = []
    pelec_w: list[float] = []
    pad_w: list[float] = []
    ttot_n: list[float] = []
    theta_deg: list[float] = []
    eelec_acum_kj: list[float] = []
    eprop_acum_kj: list[float] = []
    etot_acum_kj: list[float] = []
    fase_ids: list[int] = []

    for t in ts_raw:
        en_man = t <= t_man + 1e-9
        pt = Ptot_man if en_man else Ptot_cruc
        pe = Pelec_man if en_man else Pelec_cruc
        tt = Ttot_man if en_man else Ttot_cruc
        th = theta_man if en_man else theta_cruc
        if en_man:
            e_el_j = Ptot_man * t
        else:
            e_el_j = Ptot_man * t_man + Ptot_cruc * (t - t_man)
        e_pr_j = Pprop_equiv_w * t
        ts.append(round(t, 2))
        xs_dist.append(round(min(dm, vg * t), 2))
        ptot_w.append(round(pt, 2))
        pelec_w.append(round(pe, 2))
        pad_w.append(round(Pad, 2))
        ttot_n.append(round(tt, 3))
        theta_deg.append(round(th, 2))
        eelec_acum_kj.append(round(e_el_j / 1000.0, 3))
        eprop_acum_kj.append(round(e_pr_j / 1000.0, 3))
        etot_acum_kj.append(round((e_el_j + e_pr_j) / 1000.0, 3))
        fase_ids.append(1 if en_man else 2)

    # Integración temporal no lineal (RK2) de enfriamiento pasivo sin quemador
    T2_0 = float(valores["T2"])
    T1 = float(valores["T1"])
    dTc = float(valores["dTc"])
    T2_obj = T2_0 - dTc
    tc_lin = float(valores["tc"])
    vT_lin = float(valores["vT"])
    cp = float(valores["cp"])

    t_fin_enf = max(10.0, tc_lin * 1.4)
    n_enf = 60
    dt_enf = t_fin_enf / (n_enf - 1)

    t_enf_list = [0.0]
    t2_nl_list = [round(T2_0, 3)]
    t2_lin_list = [round(T2_0, 3)]

    T2_curr = T2_0
    tc_nolineal: float | None = None

    for k in range(1, n_enf):
        t_curr = k * dt_enf
        ev1 = evaluador.evaluar_termica_T2(valores, T2_curr)
        if ev1 is not None and ev1[1] > 0.0:
            qp1, m1 = ev1
            k1 = -qp1 / (m1 * cp)
            T2_mid = max(T1 + 0.1, T2_curr + 0.5 * dt_enf * k1)
            ev2 = evaluador.evaluar_termica_T2(valores, T2_mid)
            if ev2 is not None and ev2[1] > 0.0:
                qp2, m2 = ev2
                k2 = -qp2 / (m2 * cp)
                T2_next = max(T1 + 0.05, T2_curr + dt_enf * k2)
            else:
                T2_next = max(T1 + 0.05, T2_curr + dt_enf * k1)
        else:
            T2_next = max(T1 + 0.05, T2_curr - vT_lin * dt_enf)

        if tc_nolineal is None and T2_curr >= T2_obj >= T2_next and (T2_curr - T2_next) > 1e-12:
            frac = (T2_curr - T2_obj) / (T2_curr - T2_next)
            tc_nolineal = (k - 1 + frac) * dt_enf

        T2_curr = T2_next
        t_enf_list.append(round(t_curr, 2))
        t2_nl_list.append(round(T2_curr, 3))
        t2_lin_list.append(round(max(T1, T2_0 - vT_lin * t_curr), 3))

    return {
        "resumen_fases": {
            "t_man": round(t_man, 2),
            "t_cruc": round(t_cruc, 2),
            "tm": round(tm, 2),
            "Pad": round(Pad, 2),
            "Pelec_man": round(Pelec_man, 2),
            "Ptot_man": round(Ptot_man, 2),
            "Ttot_man": round(Ttot_man, 3),
            "theta_man": round(theta_man, 2),
            "Pelec_cruc": round(Pelec_cruc, 2),
            "Ptot_cruc": round(Ptot_cruc, 2),
            "Ttot_cruc": round(Ttot_cruc, 3),
            "theta_cruc": round(theta_cruc, 2),
            "Eelec_cas_kj": round(Eelec_cas_j / 1000.0, 3),
            "Eelec_fases_kj": round(Eelec_fases_j / 1000.0, 3),
            "ahorro_elec_pct": round(ahorro_elec_pct, 2),
            "Etot_cas_kj": round(Etot_cas_j / 1000.0, 3),
            "Etot_fases_kj": round(Etot_fases_j / 1000.0, 3),
            "ahorro_tot_pct": round(ahorro_tot_pct, 2),
            "mbe_cas_g": round(float(valores["mbe"]) * 1000.0, 2),
            "mbe_fases_g": round(mbe_fases * 1000.0, 2),
            "mbp_pico_g": round(mbp_pico * 1000.0, 2),
            "mbat_cas_g": round(float(valores["mbat"]) * 1000.0, 2),
            "mbat_fases_g": round(mbat_fases * 1000.0, 2),
        },
        "perfil_vuelo": {
            "ts": ts,
            "xs_dist": xs_dist,
            "ptot_w": ptot_w,
            "pelec_w": pelec_w,
            "pad_w": pad_w,
            "ttot_n": ttot_n,
            "theta_deg": theta_deg,
            "eelec_acum_kj": eelec_acum_kj,
            "eprop_acum_kj": eprop_acum_kj,
            "etot_acum_kj": etot_acum_kj,
            "fase_ids": fase_ids,
        },
        "enfriamiento": {
            "ts": t_enf_list,
            "T2_nolineal": t2_nl_list,
            "T2_lineal": t2_lin_list,
            "T2_inicial": round(T2_0, 2),
            "T2_objetivo": round(T2_obj, 2),
            "tc_lineal": round(tc_lin, 2),
            "tc_nolineal": round(tc_nolineal, 2) if tc_nolineal is not None else round(t_fin_enf, 2),
        },
    }


def _metricas_punto(sol: dict[str, float]) -> dict[str, Any]:
    return {
        "lam": round(sol["lam"], 4),
        "v": round(sol["v"], 4),
        "mflot": round(sol["mflot"], 4),
        "e": round(sol["e"], 6),
        "e_mm": round(sol["e"] * 1000.0, 2),
        "Etot": sol["Etot"],
        "Etot_kj": round(sol["Etot"] / 1000.0, 3),
        "Eprop_kj": round(sol["Eprop"] / 1000.0, 3),
        "Eelec_kj": round(sol["Eelec"] / 1000.0, 3),
        "mtot": round(sol["mtot"], 4),
        "mbat_g": round(sol["mbat"] * 1000.0, 2),
        "mgm_g": round(sol["mgm"] * 1000.0, 2),
        "Pelec_w": round(sol["Pelec"], 2),
        "Ptot_w": round(sol["Ptot"], 2),
        "Ttot_n": round(sol["Ttot"], 2),
        "theta_deg": round(sol["theta"], 2),
        "tm_s": round(sol["tm"], 1),
        "valido": bool(sol.get("valido", False)),
    }


def optimizar_diseno(
    valores: dict[str, float],
    objetivo: str = "Etot",
    vars_libres: list[str] | None = None,
) -> dict[str, Any]:
    """
    Capa 3: Optimiza combinaciones de `(lam, v, mflot, e)` sobre el evaluador rápido
    para minimizar `objetivo` ('Etot', 'mtot', 'mbat' o 'mgm') respetando todas las
    restricciones físicas (`mbat <= mbmax`, `theta <= thmax`, `Pelec <= Pmax`,
    `Ttot <= N*Tmax1`, `Fexc >= 0`, `cf > R`, `cr > R`).
    """
    if objetivo not in _OBJETIVOS_VALIDOS:
        raise ValueError(f"Objetivo inválido '{objetivo}'. Opciones: {', '.join(_OBJETIVOS_VALIDOS)}")

    t_ini = time.perf_counter()
    elegidas = [v for v in (vars_libres or list(_VARS_OPTIMIZABLES)) if v in _VARS_OPTIMIZABLES]
    if not elegidas:
        elegidas = list(_VARS_OPTIMIZABLES)

    vv = max(0.0, float(valores.get("vv", 0.0)))
    vpitch = float(valores["vpitch"])
    v_lo = max(0.8, vv + 0.4)
    v_hi = min(vpitch * 0.88, max(9.5, vv + 6.5))
    if v_hi <= v_lo + 0.2:
        v_hi = min(vpitch * 0.94, v_lo + 2.0)

    rangos: dict[str, tuple[float, float]] = {
        "lam": (1.5, 5.5),
        "v": (v_lo, v_hi),
        "mflot": (0.6, max(4.2, float(valores["mtot"]) * 1.15)),
        "e": (0.002, 0.060),
    }

    evaluaciones = 0
    validos: list[tuple[float, dict[str, float], dict[str, float]]] = []

    def evaluar_cand(ov: dict[str, float]) -> dict[str, float] | None:
        nonlocal evaluaciones
        evaluaciones += 1
        sol = evaluador.evaluar_punto(valores, estricto_prolado=True, **ov)
        if sol is not None and sol["valido"]:
            validos.append((sol[objetivo], ov, sol))
        return sol

    # 1. Evaluar punto actual como línea base
    ov_actual = {v: float(valores[v]) for v in elegidas}
    sol_actual = evaluador.evaluar_punto(valores, estricto_prolado=True) or dict(valores)
    if sol_actual.get("valido"):
        validos.append((sol_actual[objetivo], ov_actual, sol_actual))

    # 2. Fase 1: Exploración global Halton (500 puntos deterministas)
    n_halton = 500
    bases = [_PRIMOS_HALTON[i % len(_PRIMOS_HALTON)] for i in range(len(elegidas))]
    for k in range(1, n_halton + 1):
        ov: dict[str, float] = {}
        for d, var_nom in enumerate(elegidas):
            lo, hi = rangos[var_nom]
            ov[var_nom] = lo + (hi - lo) * _halton(k, bases[d])
        evaluar_cand(ov)

    if not validos:
        dt_ms = (time.perf_counter() - t_ini) * 1000.0
        return {
            "encontrado": False,
            "objetivo": objetivo,
            "vars_optimizadas": elegidas,
            "tiempo_ms": round(dt_ms, 2),
            "evaluaciones": evaluaciones,
            "evaluaciones_validas": 0,
            "actual": _metricas_punto(sol_actual),
            "optimo": None,
            "mejora_pct": 0.0,
            "cambios": {},
        }

    # 3. Fase 2: Refinamiento local (búsqueda por coordenadas adaptativa) desde los mejores 3
    validos.sort(key=lambda item: item[0])
    semillas_top = [(ov, sol) for _, ov, sol in validos[:3]]
    mejor_val = validos[0][0]
    mejor_ov = dict(validos[0][1])
    mejor_sol = validos[0][2]

    for ov_seed, sol_seed in semillas_top:
        curr_ov = dict(ov_seed)
        curr_val = sol_seed[objetivo]
        curr_sol = sol_seed
        for frac in (0.16, 0.06, 0.02, 0.006, 0.002):
            mejoro = True
            while mejoro:
                mejoro = False
                for var_nom in elegidas:
                    lo, hi = rangos[var_nom]
                    step = (hi - lo) * frac
                    for signo in (-1.0, 1.0):
                        cand_x = max(lo, min(hi, curr_ov[var_nom] + signo * step))
                        if abs(cand_x - curr_ov[var_nom]) < 1e-9:
                            continue
                        cand_ov = dict(curr_ov)
                        cand_ov[var_nom] = cand_x
                        cand_sol = evaluar_cand(cand_ov)
                        if cand_sol is not None and cand_sol["valido"] and cand_sol[objetivo] < curr_val * (1.0 - 1e-7):
                            curr_ov = cand_ov
                            curr_val = cand_sol[objetivo]
                            curr_sol = cand_sol
                            mejoro = True
        if curr_val < mejor_val:
            mejor_val = curr_val
            mejor_ov = curr_ov
            mejor_sol = curr_sol

    dt_ms = (time.perf_counter() - t_ini) * 1000.0
    val_actual = float(sol_actual[objetivo])
    mejora_pct = 100.0 * (val_actual - mejor_val) / max(1e-9, val_actual)

    cambios = {
        var_nom: {
            "actual": round(float(valores[var_nom]), 6),
            "optimo": round(float(mejor_sol[var_nom]), 6),
        }
        for var_nom in elegidas
    }

    return {
        "encontrado": True,
        "objetivo": objetivo,
        "vars_optimizadas": elegidas,
        "tiempo_ms": round(dt_ms, 2),
        "evaluaciones": evaluaciones,
        "evaluaciones_validas": len(validos),
        "actual": _metricas_punto(sol_actual),
        "optimo": _metricas_punto(mejor_sol),
        "mejora_pct": round(mejora_pct, 2),
        "cambios": cambios,
    }
