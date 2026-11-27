"""Suite integral de contraste físico-matemático v2/v3/v4/v5/v6/v7/v8/v9 del dirigible híbrido. Ejecutar con el Python del proyecto."""
import itertools
import json
import math
import tempfile
from pathlib import Path

from fastapi import HTTPException
import mpmath as mp

import app
import diseno
import evaluador
import flujo
import graficas
import modelo


def contrastar_casco(entradas, etiqueta):
    s = modelo.resolver(entradas)
    r = s["R"]
    # Integral de revolución con x=c*cos(t), y=R*sin(t). Sin disco de cierre.
    area = sum(
        float(
            mp.quad(
                lambda t: 2 * mp.pi * r * mp.sin(t)
                * mp.sqrt((c * mp.sin(t)) ** 2 + (r * mp.cos(t)) ** 2),
                [0, mp.pi / 2],
            )
        )
        for c in (s["cf"], s["cr"])
    )
    volumen = sum(
        float(mp.quad(lambda x: mp.pi * r * r * (1 - (x / c) ** 2), [0, c]))
        for c in (s["cf"], s["cr"])
    )
    assert math.isclose(volumen, s["V"], rel_tol=1e-12), f"{etiqueta}: volumen diverge"
    assert math.isclose(area, s["S"], rel_tol=1e-12), f"{etiqueta}: área curva diverge ({area} vs {s['S']})"
    print(f"[{etiqueta}] S={s['S']:.4f} m² (integral {area:.4f}), V={s['V']:.4f} m³, Pelec={s['Pelec']:.2f} W, mbat={s['mbat']:.4f} kg")


def verificar_punto_1_limites_hardware(candidato):
    # Lista guardada con 4 motores de 160 W (hw_Pelec = 640 W) reenviada con Pmax1 = 100 W (400 W reales)
    restr_antiguas = diseno.restricciones_defecto(candidato, activar_hardware=True)
    assert any(r["id"] == "hw_Pelec" and r["valor"] == 640.0 for r in restr_antiguas)

    peticion = app.PeticionAnalisisDiseno(
        variables=[],
        respetar_limites=True,
        restricciones=restr_antiguas,
        base_overrides=dict(candidato, Pmax1=100.0),
        ejecutar_optimizador=False,
    )
    r_api = app.analizar_diseno(peticion)
    assert r_api["encontrado"] is False, "Punto 1: API aceptó diseño con 638 W frente a límite real de 400 W"
    assert r_api["optimo"] is None
    assert r_api["actual"]["valido_hardware"] is False
    assert r_api["actual"]["avisos"], "Punto 1: faltan avisos de hardware en ficha actual"
    assert r_api["avisos_restricciones_actual"], "Punto 1: faltan avisos_restricciones_actual"
    assert any("Pelec=" in a and ("400" in a or "238" in a) for a in r_api["actual"]["avisos"])
    assert any("Pelec=" in a and ("400" in a or "238" in a) for a in r_api["avisos_restricciones_actual"])

    # También comprobar que un tope_manual más restrictivo (ej. 500 W sobre equipo de 640 W) se aplica
    restr_manual = [dict(r) for r in restr_antiguas]
    for r in restr_manual:
        if r["id"] == "hw_Pelec":
            r["tope_manual"] = 500.0
    r_man = app.analizar_diseno(app.PeticionAnalisisDiseno(
        variables=[],
        respetar_limites=True,
        restricciones=restr_manual,
        base_overrides=candidato,
        ejecutar_optimizador=False,
    ))
    assert r_man["encontrado"] is False, "Punto 1: tope manual más restrictivo (500 W) debe rechazar 638 W"
    print("[Punto 1 OK] Rechazo coherente ante cambio de Pmax1=100 W y ante tope_manual más restrictivo.")


def verificar_punto_2_capacidad_util(candidato, sol_cand):
    ev = diseno.evaluar_indicadores(sol_cand)
    esp = ev["especificaciones"]
    cap_fija = float(esp["capacidad_util_kg"])
    cap_min_fija = float(esp["mcarga_min_kg"])
    cap_redim = float(esp["capacidad_redim_kg"])

    assert cap_fija < 1.5, f"Punto 2: capacidad útil inflada ({cap_fija} kg)"
    assert cap_redim < 1.5, f"Punto 2: capacidad redimensionable inflada ({cap_redim} kg)"

    # Al reintroducir la capacidad máxima publicada con batería instalada fija debe cumplir todo
    re_fija = evaluador.evaluar_punto_equipo_fijo(sol_cand, cap_fija)
    assert re_fija is not None and re_fija["valido"], f"Punto 2: cap_fija={cap_fija} falla en equipo fijo"

    # Al reintroducir la capacidad con batería redimensionable debe cumplir todos los límites
    sol_redim = evaluador.evaluar_punto(candidato, estricto_prolado=False, mcarga=cap_redim)
    assert sol_redim is not None and sol_redim["valido"], (
        f"Punto 2: cap_redim={cap_redim} viola límites (Pelec={sol_redim['Pelec'] if sol_redim else None})"
    )

    # Verificar que por encima de cap_redim + margen falla
    sol_exc = evaluador.evaluar_punto(candidato, estricto_prolado=False, mcarga=cap_redim + 0.05)
    assert sol_exc is not None and not sol_exc["valido"]

    # Verificar detección de límite inferior por exceso de flotación
    assert cap_min_fija >= 0.0 and cap_min_fija <= sol_cand["mcarga"] <= cap_fija
    print(f"[Punto 2 OK] Fija: [{cap_min_fija:.4f}, {cap_fija:.4f}] kg | Redim.: {cap_redim:.4f} kg (lim. {esp['limitante_carga']})")


def verificar_punto_3_angulo_crucero(base):
    ref_v2 = dict(
        base,
        lam=3.321376,
        v=7.626877396121883,
        e=0.03195262551440329,
        T2=94.990625,
        ncapS=2.0,
        ncapI=1.0,
        mflot=4.171488179039247,
        mp=0.16,
        ta=30.0,
    )
    sol_c = evaluador.evaluar_punto(ref_v2, estricto_prolado=True)
    assert sol_c is not None
    assert sol_c["theta"] < sol_c["thmax"], f"Se esperaba theta maniobra < 75°, dio {sol_c['theta']}"
    assert sol_c["thcruc"] > sol_c["thmax"], f"Se esperaba thcruc > 75°, dio {sol_c['thcruc']}"
    assert sol_c["valido"] is False, "Punto 3: evaluador aceptó ángulo de crucero > thmax"

    r_est = diseno.optimizar_especificaciones(ref_v2, vars_libres=[], respetar_limites=True)
    assert r_est["encontrado"] is False, "Punto 3: diseño con thcruc > thmax fue aceptado"
    assert r_est["actual"]["valido_hardware"] is False
    assert any("θcruc" in a or "theta=" in a for a in r_est["avisos_restricciones_actual"])

    sol_m = modelo.resolver(ref_v2)
    assert math.isclose(sol_m["thcruc"], sol_c["thcruc"], rel_tol=1e-9)
    print(f"[Punto 3 OK] θman={sol_c['theta']:.3f}° (<75°), θcruc={sol_c['thcruc']:.3f}° (>75°) -> rechazado correctamente.")


def verificar_punto_4_casco_sin_aislamiento(base):
    for caps in ((0.0, 0.0), (1.0, 0.0), (0.0, 1.0)):
        ent = dict(base, ncapS=caps[0], ncapI=caps[1])
        sol_ev = evaluador.evaluar_punto(ent, estricto_prolado=True)
        assert sol_ev is not None, f"Punto 4: evaluar_punto falló en capas {caps}"
        sol_res = modelo.resolver(ent)
        for k in ("Vcel", "Vnuc", "Sc", "U", "U0", "Qp", "Qp0", "dTcel", "Rae", "Nuc"):
            assert math.isclose(sol_ev[k], sol_res[k], rel_tol=1e-9, abs_tol=1e-12), (
                f"Punto 4 ({caps}) diverge en {k}: ev={sol_ev[k]} vs res={sol_res[k]}"
            )
        if caps == (0.0, 0.0):
            assert sol_res["Vcel"] == 0.0
            assert math.isclose(sol_res["Vnuc"], sol_res["V"], rel_tol=1e-12)
            assert math.isclose(sol_res["Sc"], sol_res["S"], rel_tol=1e-12)
            assert math.isclose(sol_res["U"], sol_res["U0"], rel_tol=1e-10)
            assert math.isclose(sol_res["Qp"], sol_res["Qp0"], rel_tol=1e-10)
            assert sol_res["dTcel"] == 0.0 and sol_res["Rae"] == 0.0 and sol_res["Nuc"] == 1.0
    print("[Punto 4 OK] 0/0, 1/0 y 0/1 consistentes entre evaluador y modelo simbólico sin singularidades.")


