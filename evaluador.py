"""
Evaluador numérico puro (sin dependencias de SymPy) con descomposición por variables
de corte ("tearing") para los tres lazos acoplados del modelo del dirigible:

  1. Lazo térmico base (C4):      dTi0  -> U0
  2. Lazo térmico aislado (C5):   (dTi, dTcel) -> U
  3. Lazo masa-batería (C9-C13): mbat  -> max(mbe, mbp)

Actúa como fuente única de verdad numérica para la vía rápida de `modelo.py`,
las curvas paramétricas de `graficas.py` y el estudio de diseño en `diseno.py`.
"""
from __future__ import annotations

import math
from typing import Callable

SIGMA_SB = 5.670374419e-8


def nuc_hollands(rae: float, rac: float) -> float:
    """
    Correlación de Hollands (1976) para convección en cavidad celular superior
    con piso físico exacto en 1.0 cuando Ra_e <= Ra_c.
    """
    if rae <= rac:
        return 1.0
    t1 = 1.44 * max(0.0, 1.0 - rac / rae)
    t2 = max(0.0, (rae / 5830.0) ** (1.0 / 3.0) - 1.0)
    return 1.0 + t1 + t2


def brent_1d(
    fn: Callable[[float], float],
    a: float,
    b: float,
    tol: float = 1e-11,
    max_iter: int = 60,
) -> float | None:
    """
    Encuentra una raíz de `fn(x) = 0` en [a, b] mediante el método de Brent.
    Devuelve None si `fn(a)` y `fn(b)` tienen el mismo signo y no son cero.
    """
    fa = fn(a)
    fb = fn(b)
    if not (math.isfinite(fa) and math.isfinite(fb)):
        return None
    if fa == 0.0:
        return a
    if fb == 0.0:
        return b
    if fa * fb > 0.0:
        return None

    c, fc = a, fa
    d = e = b - a

    for _ in range(max_iter):
        if fb * fc > 0.0:
            c, fc = a, fa
            d = e = b - a
        if abs(fc) < abs(fb):
            a, b, c = b, c, b
            fa, fb, fc = fb, fc, fb

        tol1 = 2.0 * 2.220446049250313e-16 * abs(b) + 0.5 * tol
        xm = 0.5 * (c - b)
        if abs(xm) <= tol1 or fb == 0.0:
            return b

        if abs(e) >= tol1 and abs(fa) > abs(fb):
            s = fb / fa
            if a == c:
                p = 2.0 * xm * s
                q = 1.0 - s
            else:
                q_ac = fa / fc
                r_bc = fb / fc
                p = s * (2.0 * xm * q_ac * (q_ac - r_bc) - (b - a) * (r_bc - 1.0))
                q = (q_ac - 1.0) * (r_bc - 1.0) * (s - 1.0)
            if p > 0.0:
                q = -q
            p = abs(p)
            min1 = 3.0 * xm * q - abs(tol1 * q)
            min2 = abs(e * q)
            if q != 0.0 and 2.0 * p < (min1 if min1 < min2 else min2):
                e = d
                d = p / q
            else:
                d = xm
                e = d
        else:
            d = xm
            e = d

        a, fa = b, fb
        b += d if abs(d) > tol1 else (tol1 if xm > 0.0 else -tol1)
        fb = fn(b)
        if not math.isfinite(fb):
            return None

    return b


def area_semielipsoide(R: float, c: float) -> float:
    """Área superficial curva de un semielipsoide de radio R y semieje axial c (sin disco de cierre)."""
    if c <= 0.0 or R <= 0.0:
        return 0.0
    if abs(c - R) < 1e-9:
        return 2.0 * math.pi * R * R
    if c > R:
        e_val = math.sqrt(max(0.0, 1.0 - (R * R) / (c * c)))
        return math.pi * R * R + math.pi * R * c * math.asin(e_val) / e_val
    e_val = math.sqrt(max(0.0, 1.0 - (c * c) / (R * R)))
    return math.pi * R * R + (math.pi * c * c / e_val) * math.atanh(min(0.999999, e_val))


def resolver_tearing_u0(
    dT: float,
    D: float,
    g: float,
    beta: float,
    nu: float,
    alpha: float,
    fcal: float,
    ka: float,
    ep: float,
    ke: float,
    he: float,
) -> tuple[float, float, float, float, float]:
    """
    Resuelve el bloque térmico base sin aislante (C4) mediante variable de corte `dTi0`.
    Devuelve `(dTi0, RaD0, Nui0, hi0, U0)`.
    """
    k_ra = (g * beta * (D ** 3)) / (nu * alpha)
    r_ext_wall = (ep / ke) + (1.0 / he)

    def eval_u0(dti0: float) -> tuple[float, float, float, float, float]:
        rad0 = k_ra * dti0
        nui0 = 0.13 * (rad0 ** (1.0 / 3.0))
        hi0 = fcal * (nui0 * ka) / D
        u0 = 1.0 / ((1.0 / hi0) + r_ext_wall)
        return dti0, rad0, nui0, hi0, u0

    def res_dti0(dti0: float) -> float:
        _, _, _, hi0, u0 = eval_u0(dti0)
        return dti0 - (u0 / hi0) * dT

    lo = min(1e-5, dT * 1e-4)
    hi_b = max(lo * 10.0, dT * 0.9999)
    sol_dti0 = brent_1d(res_dti0, lo, hi_b, tol=1e-12)
    if sol_dti0 is None:
        # Respaldo de punto fijo en caso extremo
        sol_dti0 = 0.65 * dT
        for _ in range(40):
            _, _, _, hi0, u0 = eval_u0(sol_dti0)
            nuevo = max(1e-6, min(dT * 0.9999, (u0 / hi0) * dT))
            if abs(nuevo - sol_dti0) < 1e-11:
                sol_dti0 = nuevo
                break
            sol_dti0 = nuevo

    return eval_u0(sol_dti0)


def resolver_tearing_u(
    dT: float,
    D: float,
    e: float,
    ncapS: float,
    ncapI: float,
    g: float,
    beta: float,
    nu: float,
    alpha: float,
    fcal: float,
    ka: float,
    ep: float,
    ke: float,
    Rac: float,
    hrad: float,
    hetot: float,
    dTi_ini: float | None = None,
    dTcel_ini: float | None = None,
) -> tuple[float, float, float, float, float, float, float, float, float, float]:
    """
    Resuelve el bloque térmico asimétrico con Mylar multicapa (C5)
    mediante variables de corte `(dTi, dTcel)` con Newton 2x2 amortiguado
    y respaldo por punto fijo. Maneja sin singularidad `ncapS == 0` (`0/0` y `0/N`).
    Devuelve `(dTi, RaD, Nui, hi, dTcel, Rae, Nuc, Usup, Uinf, U)`.
    """
    if ncapS <= 0.0 and ncapI <= 0.0:
        dti0, rad0, nui0, hi0, u0 = resolver_tearing_u0(
            dT=dT, D=D, g=g, beta=beta, nu=nu, alpha=alpha,
            fcal=fcal, ka=ka, ep=ep, ke=ke, he=hetot,
        )
        return dti0, rad0, nui0, hi0, 0.0, 0.0, 1.0, u0, u0, u0

    inv_nualpha = 1.0 / (nu * alpha)
    k_rad = g * beta * (D ** 3) * inv_nualpha
    r_fijas_s = (((ncapS + 1.0) * ep) / ke) + (1.0 / hetot)
    r_fijas_i = (((ncapI + 1.0) * ep) / ke) + (1.0 / hetot)
    h_inf_cel = (ka / e) + hrad

    if ncapS <= 0.0:
        def eval_sin_sup(dti_val: float) -> tuple[float, float, float, float, float, float]:
            rad = k_rad * dti_val
            nui = 0.13 * (rad ** (1.0 / 3.0))
            hi = fcal * (nui * ka) / D
            usup = 1.0 / ((1.0 / hi) + r_fijas_s)
            uinf = 1.0 / ((1.0 / hi) + r_fijas_i + (ncapI / h_inf_cel))
            u = 0.5 * (usup + uinf)
            return rad, nui, hi, usup, uinf, u

        def res_dti(dti_val: float) -> float:
            _, _, hi, _, _, u = eval_sin_sup(dti_val)
            return dti_val - (u / hi) * dT

        lo = min(1e-5, dT * 1e-4)
        hi_b = max(lo * 10.0, dT * 0.9999)
        sol_dti = brent_1d(res_dti, lo, hi_b, tol=1e-12)
        if sol_dti is None:
            sol_dti = 0.25 * dT
            for _ in range(50):
                _, _, hi, _, _, u = eval_sin_sup(sol_dti)
                nuevo = max(1e-6, min(dT * 0.9999, (u / hi) * dT))
                if abs(nuevo - sol_dti) < 1e-11:
                    sol_dti = nuevo
                    break
                sol_dti = nuevo
        rad, nui, hi, usup, uinf, u = eval_sin_sup(sol_dti)
        return sol_dti, rad, nui, hi, 0.0, 0.0, 1.0, usup, uinf, u

    k_rae = g * beta * (e ** 3) * inv_nualpha

    def eval_vars(x1: float, x2: float) -> tuple[float, float, float, float, float, float, float, float, float]:
        rad = k_rad * x1
        nui = 0.13 * (rad ** (1.0 / 3.0))
        hi = fcal * (nui * ka) / D
        rae = k_rae * x2
        nuc = nuc_hollands(rae, Rac)
        h_sup_cel = (ka * nuc) / e + hrad
        usup = 1.0 / ((1.0 / hi) + r_fijas_s + (ncapS / h_sup_cel))
        uinf = 1.0 / ((1.0 / hi) + r_fijas_i + (ncapI / h_inf_cel))
        u = 0.5 * (usup + uinf)
        rhs2 = (usup / h_sup_cel) * dT
        return rad, nui, hi, rae, nuc, usup, uinf, u, rhs2

    def eval_res(x1: float, x2: float) -> tuple[float, float]:
        _, _, hi, _, _, _, _, u, rhs2 = eval_vars(x1, x2)
        return x1 - (u / hi) * dT, x2 - rhs2

    x1 = max(1e-4, min(0.99 * dT, dTi_ini if (dTi_ini and 0.0 < dTi_ini < dT) else 0.20 * dT))
    x2_def = (0.70 * dT) / max(1.0, ncapS)
    x2 = max(1e-4, min(0.99 * dT, dTcel_ini if (dTcel_ini and 0.0 < dTcel_ini < dT) else x2_def))

    f1, f2 = eval_res(x1, x2)
    norm = max(abs(f1), abs(f2))
    for _ in range(30):
        if norm < 1e-11:
            break
        h1 = 1e-7 * max(1.0, x1)
        h2 = 1e-7 * max(1.0, x2)
        f1_1, f2_1 = eval_res(x1 + h1, x2)
        f1_2, f2_2 = eval_res(x1, x2 + h2)
        j11 = (f1_1 - f1) / h1
        j21 = (f2_1 - f2) / h1
        j12 = (f1_2 - f1) / h2
        j22 = (f2_2 - f2) / h2
        det = j11 * j22 - j12 * j21
        if abs(det) < 1e-18:
            break
        dx1 = (-f1 * j22 + f2 * j12) / det
        dx2 = (-j11 * f2 + j21 * f1) / det

        alpha_step = 1.0
        acepto = False
        for _ in range(12):
            nx1 = x1 + alpha_step * dx1
            nx2 = x2 + alpha_step * dx2
            if 1e-6 < nx1 < dT * 1.5 and 1e-6 < nx2 < dT * 1.5:
                nf1, nf2 = eval_res(nx1, nx2)
                nnorm = max(abs(nf1), abs(nf2))
                if nnorm < norm or nnorm < 1e-11:
                    x1, x2 = nx1, nx2
                    f1, f2 = nf1, nf2
                    norm = nnorm
                    acepto = True
                    break
            alpha_step *= 0.5
        if not acepto:
            break

    # Respaldo de punto fijo amortiguado si Newton no alcanzó tolerancia
    if norm > 1e-9:
        for _ in range(80):
            _, _, hi, _, _, _, _, u, rhs2 = eval_vars(x1, x2)
            nx1 = max(1e-6, (u / hi) * dT)
            nx2 = max(1e-6, rhs2)
            x1 = 0.6 * nx1 + 0.4 * x1
            x2 = 0.6 * nx2 + 0.4 * x2
            f1, f2 = eval_res(x1, x2)
            if max(abs(f1), abs(f2)) < 1e-11:
                break

    rad, nui, hi, rae, nuc, usup, uinf, u, _ = eval_vars(x1, x2)
    return x1, rad, nui, hi, x2, rae, nuc, usup, uinf, u


