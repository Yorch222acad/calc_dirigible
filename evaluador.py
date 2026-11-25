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
    """Área superficial lateral de un semielipsoide de radio R y semieje axial c."""
    if c <= 0.0 or R <= 0.0:
        return 0.0
    if abs(c - R) < 1e-9:
        return 2.0 * math.pi * R * R
    if c > R:
        e_val = math.sqrt(max(0.0, 1.0 - (R * R) / (c * c)))
        return math.pi * R * c * math.asin(e_val) / e_val
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
    mediante dos variables de corte `(dTi, dTcel)` con Newton 2x2 amortiguado
    y respaldo por punto fijo.
    Devuelve `(dTi, RaD, Nui, hi, dTcel, Rae, Nuc, Usup, Uinf, U)`.
    """
    inv_nualpha = 1.0 / (nu * alpha)
    k_rad = g * beta * (D ** 3) * inv_nualpha
    k_rae = g * beta * (e ** 3) * inv_nualpha
    r_fijas_s = (((ncapS + 1.0) * ep) / ke) + (1.0 / hetot)
    r_fijas_i = (((ncapI + 1.0) * ep) / ke) + (1.0 / hetot)
    h_inf_cel = (ka / e) + hrad

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
    fap: float,
    g: float,
    az: float,
    ax: float,
    FD: float,
    v: float,
    tm: float,
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
) -> tuple[float, float, float, float, float, float, float, float, float, float, float, float, float] | None:
    """
    Resuelve el bloque cerrado masa <-> batería <-> propulsión (C9-C13) usando `mbat`
    como única variable de corte y `mbat_calc = max(mbe, mbp)` exacto.
    Devuelve `(mart, mtot, mres, map_val, FL, FX, Ttot, Pelec, Ptot, Ereq, mbe, mbp, mbat)` o None.
    """
    masa_fija_art = mc + N * mmot + mp + mad
    inv_sqrt_disco = 1.0 / math.sqrt(2.0 * rho1 * N * Ap)
    k_elec = km / ntot
    k_mbe = 1.0 / (ebat * DoD * ntemp)
    k_mbp = 1.0 / (ebat * Cmax * ntemp)

    def eval_con_mbat(mbat_cand: float) -> tuple[float, float, float, float, float, float, float, float, float, float, float, float, float]:
        mart = masa_fija_art + mbat_cand
        mtot = mart + mcarga
        mres = mtot - mflot
        map_val = fap * mtot
        fl = mres * g + mtot * az
        fx = FD + map_val * ax
        ttot = math.hypot(fl, fx)
        pelec = k_elec * ((ttot ** 1.5) * inv_sqrt_disco + fx * v)
        ptot = pelec + Pad
        ereq = (ptot * tm) / 3600.0
        mbe = ereq * k_mbe
        mbp = ptot * k_mbp
        mbat_calc = mbe if mbe >= mbp else mbp
        return mart, mtot, mres, map_val, fl, fx, ttot, pelec, ptot, ereq, mbe, mbp, mbat_calc

    def residual(mbat_cand: float) -> float:
        return mbat_cand - eval_con_mbat(mbat_cand)[12]

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
    if not math.isfinite(res[12]) or res[12] <= 0.0 or res[12] > 60.0:
        return None
    return (
        res[0], res[1], res[2], res[3], res[4], res[5],
        res[6], res[7], res[8], res[9], res[10], res[11], sol_m,
    )


def evaluar_termica_T2(base: dict[str, float], T2_val: float) -> tuple[float, float] | None:
    """
    Recalcula `(Qp, m)` para una temperatura instantánea `T2_val` manteniendo fijos la
    geometría del casco (`V, D, S`) y el coeficiente externo convectivo (`he`), sin SymPy.
    """
    try:
        T1 = base["T1"]
        P2 = base["P2"]
        R2 = base["R2"]
        rho2 = P2 / (R2 * (T2_val + 273.15))
        dT = T2_val - T1
        m = rho2 * base["V"]
        if dT <= 0.05:
            return 0.0, m
        Tm = 0.5 * (T1 + T2_val) + 273.15
        epsef = base["epsef"]
        hrad = 4.0 * epsef * SIGMA_SB * (Tm ** 3)
        hetot = base.get("hetot", base["he"] + base.get("hrade", 0.0))
        _, _, _, _, _, _, _, _, _, U = resolver_tearing_u(
            dT=dT,
            D=base["D"],
            e=base["e"],
            ncapS=base["ncapS"],
            ncapI=base["ncapI"],
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

        F = mflot * g
        V = F / (drho * g)
        # V = (2/3) * pi * R^2 * L = (4/3) * pi * lam * R^3
        R = ((3.0 * V) / (4.0 * math.pi * lam)) ** (1.0 / 3.0)
        D = 2.0 * R
        L = lam * D
        cf = xf * L
        cr = L - cf

        if estricto_prolado:
            if cf <= R or cr <= R:
                return None
            ef = math.sqrt(1.0 - (R * R) / (cf * cf))
            er = math.sqrt(1.0 - (R * R) / (cr * cr))
            if not (0.0 < ef < 1.0 and 0.0 < er < 1.0):
                return None
            Sf = math.pi * R * cf * math.asin(ef) / ef
            Sr = math.pi * R * cr * math.asin(er) / er
        else:
            ef = math.sqrt(max(1e-12, 1.0 - (R * R) / (cf * cf))) if cf > R else 0.01
            er = math.sqrt(max(1e-12, 1.0 - (R * R) / (cr * cr))) if cr > R else 0.01
            Sf = area_semielipsoide(R, cf)
            Sr = area_semielipsoide(R, cr)
        S = Sf + Sr

        m = rho2 * V
        cp = float(p["cp"])
        npre = float(p["npre"])
        cpre = float(p["cpre"])
        if cp <= 0.0 or not (0.0 < npre < 1.0) or cpre < 0.0:
            return None
        Q = m * cp * dT
        Epre = Q / npre
        Cpre = (Epre / 1.0e6) * cpre

        v = float(p["v"]) if estricto_prolado else max(0.2, float(p["v"]))
        vv = float(p.get("vv", 0.0))
        if v <= 0.0 or vv < 0.0:
            return None
        vg = v - vv
        if vg <= (0.0 if estricto_prolado else 0.05):
            return None

        d1 = float(p["d1"])
        nv = float(p["nv"])
        if d1 <= 0.0 or nv <= 0.0:
            return None

        if "tm" in overrides and "dm" not in overrides and "nv" not in overrides and "v" not in overrides:
            tm = max(1.0, float(overrides["tm"]))
            dm = vg * tm
            nv = dm / d1
        elif "dm" in overrides and "nv" not in overrides:
            dm = float(overrides["dm"]) if estricto_prolado else max(1.0, float(overrides["dm"]))
            if dm <= 0.0:
                return None
            nv = dm / d1
            tm = dm / vg
        else:
            dm = nv * d1
            if not estricto_prolado:
                dm = max(1.0, dm)
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

        e = float(p["e"]) if estricto_prolado else max(1e-5, float(p["e"]))
        W = float(p["W"])
        ncapS = float(p["ncapS"])
        ncapI = float(p["ncapI"])
        ep, ke, eps = float(p["ep"]), float(p["ke"]), float(p["eps"])
        fcal = float(p["fcal"])
        beta, nu, alpha = float(p["beta"]), float(p["nu"]), float(p["alpha"])
        Rac, ka, sigma = float(p["Rac"]), float(p["ka"]), float(p["sigma"])
        if min(e, W, ep, ke, fcal, beta, nu, alpha, Rac, ka, sigma) <= 0.0:
            return None
        if estricto_prolado and (ncapS <= 0.0 or ncapI <= 0.0):
            return None
        if ncapS < 0.0 or ncapI < 0.0:
            return None
        if not (0.0 < eps < 1.0):
            return None

        ncap = 0.5 * (ncapS + ncapI)

        Pr = nu / alpha
        Nue = 0.037 * (ReL ** 0.8) * (Pr ** (1.0 / 3.0))
        he = (Nue * ka) / L
        hrade = 4.0 * eps * SIGMA_SB * ((T1 + 273.15) ** 3)
        hetot = he + hrade

        Tm = 0.5 * (T1 + T2) + 273.15
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
            Sc = S
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
            if estricto_prolado and not (0.0 < fais < 1.0):
                return None
            Sc_cel = ncap * S * (1.0 + 2.0 * e / W)
            Sc = Sc_cel if estricto_prolado else max(S, Sc_cel)
        mc = Sc * sigma

        dTc = float(p["dTc"])
        PC = float(p["PC"])
        ncal = float(p["ncal"])
        ccomb = float(p["ccomb"])
        celecU = float(p["celecU"])
        if min(dTc, PC, ncal) <= 0.0 or ccomb < 0.0 or celecU < 0.0:
            return None
        vT = Qp / (m * cp)
        Qc = m * cp * dTc
        tc = Qc / Qp
        mgc = Qc / (ncal * PC)

        Em0 = Qp0 * tm
        Em = Qp * tm
        Eah = dQp * tm
        Eprop = Em / ncal
        mgm = Eprop / PC
        ED = FD * dm

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
        if Pad < 0.0:
            return None
        if not (0.0 < nprop0 < 1.0 and 0.0 < nm < 1.0 and 0.0 < nESC < 1.0 and 0.0 < DoD < 1.0 and 0.0 < ntemp < 1.0):
            return None

        az = vz / ta
        ax = vx / ta
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
            mflot=mflot, fap=fap, g=g, az=az, ax=ax, FD=FD,
            v=v, tm=tm, rho1=rho1, Ap=Ap, ntot=ntot, km=km,
            Pad=Pad, ebat=ebat, DoD=DoD, ntemp=ntemp, Cmax=Cmax,
            mbat_ini=base.get("mbat"),
        )
        if sol_mbat is None:
            return None

        mart, mtot, mres, map_val, FL, FX, Ttot, Pelec, Ptot, Ereq, mbe, mbp, mbat = sol_mbat
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
        if estricto_prolado and not (0.0 < theta < 90.0):
            return None
        dth = thmax - theta

        cap_sq = (N * Tmax1) ** 2 - FX ** 2
        if estricto_prolado and cap_sq <= 0.0:
            return None
        FLmax = math.sqrt(cap_sq) if cap_sq > 0.0 else 0.0
        Fexc = F + FLmax - mtot * g
        dPelec = Pmax - Pelec
        dTtot = N * Tmax1 - Ttot
        dmbat = mbmax - mbat

        valido = (
            (mbat <= mbmax)
            and (theta <= thmax)
            and (Pelec <= Pmax)
            and (Ttot <= N * Tmax1)
            and (Fexc >= 0.0)
            and (cf > R)
            and (cr > R)
            and (mres > 0.0)
        )

        return {
            "P1": P1, "T1": T1, "R1": R1, "rho1": rho1,
            "P2": P2, "T2": T2, "R2": R2, "rho2": rho2,
            "drho": drho, "R": R, "D": D, "lam": lam, "xf": xf,
            "cf": cf, "cr": cr, "L": L, "V": V, "ef": ef, "er": er,
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
            "FL": FL, "FX": FX, "Ttot": Ttot, "Tmax1": Tmax1, "dTtot": dTtot,
            "theta": theta, "thmax": thmax, "dth": dth, "FLmax": FLmax, "Fexc": Fexc,
            "dp": dp, "Ap": Ap, "nprop0": nprop0, "vpitch": vpitch, "nprop": nprop,
            "nm": nm, "nESC": nESC, "ntot": ntot, "km": km,
            "Pelec": Pelec, "Pmax1": Pmax1, "Pmax": Pmax, "dPelec": dPelec,
            "Pad": Pad, "Ptot": Ptot,
            "Ereq": Ereq, "Eelec": Eelec, "Eelec_J": Eelec, "celec": celec,
            "Etot": Etot, "ctot": ctot,
            "ccomb": ccomb, "Ccomb": Ccomb, "celecU": celecU, "Celec": Celec, "Cop": Cop,
            "ebat": ebat, "DoD": DoD, "ntemp": ntemp, "Cmax": Cmax,
            "mbe": mbe, "mbp": mbp, "mbat": mbat, "mbmax": mbmax, "dmbat": dmbat,
            "valido": valido,
        }
    except (ValueError, ZeroDivisionError, OverflowError):
        return None