def verificar_punto_5_precalentamiento_regional(base, hist_ent):
    for nombre, ent in (("Base", base), ("Histórico v1", hist_ent)):
        s_ev = evaluador.evaluar_punto(ent, estricto_prolado=True)
        s_mod = modelo.resolver(ent)
        assert s_ev is not None
        q_esp = s_ev["cp"] * (
            s_ev["rho2"] * s_ev["Vnuc"] * (s_ev["T2"] - s_ev["T1"])
            + s_ev["rhocel"] * s_ev["Vcel"] * (s_ev["Tm"] - 273.15 - s_ev["T1"])
        )
        assert math.isclose(s_ev["Q"], q_esp, rel_tol=1e-11)
        assert math.isclose(s_mod["Q"], q_esp, rel_tol=1e-11)
        print(f"[Punto 5 OK] {nombre}: Q regional = {s_mod['Q']/1000.0:.2f} kJ, Epre = {s_mod['Epre']/1000.0:.2f} kJ, Cpre = {s_mod['Cpre']:.4f} Bs")


def verificar_punto_6_g7_termica(base):
    sol_base = modelo.resolver(base)
    qp_t, m_t = evaluador.evaluar_termica_T2(sol_base, sol_base["T2"])
    assert math.isclose(m_t, sol_base["m"], rel_tol=1e-12), f"Punto 6: masa auxiliar {m_t} != {sol_base['m']}"
    assert math.isclose(qp_t, sol_base["Qp"], rel_tol=1e-9)

    gs = graficas.construir_datos_graficas(sol_base, set(modelo.FIJAS_INI))
    g7 = next(g for g in gs if g["id"] == "temperatura_escalabilidad")
    pan_a = g7["paneles"][0]
    idx_base = min(range(len(pan_a["xs"])), key=lambda i: abs(pan_a["xs"][i] - sol_base["T2"]))
    pct_g7 = pan_a["series"][3]["valores"][idx_base]

    # Contraste exacto a casco fijo en dos regiones (-10 K)
    t2_drop = sol_base["T2"] - 10.0
    rho2_drop = sol_base["P2"] / (sol_base["R2"] * (t2_drop + 273.15))
    rhocel_drop = sol_base["P2"] / (sol_base["R2"] * (0.5 * (sol_base["T1"] + t2_drop) + 273.15))
    f_drop = (
        (sol_base["rho1"] - rho2_drop) * sol_base["g"] * sol_base["Vnuc"]
        + (sol_base["rho1"] - rhocel_drop) * sol_base["g"] * sol_base["Vcel"]
    )
    pct_ref = 100.0 * (1.0 - f_drop / sol_base["F"])
    assert abs(pct_g7 - pct_ref) < 0.06, f"Punto 6: G7={pct_g7}% vs regional={pct_ref:.4f}%"
    print(f"[Punto 6 OK] m_aux({m_t:.4f} kg) == m_base({sol_base['m']:.4f} kg) | Caída -10 K = {pct_ref:.4f}%")


def verificar_punto_7_dron_g7(sol_cand):
    dron = evaluador.evaluar_dron_referencia(sol_cand)
    assert dron["factible_cierre"] is True
    ereq_fases = (
        dron["Ptot_man_dron"] * sol_cand["tman"]
        + dron["Ptot_cruc_dron"] * (sol_cand["tm"] - sol_cand["tman"])
    ) / 3600.0
    assert math.isclose(dron["Ereq_dron"], ereq_fases, rel_tol=1e-12)
    ereq_dir = (
        sol_cand["Ptot"] * sol_cand["tman"]
        + (sol_cand["Pcruc"] + sol_cand["Pad"]) * (sol_cand["tm"] - sol_cand["tman"])
    ) / 3600.0
    assert math.isclose(sol_cand["Ereq"], ereq_dir, rel_tol=1e-12)
    print(
        f"[Punto 7 OK] Dron ref (est=0.65 kg, CDA=0.06 m²): mbat={dron['mbat_dron']*1000:.1f} g, "
        f"Pman={dron['Ptot_man_dron']:.1f} W, Pcruc={dron['Ptot_cruc_dron']:.1f} W, Ereq={dron['Ereq_dron']:.1f} Wh"
    )


def verificar_v3_punto_1_operador_hardware(candidato):
    # Intentar invertir hw_Pelec a >= y hw_Fexc a <= en una petición con Pmax1 = 100 W
    restr_inv = diseno.restricciones_defecto(candidato, activar_hardware=True)
    for r in restr_inv:
        if r["id"] == "hw_Pelec":
            r["op"] = ">="
        elif r["id"] == "hw_Fexc":
            r["op"] = "<="

    r_api = app.analizar_diseno(app.PeticionAnalisisDiseno(
        variables=[],
        respetar_limites=True,
        restricciones=restr_inv,
        base_overrides=dict(candidato, Pmax1=100.0),
        ejecutar_optimizador=False,
    ))
    assert r_api["encontrado"] is False, "V3 Punto 1: aceptó diseño con operador invertido en hw_Pelec"
    assert r_api["actual"]["valido_hardware"] is False
    assert r_api["avisos_restricciones_actual"], "V3 Punto 1: faltan avisos_restricciones_actual tras normalización"
    assert any("Pelec=" in a for a in r_api["avisos_restricciones_actual"])

    por_id = {r["id"]: r for r in r_api["restricciones"]}
    assert por_id["hw_Pelec"]["op"] == "<=", "V3 Punto 1: hw_Pelec no quedó bloqueado en <="
    assert por_id["hw_Fexc"]["op"] == ">=", "V3 Punto 1: hw_Fexc no quedó bloqueado en >="

    # Una regla custom Pelec >= 300 W sí conserva su operador y coexiste con hw_Pelec <= 640 W
    restr_custom = diseno.restricciones_defecto(candidato, activar_hardware=True)
    restr_custom.append({
        "id": "custom_pelec_min",
        "variable": "Pelec",
        "op": ">=",
        "valor": 300.0,
        "activa": True,
        "grupo": "custom",
    })
    r_ok = app.analizar_diseno(app.PeticionAnalisisDiseno(
        variables=[],
        respetar_limites=True,
        restricciones=restr_custom,
        base_overrides=candidato,
        ejecutar_optimizador=False,
    ))
    assert r_ok["encontrado"] is True, "V3 Punto 1: regla custom Pelec >= 300 debe coexistir con hw_Pelec <= 640"
    por_id_ok = {r["id"]: r for r in r_ok["restricciones"]}
    assert por_id_ok["hw_Pelec"]["op"] == "<="
    assert por_id_ok["custom_pelec_min"]["op"] == ">="

    r_fail = app.analizar_diseno(app.PeticionAnalisisDiseno(
        variables=[],
        respetar_limites=True,
        restricciones=restr_custom,
        base_overrides=dict(candidato, Pmax1=100.0),
        ejecutar_optimizador=False,
    ))
    assert r_fail["encontrado"] is False
    print("[V3 Punto 1 OK] Sentido físico de hardware bloqueado (backend) y compatible con reglas custom opuestas.")


def verificar_v3_punto_2_cotas_min_max_mtot(candidato, sol_cand):
    # Caso A: solo cota inferior mtot >= 1.0 kg no debe leerse como mtot <= 1.0 kg
    restr_a = diseno.restricciones_defecto(candidato, activar_hardware=True)
    restr_a.append({
        "id": "c_mtot_min",
        "variable": "mtot",
        "op": ">=",
        "valor": 1.0,
        "activa": True,
        "grupo": "custom",
    })
    ev_a = diseno.evaluar_indicadores(sol_cand, restricciones=restr_a)
    esp_a = ev_a["especificaciones"]
    assert esp_a["carga_factible_instalada"] is True
    assert float(esp_a["capacidad_util_kg"]) >= 0.99, (
        f"V3 Punto 2: mtot >= 1.0 colapsó capacidad útil a {esp_a['capacidad_util_kg']} kg"
    )
    assert float(esp_a["mcarga_min_kg"]) <= float(sol_cand["mcarga"]) <= float(esp_a["capacidad_util_kg"])

    # Caso B: cotas opuestas mtot >= 4.0 y mtot <= 4.2 en ambos órdenes de lista
    r_min = {"id": "c_min", "variable": "mtot", "op": ">=", "valor": 4.0, "activa": True, "grupo": "custom"}
    r_max = {"id": "c_max", "variable": "mtot", "op": "<=", "valor": 4.2, "activa": True, "grupo": "custom"}
    base_hw = diseno.restricciones_defecto(candidato, activar_hardware=True)

    restr_ab = base_hw + [dict(r_min), dict(r_max)]
    restr_ba = base_hw + [dict(r_max), dict(r_min)]

    ev_ab = diseno.evaluar_indicadores(sol_cand, restricciones=restr_ab)
    ev_ba = diseno.evaluar_indicadores(sol_cand, restricciones=restr_ba)
    min_ab = float(ev_ab["especificaciones"]["mcarga_min_kg"])
    max_ab = float(ev_ab["especificaciones"]["capacidad_util_kg"])
    min_ba = float(ev_ba["especificaciones"]["mcarga_min_kg"])
    max_ba = float(ev_ba["especificaciones"]["capacidad_util_kg"])

    assert ev_ab["especificaciones"]["carga_factible_instalada"] is True
    assert min_ab == min_ba and max_ab == max_ba, (
        f"V3 Punto 2: orden de reglas alteró el rango ({min_ab}-{max_ab} vs {min_ba}-{max_ba})"
    )
    assert max_ab > min_ab > 0.0

    lim_map = diseno._limites_efectivos_mapa(sol_cand, restr_ab)
    assert lim_map["mtot"]["min"] == 4.0 and lim_map["mtot"]["max"] == 4.2
    for mc_extremo in (min_ab, max_ab):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, mc_extremo, limites_efectivos=lim_map)
        assert det is not None and det["valido"] is True, f"V3 Punto 2: extremo {mc_extremo} inválido"
        assert 4.0 - 1e-5 <= det["mtot"] <= 4.2 + 1e-5, f"V3 Punto 2: mtot={det['mtot']} fuera de [4.0, 4.2]"
    print(f"[V3 Punto 2 OK] Cotas min/max separadas e invariantes al orden: [{min_ab:.4f}, {max_ab:.4f}] kg para mtot in [4.0, 4.2].")


