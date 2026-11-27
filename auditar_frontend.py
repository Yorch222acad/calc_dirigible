"""Suite E2E de auditoría del frontend con Playwright (Chromium real contra app.py)."""
from __future__ import annotations

import json
import re
import socket
import tempfile
import threading
import time
import urllib.request
from pathlib import Path

import uvicorn
from playwright.sync_api import sync_playwright

import app
import diseno


def _puerto_libre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return int(s.getsockname()[1])


def _esperar_servidor(url: str, timeout_s: float = 15.0) -> None:
    t0 = time.monotonic()
    while time.monotonic() - t0 < timeout_s:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as resp:
                if resp.status == 200:
                    return
        except Exception:
            time.sleep(0.15)
    raise RuntimeError(f"El servidor no respondió en {url} tras {timeout_s}s.")


def main() -> None:
    app.estado.reiniciar()
    puerto = _puerto_libre()
    base_url = f"http://127.0.0.1:{puerto}"

    config = uvicorn.Config(app.app, host="127.0.0.1", port=puerto, log_level="warning")
    server = uvicorn.Server(config)
    hilo = threading.Thread(target=server.run, daemon=True)
    hilo.start()

    orig_hist_path = diseno.HISTORICO_PATH
    try:
        _esperar_servidor(f"{base_url}/api/estado")

        with tempfile.TemporaryDirectory() as tmpdir:
            hist_tmp = Path(tmpdir) / "historico_e2e.json"
            diseno.HISTORICO_PATH = hist_tmp

            page_errors: list[str] = []
            local_console_errors: list[str] = []

            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                context = browser.new_context(viewport={"width": 1440, "height": 960})
                page = context.new_page()

                page.on("pageerror", lambda err: page_errors.append(str(err)))
                page.on(
                    "console",
                    lambda msg: (
                        local_console_errors.append(msg.text)
                        if msg.type == "error" and ("127.0.0.1" in msg.text or "TypeError" in msg.text or "SyntaxError" in msg.text)
                        else None
                    ),
                )

                # 1. Carga inicial y conteo del sistema CAS
                page.goto(base_url, wait_until="domcontentloaded")
                page.wait_for_function(
                    """() => {
                      const f = document.querySelector('#count-fixed')?.textContent?.trim();
                      const c = document.querySelector('#count-calc')?.textContent?.trim();
                      return f === '62' && c === '108';
                    }""",
                    timeout=15000,
                )
                print("[E2E 1 OK] App cargada en Chromium (62 fijas / 108 calculadas, sin errores de módulos ES6).")

                # 2. Gráfica G7 Panel B: curvas segmentadas y hover sobre valores null ("Sin solución")
                page.locator("#charts-nav-list button", has_text="G7.").click()
                panel_b = page.locator(".chart-subpanel-card").nth(1)
                panel_b.wait_for(state="visible", timeout=10000)
                overlay = panel_b.locator('svg.chart-svg rect[fill="transparent"]')
                box = overlay.bounding_box()
                assert box is not None and box["width"] > 100
                # Mover el cursor cerca del extremo derecho de nv donde la batería del dron diverge (null)
                page.mouse.move(box["x"] + box["width"] - 8, box["y"] + box["height"] * 0.5)
                readout_txt = panel_b.locator(".chart-readout-bar").inner_text()
                assert "Sin solución" in readout_txt, f"Se esperaba 'Sin solución' en readout G7 Panel B, dio: {readout_txt}"
                assert panel_b.locator("svg.chart-svg polyline").count() >= 3
                print("[E2E 2 OK] G7 Panel B renderiza SVG y reporta 'Sin solución' sin colapsar null a 0.")

                # 3. Abrir Diseño Óptimo y validar operadores bloqueados + guardado v5/v6 inmutable
                with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST") as resp_init_info:
                    page.locator("#btn-open-design").click()
                init_json = resp_init_info.value.json()
                assert init_json["encontrado"] is True
                init_score = float(init_json["optimo"]["score_total"])
                init_recambio = float(init_json["optimo"]["especificaciones"]["c_recambio"])
                assert init_json["cbat_kg"] == 750.0

                page.locator("#btn-save-opt-hist").wait_for(state="visible", timeout=15000)
                page.wait_for_function(
                    "() => !document.querySelector('#btn-save-opt-hist')?.disabled",
                    timeout=15000,
                )

                op_selects = page.locator(".design-limit-row select.design-lim-op")
                assert op_selects.count() >= 7
                for i in range(2, 7):
                    assert op_selects.nth(i).is_disabled(), f"El selector hardware #{i} debería estar disabled"

                # Editar precio de batería a 1500 y mover un peso SIN recalcular
                cbat_inp = page.locator("#design-cbat-input")
                cbat_inp.fill("1500")
                cbat_inp.dispatch_event("input")
                slider0 = page.locator(".design-weight-slider").first
                slider0.fill("10")
                slider0.dispatch_event("input")

                # Botón 1: Guardar en histórico desde ficha -> debe conservar análisis de 750 Bs/kg
                with page.expect_response(lambda r: r.url.endswith("/api/historico") and r.request.method == "POST"):
                    page.locator("#btn-save-opt-hist").click()

                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 1
                assert regs[0]["cbat_kg"] == 750.0, f"Botón 1 usó cbat editado ({regs[0]['cbat_kg']})"
                assert abs(regs[0]["score_total"] - init_score) < 1e-6
                assert abs(regs[0]["especificaciones"]["c_recambio"] - init_recambio) < 1e-6

                # Botón 2: Cambiar a pestaña Histórico Manual y pulsar "Guardar último óptimo" sin recalcular
                page.locator('.design-tab-btn[data-tab="historico"]').click()
                with page.expect_response(lambda r: r.url.endswith("/api/historico") and r.request.method == "POST"):
                    page.locator("#btn-hist-save-optimo").click()

                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 2
                assert regs[0]["cbat_kg"] == 750.0, f"Botón 2 usó cbat editado ({regs[0]['cbat_kg']})"
                assert abs(regs[0]["score_total"] - init_score) < 1e-6
                assert abs(regs[0]["especificaciones"]["c_recambio"] - init_recambio) < 1e-6

                # Botón 3 (V6 Punto 3): Abrir Casos Tipo sin recalcular y guardar fila "★ Punto óptimo base"
                page.locator('.design-tab-btn[data-tab="casos"]').click()
                with page.expect_response(lambda r: r.url.endswith("/api/historico") and r.request.method == "POST"):
                    page.locator(".caso-save-btn").first.click()

                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 3
                assert regs[0]["cbat_kg"] == 750.0, f"Casos Tipo usó cbat editado ({regs[0]['cbat_kg']})"
                assert abs(regs[0]["score_total"] - init_score) < 1e-6
                assert abs(regs[0]["especificaciones"]["c_recambio"] - init_recambio) < 1e-6
                print("[E2E 3 OK] Hardware bloqueado y los 3 botones de guardado (ficha, histórico, Casos Tipo) inmutables ante ediciones sin recalcular.")

                # 4. Recalcular con 1500 Bs/kg + regla mtot >= 4.1 -> guardar, aplicar al sistema y reevaluar
                page.locator('.design-tab-btn[data-tab="optimo"]').click()
                page.locator("#design-new-lim-var").select_option("mtot")
                page.locator("#design-new-lim-op").select_option(">=")
                page.locator("#design-new-lim-val").fill("4.1")
                page.locator("#btn-add-design-limit").click()

                with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST") as resp_ana_info:
                    page.locator("#btn-run-design-opt").click()
                analizar_json = resp_ana_info.value.json()
                assert analizar_json["encontrado"] is True
                assert analizar_json["cbat_kg"] == 1500.0

                with page.expect_response(lambda r: r.url.endswith("/api/historico") and r.request.method == "POST"):
                    page.locator("#btn-save-opt-hist").click()

                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 4
                reg_recalc = regs[0]
                assert reg_recalc["cbat_kg"] == 1500.0
                assert abs(reg_recalc["score_total"] - analizar_json["optimo"]["score_total"]) < 1e-6
                assert abs(
                    reg_recalc["especificaciones"]["c_recambio"]
                    - analizar_json["optimo"]["especificaciones"]["c_recambio"]
                ) < 1e-6
                assert abs(
                    reg_recalc["especificaciones"]["mcarga_min_kg"]
                    - analizar_json["optimo"]["especificaciones"]["mcarga_min_kg"]
                ) < 1e-6
                assert any(
                    r["variable"] == "mtot" and r["op"] == ">=" and abs(r["valor"] - 4.1) < 1e-6
                    for r in (reg_recalc.get("restricciones") or [])
                )

                # Verificar también Casos Tipo tras recalcular a 1500 Bs/kg
                page.locator('.design-tab-btn[data-tab="casos"]').click()
                with page.expect_response(lambda r: r.url.endswith("/api/historico") and r.request.method == "POST"):
                    page.locator(".caso-save-btn").first.click()
                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 5
                assert regs[0]["cbat_kg"] == 1500.0
                assert abs(regs[0]["score_total"] - analizar_json["casos_tipo"][0]["score_total"]) < 1e-6

                # V6 Punto 2: Aplicar óptimo al sistema y verificar que /api/diseno/analizar posterior parte de la base aplicada
                page.locator('.design-tab-btn[data-tab="optimo"]').click()
                with page.expect_response(lambda r: r.url.endswith("/api/modificar") and r.request.method == "POST") as resp_mod_info:
                    with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST") as resp_post_apply_info:
                        page.locator("#btn-apply-design-opt").click()
                assert resp_mod_info.value.status == 200
                post_apply_json = resp_post_apply_info.value.json()
                for var_chk in ("T2", "lam", "mflot"):
                    assert abs(
                        post_apply_json["entradas_actual"][var_chk] - analizar_json["entradas_optimo"][var_chk]
                    ) < 1e-5, f"V6 Punto 2: {var_chk} quedó con base vieja ({post_apply_json['entradas_actual'][var_chk]} != {analizar_json['entradas_optimo'][var_chk]})"

                # Reevaluar desde la pestaña Histórico -> debe generar un 6º registro trazando origen_id
                page.locator('.design-tab-btn[data-tab="historico"]').click()
                with page.expect_response(lambda r: r.url.endswith("/reevaluar") and r.request.method == "POST"):
                    page.locator(".hist-reeval-btn").nth(1).click()

                regs = json.loads(hist_tmp.read_text(encoding="utf-8"))
                assert len(regs) == 6
                assert regs[0]["origen_id"] == reg_recalc["id"]
                assert regs[0]["modelo_version"] == "v2"
                print("[E2E 4 OK] Recálculo 1500 Bs/kg + mtot>=4.1, Aplicar óptimo (sin base vieja), Casos Tipo y reevaluación verificados.")

                # 5. V7 Punto 4: Enfriamiento dTc dinámico en la ficha (10 K -> 72.4 s y 20 K -> 158 s)
                with page.expect_response(lambda r: r.url.endswith("/api/reiniciar") and r.request.method == "POST"):
                    with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST"):
                        page.locator("#btn-reset").click()

                page.locator('.design-tab-btn[data-tab="optimo"]').click()
                page.locator("#design-limits-toggle").uncheck()
                chks = page.locator(".design-var-check")
                for i in range(chks.count()):
                    if chks.nth(i).is_checked():
                        chks.nth(i).uncheck()
                page.locator("#design-new-var-sel").select_option("dTc")
                page.locator("#btn-add-design-var").click()
                dtc_chk = page.locator('.design-var-check[value="dTc"]')
                if dtc_chk.is_checked():
                    dtc_chk.uncheck()

                dtc_inp = page.locator('.design-var-num[data-var="dTc"]')
                dtc_inp.fill("10")
                dtc_inp.dispatch_event("input")
                with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST"):
                    page.locator("#btn-run-design-opt").click()
                spec_txt_10 = page.locator(".design-spec-grid").inner_text()
                assert re.search(r"Enfriamiento 10 K \(tc\)\s*72\.4 s", spec_txt_10), (
                    f"V7 Punto 4: se esperaba 'Enfriamiento 10 K (tc)' con 72.4 s, got:\n{spec_txt_10}"
                )

                dtc_inp.fill("20")
                dtc_inp.dispatch_event("input")
                with page.expect_response(lambda r: r.url.endswith("/api/diseno/analizar") and r.request.method == "POST"):
                    page.locator("#btn-run-design-opt").click()
                spec_txt_20 = page.locator(".design-spec-grid").inner_text()
                assert re.search(r"Enfriamiento 20 K \(tc\)\s*158(?:\.0)? s", spec_txt_20), (
                    f"V7 Punto 4: se esperaba 'Enfriamiento 20 K (tc)' con 158 s, got:\n{spec_txt_20}"
                )
                print("[E2E 5 OK] Ficha muestra dinámicamente 'Enfriamiento 10 K (tc)' (72.4 s) y 'Enfriamiento 20 K (tc)' (158 s).")

                browser.close()

            assert not page_errors, f"Errores JS en página: {page_errors}"
            assert not local_console_errors, f"Errores de consola: {local_console_errors}"
            print("AUDITORIA FRONTEND PLAYWRIGHT SUPERADA")
    finally:
        diseno.HISTORICO_PATH = orig_hist_path
        server.should_exit = True
        hilo.join(timeout=5.0)


if __name__ == "__main__":
    main()