def resolver_tearing_mbat(
    mc: float,
    N: float,
    mmot: float,
    mp: float,
    mad: float,
    mcarga: float,
    mflot: float,
    m: float,
    fap: float,
    g: float,
    az: float,
    ax: float,
    FD: float,
    v: float,
    tm: float,
    tman: float,
    rho1: float,
    Ap: float,
    ntot: float,
    km: float,
    Pad: float,
    ebat: float,
    DoD: float,
    ntemp: float,
    Cmax: float,
    mbat_ini: float | None = None,
) -> tuple[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float] | None:
    """
    Resuelve el bloque cerrado masa <-> batería <-> propulsión (C9-C13) usando `mbat`
    como única variable de corte y `mbat_calc = max(mbe, mbp)` exacto.
    Devuelve `(mart, mtot, mres, map_val, FL, FX, Ttot, Tcruc, Pelec, Pcruc, Ptot, Ereq, mbe, mbp, mbat)` o None.
    """
    masa_fija_art = mc + N * mmot + mp + mad
    inv_sqrt_disco = 1.0 / math.sqrt(2.0 * rho1 * N * Ap)
    k_elec = km / ntot
    k_mbe = 1.0 / (ebat * DoD * ntemp)
    k_mbp = 1.0 / (ebat * Cmax * ntemp)
    t_cruc = max(0.0, tm - tman)

    def eval_con_mbat(mbat_cand: float) -> tuple[float, float, float, float, float, float, float, float, float, float, float, float, float, float, float]:
        mart = masa_fija_art + mbat_cand
        mtot = mart + mcarga
        mres = mtot - mflot
        map_val = fap * (mtot + m)
        fl = mres * g + map_val * az
        fx = FD + map_val * ax
        ttot = math.hypot(fl, fx)
        pelec = k_elec * ((ttot ** 1.5) * inv_sqrt_disco + fx * v)
        ptot = pelec + Pad
        tcruc = math.hypot(mres * g, FD)
        pcruc = k_elec * ((tcruc ** 1.5) * inv_sqrt_disco + FD * v)
        ereq = (ptot * tman + (pcruc + Pad) * t_cruc) / 3600.0
        mbe = ereq * k_mbe
        mbp = ptot * k_mbp
        mbat_calc = mbe if mbe >= mbp else mbp
        return mart, mtot, mres, map_val, fl, fx, ttot, tcruc, pelec, pcruc, ptot, ereq, mbe, mbp, mbat_calc

    def residual(mbat_cand: float) -> float:
        return mbat_cand - eval_con_mbat(mbat_cand)[14]

    sol_m = None
    if mbat_ini is not None and math.isfinite(mbat_ini) and mbat_ini > 1e-4:
        lo_w = max(1e-5, 0.65 * mbat_ini)
        hi_w = min(60.0, 1.45 * mbat_ini)
        if lo_w < hi_w:
            r_lo = residual(lo_w)
            r_hi = residual(hi_w)
            if r_lo * r_hi <= 0.0:
                sol_m = brent_1d(residual, lo_w, hi_w, tol=1e-12, max_iter=60)

    if sol_m is None:
        malla = (1e-5, 0.02, 0.08, 0.25, 0.7, 1.8, 4.5, 10.0, 25.0, 60.0)
        a_prev = malla[0]
        r_prev = residual(a_prev)
        if abs(r_prev) < 1e-12:
            sol_m = a_prev
        else:
            for b_curr in malla[1:]:
                r_curr = residual(b_curr)
                if r_prev * r_curr <= 0.0:
                    sol_m = brent_1d(residual, a_prev, b_curr, tol=1e-12, max_iter=60)
                    break
                a_prev, r_prev = b_curr, r_curr
            if sol_m is None:
                return None

    res = eval_con_mbat(sol_m)
    if not math.isfinite(res[14]) or res[14] <= 0.0 or res[14] > 60.0:
        return None
    return (
        res[0], res[1], res[2], res[3], res[4], res[5],
        res[6], res[7], res[8], res[9], res[10], res[11], res[12], res[13], sol_m,
    )


def evaluar_termica_T2(base: dict[str, float], T2_val: float) -> tuple[float, float] | None:
    """
    Recalcula `(Qp, m)` para una temperatura instantánea `T2_val` manteniendo fijos la
    geometría regional del casco (`Vnuc, Vcel, D, S`) y el coeficiente externo (`he`), sin SymPy.
    """
    try:
        T1 = base["T1"]
        P2 = base["P2"]
        R2 = base["R2"]
        rho2 = P2 / (R2 * (T2_val + 273.15))
        Tm = 0.5 * (T1 + T2_val) + 273.15
        rhocel = P2 / (R2 * Tm)
        dT = T2_val - T1
        vnuc = float(base.get("Vnuc", base["V"]))
        vcel = float(base.get("Vcel", 0.0))
        m = rho2 * vnuc + rhocel * vcel
        if dT <= 0.05:
            return 0.0, m
        epsef = base["epsef"]
        hrad = 4.0 * epsef * SIGMA_SB * (Tm ** 3)
        hetot = base["hetot"] if "hetot" in base else (base["he"] + base.get("hrade", 0.0))
        ncapS = float(base["ncapS"])
        ncapI = float(base["ncapI"])
        if ncapS == 0.0 and ncapI == 0.0:
            _, _, _, _, U = resolver_tearing_u0(
                dT=dT, D=base["D"], g=base["g"], beta=base["beta"], nu=base["nu"], alpha=base["alpha"],
                fcal=base["fcal"], ka=base["ka"], ep=base["ep"], ke=base["ke"], he=hetot,
            )
        else:
            _, _, _, _, _, _, _, _, _, U = resolver_tearing_u(
                dT=dT,
                D=base["D"],
                e=base["e"],
                ncapS=ncapS,
                ncapI=ncapI,
                g=base["g"],
                beta=base["beta"],
                nu=base["nu"],
                alpha=base["alpha"],
                fcal=base["fcal"],
                ka=base["ka"],
                ep=base["ep"],
                ke=base["ke"],
                Rac=base["Rac"],
                hrad=hrad,
                hetot=hetot,
                dTi_ini=base.get("dTi"),
                dTcel_ini=base.get("dTcel"),
            )
        return U * base["S"] * dT, m
    except (ValueError, ZeroDivisionError, OverflowError, KeyError):
        return None