def verificar_v3_punto_3_importar_y_reevaluar_v1(registro_path):
    raw_hist = json.loads(registro_path.read_text(encoding="utf-8"))
    orig_path = diseno.HISTORICO_PATH
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            diseno.HISTORICO_PATH = Path(tmpdir) / "historico_test.json"
            importados = diseno.importar_historico(raw_hist)
            assert len(importados) == 1
            rec_v1 = importados[0]
            assert rec_v1["id"] == "36e082c5e2"
            assert rec_v1["fecha"] == "2026-11-25 18:29"
            assert rec_v1["modelo_version"] == "v1", f"Debió etiquetarse v1, dio {rec_v1.get('modelo_version')}"
            assert math.isclose(rec_v1["score_total"], 49.99, abs_tol=1e-6)
            assert math.isclose(rec_v1["especificaciones"]["Pelec"], 637.3, abs_tol=1e-6)
            assert rec_v1["valido_hardware"] is True

            resp_re = app.reevaluar_de_historico("36e082c5e2")
            reg_v2 = resp_re["registro"]
            todos = resp_re["registros"]
            assert len(todos) == 2, "La reevaluación debe crear un nuevo registro sin borrar el v1"
            assert reg_v2["id"] != "36e082c5e2"
            assert reg_v2["modelo_version"] == "v2"
            assert reg_v2["origen_id"] == "36e082c5e2"
            assert reg_v2["origen_version"] == "v1"
            assert reg_v2["especificaciones"]["Pelec"] > 1000.0
            assert reg_v2["valido_hardware"] is False

            # El registro original v1 sigue intacto
            rec_v1_despues = next(r for r in todos if r["id"] == "36e082c5e2")
            assert rec_v1_despues["modelo_version"] == "v1"
            assert rec_v1_despues["especificaciones"]["Pelec"] == 637.3
    finally:
        diseno.HISTORICO_PATH = orig_path
    print("[V3 Punto 3 OK] Histórico v1 importado intacto y reevaluación v2 creada como registro separado.")


def verificar_v3_punto_4_dron_g7_y_nulls(base, sol_cand):
    dron_opt = evaluador.evaluar_dron_referencia(sol_cand)
    assert dron_opt["factible_cierre"] is True
    assert dron_opt["valido_hardware_dron"] is False
    assert dron_opt["excede_potencia"] is True
    assert dron_opt["excede_empuje"] is True
    assert dron_opt["excede_bateria"] is True
    assert len(dron_opt["motivos_inviable"]) == 3

    sol_base = modelo.resolver(base)
    gs = graficas.construir_datos_graficas(sol_base, set(modelo.FIJAS_INI))
    g7 = next(g for g in gs if g["id"] == "temperatura_escalabilidad")
    pan_b = g7["paneles"][1]
    serie_dron = next(s for s in pan_b["series"] if "dron" in s["nombre"].lower())
    assert "excede equipo" in serie_dron["nombre"].lower()
    assert len(serie_dron["estados"]) == len(serie_dron["valores"])
    assert len(serie_dron["valido_hardware"]) == len(serie_dron["valores"])
    indices_null = [i for i, v in enumerate(serie_dron["valores"]) if v is None]
    assert indices_null, "En Base G7 Panel B debe haber puntos sin solución (null) cuando diverge la batería del dron"
    assert all("sin solución" in serie_dron["estados"][i].lower() for i in indices_null)

    # Contraste estático en frontend (charts.js no coerciona null a 0; designStudio.js deshabilita select hardware)
    charts_js = (Path(__file__).parent / "frontend/js/components/charts.js").read_text(encoding="utf-8")
    assert "esValidoNum" in charts_js
    assert "serie.valores\n        .map((val, i) => `${toX(xs[i]).toFixed(1)},${toY(val).toFixed(1)}`)" not in charts_js
    assert 'msgSinSol = estadoPt || "Sin solución"' in charts_js

    ds_js = (Path(__file__).parent / "frontend/js/components/designStudio.js").read_text(encoding="utf-8")
    assert '${esHw ? "disabled" : ""}' in ds_js
    assert 'designUi.restricciones[idx].grupo !== "hardware"' in ds_js
    print("[V3 Punto 4 OK] Factibilidad hardware del dron expuesta en G7 y renderizado SVG seguro ante valores null.")


def verificar_v4_punto_1_intervalo_estrecho_pelec(candidato, sol_cand, reglas_equipo):
    r_pmin = {"id": "c_pmin", "variable": "Pelec", "op": ">=", "valor": 607.0, "activa": True, "grupo": "custom"}
    r_pmax = {"id": "c_pmax", "variable": "Pelec", "op": "<=", "valor": 608.0, "activa": True, "grupo": "custom"}

    reglas_ab = list(reglas_equipo) + [dict(r_pmin), dict(r_pmax)]
    reglas_ba = list(reglas_equipo) + [dict(r_pmax), dict(r_pmin)]

    ficha_ab = diseno.evaluar_indicadores(sol_cand, restricciones=reglas_ab)["especificaciones"]
    ficha_ba = diseno.evaluar_indicadores(sol_cand, restricciones=reglas_ba)["especificaciones"]

    assert ficha_ab["carga_factible_instalada"] is True, "V4 Punto 1: descartó banda factible Pelec in [607, 608] W"
    min_ab = float(ficha_ab["mcarga_min_kg"])
    max_ab = float(ficha_ab["capacidad_util_kg"])
    min_ba = float(ficha_ba["mcarga_min_kg"])
    max_ba = float(ficha_ba["capacidad_util_kg"])

    assert min_ab == min_ba and max_ab == max_ba, "V4 Punto 1: el orden de las reglas alteró el intervalo"
    assert min_ab <= 0.8000 <= max_ab, f"V4 Punto 1: 0.8000 kg quedó fuera de [{min_ab}, {max_ab}]"

    lim_map = diseno._limites_efectivos_mapa(sol_cand, reglas_ab)
    directo_mid = evaluador.evaluar_punto_equipo_fijo(sol_cand, 0.8, lim_map)
    assert directo_mid is not None and directo_mid["valido"] is True
    for mc_ext in (min_ab, max_ab):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, mc_ext, lim_map)
        assert det is not None and det["valido"] is True, f"V4 Punto 1: extremo {mc_ext} inválido"
        assert 607.0 - 1e-4 <= max(det["Pelec"], det["Pcruc"]) <= 608.0 + 1e-4

    # Casos realmente incompatibles deben devolver intervalo vacío (estado_busqueda == "vacio")
    reglas_incomp_directo = list(reglas_equipo) + [
        {"id": "c_bad1", "variable": "Pelec", "op": ">=", "valor": 620.0, "activa": True, "grupo": "custom"},
        {"id": "c_bad2", "variable": "Pelec", "op": "<=", "valor": 610.0, "activa": True, "grupo": "custom"},
    ]
    rango_bad1 = evaluador.evaluar_rango_carga_mision(
        sol_cand, redimensionar_bateria=False, mres_min=1e-4,
        limites_efectivos=diseno._limites_efectivos_mapa(sol_cand, reglas_incomp_directo),
    )
    assert rango_bad1["factible"] is False and rango_bad1["estado_busqueda"] == "vacio"

    reglas_incomp_cruzado = list(reglas_equipo) + [
        {"id": "c_bad3", "variable": "mtot", "op": "<=", "valor": 3.9, "activa": True, "grupo": "custom"},
        {"id": "c_bad4", "variable": "Pelec", "op": ">=", "valor": 620.0, "activa": True, "grupo": "custom"},
    ]
    rango_bad2 = evaluador.evaluar_rango_carga_mision(
        sol_cand, redimensionar_bateria=False, mres_min=1e-4,
        limites_efectivos=diseno._limites_efectivos_mapa(sol_cand, reglas_incomp_cruzado),
    )
    assert rango_bad2["factible"] is False and rango_bad2["estado_busqueda"] == "vacio"
    print(f"[V4 Punto 1 OK] Banda estrecha Pelec∈[607, 608] W -> [{min_ab:.4f}, {max_ab:.4f}] kg (incluye 0.8000 kg) e incompatibles vacíos.")


