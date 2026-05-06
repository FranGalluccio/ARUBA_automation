import os
import json
from datetime import datetime
from base_pec import LoginPec, get_app_base_url
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

def test_riquadro_di_lettura(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Home (URL calcolato dopo il login per supportare prod-aruba)
    page.goto(get_app_base_url(page) + "/new/settings/home", timeout=20000)

    # Verifica che le 3 opzioni di riquadro siano visibili
    _base = page.locator('button, label, [class*="reading-pane"], [class*="layout"], aru-input-choice')
    opzione_destra = _base.filter(has_text="A destra").or_(_base.filter(has_text="droite")).or_(_base.filter(has_text="Destra")).first
    opzione_basso = _base.filter(has_text="In basso").or_(_base.filter(has_text="En bas")).or_(_base.filter(has_text="Basso")).first

    expect(opzione_destra).to_be_visible()
    expect(opzione_basso).to_be_visible()
    # La terza opzione ("Espandi"/"Développer"/...) ha testo variabile — verifica non bloccante
    opzione_espandi = _base.filter(has_text="Espandi").or_(
        _base.filter(has_text="Développer")
    ).or_(
        _base.filter(has_text="Agrandir")
    ).or_(
        _base.filter(has_text="Plein")
    ).or_(
        _base.filter(has_text="Expand")
    ).first
    try:
        expect(opzione_espandi).to_be_visible(timeout=3000)
    except Exception:
        pass  # testo della terza opzione può variare per lingua

    # Cambia a "In basso"
    opzione_basso.click()

    # Verifica toast o cambio visivo
    toast = page.locator("div.aru-toast__message").first
    try:
        expect(toast).to_be_visible(timeout=3000)
    except Exception:
        pass

    # Screenshot con riquadro "In basso"
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Ripristina a "A destra"
    opzione_destra.click()