def evaluar_punto(
    base: dict[str, float],
    estricto_prolado: bool = False,
    **overrides: float,
) -> dict[str, float] | None:
    """
    Evalúa las 167 variables del modelo en ~60 microsegundos usando aritmética `float`
    y descomposición por variables de corte (`tearing`).
    Si `estricto_prolado=True`, exige todas las restricciones de dominio del solver CAS.
    """
    p = dict(base)
    p.update(overrides)

    try:
        P1, T1, R1 = float(p["P1"]), float(p["T1"]), float(p["R1"])
        P2, T2, R2 = float(p["P2"]), float(p["T2"]), float(p["R2"])
        if P1 <= 0.0 or R1 <= 0.0 or P2 <= 0.0 or R2 <= 0.0:
            return None
        if (T1 + 273.15) <= 0.0 or (T2 + 273.15) <= 0.0:
            return None

        rho1 = P1 / (R1 * (T1 + 273.15))
        rho2 = P2 / (R2 * (T2 + 273.15))
        drho = rho1 - rho2
        dT = T2 - T1
        if rho1 <= 0.0 or rho2 <= 0.0 or drho <= 0.0 or dT <= 0.0:
            return None

        g = float(p["g"])
        lam = float(p["lam"])
        xf = float(p["xf"])
        mflot = float(p["mflot"])
        if g <= 0.0 or lam <= 0.4 or not (0.0 < xf < 1.0):
            return None
        if mflot <= (0.0 if estricto_prolado else 0.05):
            return None

        e = float(p["e"])
        W = float(p["W"])
        ncapS = float(p["ncapS"])
        ncapI = float(p["ncapI"])
        ep, ke, eps = float(p["ep"]), float(p["ke"]), float(p["eps"])
        fcal = float(p["fcal"])
        beta, nu, alpha = float(p["beta"]), float(p["nu"]), float(p["alpha"])
        Rac, ka, sigma = float(p["Rac"]), float(p["ka"]), float(p["sigma"])
        if min(e, W, ep, ke, fcal, beta, nu, alpha, Rac, ka, sigma) <= 0.0:
            return None
        if ncapS < 0.0 or ncapI < 0.0:
            return None
        if abs(ncapS - round(ncapS)) > 1e-7 or abs(ncapI - round(ncapI)) > 1e-7:
            return None
        if not (0.0 < eps < 1.0):
            return None

        Tm = 0.5 * (T1 + T2) + 273.15
        rhocel = P2 / (R2 * Tm)
        if rhocel <= 0.0:
            return None

        F = mflot * g
        if ncapS == 0.0 and ncapI == 0.0:
            V = F / (drho * g)
            R = ((3.0 * V) / (4.0 * math.pi * lam)) ** (1.0 / 3.0)
            D = 2.0 * R
            L = lam * D
            Vnuc = V
            Vcel = 0.0
        else:
            def _calc_vnuc(V_cand: float) -> tuple[float, float, float] | None:
                R_c = ((3.0 * V_cand) / (4.0 * math.pi * lam)) ** (1.0 / 3.0)
                L_c = 2.0 * lam * R_c
                r_s = R_c - ncapS * e
                l_s = L_c - 2.0 * ncapS * e
                r_i = R_c - ncapI * e
                l_i = L_c - 2.0 * ncapI * e
                if r_s <= 0.0 or l_s <= 0.0 or r_i <= 0.0 or l_i <= 0.0:
                    return None
                vn = (math.pi / 3.0) * ((r_s * r_s) * l_s + (r_i * r_i) * l_i)
                return R_c, L_c, vn

            def _res_vol(V_cand: float) -> float:
                out_vn = _calc_vnuc(V_cand)
                if out_vn is None:
                    return -F
                _, _, vn = out_vn
                vc = V_cand - vn
                return (drho * g * vn + (rho1 - rhocel) * g * vc) - F

            V0 = F / (drho * g)
            R_min = max(ncapS, ncapI) * e * 1.02
            V_min = max(V0 * 0.95, (4.0 / 3.0) * math.pi * lam * (R_min ** 3))
            V_max = max(V_min * 3.0, V0 * 3.0)
            V_sol = brent_1d(_res_vol, V_min, V_max, tol=1e-13, max_iter=80)
            if V_sol is None:
                return None
            out_vn = _calc_vnuc(V_sol)
            if out_vn is None:
                return None
            V = V_sol
            R, L, Vnuc = out_vn
            D = 2.0 * R
            Vcel = max(0.0, V - Vnuc)
            if Vnuc <= 0.0 or (V - Vnuc) < -1e-9:
                return None

        cf = xf * L
        cr = L - cf

        if estricto_prolado:
            if cf <= R or cr <= R:
                return None
            ef = math.sqrt(1.0 - (R * R) / (cf * cf))
            er = math.sqrt(1.0 - (R * R) / (cr * cr))
            if not (0.0 < ef < 1.0 and 0.0 < er < 1.0):
                return None
            Sf = math.pi * R * R + math.pi * R * cf * math.asin(ef) / ef
            Sr = math.pi * R * R + math.pi * R * cr * math.asin(er) / er
        else:
            ef = math.sqrt(max(1e-12, 1.0 - (R * R) / (cf * cf))) if cf > R else 0.01
            er = math.sqrt(max(1e-12, 1.0 - (R * R) / (cr * cr))) if cr > R else 0.01
            Sf = area_semielipsoide(R, cf)
            Sr = area_semielipsoide(R, cr)
        S = Sf + Sr

        m = rho2 * Vnuc + rhocel * Vcel
        cp = float(p["cp"])
        npre = float(p["npre"])
        cpre = float(p["cpre"])
        if cp <= 0.0 or not (0.0 < npre < 1.0) or cpre < 0.0:
            return None
        Q = cp * (rho2 * Vnuc * dT + 0.5 * rhocel * Vcel * dT)
        Epre = Q / npre
        Cpre = (Epre / 1.0e6) * cpre

        v = float(p["v"])
        vv = float(p.get("vv", 0.0))
        if v <= 0.0 or vv < 0.0:
            return None
        vg = v - vv
        if vg <= 0.0:
            return None

        d1 = float(p["d1"])
        nv = float(p["nv"])
        if d1 <= 0.0 or nv <= 0.0:
            return None

        if "tm" in overrides and "dm" not in overrides and "nv" not in overrides and "v" not in overrides:
            tm = float(overrides["tm"])
            if tm <= 0.0:
                return None
            dm = vg * tm
            nv = dm / d1
        elif "dm" in overrides and "nv" not in overrides:
            dm = float(overrides["dm"])
            if dm <= 0.0:
                return None
            nv = dm / d1
            tm = dm / vg
        else:
            dm = nv * d1
            if dm <= 0.0:
                return None
            tm = dm / vg

        mu, kp = float(p["mu"]), float(p["kp"])
        if mu <= 0.0 or kp <= 0.0:
            return None
        ReL = (rho1 * v * L) / mu
        if ReL <= (1.0 if estricto_prolado else 10.0):
            return None
        Cf = 0.455 / ((math.log10(ReL)) ** 2.58)
        CDVc = Cf * (4.0 * (lam ** (1.0 / 3.0)) + 6.0 * (lam ** -1.2) + 24.0 * (lam ** -2.7))
        CDV = kp * CDVc
        FD = 0.5 * rho1 * (v ** 2) * CDV * (V ** (2.0 / 3.0))

        ncap = 0.5 * (ncapS + ncapI)

        Pr = nu / alpha
        Nue = 0.037 * (ReL ** 0.8) * (Pr ** (1.0 / 3.0))
        he = (Nue * ka) / L
        hrade = 4.0 * eps * SIGMA_SB * ((T1 + 273.15) ** 3)
        hetot = he + hrade

        epsef = eps / (2.0 - eps)
        hrad = 4.0 * epsef * SIGMA_SB * (Tm ** 3)

        # U0: estrictamente independiente de e, W, ncapS, ncapI, Nuc y hrad
        dTi0, RaD0, Nui0, hi0, U0 = resolver_tearing_u0(
            dT=dT, D=D, g=g, beta=beta, nu=nu, alpha=alpha,
            fcal=fcal, ka=ka, ep=ep, ke=ke, he=hetot,
        )
        if ncapS == 0.0 and ncapI == 0.0:
            dTi, RaD, Nui, hi = dTi0, RaD0, Nui0, hi0
            dTcel, Rae, Nuc = 0.0, 0.0, 1.0
            Usup, Uinf, U = U0, U0, U0
            Qp0 = U0 * S * dT
            Qp = Qp0
            dQp = 0.0
            fais = 0.0
        else:
            dTi, RaD, Nui, hi, dTcel, Rae, Nuc, Usup, Uinf, U = resolver_tearing_u(
                dT=dT, D=D, e=e, ncapS=ncapS, ncapI=ncapI, g=g, beta=beta, nu=nu, alpha=alpha,
                fcal=fcal, ka=ka, ep=ep, ke=ke, Rac=Rac, hrad=hrad, hetot=hetot,
                dTi_ini=base.get("dTi"), dTcel_ini=base.get("dTcel"),
            )
            Qp0 = U0 * S * dT
            Qp = U * S * dT
            dQp = Qp0 - Qp
            fais = dQp / Qp0 if Qp0 > 0.0 else 0.0
            if estricto_prolado and not (0.0 <= fais < 1.0):
                return None
        Sc = S * (1.0 + ncap * (1.0 + 2.0 * e / W))
        mc = Sc * sigma

        dTc = float(p["dTc"])
        PC = float(p["PC"])
        ncal = float(p["ncal"])
        ccomb = float(p["ccomb"])
        celecU = float(p["celecU"])
        if min(dTc, PC, ncal) <= 0.0 or dTc >= dT or ncal >= 1.0 or ccomb < 0.0 or celecU < 0.0:
            return None
        c_ef = Q / dT
        vT = Qp / c_ef
        Qc = c_ef * dTc
        tc = (Q / Qp) * math.log(dT / (dT - dTc))
        mgc = Qc / (ncal * PC)

        Em0 = Qp0 * tm
        Em = Qp * tm
        Eah = dQp * tm
        Eprop = Em / ncal
        mgm = Eprop / PC
        ED = FD * v * tm

        N = float(p["N"])
        mmot, mp, mad, mcarga, fap = (
            float(p["mmot"]), float(p["mp"]), float(p["mad"]),
            float(p["mcarga"]), float(p["fap"]),
        )
        vz, vx, ta = float(p["vz"]), float(p["vx"]), float(p["ta"])
        dp = float(p["dp"])
        nprop0, vpitch = float(p["nprop0"]), float(p["vpitch"])
        nm, nESC, km = float(p["nm"]), float(p["nESC"]), float(p["km"])
        ebat, DoD, ntemp, Cmax = float(p["ebat"]), float(p["DoD"]), float(p["ntemp"]), float(p["Cmax"])
        Tmax1, Pmax1, Pad = float(p["Tmax1"]), float(p["Pmax1"]), float(p["Pad"])
        thmax, mbmax = float(p["thmax"]), float(p["mbmax"])

        if min(N, mmot, mp, mad, mcarga, fap, vz, vx, ta, dp, nprop0, vpitch, nm, nESC, km,
               ebat, DoD, ntemp, Cmax, Tmax1, Pmax1, thmax, mbmax) <= 0.0:
            return None
        if N < 1.0 or abs(N - round(N)) > 1e-7:
            return None
        if Pad < 0.0:
            return None
        if not (0.0 < nprop0 < 1.0 and 0.0 < nm < 1.0 and 0.0 < nESC < 1.0 and 0.0 < DoD < 1.0 and 0.0 < ntemp < 1.0):
            return None

        az = vz / ta
        ax = vx / ta
        tman = min(tm, nv * ta)
        Ap = math.pi * (dp ** 2) / 4.0
        nprop = nprop0 * (1.0 - (v / vpitch) ** 2)
        if not (0.0 < nprop < 1.0):
            return None
        ntot = nprop * nm * nESC
        if not (0.0 < ntot < 1.0):
            return None
        Pmax = N * Pmax1

        sol_mbat = resolver_tearing_mbat(
            mc=mc, N=N, mmot=mmot, mp=mp, mad=mad, mcarga=mcarga,
            mflot=mflot, m=m, fap=fap, g=g, az=az, ax=ax, FD=FD,
            v=v, tm=tm, tman=tman, rho1=rho1, Ap=Ap, ntot=ntot, km=km,
            Pad=Pad, ebat=ebat, DoD=DoD, ntemp=ntemp, Cmax=Cmax,
            mbat_ini=base.get("mbat"),
        )
        if sol_mbat is None:
            return None

        mart, mtot, mres, map_val, FL, FX, Ttot, Tcruc, Pelec, Pcruc, Ptot, Ereq, mbe, mbp, mbat = sol_mbat
        if estricto_prolado and (mres <= 0.0 or FL <= 0.0 or FX <= 0.0 or Ttot <= 0.0):
            return None

        celec = Ereq / dm
        Eelec = 3600.0 * Ereq
        Etot = Eprop + Eelec
        ctot = Etot / dm
        Ccomb = mgm * ccomb
        Celec = (Ereq / 1000.0) * celecU
        Cop = Cpre + Ccomb + Celec

        theta = math.degrees(math.atan2(FX, FL)) if FL > 0.0 else 90.0
        thcruc = math.degrees(math.atan2(FD, mres * g)) if mres > 0.0 else 90.0
        if estricto_prolado and (not (0.0 < theta < 90.0) or not (0.0 < thcruc < 90.0)):
            return None
        dth = thmax - max(theta, thcruc)

        cap_sq = (N * Tmax1) ** 2 - FX ** 2
        if estricto_prolado and cap_sq <= 0.0:
            return None
        FLmax = math.sqrt(cap_sq) if cap_sq > 0.0 else 0.0
        Fexc = F + FLmax - mtot * g
        dPelec = Pmax - Pelec
        dTtot = N * Tmax1 - Ttot
        dmbat = mbmax - mbat

        tmax_tot = N * Tmax1
        valido = (
            (mbat <= mbmax)
            and (theta <= thmax)
            and (thcruc <= thmax)
            and (Pelec <= Pmax)
            and (Pcruc <= Pmax)
            and (Ttot <= tmax_tot)
            and (Tcruc <= tmax_tot)
            and (Fexc >= 0.0)
            and (mp >= mgm)
            and (cf > R)
            and (cr > R)
            and (mres > 0.0)
        )

        return {
            "P1": P1, "T1": T1, "R1": R1, "rho1": rho1,
            "P2": P2, "T2": T2, "R2": R2, "rho2": rho2, "rhocel": rhocel,
            "drho": drho, "R": R, "D": D, "lam": lam, "xf": xf,
            "cf": cf, "cr": cr, "L": L, "V": V, "Vnuc": Vnuc, "Vcel": Vcel, "ef": ef, "er": er,
            "Sf": Sf, "Sr": Sr, "S": S,
            "m": m, "cp": cp, "dT": dT, "Q": Q, "g": g, "F": F,
            "e": e, "W": W, "ncapS": ncapS, "ncapI": ncapI, "ncap": ncap,
            "ep": ep, "ke": ke, "eps": eps, "fcal": fcal,
            "beta": beta, "nu": nu, "alpha": alpha, "Pr": Pr, "Nue": Nue,
            "he": he, "hrade": hrade, "hetot": hetot,
            "dTi0": dTi0, "RaD0": RaD0, "Nui0": Nui0, "hi0": hi0, "U0": U0,
            "dTi": dTi, "RaD": RaD, "Nui": Nui, "hi": hi,
            "Tm": Tm, "epsef": epsef, "hrad": hrad,
            "dTcel": dTcel, "Rae": Rae, "Rac": Rac, "Nuc": Nuc, "ka": ka,
            "Usup": Usup, "Uinf": Uinf, "U": U,
            "Qp0": Qp0, "Qp": Qp, "dQp": dQp, "fais": fais,
            "Sc": Sc, "sigma": sigma, "mc": mc,
            "vT": vT, "dTc": dTc, "Qc": Qc, "tc": tc,
            "npre": npre, "Epre": Epre, "cpre": cpre, "Cpre": Cpre,
            "PC": PC, "ncal": ncal, "mgc": mgc, "tm": tm,
            "Em0": Em0, "Em": Em, "Eah": Eah, "Eprop": Eprop, "mgm": mgm,
            "v": v, "vv": vv, "vg": vg, "d1": d1, "nv": nv, "dm": dm, "mu": mu,
            "ReL": ReL, "Cf": Cf, "CDVc": CDVc, "kp": kp, "CDV": CDV, "FD": FD, "ED": ED,
            "N": N, "mmot": mmot, "mp": mp, "mad": mad, "mart": mart,
            "mcarga": mcarga, "mtot": mtot, "mflot": mflot, "mres": mres,
            "fap": fap, "map": map_val,
            "vz": vz, "vx": vx, "ta": ta, "az": az, "ax": ax,
            "FL": FL, "FX": FX, "Ttot": Ttot, "Tcruc": Tcruc, "Tmax1": Tmax1, "dTtot": dTtot,
            "theta": theta, "thcruc": thcruc, "thmax": thmax, "dth": dth, "FLmax": FLmax, "Fexc": Fexc,
            "dp": dp, "Ap": Ap, "nprop0": nprop0, "vpitch": vpitch, "nprop": nprop,
            "nm": nm, "nESC": nESC, "ntot": ntot, "km": km,
            "Pelec": Pelec, "Pcruc": Pcruc, "Pmax1": Pmax1, "Pmax": Pmax, "dPelec": dPelec,
            "Pad": Pad, "Ptot": Ptot, "tman": tman,
            "Ereq": Ereq, "Eelec": Eelec, "Eelec_J": Eelec, "celec": celec,
            "Etot": Etot, "ctot": ctot,
            "ccomb": ccomb, "Ccomb": Ccomb, "celecU": celecU, "Celec": Celec, "Cop": Cop,
            "ebat": ebat, "DoD": DoD, "ntemp": ntemp, "Cmax": Cmax,
            "mbe": mbe, "mbp": mbp, "mbat": mbat, "mbmax": mbmax, "dmbat": dmbat,
            "valido": valido,
        }
    except (ValueError, ZeroDivisionError, OverflowError):
        return None