def verificar_v4_punto_2_historico_conserva_restricciones(candidato, reglas_equipo):
    reglas = list(reglas_equipo) + [
        {"id": "c_mtot_41", "variable": "mtot", "op": ">=", "valor": 4.1, "activa": True, "grupo": "custom"}
    ]
    analisis = app.analizar_diseno(app.PeticionAnalisisDiseno(
        variables=[],
        base_overrides=candidato,
        ejecutar_optimizador=False,
        respetar_limites=True,
        restricciones=reglas,
    ))
    assert analisis["encontrado"] is True
    mc_min_aprobado = float(analisis["actual"]["especificaciones"]["mcarga_min_kg"])
    mc_max_aprobado = float(analisis["actual"]["especificaciones"]["capacidad_util_kg"])
    assert math.isclose(mc_min_aprobado, 0.8423, abs_tol=1e-4), (
        f"V4 Punto 2: mínimo analizado inesperado {mc_min_aprobado}"
    )

    orig_path = diseno.HISTORICO_PATH
    try:
        with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
            diseno.HISTORICO_PATH = Path(tmp1) / "historico_v4.json"
            resp_save = app.guardar_en_historico(app.PeticionGuardarHistorico(
                nombre="Prueba v4",
                entradas=candidato,
                restricciones=analisis["restricciones"],
                respetar_limites=analisis["respetar_limites"],
            ))
            guardado = resp_save["registro"]
            assert float(guardado["especificaciones"]["mcarga_min_kg"]) == mc_min_aprobado, (
                f"V4 Punto 2: guardado perdió cota min ({guardado['especificaciones']['mcarga_min_kg']} != {mc_min_aprobado})"
            )
            assert float(guardado["especificaciones"]["capacidad_util_kg"]) == mc_max_aprobado
            assert any(
                r["variable"] == "mtot" and r["op"] == ">=" and math.isclose(r["valor"], 4.1, abs_tol=1e-6)
                for r in (guardado.get("restricciones") or [])
            )

            # Exportar -> Importar en otro almacenamiento debe preservar ficha, procedencia y restricciones
            exportado = json.loads(json.dumps(diseno.cargar_historico()))
            diseno.HISTORICO_PATH = Path(tmp2) / "historico_v4_imp.json"
            importados = diseno.importar_historico(exportado)
            assert len(importados) == 1
            reimp = importados[0]
            assert reimp["id"] == guardado["id"]
            assert reimp["modelo_version"] == "v2"
            assert float(reimp["especificaciones"]["mcarga_min_kg"]) == mc_min_aprobado
            assert any(r["variable"] == "mtot" and r["op"] == ">=" for r in (reimp.get("restricciones") or []))

            # Reevaluar en v2 debe heredar las restricciones y mantener el intervalo aprobado
            reeval = app.reevaluar_de_historico(reimp["id"])["registro"]
            assert reeval["id"] != reimp["id"]
            assert reeval["origen_id"] == reimp["id"]
            assert float(reeval["especificaciones"]["mcarga_min_kg"]) == mc_min_aprobado
    finally:
        diseno.HISTORICO_PATH = orig_path
    print(f"[V4 Punto 2 OK] Histórico v2 conserva restricciones activas (mtot>=4.1 -> min={mc_min_aprobado:.4f} kg) al guardar, exportar/importar y reevaluar.")


def verificar_v5_punto_1_precision_extremos_estrechos(sol_cand, reglas_equipo):
    reglas = list(reglas_equipo) + [
        {"id": "c_pmin_5", "variable": "Pelec", "op": ">=", "valor": 607.30, "activa": True, "grupo": "custom"},
        {"id": "c_pmax_5", "variable": "Pelec", "op": "<=", "valor": 607.31, "activa": True, "grupo": "custom"},
    ]
    lim_map = diseno._limites_efectivos_mapa(sol_cand, reglas)
    ficha = diseno.evaluar_indicadores(sol_cand, restricciones=reglas)["especificaciones"]
    assert ficha["carga_factible_instalada"] is True
    mc_min = float(ficha["mcarga_min_kg"])
    mc_max = float(ficha["capacidad_util_kg"])
    assert mc_min <= 0.80004 <= mc_max, (
        f"V5 Punto 1: 0.80004 kg quedó fuera de [{mc_min}, {mc_max}]"
    )

    for carga in (mc_min, 0.80004, mc_max):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, carga, lim_map)
        assert det is not None and det["valido"] is True, f"V5 Punto 1: extremo publicado {carga} kg rechazado"
        assert 607.30 - 1e-6 <= max(det["Pelec"], det["Pcruc"]) <= 607.31 + 1e-6

    # Los dos vecinos exactos de 4 decimales deben seguir siendo rechazados (None) en esta banda
    for vecino_bad in (0.80000, 0.80010):
        det_b = evaluador.evaluar_punto_equipo_fijo(sol_cand, vecino_bad, lim_map)
        assert det_b is None, f"V5 Punto 1: {vecino_bad} debió ser rechazado (None)"
    print(f"[V5 Punto 1 OK] Banda estrecha [607.30, 607.31] W -> [{mc_min}, {mc_max}] kg, ambos extremos pasan evaluador fijo.")


def verificar_v5_punto_2_guardado_optimo_inmutable(candidato, opt_res):
    ds_js = (Path(__file__).parent / "frontend/js/components/designStudio.js").read_text(encoding="utf-8")
    assert ds_js.count("const pesosSave = res?.pesos ? { ...res.pesos } : { ...designUi.pesos };") >= 3
    assert ds_js.count("const cbatSave = Number.isFinite(Number(res?.cbat_kg)) ? Number(res.cbat_kg) : designUi.cbat_kg;") >= 3

    orig_path = diseno.HISTORICO_PATH
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            diseno.HISTORICO_PATH = Path(tmpdir) / "historico_v5.json"
            reg = app.guardar_en_historico(app.PeticionGuardarHistorico(
                nombre="Óptimo v5",
                entradas=candidato,
                pesos=opt_res["pesos"],
                cbat_kg=opt_res["cbat_kg"],
                restricciones=opt_res["restricciones"],
                respetar_limites=opt_res["respetar_limites"],
            ))["registro"]
            assert math.isclose(reg["score_total"], opt_res["optimo"]["score_total"], abs_tol=1e-6)
            assert math.isclose(
                reg["especificaciones"]["c_recambio"],
                opt_res["optimo"]["especificaciones"]["c_recambio"],
                abs_tol=1e-6,
            )
    finally:
        diseno.HISTORICO_PATH = orig_path
    print("[V5 Punto 2 OK] Guardado del último óptimo y Casos Tipo bloqueado a pesos y cbat_kg del análisis aprobado.")


def verificar_v6_punto_1_cop_en_rango_carga(sol_95, reglas_equipo):
    # Cota inferior Cop >= 2.046 Bs: ambos extremos publicados deben cumplirla de forma independiente
    reglas_inf = list(reglas_equipo) + [
        {"id": "c_cop_min", "variable": "Cop", "op": ">=", "valor": 2.046, "activa": True, "grupo": "custom"},
    ]
    ficha_inf = diseno.evaluar_indicadores(sol_95, restricciones=reglas_inf)["especificaciones"]
    assert ficha_inf["carga_factible_instalada"] is True
    mc_min = float(ficha_inf["mcarga_min_kg"])
    mc_max = float(ficha_inf["capacidad_util_kg"])
    assert mc_min > 0.6716, f"V6 Punto 1: Cop >= 2.046 debió excluir 0.6716 kg (dio min={mc_min})"
    lim_inf = diseno._limites_efectivos_mapa(sol_95, reglas_inf)
    for carga in (mc_min, mc_max):
        det = evaluador.evaluar_punto_equipo_fijo(sol_95, carga, lim_inf)
        assert det is not None and det["valido"] is True
        cop_indep = sol_95["Cpre"] + sol_95["Ccomb"] + (det["Ereq"] / 1000.0) * sol_95["celecU"]
        assert cop_indep >= 2.046 - 1e-6, f"V6 Punto 1: Cop independiente {cop_indep} < 2.046"

    # Cota superior Cop <= 2.045 Bs: debe excluir el punto nominal (2.04655 Bs) y acotar por arriba
    reglas_sup = list(reglas_equipo) + [
        {"id": "c_cop_max", "variable": "Cop", "op": "<=", "valor": 2.045, "activa": True, "grupo": "custom"},
    ]
    ficha_sup = diseno.evaluar_indicadores(sol_95, restricciones=reglas_sup)["especificaciones"]
    assert ficha_sup["carga_factible_instalada"] is True
    mc_min_s = float(ficha_sup["mcarga_min_kg"])
    mc_max_s = float(ficha_sup["capacidad_util_kg"])
    assert mc_max_s < 1.0, f"V6 Punto 1: Cop <= 2.045 debió acotar por debajo de 1.0 kg (dio max={mc_max_s})"
    lim_sup = diseno._limites_efectivos_mapa(sol_95, reglas_sup)
    for carga in (mc_min_s, mc_max_s):
        det = evaluador.evaluar_punto_equipo_fijo(sol_95, carga, lim_sup)
        assert det is not None and det["valido"] is True
        cop_indep = sol_95["Cpre"] + sol_95["Ccomb"] + (det["Ereq"] / 1000.0) * sol_95["celecU"]
        assert cop_indep <= 2.045 + 1e-6, f"V6 Punto 1: Cop independiente {cop_indep} > 2.045"
    print(f"[V6 Punto 1 OK] Cop aplicado en intervalo de carga: >=2.046->[{mc_min}, {mc_max}] kg | <=2.045->[{mc_min_s}, {mc_max_s}] kg.")


