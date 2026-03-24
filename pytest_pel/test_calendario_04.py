import os
import json
import time
from datetime import datetime
from base_pel import LoginPel, elimina_evento_pel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw_ics = config.get("calendario_import", "dati_test/calendario-test.ics")
FILE_ICS = os.path.normpath(os.path.join(GIT_ROOT, _raw_ics))
assert os.path.exists(FILE_ICS), f"File ICS non trovato: {FILE_ICS}"


def test_import_export_calendario(page):
    """Importa calendario da .ics, poi esporta e verifica che il dialog si chiuda."""
    LoginPel(page).login_pel(config)

    try:
        page.get_by_role("button", name="Calendario").click()
        page.wait_for_load_state("load")
        page.wait_for_timeout(1000)

        # --- Importa ---
        page.get_by_role("button", name="Importa").first.click()
        page.locator("#hidden_input").wait_for(state="attached", timeout=5000)
        page.locator("#hidden_input").set_input_files(FILE_ICS)

        page.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')];
            const btn = btns.find(b => b.textContent.trim() === 'Importa');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(3000)

        # Chiudi dialog se ancora aperto
        if page.locator('.cdk-overlay-pane').count() > 0:
            try:
                page.locator('button').filter(has_text="Annulla").last.click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass

        # Reload per ripristinare sidebar
        page.reload()
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_04_post_import_{datetime.now():%H-%M-%S}.png"))

        # --- Esporta ---
        esporta_btn = page.locator('[title="Esporta"]').first
        esporta_btn.wait_for(state="visible", timeout=8000)
        esporta_btn.click()

        dialog_esporta = page.locator('.cdk-overlay-pane button').filter(has_text="Esporta").first
        dialog_esporta.wait_for(state="visible", timeout=5000)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        try:
            with page.expect_download(timeout=8000) as dl:
                dialog_esporta.click()
            dl.value
            print("Export: download catturato")
        except Exception:
            page.wait_for_timeout(2000)
            assert page.locator('.cdk-overlay-pane button').filter(has_text="Annulla").count() == 0, \
                "Dialog Esporta ancora aperto dopo il click su Esporta"
            print("Export: dialog chiuso (blob download)")

        print("test_calendario_04 PASSED")

    finally:
        # Elimina eventi importati (contengono "test" nel titolo)
        elimina_evento_pel(page, "test")