def _extraer_cotas_limite(
    limites_efectivos: dict[str, Any] | None,
    var_nom: str,
) -> tuple[float | None, float | None]:
    """Extrae `(cota_min, cota_max)` de una variable aceptando dict `{"min","max"}` o tupla `(op, val)`."""
    if not limites_efectivos or var_nom not in limites_efectivos:
        return None, None
    entry = limites_efectivos[var_nom]
    if isinstance(entry, dict):
        c_min = entry.get("min")
        c_max = entry.get("max")
        return (float(c_min) if c_min is not None else None), (float(c_max) if c_max is not None else None)
    if isinstance(entry, (tuple, list)) and len(entry) == 2:
        op, val = entry
        vf = float(val)
        return (vf, None) if op == ">=" else (None, vf)
    return None, None


def diagnosticar_fases_y_limites(
    sol: dict[str, float],
    limites_efectivos: dict[str, Any] | None = None,
) -> dict[str, object]:
    """
    Evalúa los márgenes de maniobra y crucero respecto al equipo y topes efectivos,
    identificando la fase y el componente limitante de la misión.
    """
    _, pmax_u = _extraer_cotas_limite(limites_efectivos, "Pelec")
    _, tmax_u = _extraer_cotas_limite(limites_efectivos, "Ttot")
    _, th_u = _extraer_cotas_limite(limites_efectivos, "theta")
    _, mb_u = _extraer_cotas_limite(limites_efectivos, "mbat")

    pmax_base = sol["Pmax"]
    tmax_base = sol["N"] * sol["Tmax1"]
    th_base = sol["thmax"]
    mbmax_g_base = sol["mbmax"] * 1000.0

    pmax_lim = min(pmax_base, pmax_u) if pmax_u is not None else pmax_base
    tmax_lim = min(tmax_base, tmax_u) if tmax_u is not None else tmax_base
    th_lim = min(th_base, th_u) if th_u is not None else th_base
    mbmax_g_lim = min(mbmax_g_base, mb_u) if mb_u is not None else mbmax_g_base

    mres_g = sol["mres"] * sol["g"]
    thcruc = float(sol.get("thcruc", math.degrees(math.atan2(sol["FD"], mres_g)) if sol["mres"] > 0.0 else 90.0))

    ratios: list[tuple[float, str, str]] = [
        (sol["Pelec"] / max(1e-9, pmax_lim), "Maniobra", "Potencia eléctrica"),
        (sol["Pcruc"] / max(1e-9, pmax_lim), "Crucero", "Potencia eléctrica"),
        (sol["Ttot"] / max(1e-9, tmax_lim), "Maniobra", "Empuje motores"),
        (sol["Tcruc"] / max(1e-9, tmax_lim), "Crucero", "Empuje motores"),
        (sol["theta"] / max(1e-9, th_lim), "Maniobra", "Inclinación motores"),
        (thcruc / max(1e-9, th_lim), "Crucero", "Inclinación motores"),
        ((sol["mbat"] * 1000.0) / max(1e-9, mbmax_g_lim), "Misión completa", "Batería"),
        (sol["mgm"] / max(1e-9, sol["mp"]), "Misión completa", "Combustible térmico"),
    ]
    _, fase_lim, comp_lim = max(ratios, key=lambda x: x[0])

    return {
        "maniobra": {
            "FL_N": sol["FL"],
            "FX_N": sol["FX"],
            "Ttot_N": sol["Ttot"],
            "theta_deg": sol["theta"],
            "Pelec_W": sol["Pelec"],
            "Ptot_W": sol["Ptot"],
            "duracion_s": sol["tman"],
        },
        "crucero": {
            "FL_N": mres_g,
            "FX_N": sol["FD"],
            "Tcruc_N": sol["Tcruc"],
            "thcruc_deg": thcruc,
            "Pcruc_W": sol["Pcruc"],
            "Ptot_W": sol["Pcruc"] + sol["Pad"],
            "duracion_s": max(0.0, sol["tm"] - sol["tman"]),
        },
        "fase_limitante": fase_lim,
        "componente_limitante": comp_lim,
    }