def verificar_v6_punto_4_casos_fraccion_aire(candidato_95, candidato_130):
    import re

    for etiqueta, ent in (("95°C", candidato_95), ("130°C", candidato_130)):
        casos = diseno.generar_casos_tipo(ent)["casos"]
        frac_casos = [c for c in casos if c["familia"] in ("motores_bateria", "masa_residual") and "%" in c["nombre"]]
        assert len(frac_casos) >= 2
        for c in frac_casos:
            real_pct = float(c["especificaciones"]["frac_aire_pct"])
            nums = [float(x) for x in re.findall(r"(\d+(?:\.\d+)?)\s*%", c["nombre"])]
            assert nums, f"{etiqueta}: caso sin porcentaje legible en título: {c['nombre']}"
            # El porcentaje anunciado o alcanzado (último % si indica "alcanzada X%") debe coincidir con la ficha
            anunciado = nums[-1]
            assert abs(real_pct - anunciado) <= 1.0, (
                f"V6 Punto 4 ({etiqueta}): '{c['nombre']}' reporta {anunciado}% pero ficha da {real_pct}%"
            )
    print("[V6 Punto 4 OK] Casos de porcentaje de aire reflejan exactamente frac_aire_pct o marcan aproximación alcanzada.")


def verificar_v6_punto_5_titulos_viajes_d1(candidato_95, historico_ent):
    casos_280 = diseno.generar_casos_tipo(candidato_95)["casos"]
    c3_280 = next(c for c in casos_280 if c["familia"] == "viajes" and c["especificaciones"]["nv"] == 3.0)
    assert c3_280["nombre"] == "3 viajes (840 m)" and c3_280["especificaciones"]["dm"] == 840.0

    casos_330 = diseno.generar_casos_tipo(historico_ent)["casos"]
    c3_330 = next(c for c in casos_330 if c["familia"] == "viajes" and c["especificaciones"]["nv"] == 3.0)
    assert c3_330["nombre"] == "3 viajes (990 m)" and c3_330["especificaciones"]["dm"] == 990.0
    print("[V6 Punto 5 OK] Títulos de viajes reflejan d1 dinámico (840 m para 280 m; 990 m para 330 m).")


def verificar_v6_hipotesis_b_enfriamiento(base):
    s_ev = evaluador.evaluar_punto(base, estricto_prolado=True)
    s_mod = modelo.resolver(base)
    assert s_ev is not None
    c_ef = s_mod["Q"] / s_mod["dT"]
    assert math.isclose(s_mod["Qc"], c_ef * s_mod["dTc"], rel_tol=1e-12)
    assert math.isclose(s_mod["vT"], s_mod["Qp"] / c_ef, rel_tol=1e-12)
    assert math.isclose(
        s_mod["tc"],
        (s_mod["Q"] / s_mod["Qp"]) * math.log(s_mod["dT"] / (s_mod["dT"] - s_mod["dTc"])),
        rel_tol=1e-12,
    )
    assert math.isclose(s_ev["Qc"], s_mod["Qc"], rel_tol=1e-12)
    assert math.isclose(s_ev["vT"], s_mod["vT"], rel_tol=1e-12)
    assert math.isclose(s_ev["tc"], s_mod["tc"], rel_tol=1e-12)
    assert math.isclose(s_mod["Qc"] / 1000.0, 264.77, abs_tol=0.02)
    print(f"[Hipótesis B OK] Enfriamiento regional consistente con Q: Qc={s_mod['Qc']/1000:.2f} kJ, tc={s_mod['tc']:.2f} s.")


def verificar_v7_punto_1_techo_busqueda_t2(candidato):
    base_150 = dict(candidato, T2=150.0)
    restr_desact = diseno.restricciones_defecto(base_150, activar_hardware=True)
    for r in restr_desact:
        if r["id"] == "lim_T2":
            r["activa"] = False
    pesos_rec = {k: (100.0 if k == "costo_recambio" else 0.0) for k in diseno.PESOS_DEFECTO}

    r_140 = diseno.optimizar_especificaciones(
        base_150, pesos=pesos_rec, vars_libres=["T2"], respetar_limites=True, restricciones=restr_desact
    )
    assert r_140["actual"]["especificaciones"]["T2"] == 150.0
    if r_140["encontrado"]:
        assert r_140["entradas_optimo"]["T2"] <= 140.0 + 1e-6, (
            f"V7 Punto 1: devolvió T2={r_140['entradas_optimo']['T2']} > techo 140 °C"
        )

    # Con límite de 130 °C activo debe respetar <= 130 °C aunque arranque en 150 °C
    restr_130 = diseno.restricciones_defecto(base_150, activar_hardware=True)
    r_130 = diseno.optimizar_especificaciones(
        base_150, pesos=pesos_rec, vars_libres=["T2"], respetar_limites=True, restricciones=restr_130
    )
    assert r_130["encontrado"] is True
    assert r_130["entradas_optimo"]["T2"] <= 130.0 + 1e-6

    # Un candidato inicial exactamente en el techo (140 °C) sí puede participar como candidato
    base_140 = dict(candidato, T2=140.0)
    r_en_techo = diseno.optimizar_especificaciones(
        base_140, pesos=pesos_rec, vars_libres=["T2"], respetar_limites=True, restricciones=restr_desact
    )
    assert r_en_techo["encontrado"] is True
    assert r_en_techo["entradas_optimo"]["T2"] <= 140.0 + 1e-6
    print("[V7 Punto 1 OK] Candidato inicial fuera de techo (150 °C) conservado en 'actual' pero excluido del óptimo (<=140/<=130 °C).")


def verificar_v7_punto_2_autonomia_en_rango_carga(sol_cand, reglas_equipo):
    dm = float(sol_cand["dm"])

    # Cota superior dm_aut <= 850 m: 1 kg (840 m) cumple, 0.6668 kg (914.84 m) debe excluirse
    reglas_max = list(reglas_equipo) + [
        {"id": "c_aut_max", "variable": "dm_aut", "op": "<=", "valor": 850.0, "activa": True, "grupo": "custom"}
    ]
    ficha_max = diseno.evaluar_indicadores(sol_cand, restricciones=reglas_max)["especificaciones"]
    assert ficha_max["carga_factible_instalada"] is True
    mc_min = float(ficha_max["mcarga_min_kg"])
    mc_max = float(ficha_max["capacidad_util_kg"])
    assert mc_min > 0.6668 and mc_min <= 1.0 <= mc_max, (
        f"V7 Punto 2 (<=850 m): intervalo inesperado [{mc_min}, {mc_max}]"
    )
    lim_max = diseno._limites_efectivos_mapa(sol_cand, reglas_max)
    assert evaluador.evaluar_punto_equipo_fijo(sol_cand, 0.6668, lim_max) is None
    for carga in (mc_min, mc_max):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, carga, lim_max)
        assert det is not None and det["valido"] is True
        aut_indep = min(dm * sol_cand["mp"] / sol_cand["mgm"], dm * sol_cand["mbat"] / det["mbe"])
        assert aut_indep <= 850.0 + 1e-4, f"V7 Punto 2: carga {carga} dio autonomía {aut_indep} > 850 m"

    # Cota inferior dm_aut >= 860 m: 1 kg (840 m) debe excluirse
    reglas_min = list(reglas_equipo) + [
        {"id": "c_aut_min", "variable": "dm_aut", "op": ">=", "valor": 860.0, "activa": True, "grupo": "custom"}
    ]
    ficha_min = diseno.evaluar_indicadores(sol_cand, restricciones=reglas_min)["especificaciones"]
    assert ficha_min["carga_factible_instalada"] is True
    mc_min_i = float(ficha_min["mcarga_min_kg"])
    mc_max_i = float(ficha_min["capacidad_util_kg"])
    assert mc_max_i < 1.0, f"V7 Punto 2 (>=860 m): debió excluir 1.0 kg (max={mc_max_i})"
    lim_min = diseno._limites_efectivos_mapa(sol_cand, reglas_min)
    for carga in (mc_min_i, mc_max_i):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, carga, lim_min)
        assert det is not None and det["valido"] is True
        aut_indep = min(dm * sol_cand["mp"] / sol_cand["mgm"], dm * sol_cand["mbat"] / det["mbe"])
        assert aut_indep >= 860.0 - 1e-4
    print(f"[V7 Punto 2 OK] Autonomía dm_aut en rango de carga: <=850 m->[{mc_min}, {mc_max}] kg | >=860 m->[{mc_min_i}, {mc_max_i}] kg.")