def _calcular_metricas_carga(
    sol: dict[str, float],
    mc_cand: float,
    mbat_fija: float | None,
    tmax_lim: float,
    cbat_kg: float = 750.0,
) -> dict[str, float] | None:
    """Calcula las magnitudes físicas de maniobra, crucero y energía para una carga `mc_cand`."""
    mc = sol["mc"]
    N = sol["N"]
    mmot = sol["mmot"]
    mp = sol["mp"]
    mad = sol["mad"]
    mflot = sol["mflot"]
    m = sol["m"]
    fap = sol["fap"]
    g = sol["g"]
    az = sol["az"]
    ax = sol["ax"]
    FD = sol["FD"]
    v = sol["v"]
    tm = sol["tm"]
    tman = sol["tman"]
    rho1 = sol["rho1"]
    Ap = sol["Ap"]
    ntot = sol["ntot"]
    km = sol["km"]
    Pad = sol["Pad"]
    ebat = sol["ebat"]
    DoD = sol["DoD"]
    ntemp = sol["ntemp"]
    Cmax = sol["Cmax"]

    if mbat_fija is None:
        res_b = resolver_tearing_mbat(
            mc=mc, N=N, mmot=mmot, mp=mp, mad=mad, mcarga=mc_cand,
            mflot=mflot, m=m, fap=fap, g=g, az=az, ax=ax, FD=FD,
            v=v, tm=tm, tman=tman, rho1=rho1, Ap=Ap, ntot=ntot, km=km,
            Pad=Pad, ebat=ebat, DoD=DoD, ntemp=ntemp, Cmax=Cmax,
            mbat_ini=sol["mbat"],
        )
        if res_b is None:
            return None
        mart, mtot, mres, map_val, fl, fx, ttot, tcruc, pelec, pcruc, ptot, ereq, mbe, mbp, mbat_val = res_b
    else:
        mbat_val = mbat_fija
        mart = mc + N * mmot + mp + mad + mbat_val
        mtot = mart + mc_cand
        mres = mtot - mflot
        map_val = fap * (mtot + m)
        fl = mres * g + map_val * az
        fx = FD + map_val * ax
        ttot = math.hypot(fl, fx)
        inv_sqrt_disco = 1.0 / math.sqrt(2.0 * rho1 * N * Ap)
        k_elec = km / ntot
        pelec = k_elec * ((ttot ** 1.5) * inv_sqrt_disco + fx * v)
        ptot = pelec + Pad
        tcruc = math.hypot(mres * g, FD)
        pcruc = k_elec * ((tcruc ** 1.5) * inv_sqrt_disco + FD * v)
        t_cruc = max(0.0, tm - tman)
        ereq = (ptot * tman + (pcruc + Pad) * t_cruc) / 3600.0
        mbe = ereq / (ebat * DoD * ntemp)
        mbp = ptot / (ebat * Cmax * ntemp)

    theta_man = math.degrees(math.atan2(fx, fl))
    thcruc_c = math.degrees(math.atan2(FD, mres * g))
    tmax_eq = N * float(sol["Tmax1"])
    cap_sq = tmax_eq * tmax_eq - fx * fx
    flmax_c = math.sqrt(cap_sq) if cap_sq > 0.0 else 0.0
    fexc_c = sol["F"] + flmax_c - mtot * g
    etot_c = sol["Eprop"] + 3600.0 * ereq
    celec_c = (ereq / 1000.0) * sol["celecU"]
    cop_c = sol["Cpre"] + sol["Ccomb"] + celec_c
    c_recambio_c = mp * float(sol["ccomb"]) + mbat_val * max(0.0, float(cbat_kg))
    dm_c = float(sol["dm"])
    if dm_c <= 0.0:
        return None
    dm_aut_c = min(
        dm_c * (mp / max(1e-9, float(sol["mgm"]))),
        dm_c * (mbat_val / max(1e-9, mbe)),
    )
    return {
        "mcarga": mc_cand,
        "mart": mart,
        "mtot": mtot,
        "mres": mres,
        "map": map_val,
        "FL": fl,
        "FX": fx,
        "Ttot": ttot,
        "Tcruc": tcruc,
        "Tmax_fase": max(ttot, tcruc),
        "theta": theta_man,
        "thcruc": thcruc_c,
        "thmax_fase": max(theta_man, thcruc_c),
        "Pelec": pelec,
        "Pcruc": pcruc,
        "Pmax_fase": max(pelec, pcruc),
        "Ptot": ptot,
        "Ereq": ereq,
        "Etot": etot_c,
        "Celec": celec_c,
        "Cop": cop_c,
        "c_recambio": c_recambio_c,
        "dm_aut": dm_aut_c,
        "mbe": mbe,
        "mbp": mbp,
        "mbat": mbat_val,
        "Fexc": fexc_c,
    }


def _evaluar_carga_interna(
    sol: dict[str, float],
    mc_cand: float,
    mbat_fija: float | None,
    pmax_lim: float,
    tmax_lim: float,
    thmax_lim: float,
    mbmax_lim: float,
    fexc_min_lim: float,
    mtot_max_lim: float | None,
    etot_max_lim: float | None,
    mres_min: float,
    cbat_kg: float = 750.0,
    pmin_lim: float | None = None,
    tmin_lim: float | None = None,
    thmin_lim: float | None = None,
    mbmin_lim: float | None = None,
    fexc_max_lim: float | None = None,
    mtot_min_lim: float | None = None,
    etot_min_lim: float | None = None,
    cop_min_lim: float | None = None,
    cop_max_lim: float | None = None,
    c_recambio_min_lim: float | None = None,
    c_recambio_max_lim: float | None = None,
    dm_aut_min_lim: float | None = None,
    dm_aut_max_lim: float | None = None,
) -> tuple[bool, str, dict[str, float] | None]:
    """Evalúa una carga útil `mc_cand` sobre un casco, propulsión y misión fijos."""
    det = _calcular_metricas_carga(sol, mc_cand, mbat_fija, tmax_lim, cbat_kg=cbat_kg)
    if det is None:
        return False, "Batería (lazo sin cierre)", None

    mres = det["mres"]
    fl = det["FL"]
    pelec = det["Pelec"]
    pcruc = det["Pcruc"]
    ttot = det["Ttot"]
    tcruc = det["Tcruc"]
    theta_man = det["theta"]
    thcruc_c = det["thcruc"]
    fexc_c = det["Fexc"]
    mbat_val = det["mbat"]
    mbe = det["mbe"]
    mbp = det["mbp"]
    mtot = det["mtot"]
    etot_c = det["Etot"]
    cop_c = det["Cop"]
    c_rec_c = det["c_recambio"]
    dm_aut_c = det["dm_aut"]

    if mres < mres_min:
        return False, "Exceso de flotación (mres)", None
    if fl <= 0.0:
        return False, "Sustentación vertical negativa", None

    # Comprobar todos los límites activos (cotas superiores e inferiores) por orden de relevancia física
    if pelec > pmax_lim + 1e-9 or pcruc > pmax_lim + 1e-9:
        return False, "Potencia eléctrica (Pelec)", None
    if pmin_lim is not None and max(pelec, pcruc) < pmin_lim - 1e-6:
        return False, "Potencia eléctrica mín. (Pelec)", None
    if ttot > tmax_lim + 1e-9 or tcruc > tmax_lim + 1e-9:
        return False, "Empuje motores (Ttot)", None
    if tmin_lim is not None and max(ttot, tcruc) < tmin_lim - 1e-6:
        return False, "Empuje motores mín. (Ttot)", None
    if theta_man > thmax_lim + 1e-9 or thcruc_c > thmax_lim + 1e-9:
        return False, "Inclinación (θ)", None
    if thmin_lim is not None and max(theta_man, thcruc_c) < thmin_lim - 1e-6:
        return False, "Inclinación mín. (θ)", None
    if fexc_c < fexc_min_lim - 1e-9:
        return False, "Excedente Fexc", None
    if fexc_max_lim is not None and fexc_c > fexc_max_lim + 1e-6:
        return False, "Excedente máx. (Fexc)", None
    if mbat_fija is None:
        if mbat_val > mbmax_lim + 1e-9:
            return False, "Masa batería máx. (mbmax)", None
    else:
        if mbe > mbat_fija + 1e-9 or mbp > mbat_fija + 1e-9 or mbat_fija > mbmax_lim + 1e-9:
            return False, "Batería instalada (Ereq/Ptot)", None
    if mbmin_lim is not None and mbat_val < mbmin_lim - 1e-9:
        return False, "Masa batería mín. (mbat)", None
    if mtot_min_lim is not None and mtot < mtot_min_lim - 1e-6:
        return False, "Masa total mín. (mtot)", None
    if mtot_max_lim is not None and mtot > mtot_max_lim + 1e-6:
        return False, "Masa total máx. (mtot)", None
    if etot_min_lim is not None and etot_c < etot_min_lim - 1e-3:
        return False, "Energía total mín. (Etot)", None
    if etot_max_lim is not None and etot_c > etot_max_lim + 1e-3:
        return False, "Energía total máx. (Etot)", None
    if cop_min_lim is not None and cop_c < cop_min_lim - 1e-6:
        return False, "Costo operativo mín. (Cop)", None
    if cop_max_lim is not None and cop_c > cop_max_lim + 1e-6:
        return False, "Costo operativo máx. (Cop)", None
    if c_recambio_min_lim is not None and c_rec_c < c_recambio_min_lim - 1e-9:
        return False, "Costo recambio mín. (c_recambio)", None
    if c_recambio_max_lim is not None and c_rec_c > c_recambio_max_lim + 1e-9:
        return False, "Costo recambio máx. (c_recambio)", None
    if dm_aut_min_lim is not None and dm_aut_c < dm_aut_min_lim - 1e-6:
        return False, "Autonomía mín. (dm_aut)", None
    if dm_aut_max_lim is not None and dm_aut_c > dm_aut_max_lim + 1e-6:
        return False, "Autonomía máx. (dm_aut)", None

    return True, "OK", det


def _construir_limites_carga(
    sol: dict[str, float],
    limites_efectivos: dict[str, Any] | None,
) -> dict[str, float | None]:
    """Combina cotas mínimas y máximas de `limites_efectivos` con los topes del equipo."""
    pmin_u, pmax_u = _extraer_cotas_limite(limites_efectivos, "Pelec")
    tmin_u, tmax_u = _extraer_cotas_limite(limites_efectivos, "Ttot")
    thmin_u, thmax_u = _extraer_cotas_limite(limites_efectivos, "theta")
    mbmin_u_g, mbmax_u_g = _extraer_cotas_limite(limites_efectivos, "mbat")
    fmin_u, fmax_u = _extraer_cotas_limite(limites_efectivos, "Fexc")
    mtot_min_u, mtot_max_u = _extraer_cotas_limite(limites_efectivos, "mtot")
    emin_u_kj, emax_u_kj = _extraer_cotas_limite(limites_efectivos, "Etot")
    cop_min_u, cop_max_u = _extraer_cotas_limite(limites_efectivos, "Cop")
    c_rec_min_u, c_rec_max_u = _extraer_cotas_limite(limites_efectivos, "c_recambio")
    dm_aut_min_u, dm_aut_max_u = _extraer_cotas_limite(limites_efectivos, "dm_aut")

    tmax_eq = sol["N"] * sol["Tmax1"]
    return {
        "pmax_lim": min(sol["Pmax"], pmax_u) if pmax_u is not None else sol["Pmax"],
        "pmin_lim": pmin_u,
        "tmax_lim": min(tmax_eq, tmax_u) if tmax_u is not None else tmax_eq,
        "tmin_lim": tmin_u,
        "thmax_lim": min(sol["thmax"], thmax_u) if thmax_u is not None else sol["thmax"],
        "thmin_lim": thmin_u,
        "mbmax_lim": min(sol["mbmax"], mbmax_u_g / 1000.0) if mbmax_u_g is not None else sol["mbmax"],
        "mbmin_lim": (mbmin_u_g / 1000.0) if mbmin_u_g is not None else None,
        "fexc_min_lim": max(0.0, fmin_u) if fmin_u is not None else 0.0,
        "fexc_max_lim": fmax_u,
        "mtot_min_lim": mtot_min_u,
        "mtot_max_lim": mtot_max_u,
        "etot_min_lim": (emin_u_kj * 1000.0) if emin_u_kj is not None else None,
        "etot_max_lim": (emax_u_kj * 1000.0) if emax_u_kj is not None else None,
        "cop_min_lim": cop_min_u,
        "cop_max_lim": cop_max_u,
        "c_recambio_min_lim": c_rec_min_u,
        "c_recambio_max_lim": c_rec_max_u,
        "dm_aut_min_lim": dm_aut_min_u,
        "dm_aut_max_lim": dm_aut_max_u,
    }


def evaluar_punto_equipo_fijo(
    sol_instalado: dict[str, float],
    mcarga: float,
    limites_efectivos: dict[str, Any] | None = None,
    cbat_kg: float = 750.0,
) -> dict[str, float] | None:
    """
    Evalúa el diseño ya construido (casco, propulsión, mp y batería `mbat` instalada fija)
    para una carga útil dada `mcarga`, retornando el estado por fase o None si falla físicamente.
    """
    lims = _construir_limites_carga(sol_instalado, limites_efectivos)

    if sol_instalado["mp"] < sol_instalado["mgm"]:
        return None
    ok, motivo, det = _evaluar_carga_interna(
        sol=sol_instalado,
        mc_cand=float(mcarga),
        mbat_fija=float(sol_instalado["mbat"]),
        mres_min=1e-6,
        cbat_kg=cbat_kg,
        **lims,
    )
    if det is None:
        return None
    det["valido"] = ok
    det["motivo_limite"] = motivo
    return det