def verificar_v7_punto_3_etiqueta_g7(candidato):
    sol_150 = evaluador.evaluar_punto(dict(candidato, T2=150.0), estricto_prolado=False)
    assert sol_150 is not None
    gs = graficas.construir_datos_graficas(sol_150, set(modelo.FIJAS_INI))
    g7 = next(g for g in gs if g["id"] == "temperatura_escalabilidad")
    pan_a = g7["paneles"][0]
    assert max(pan_a["xs"]) >= 140.0
    lbl = pan_a["x_optimo_label"]
    assert "Óptimo seguro" not in lbl
    assert "Mín. Etot" in lbl and "16%" in lbl and "equipo OK" in lbl
    print(f"[V7 Punto 3 OK] Etiqueta G7 Panel A explicita criterios independientes: '{lbl}'.")


def verificar_v7_punto_4_y_5_dtc_y_readme(base):
    s_10 = evaluador.evaluar_punto(dict(base, dTc=10.0), estricto_prolado=True)
    s_20 = evaluador.evaluar_punto(dict(base, dTc=20.0), estricto_prolado=True)
    assert s_10 is not None and s_20 is not None
    esp_10 = diseno.evaluar_indicadores(s_10)["especificaciones"]
    esp_20 = diseno.evaluar_indicadores(s_20)["especificaciones"]
    assert esp_10["dTc"] == 10.0 and esp_10["tc_s"] == 72.4
    assert esp_20["dTc"] == 20.0 and esp_20["tc_s"] == 158.0

    readme = (Path(__file__).parent / "README.md").read_text(encoding="utf-8")
    lim_t2_def = next(r for r in diseno.restricciones_defecto(base) if r["id"] == "lim_T2")["valor"]
    assert lim_t2_def == 130.0
    assert "T2 <= 130 °C" in readme and "140 °C" in readme
    assert "163.8 s" not in readme and f"{round(s_20['tc'], 1)} s" in readme
    print("[V7 Punto 4 y 5 OK] Ficha expone dTc dinámico (10 K->72.4 s, 20 K->158.0 s) y README sincronizado.")


def verificar_v8_punto_1_c_recambio_en_rango_carga(candidato, reglas_equipo):
    res_sin = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_equipo
    )
    cap_sin = float(res_sin["actual"]["especificaciones"]["capacidad_redim_kg"])

    # Límite superior c_recambio <= 424.15 Bs: 1 kg cumple, 1.0073 kg excede (~425.43 Bs) y queda excluido
    reglas_max = list(reglas_equipo) + [
        {"id": "c_rec_max_v8", "variable": "c_recambio", "op": "<=", "valor": 424.15, "activa": True, "grupo": "custom"}
    ]
    res_max = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_max
    )
    esp_max = res_max["actual"]["especificaciones"]
    assert esp_max["carga_factible_instalada"] is True
    cap_min = float(esp_max["mcarga_min_redim_kg"])
    cap_max = float(esp_max["capacidad_redim_kg"])
    assert cap_min <= 1.0 <= cap_max < 1.0073, (
        f"V8 Punto 1: intervalo esperado con 1 kg incluido y <1.0073, obtenido [{cap_min}, {cap_max}]"
    )
    sol_edge = evaluador.evaluar_punto(candidato, estricto_prolado=True, mcarga=cap_max)
    assert sol_edge is not None
    costo_edge = sol_edge["mp"] * sol_edge["ccomb"] + sol_edge["mbat"] * 750.0
    assert costo_edge <= 424.15 + 1e-9, f"V8 Punto 1: extremo {cap_max} cuesta {costo_edge:.4f} > 424.15 Bs"

    # Cota inferior c_recambio >= 424.145 Bs: excluye 1.0 kg (~424.14 Bs) y verifica extremo inferior
    reglas_min = list(reglas_equipo) + [
        {"id": "c_rec_min_v8", "variable": "c_recambio", "op": ">=", "valor": 424.145, "activa": True, "grupo": "custom"}
    ]
    res_min = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_min
    )
    esp_min = res_min["actual"]["especificaciones"]
    cap_min_i = float(esp_min["mcarga_min_redim_kg"])
    cap_max_i = float(esp_min["capacidad_redim_kg"])
    assert 1.0 < cap_min_i <= cap_max_i, f"V8 Punto 1 (cota inf): intervalo inesperado [{cap_min_i}, {cap_max_i}]"
    sol_min_i = evaluador.evaluar_punto(candidato, estricto_prolado=True, mcarga=cap_min_i)
    assert sol_min_i is not None
    costo_min_i = sol_min_i["mp"] * sol_min_i["ccomb"] + sol_min_i["mbat"] * 750.0
    assert costo_min_i >= 424.145 - 1e-9, f"V8 Punto 1: extremo mín {cap_min_i} cuesta {costo_min_i:.4f} < 424.145 Bs"

    # Con la restricción desactivada debe recuperar exactamente cap_sin
    reglas_off = list(reglas_equipo) + [
        {"id": "c_rec_off_v8", "variable": "c_recambio", "op": "<=", "valor": 424.15, "activa": False, "grupo": "custom"}
    ]
    res_off = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_off
    )
    cap_off = float(res_off["actual"]["especificaciones"]["capacidad_redim_kg"])
    assert cap_off == cap_sin, f"V8 Punto 1: desactivada dio {cap_off} != {cap_sin}"
    print(f"[V8 Punto 1 OK] c_recambio en rango redimensionado: <=424.15->max={cap_max} kg ({costo_edge:.3f} Bs) | desact.->{cap_off} kg.")


def verificar_v8_punto_2_distancia_submetro(candidato):
    for d1_val in (0.5, 1.0, 2.0):
        s_sym = modelo.resolver(dict(candidato, nv=1.0, d1=d1_val))
        s_ev = evaluador.evaluar_punto(candidato, estricto_prolado=False, nv=1.0, d1=d1_val)
        assert s_ev is not None
        res_dir = diseno.optimizar_especificaciones(
            candidato,
            vars_libres=[],
            cbat_kg=750.0,
            respetar_limites=True,
            base_overrides={"nv": 1.0, "d1": d1_val},
        )
        esp = res_dir["actual"]["especificaciones"]
        desg = res_dir["actual"]["desglose"]
        assert math.isclose(s_sym["dm"], d1_val, rel_tol=1e-12)
        assert math.isclose(s_sym["tm"], d1_val / s_sym["vg"], rel_tol=1e-12)
        assert math.isclose(s_ev["dm"], d1_val, rel_tol=1e-12)
        assert math.isclose(s_ev["tm"], s_sym["tm"], rel_tol=1e-12)
        assert esp["dm"] == d1_val, f"V8 Punto 2: ficha mostró dm={esp['dm']} != {d1_val}"
        assert math.isclose(desg["tm_s"], round(s_sym["tm"], 4), abs_tol=1e-9), (
            f"V8 Punto 2: tm={desg['tm_s']} != simbólico {s_sym['tm']}"
        )
        assert math.isclose(esp["tm_s"], round(s_sym["tm"], 3 if s_sym["tm"] < 10.0 else 1), abs_tol=1e-9)
        if d1_val == 0.5:
            esperado_km = s_sym["Cop"] / 0.0005
            assert math.isclose(desg["cop_por_km"], round(esperado_km, 4), abs_tol=1e-4), (
                f"V8 Punto 2: cop_por_km={desg['cop_por_km']} != {esperado_km}"
            )
            assert math.isclose(esp["cop_por_km"], round(esperado_km, 3), abs_tol=1e-3)
    print("[V8 Punto 2 OK] Distancias 0.5 m, 1.0 m y 2.0 m conservan dm = nv*d1, tm = dm/vg y cop_por_km.")