def evaluar_rango_carga_mision(
    sol: dict[str, float],
    redimensionar_bateria: bool = False,
    mres_min: float = 0.05,
    limites_efectivos: dict[str, Any] | None = None,
    cbat_kg: float = 750.0,
) -> dict[str, float | str | bool]:
    """
    Calcula el intervalo real de carga útil `[mcarga_min, mcarga_max]` que cumple
    simultáneamente todas las restricciones de la misión completa (maniobra, crucero,
    batería, inclinación, empuje, potencia y cotas min/max adicionales).
    Si la malla inicial no intercepta un intervalo estrecho, localiza por raíces 1D
    los cruces de todas las fronteras activas y evalúa sus puntos medios.
    Distingue explícitamente `estado_busqueda` (`"factible"`, `"vacio"`, `"inconclusa"`).
    """
    lims = _construir_limites_carga(sol, limites_efectivos)
    pmax_lim = float(lims["pmax_lim"])
    pmin_lim = lims["pmin_lim"]
    tmax_lim = float(lims["tmax_lim"])
    tmin_lim = lims["tmin_lim"]
    thmax_lim = float(lims["thmax_lim"])
    thmin_lim = lims["thmin_lim"]
    mbmax_lim = float(lims["mbmax_lim"])
    mbmin_lim = lims["mbmin_lim"]
    fexc_min_lim = float(lims["fexc_min_lim"])
    fexc_max_lim = lims["fexc_max_lim"]
    mtot_min_lim = lims["mtot_min_lim"]
    mtot_max_lim = lims["mtot_max_lim"]
    etot_min_lim = lims["etot_min_lim"]
    etot_max_lim = lims["etot_max_lim"]
    cop_min_lim = lims["cop_min_lim"]
    cop_max_lim = lims["cop_max_lim"]
    c_recambio_min_lim = lims["c_recambio_min_lim"]
    c_recambio_max_lim = lims["c_recambio_max_lim"]
    dm_aut_min_lim = lims["dm_aut_min_lim"]
    dm_aut_max_lim = lims["dm_aut_max_lim"]

    def _vacio(motivo: str, estado: str = "vacio") -> dict[str, float | str | bool]:
        return {
            "factible": False,
            "estado_busqueda": estado,
            "mcarga_min": 0.0,
            "mcarga_max": 0.0,
            "limitante_max": motivo,
        }

    # Comprobar incompatibilidades algebraicas directas entre cota mínima y máxima
    if pmin_lim is not None and pmin_lim > pmax_lim + 1e-6:
        return _vacio("Cotas incompatibles (Pelec mín. > máx.)")
    if tmin_lim is not None and tmin_lim > tmax_lim + 1e-6:
        return _vacio("Cotas incompatibles (Ttot mín. > máx.)")
    if thmin_lim is not None and thmin_lim > thmax_lim + 1e-6:
        return _vacio("Cotas incompatibles (θ mín. > máx.)")
    if mbmin_lim is not None and mbmin_lim > mbmax_lim + 1e-9:
        return _vacio("Cotas incompatibles (mbat mín. > máx.)")
    if fexc_max_lim is not None and fexc_min_lim > fexc_max_lim + 1e-6:
        return _vacio("Cotas incompatibles (Fexc mín. > máx.)")
    if mtot_min_lim is not None and mtot_max_lim is not None and mtot_min_lim > mtot_max_lim + 1e-6:
        return _vacio("Cotas incompatibles (mtot mín. > máx.)")
    if etot_min_lim is not None and etot_max_lim is not None and etot_min_lim > etot_max_lim + 1e-3:
        return _vacio("Cotas incompatibles (Etot mín. > máx.)")
    if cop_min_lim is not None and cop_max_lim is not None and cop_min_lim > cop_max_lim + 1e-6:
        return _vacio("Cotas incompatibles (Cop mín. > máx.)")
    if (
        c_recambio_min_lim is not None
        and c_recambio_max_lim is not None
        and c_recambio_min_lim > c_recambio_max_lim + 1e-9
    ):
        return _vacio("Cotas incompatibles (c_recambio mín. > máx.)")
    if dm_aut_min_lim is not None and dm_aut_max_lim is not None and dm_aut_min_lim > dm_aut_max_lim + 1e-6:
        return _vacio("Cotas incompatibles (dm_aut mín. > máx.)")

    if sol["cf"] <= sol["R"] or sol["cr"] <= sol["R"] or sol["vg"] <= 0.0:
        return _vacio("Geometría/viento")
    if sol["mp"] < sol["mgm"]:
        return _vacio("Combustible térmico (mp)")
    if not redimensionar_bateria:
        if sol["mbat"] > mbmax_lim + 1e-9:
            return _vacio("Masa batería máx. (mbmax)")
        if mbmin_lim is not None and sol["mbat"] < mbmin_lim - 1e-9:
            return _vacio("Masa batería mín. (mbat)")
        c_rec_fijo = float(sol["mp"]) * float(sol["ccomb"]) + float(sol["mbat"]) * max(0.0, float(cbat_kg))
        if c_recambio_max_lim is not None and c_rec_fijo > c_recambio_max_lim + 1e-9:
            return _vacio("Costo recambio máx. (c_recambio)")
        if c_recambio_min_lim is not None and c_rec_fijo < c_recambio_min_lim - 1e-9:
            return _vacio("Costo recambio mín. (c_recambio)")

    mbat_fija = None if redimensionar_bateria else float(sol["mbat"])

    def probar(mc_val: float) -> tuple[bool, str]:
        ok, mot, _ = _evaluar_carga_interna(
            sol=sol, mc_cand=mc_val, mbat_fija=mbat_fija, mres_min=mres_min, cbat_kg=cbat_kg, **lims
        )
        return ok, mot

    # Cota superior física conservadora por empuje estático máximo posible
    mbat_ref = mbmax_lim if redimensionar_bateria else float(sol["mbat"])
    mart_ref = sol["mc"] + sol["N"] * sol["mmot"] + sol["mp"] + sol["mad"] + mbat_ref
    mc_max_est = max(float(sol["mcarga"]) + 3.0, sol["mflot"] + tmax_lim / sol["g"] - mart_ref + 1.0)
    if mtot_max_lim is not None:
        mc_max_est = max(mc_max_est, mtot_max_lim - (sol["mc"] + sol["N"] * sol["mmot"] + sol["mp"] + sol["mad"]) + 0.5)
    mc_hi_scan = max(0.2, min(30.0, mc_max_est))

    puntos_extra: list[float] = []
    mart_est = sol["mc"] + sol["N"] * sol["mmot"] + sol["mp"] + sol["mad"] + float(sol["mbat"])
    if mbat_fija is not None:
        mc_lo_fis = max(0.0, sol["mflot"] + mres_min - mart_est)
        puntos_extra.extend([mc_lo_fis, mc_lo_fis + 1e-4])
    if mtot_min_lim is not None:
        mc_lo_t = max(0.0, mtot_min_lim - mart_est)
        puntos_extra.extend([mc_lo_t, mc_lo_t + 0.005, mc_lo_t + 0.02])
    if mtot_max_lim is not None:
        mc_hi_t = max(0.0, mtot_max_lim - mart_est)
        puntos_extra.extend([max(0.0, mc_hi_t - 0.02), max(0.0, mc_hi_t - 0.005), mc_hi_t])
    if mtot_min_lim is not None and mtot_max_lim is not None and mtot_max_lim >= mtot_min_lim:
        mc_mid_t = max(0.0, 0.5 * (mtot_min_lim + mtot_max_lim) - mart_est)
        puntos_extra.append(mc_mid_t)

    # Malla inicial + vecindario alrededor de la carga actual y cotas de masa total
    malla = sorted({
        0.0,
        *[mc_hi_scan * (k / 24.0) for k in range(1, 25)],
        max(0.0, float(sol["mcarga"]) - 0.1),
        float(sol["mcarga"]),
        float(sol["mcarga"]) + 0.02,
        *puntos_extra,
    })

    validos: list[float] = []
    motivo_fallo_nominal = "Restricciones de misión"
    for mv in malla:
        ok, mot = probar(mv)
        if ok:
            validos.append(mv)
        elif abs(mv - sol["mcarga"]) < 1e-6:
            motivo_fallo_nominal = mot

    hubo_fallo_cierre = False
    metricas_hi_cache: dict[str, float] | None = None

    # Paso 2 (si la malla discreta no encontró muestra válida): localizar fronteras exactas por raíces 1D
    if not validos:
        metricas_malla: list[tuple[float, dict[str, float] | None]] = []
        for mv in malla:
            det_mv = _calcular_metricas_carga(sol, mv, mbat_fija, tmax_lim, cbat_kg=cbat_kg)
            if det_mv is None:
                hubo_fallo_cierre = True
            metricas_malla.append((mv, det_mv))
        if metricas_malla:
            metricas_hi_cache = metricas_malla[-1][1]

        # Localizar transiciones entre lazo cerrado y divergencia (mbat_fija is None)
        puntos_transicion: list[float] = []
        for i in range(len(metricas_malla) - 1):
            mc_a, det_a = metricas_malla[i]
            mc_b, det_b = metricas_malla[i + 1]
            if (det_a is None) != (det_b is None):
                a_t, b_t = mc_a, mc_b
                ok_a = det_a is not None
                for _ in range(20):
                    mid_t = 0.5 * (a_t + b_t)
                    ok_mid = _calcular_metricas_carga(sol, mid_t, mbat_fija, tmax_lim, cbat_kg=cbat_kg) is not None
                    if ok_mid == ok_a:
                        a_t = mid_t
                    else:
                        b_t = mid_t
                mc_cierre = a_t if ok_a else b_t
                det_c = _calcular_metricas_carga(sol, mc_cierre, mbat_fija, tmax_lim, cbat_kg=cbat_kg)
                if det_c is not None:
                    puntos_transicion.append(mc_cierre)
                    metricas_malla.append((mc_cierre, det_c))

        metricas_malla.sort(key=lambda item: item[0])

        # Fronteras de todas las restricciones activas sobre el intervalo de carga
        fronteras_spec: list[tuple[str, float]] = [
            ("mres", mres_min),
            ("Pmax_fase", pmax_lim),
            ("Tmax_fase", tmax_lim),
            ("thmax_fase", thmax_lim),
            ("Fexc", fexc_min_lim),
        ]
        if pmin_lim is not None:
            fronteras_spec.append(("Pmax_fase", pmin_lim))
        if tmin_lim is not None:
            fronteras_spec.append(("Tmax_fase", tmin_lim))
        if thmin_lim is not None:
            fronteras_spec.append(("thmax_fase", thmin_lim))
        if fexc_max_lim is not None:
            fronteras_spec.append(("Fexc", fexc_max_lim))
        if mbat_fija is None:
            fronteras_spec.append(("mbat", mbmax_lim))
        else:
            fronteras_spec.append(("mbe", mbat_fija))
            fronteras_spec.append(("mbp", mbat_fija))
        if mbmin_lim is not None:
            fronteras_spec.append(("mbat", mbmin_lim))
        if mtot_min_lim is not None:
            fronteras_spec.append(("mtot", mtot_min_lim))
        if mtot_max_lim is not None:
            fronteras_spec.append(("mtot", mtot_max_lim))
        if etot_min_lim is not None:
            fronteras_spec.append(("Etot", etot_min_lim))
        if etot_max_lim is not None:
            fronteras_spec.append(("Etot", etot_max_lim))
        if cop_min_lim is not None:
            fronteras_spec.append(("Cop", cop_min_lim))
        if cop_max_lim is not None:
            fronteras_spec.append(("Cop", cop_max_lim))
        if c_recambio_min_lim is not None:
            fronteras_spec.append(("c_recambio", c_recambio_min_lim))
        if c_recambio_max_lim is not None:
            fronteras_spec.append(("c_recambio", c_recambio_max_lim))
        if dm_aut_min_lim is not None:
            fronteras_spec.append(("dm_aut", dm_aut_min_lim))
        if dm_aut_max_lim is not None:
            fronteras_spec.append(("dm_aut", dm_aut_max_lim))

        raices: list[float] = list(puntos_transicion)
        for clave, umbral in fronteras_spec:
            def f_front(mc_x: float, _clave: str = clave, _umb: float = umbral) -> float:
                det_x = _calcular_metricas_carga(sol, mc_x, mbat_fija, tmax_lim, cbat_kg=cbat_kg)
                if det_x is None:
                    return 0.0
                return det_x[_clave] - _umb

            for i in range(len(metricas_malla) - 1):
                mc_a, det_a = metricas_malla[i]
                mc_b, det_b = metricas_malla[i + 1]
                if det_a is None or det_b is None:
                    continue
                ra = det_a[clave] - umbral
                rb = det_b[clave] - umbral
                if ra == 0.0:
                    raices.append(mc_a)
                if rb == 0.0:
                    raices.append(mc_b)
                if ra * rb < 0.0:
                    raiz = brent_1d(f_front, mc_a, mc_b, tol=1e-10, max_iter=50)
                    raices.append(raiz)

        pts_front = sorted({*malla, *[max(0.0, min(mc_hi_scan, r)) for r in raices]})
        candidatos_ext: set[float] = set(pts_front)
        for i in range(len(pts_front) - 1):
            candidatos_ext.add(0.5 * (pts_front[i] + pts_front[i + 1]))
        for r in raices:
            for delta in (-1e-6, 1e-6):
                rc = r + delta
                if 0.0 <= rc <= mc_hi_scan:
                    candidatos_ext.add(rc)

        malla_ext = sorted(candidatos_ext)
        nuevos = [mv for mv in malla_ext if mv not in malla]
        for mv in nuevos:
            ok, mot = probar(mv)
            if ok:
                validos.append(mv)
            elif abs(mv - sol["mcarga"]) < 1e-6:
                motivo_fallo_nominal = mot
        malla = malla_ext

    if not validos:
        _, mot0 = probar(float(sol["mcarga"]))
        cotas_inf_no_alcanzadas = False
        if mc_hi_scan >= 30.0 - 1e-6 and metricas_hi_cache is not None:
            if (
                (pmin_lim is not None and metricas_hi_cache["Pmax_fase"] < pmin_lim - 1e-6)
                or (tmin_lim is not None and metricas_hi_cache["Tmax_fase"] < tmin_lim - 1e-6)
                or (mtot_min_lim is not None and metricas_hi_cache["mtot"] < mtot_min_lim - 1e-6)
                or (etot_min_lim is not None and metricas_hi_cache["Etot"] < etot_min_lim - 1e-3)
                or (cop_min_lim is not None and metricas_hi_cache["Cop"] < cop_min_lim - 1e-6)
                or (c_recambio_min_lim is not None and metricas_hi_cache["c_recambio"] < c_recambio_min_lim - 1e-9)
                or (dm_aut_max_lim is not None and metricas_hi_cache["dm_aut"] > dm_aut_max_lim + 1e-6)
                or (mbmin_lim is not None and metricas_hi_cache["mbat"] < mbmin_lim - 1e-9)
            ):
                cotas_inf_no_alcanzadas = True
        estado_busqueda = "inconclusa" if (cotas_inf_no_alcanzadas or hubo_fallo_cierre) else "vacio"
        return _vacio(mot0 if mot0 != "OK" else motivo_fallo_nominal, estado=estado_busqueda)

    low_ok = min(validos)
    high_ok = max(validos)

    # Bisección inferior para mcarga_min
    mc_min = 0.0
    if low_ok > 0.0:
        idx_low = malla.index(low_ok)
        lo_bad = malla[idx_low - 1]
        hi_good = low_ok
        for _ in range(24):
            mid = 0.5 * (lo_bad + hi_good)
            ok_m, _ = probar(mid)
            if ok_m:
                hi_good = mid
            else:
                lo_bad = mid
        mc_min = hi_good

    # Bisección superior para mcarga_max
    idx_hi = malla.index(high_ok)
    lo_good = high_ok
    if idx_hi + 1 < len(malla):
        hi_bad = malla[idx_hi + 1]
        _, limitante_max = probar(hi_bad)
    else:
        hi_bad = high_ok * 1.5 + 1.0
        limitante_max = "Empuje/Potencia"
    for _ in range(24):
        mid = 0.5 * (lo_good + hi_bad)
        ok_m, mot_m = probar(mid)
        if ok_m:
            lo_good = mid
        else:
            hi_bad = mid
            limitante_max = mot_m

    # Elegir la menor precisión decimal (4..8) cuyos extremos ya redondeados cumplan todas las cotas
    mc_min_seg = round(mc_min, 4) if mc_min > 0.0 else 0.0
    mc_max_seg = round(lo_good, 4)
    encontrado_redondeo = False
    for dec in (4, 5, 6, 7, 8):
        factor = 10.0 ** dec
        step = 1.0 / factor

        cand_max = round(lo_good, dec)
        if not probar(cand_max)[0]:
            cand_max = round(math.floor(lo_good * factor) / factor, dec)
        if not probar(cand_max)[0]:
            cand_max = round(max(0.0, cand_max - step), dec)

        if mc_min <= 0.0:
            cand_min = 0.0
        else:
            cand_min = round(mc_min, dec)
            if not probar(cand_min)[0]:
                cand_min = round(math.ceil(mc_min * factor) / factor, dec)
            if not probar(cand_min)[0]:
                cand_min = round(cand_min + step, dec)

        if cand_min <= cand_max and probar(cand_min)[0] and probar(cand_max)[0]:
            mc_min_seg, mc_max_seg = cand_min, cand_max
            encontrado_redondeo = True
            break

    if not encontrado_redondeo:
        if probar(mc_min)[0] and probar(lo_good)[0] and mc_min <= lo_good:
            mc_min_seg, mc_max_seg = mc_min, lo_good
        else:
            mc_mid_val = validos[len(validos) // 2]
            mc_min_seg, mc_max_seg = mc_mid_val, mc_mid_val

    return {
        "factible": True,
        "estado_busqueda": "factible",
        "mcarga_min": mc_min_seg,
        "mcarga_max": mc_max_seg,
        "limitante_max": limitante_max,
    }


def evaluar_dron_referencia(p_ref: dict[str, float]) -> dict[str, Any]:
    """
    Calcula la demanda eléctrica y batería de un dron multirrotor puro equivalente
    compartiendo carga útil (`mcarga`), misión (`dm, vv, vg, v, tm, tman, az, ax`),
    propulsión (`N, mmot, Ap, ntot, km, Pad`) y tecnología de batería, pero con su propia
    masa estructural (`0.65 kg`), área equivalente de arrastre (`CD·A = 0.06 m²`) y
    cero masa de gas encerrado (`fap = 1.0`).
    Evalúa además explícitamente si el dron cabe dentro del hardware de referencia (`Pmax`, `N·Tmax1`, `mbmax`).
    """
    m_est_dron = 0.65  # kg (chasis carbono, tren de aterrizaje, electrónica y brazos)
    cda_dron = 0.06    # m² (área equivalente de resistencia aerodinámica del multirrotor)
    N = float(p_ref["N"])
    mmot = float(p_ref["mmot"])
    mcarga = float(p_ref["mcarga"])
    g = float(p_ref["g"])
    az = float(p_ref["az"])
    ax = float(p_ref["ax"])
    v = float(p_ref["v"])
    rho1 = float(p_ref["rho1"])
    Ap = float(p_ref["Ap"])
    ntot = float(p_ref["ntot"])
    km = float(p_ref["km"])
    Pad = float(p_ref["Pad"])
    tm = float(p_ref["tm"])
    tman = float(p_ref["tman"])
    t_cruc = max(0.0, tm - tman)

    k_elec = km / ntot
    inv_sqrt_disco = 1.0 / math.sqrt(2.0 * rho1 * N * Ap)
    k_mbe = 1.0 / (float(p_ref["ebat"]) * float(p_ref["DoD"]) * float(p_ref["ntemp"]))
    k_mbp = 1.0 / (float(p_ref["ebat"]) * float(p_ref["Cmax"]) * float(p_ref["ntemp"]))

    fd_dron = 0.5 * rho1 * (v ** 2) * cda_dron
    masa_sin_bat = m_est_dron + N * mmot + mcarga

    def eval_dron(mbat_cand: float) -> tuple[float, float, float, float, float, float, float, float, float]:
        mtot_d = masa_sin_bat + mbat_cand
        fl_man = mtot_d * (g + az)
        fx_man = fd_dron + mtot_d * ax
        t_man = math.hypot(fl_man, fx_man)
        pelec_man = k_elec * ((t_man ** 1.5) * inv_sqrt_disco + fx_man * v)
        ptot_man = pelec_man + Pad

        t_cruc_v = math.hypot(mtot_d * g, fd_dron)
        pcruc_d = k_elec * ((t_cruc_v ** 1.5) * inv_sqrt_disco + fd_dron * v)
        ptot_cruc = pcruc_d + Pad

        ereq_d = (ptot_man * tman + ptot_cruc * t_cruc) / 3600.0
        mbe_d = ereq_d * k_mbe
        mbp_d = ptot_man * k_mbp
        mbat_calc = mbe_d if mbe_d >= mbp_d else mbp_d
        return mtot_d, t_man, t_cruc_v, pelec_man, pcruc_d, ptot_man, ptot_cruc, ereq_d, mbat_calc

    def res_dron(mbat_cand: float) -> float:
        return mbat_cand - eval_dron(mbat_cand)[8]

    sol_mb = None
    malla = (0.05, 0.25, 0.7, 1.5, 3.0, 6.0, 12.0, 25.0, 50.0, 80.0)
    a_p = malla[0]
    r_p = res_dron(a_p)
    for b_c in malla[1:]:
        r_c = res_dron(b_c)
        if r_p * r_c <= 0.0:
            sol_mb = brent_1d(res_dron, a_p, b_c, tol=1e-11, max_iter=60)
            break
        a_p, r_p = b_c, r_c

    factible_cierre = sol_mb is not None
    mbat_final = sol_mb if sol_mb is not None else 80.0
    mtot_d, t_man, t_cruc_v, pelec_man, pcruc_d, ptot_man, ptot_cruc, ereq_d, _ = eval_dron(mbat_final)

    pmax_eq = float(p_ref.get("Pmax", N * float(p_ref.get("Pmax1", 160.0))))
    tmax_eq = N * float(p_ref.get("Tmax1", 5.5))
    mbmax_eq = float(p_ref.get("mbmax", 1.0))

    excede_potencia = (not factible_cierre) or (pelec_man > pmax_eq + 1e-6) or (pcruc_d > pmax_eq + 1e-6)
    excede_empuje = (not factible_cierre) or (t_man > tmax_eq + 1e-6) or (t_cruc_v > tmax_eq + 1e-6)
    excede_bateria = (not factible_cierre) or (mbat_final > mbmax_eq + 1e-9)
    valido_hardware_dron = bool(factible_cierre and not excede_potencia and not excede_empuje and not excede_bateria)

    motivos_inviable: list[str] = []
    if not factible_cierre:
        motivos_inviable.append("Sin cierre de batería (>80 kg)")
    else:
        if excede_potencia:
            motivos_inviable.append(f"Pelec={max(pelec_man, pcruc_d):.0f}W > {pmax_eq:.0f}W")
        if excede_empuje:
            motivos_inviable.append(f"T={max(t_man, t_cruc_v):.1f}N > {tmax_eq:.1f}N")
        if excede_bateria:
            motivos_inviable.append(f"mbat={mbat_final*1000:.0f}g > {mbmax_eq*1000:.0f}g")

    return {
        "factible_cierre": factible_cierre,
        "valido_hardware_dron": valido_hardware_dron,
        "excede_potencia": excede_potencia,
        "excede_empuje": excede_empuje,
        "excede_bateria": excede_bateria,
        "motivos_inviable": motivos_inviable,
        "Pmax_ref": pmax_eq,
        "Tmax_ref": tmax_eq,
        "mbmax_ref": mbmax_eq,
        "m_estructura_kg": m_est_dron,
        "cda_m2": cda_dron,
        "FD_dron": fd_dron,
        "mtot_dron": mtot_d,
        "T_man_dron": t_man,
        "T_cruc_dron": t_cruc_v,
        "Pelec_man_dron": pelec_man,
        "Pelec_cruc_dron": pcruc_d,
        "Ptot_man_dron": ptot_man,
        "Ptot_cruc_dron": ptot_cruc,
        "Ereq_dron": ereq_d,
        "Eelec_dron": 3600.0 * ereq_d,
        "mbat_dron": mbat_final,
    }