def verificar_v8_punto_3_rechazo_espesor_no_positivo(candidato):
    for e_bad in (-0.01, 0.0):
        try:
            modelo.resolver(dict(candidato, e=e_bad))
            raise AssertionError(f"V8 Punto 3: modelo.resolver debió rechazar e={e_bad}")
        except ValueError as exc:
            assert "'e'" in str(exc)

        assert evaluador.evaluar_punto(candidato, estricto_prolado=False, e=e_bad) is None
        assert evaluador.evaluar_punto(candidato, estricto_prolado=True, e=e_bad) is None

        try:
            diseno.optimizar_especificaciones(candidato, vars_libres=[], base_overrides={"e": e_bad})
            raise AssertionError(f"V8 Punto 3: diseno debió rechazar e={e_bad}")
        except ValueError as exc:
            msg = str(exc)
            assert "'e'" in msg and str(e_bad) in msg, f"Mensaje inesperado: {msg}"

        try:
            app.analizar_diseno(app.PeticionAnalisisDiseno(
                ejecutar_optimizador=False,
                base_overrides={**candidato, "e": e_bad},
            ))
            raise AssertionError(f"V8 Punto 3: API debió rechazar e={e_bad}")
        except HTTPException as exc:
            assert exc.status_code == 400
            assert "'e'" in str(exc.detail) and str(e_bad) in str(exc.detail)

    # Con el espesor positivo de referencia, ambas rutas conservan e y coinciden
    s_ref_sym = modelo.resolver(candidato)
    res_ref = diseno.optimizar_especificaciones(candidato, vars_libres=[])
    assert res_ref["entradas_actual"]["e"] == candidato["e"]
    assert res_ref["actual"]["especificaciones"]["e_mm"] == round(s_ref_sym["e"] * 1000.0, 1)
    assert math.isclose(res_ref["actual"]["especificaciones"]["Pelec"], round(s_ref_sym["Pelec"], 1), abs_tol=1e-9)
    print("[V8 Punto 3 OK] Espesor e <= 0 (-0.01 y 0.0 m) rechazado en modelo, evaluador rápido, diseño y API (400).")


def verificar_v9_punto_1_fexc_y_tope_empuje(candidato, sol_cand, reglas_equipo):
    # Reglas Ttot <= 13 N y Fexc >= 10 N sobre el candidato de 130 °C (Ttot=12.22 N, Fexc=13.90 N)
    reglas_13 = list(reglas_equipo) + [
        {"id": "c_ttot_13", "variable": "Ttot", "op": "<=", "valor": 13.0, "activa": True, "grupo": "custom"},
        {"id": "c_fexc_10", "variable": "Fexc", "op": ">=", "valor": 10.0, "activa": True, "grupo": "custom"},
    ]
    res_13 = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_13
    )
    assert res_13["encontrado"] is True
    assert not res_13["avisos_restricciones_actual"], (
        f"V9 Punto 1: avisos inesperados {res_13['avisos_restricciones_actual']}"
    )
    esp_13 = res_13["actual"]["especificaciones"]
    assert esp_13["carga_factible_instalada"] is True
    mc_min = float(esp_13["mcarga_min_kg"])
    mc_max = float(esp_13["capacidad_util_kg"])
    assert mc_min <= 1.0 <= mc_max, f"V9 Punto 1: 1.0 kg excluido de [{mc_min}, {mc_max}]"

    lim_13 = diseno._limites_efectivos_mapa(sol_cand, reglas_13)
    det_nom = evaluador.evaluar_punto_equipo_fijo(sol_cand, 1.0, lim_13)
    assert det_nom is not None and det_nom["valido"] is True
    assert math.isclose(det_nom["Fexc"], sol_cand["Fexc"], rel_tol=1e-12)
    assert math.isclose(det_nom["Fexc"], 13.90, abs_tol=0.05)

    for carga in (mc_min, 1.0, mc_max):
        det = evaluador.evaluar_punto_equipo_fijo(sol_cand, carga, lim_13)
        assert det is not None and det["valido"] is True, f"V9 Punto 1: carga {carga} rechazada"
        assert max(det["Ttot"], det["Tcruc"]) <= 13.0 + 1e-9
        assert det["Fexc"] >= 10.0 - 1e-9

    # Control con tope de empuje Ttot <= 12 N (inferior al nominal 12.22 N): ambas rutas deben rechazar 1 kg
    reglas_12 = list(reglas_equipo) + [
        {"id": "c_ttot_12", "variable": "Ttot", "op": "<=", "valor": 12.0, "activa": True, "grupo": "custom"},
        {"id": "c_fexc_10", "variable": "Fexc", "op": ">=", "valor": 10.0, "activa": True, "grupo": "custom"},
    ]
    res_12 = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True, restricciones=reglas_12
    )
    assert res_12["encontrado"] is False
    assert any("Ttot=" in a for a in res_12["avisos_restricciones_actual"])
    lim_12 = diseno._limites_efectivos_mapa(sol_cand, reglas_12)
    det_12 = evaluador.evaluar_punto_equipo_fijo(sol_cand, 1.0, lim_12)
    assert det_12 is None, f"V9 Punto 1: 1.0 kg debió ser rechazado (None) con Ttot<=12 N, dio {det_12}"
    esp_12 = res_12["actual"]["especificaciones"]
    assert (not esp_12["carga_factible_instalada"]) or (float(esp_12["capacidad_util_kg"]) < 1.0)
    print(f"[V9 Punto 1 OK] Fexc conserva N*Tmax1 ({det_nom['Fexc']:.2f} N); Ttot<=13 N admite 1 kg en [{mc_min}, {mc_max}] kg y Ttot<=12 N lo rechaza.")


def verificar_v9_punto_2_velocidad_baja(candidato):
    # Caso 1: v = 0.1 m/s, vv = 0 m/s, d1 = 0.5 m, nv = 1 -> vg = 0.1 m/s, tm = 5.0 s
    ent_01 = dict(candidato, nv=1.0, d1=0.5, v=0.1, vv=0.0)
    s_sym_01 = modelo.resolver(ent_01)
    s_ev_01 = evaluador.evaluar_punto(candidato, estricto_prolado=False, nv=1.0, d1=0.5, v=0.1, vv=0.0)
    res_api_01 = app.analizar_diseno(app.PeticionAnalisisDiseno(
        ejecutar_optimizador=False,
        base_overrides=ent_01,
    ))
    assert s_ev_01 is not None and res_api_01["actual"] is not None
    assert math.isclose(s_sym_01["vg"], 0.1, rel_tol=1e-12)
    assert math.isclose(s_sym_01["tm"], 5.0, rel_tol=1e-12)
    assert math.isclose(s_ev_01["v"], 0.1, rel_tol=1e-12)
    assert math.isclose(s_ev_01["vg"], 0.1, rel_tol=1e-12)
    assert math.isclose(s_ev_01["tm"], 5.0, rel_tol=1e-12)
    esp_01 = res_api_01["actual"]["especificaciones"]
    assert esp_01["v"] == 0.1 and esp_01["vg"] == 0.1 and esp_01["dm"] == 0.5 and esp_01["tm_s"] == 5.0

    # Caso 2: v = 0.1 m/s, vv = 0.12 m/s (vg = -0.02 m/s) -> rechazado sin publicar duración de avance
    try:
        modelo.resolver(dict(candidato, nv=1.0, d1=0.5, v=0.1, vv=0.12))
        raise AssertionError("V9 Punto 2: modelo.resolver debió rechazar vg = -0.02 m/s")
    except ValueError:
        pass
    assert evaluador.evaluar_punto(candidato, estricto_prolado=False, nv=1.0, d1=0.5, v=0.1, vv=0.12) is None
    try:
        app.analizar_diseno(app.PeticionAnalisisDiseno(
            ejecutar_optimizador=False,
            base_overrides={**candidato, "nv": 1.0, "d1": 0.5, "v": 0.1, "vv": 0.12},
        ))
        raise AssertionError("V9 Punto 2: API debió rechazar v=0.1 frente a vv=0.12")
    except HTTPException as exc:
        assert exc.status_code == 400
        assert "vg" in str(exc.detail) and "0.1" in str(exc.detail)

    # Caso control: v = 0.2 m/s, vv = 0 m/s -> vg = 0.2 m/s, tm = 2.5 s
    s_sym_02 = modelo.resolver(dict(candidato, nv=1.0, d1=0.5, v=0.2, vv=0.0))
    res_dir_02 = diseno.optimizar_especificaciones(
        candidato, vars_libres=[], cbat_kg=750.0, respetar_limites=True,
        base_overrides={"nv": 1.0, "d1": 0.5, "v": 0.2, "vv": 0.0},
    )
    esp_02 = res_dir_02["actual"]["especificaciones"]
    assert math.isclose(s_sym_02["tm"], 2.5, rel_tol=1e-12)
    assert esp_02["v"] == 0.2 and esp_02["vg"] == 0.2 and esp_02["dm"] == 0.5 and esp_02["tm_s"] == 2.5
    print("[V9 Punto 2 OK] Baja velocidad conservada (v=0.1->tm=5.0 s, v=0.2->tm=2.5 s) y viento contrario vv=0.12 rechazado (HTTP 400).")


def contrastar_ecuaciones(base):
    validos = rechazados = 0
    max_residuo = 0.0
    for v, t, lam, capas in itertools.product((7, 8.5, 10), (70, 85, 95), (1.6, 2.3, 4), ((0, 0), (1, 1), (3, 2))):
        entradas = dict(base, v=v, T2=t, lam=lam, ncapS=capas[0], ncapI=capas[1])
        s = evaluador.evaluar_punto(entradas, estricto_prolado=True)
        if s is None:
            rechazados += 1
            continue
        modelo._verificar_consistencia_global(s)
        for _, args, fn in modelo._RESIDUAL_EVAL_CACHE:
            a, b = fn(*(s[k] for k in args))
            max_residuo = max(max_residuo, abs(a - b) / max(1.0, abs(a), abs(b)))
        validos += 1
    assert validos > 0 and max_residuo < 1e-10, f"Residuo excesivo: {max_residuo}"
    print(f"[Barrido] soluciones={validos}, descartes={rechazados}, residuo máximo={max_residuo:.3e}")

    ref = modelo.resolver(base)
    for libre, objetivo, nuevo in (("nv", "dm", 2), ("T2", "rho2", 90), ("mflot", "V", 3.4), ("e", "U", 0.016)):
        conocido = modelo.resolver(dict(base, **{libre: nuevo}))
        inv = dict(base)
        del inv[libre]
        inv[objetivo] = conocido[objetivo]
        recuperado = modelo.resolver(inv, referencia=ref)[libre]
        vuelta = modelo.resolver(dict(base, **{libre: recuperado}))
        assert math.isclose(conocido[objetivo], vuelta[objetivo], rel_tol=1e-7)


def main():
    flujo.validar_integridad_flujo()
    base = modelo.valores_iniciales()
    registro = Path(__file__).parent / "especf_optm_hist/historico_dirigible_2026-11-25.json"
    historico_ent = json.loads(registro.read_text())[0]["entradas"]

    for nombre, punto in (("Base", base), ("Histórico v1", historico_ent)):
        contrastar_casco(punto, nombre)

    # Óptimo predeterminado actual (Mylar + Kapton/PET: lim_T2 = 130 °C, techo interno 140 °C)
    opt = diseno.optimizar_especificaciones(base, respetar_limites=True)
    assert opt["encontrado"] is True
    lim_t2 = next(r for r in opt["restricciones"] if r["id"] == "lim_T2")
    assert lim_t2["valor"] == 130.0
    candidato = opt["entradas_optimo"]
    sol_cand = evaluador.evaluar_punto(candidato, estricto_prolado=True)
    assert sol_cand is not None and sol_cand["valido"] and sol_cand["T2"] <= 130.0 + 1e-6

    # Verificar que G7 Panel A barre al menos hasta 140 °C
    gs_opt = graficas.construir_datos_graficas(sol_cand, set(modelo.FIJAS_INI))
    g7_opt = next(g for g in gs_opt if g["id"] == "temperatura_escalabilidad")
    assert max(g7_opt["paneles"][0]["xs"]) >= 140.0

    # Referencia calibrada a lim_T2 = 95 °C para preservar exactamente las regresiones históricas V2-V6
    restr_95 = diseno.restricciones_defecto(base, activar_hardware=True)
    for r in restr_95:
        if r["id"] == "lim_T2":
            r["valor"] = 95.0
    opt_95 = diseno.optimizar_especificaciones(base, respetar_limites=True, restricciones=restr_95)
    assert opt_95["encontrado"] is True
    candidato_95 = opt_95["entradas_optimo"]
    sol_95 = evaluador.evaluar_punto(candidato_95, estricto_prolado=True)
    assert sol_95 is not None and sol_95["valido"]

    # Verificar invariancia al orden de variables
    opt_inv = diseno.optimizar_especificaciones(
        base, respetar_limites=True, vars_libres=list(reversed(diseno.VARS_OPTIMIZABLES_DISENO))
    )
    assert math.isclose(opt["optimo"]["score_total"], opt_inv["optimo"]["score_total"], abs_tol=1e-6)

    # Verificar rechazos de dominio esperados (Punto 8)
    for invalida in ({"ncal": 1.5}, {"dTc": 80.0}, {"N": 3.5}):
        try:
            modelo.resolver(dict(base, **invalida))
            raise AssertionError(f"Debió rechazar entrada inválida {invalida}")
        except ValueError:
            pass

    verificar_punto_1_limites_hardware(candidato_95)
    verificar_punto_2_capacidad_util(candidato_95, sol_95)
    verificar_punto_3_angulo_crucero(base)
    verificar_punto_4_casco_sin_aislamiento(base)
    verificar_punto_5_precalentamiento_regional(base, historico_ent)
    verificar_punto_6_g7_termica(base)
    verificar_punto_7_dron_g7(sol_95)
    verificar_v3_punto_1_operador_hardware(candidato_95)
    verificar_v3_punto_2_cotas_min_max_mtot(candidato_95, sol_95)
    verificar_v3_punto_3_importar_y_reevaluar_v1(registro)
    verificar_v3_punto_4_dron_g7_y_nulls(base, sol_95)
    verificar_v4_punto_1_intervalo_estrecho_pelec(candidato_95, sol_95, opt_95["restricciones"])
    verificar_v4_punto_2_historico_conserva_restricciones(candidato_95, opt_95["restricciones"])
    verificar_v5_punto_1_precision_extremos_estrechos(sol_95, opt_95["restricciones"])
    opt_api = app.analizar_diseno(app.PeticionAnalisisDiseno(cbat_kg=750.0, respetar_limites=True))
    verificar_v5_punto_2_guardado_optimo_inmutable(opt_api["entradas_optimo"], opt_api)
    verificar_v6_punto_1_cop_en_rango_carga(sol_95, opt_95["restricciones"])
    verificar_v6_punto_4_casos_fraccion_aire(candidato_95, candidato)
    verificar_v6_punto_5_titulos_viajes_d1(candidato_95, historico_ent)
    verificar_v6_hipotesis_b_enfriamiento(base)
    verificar_v7_punto_1_techo_busqueda_t2(candidato)
    verificar_v7_punto_2_autonomia_en_rango_carga(sol_cand, opt["restricciones"])
    verificar_v7_punto_3_etiqueta_g7(candidato)
    verificar_v7_punto_4_y_5_dtc_y_readme(base)
    verificar_v8_punto_1_c_recambio_en_rango_carga(candidato, opt["restricciones"])
    verificar_v8_punto_2_distancia_submetro(candidato)
    verificar_v8_punto_3_rechazo_espesor_no_positivo(candidato)
    verificar_v9_punto_1_fexc_y_tope_empuje(candidato, sol_cand, opt["restricciones"])
    verificar_v9_punto_2_velocidad_baja(candidato)
    contrastar_ecuaciones(base)

    # Verificar carga y renderizado completo de la API (incluye KaTeX, gráficas y alertas)
    estado = app.obtener_estado()
    assert estado["resumen"]["total_variables"] == len(modelo.VARIABLES) == 170
    assert estado["resumen"]["total_ecuaciones"] == len(modelo.ECUACIONES) == 108
    assert estado["resumen"]["total_fijas"] == len(modelo.FIJAS_INI) == 62

    print("\n=== RESUMEN CANDIDATO OPTIMO T2<=130°C (DEFECTO MYLAR) ===")
    print(
        f"Score={opt['optimo']['score_total']} | T2={sol_cand['T2']:.2f} °C | Pelec={sol_cand['Pelec']:.2f} W | "
        f"Pcruc={sol_cand['Pcruc']:.2f} W | Ttot={sol_cand['Ttot']:.2f} N | mbat={sol_cand['mbat']*1000:.1f} g | "
        f"Cop={sol_cand['Cop']:.3f} Bs | Cap.fija={opt['optimo']['especificaciones']['mcarga_min_kg']}–{opt['optimo']['especificaciones']['capacidad_util_kg']} kg"
    )
    print("=== REFERENCIA T2<=95°C ===")
    print(
        f"Score={opt_95['optimo']['score_total']} | Pelec={sol_95['Pelec']:.2f} W | Pcruc={sol_95['Pcruc']:.2f} W | "
        f"Ttot={sol_95['Ttot']:.2f} N | θman={sol_95['theta']:.2f}° | θcruc={sol_95['thcruc']:.2f}° | "
        f"mbat={sol_95['mbat']*1000:.1f} g | Epre={sol_95['Epre']/1000:.1f} kJ | Cop={sol_95['Cop']:.3f} Bs | "
        f"Cap.fija={opt_95['optimo']['especificaciones']['mcarga_min_kg']}–{opt_95['optimo']['especificaciones']['capacidad_util_kg']} kg"
    )
    print("AUDITORIA V2/V3/V4/V5/V6/V7/V8/V9 SUPERADA")
    print(
        "\nNota v1->v2: la primera auditoría incluía un escenario que añadía una piel extra con mad + area*sigma; "
        "al estar ya integrada la piel exterior en Sc, ese escenario equivale a añadir una segunda piel adicional."
    )


if __name__ == "__main__":
    main()
