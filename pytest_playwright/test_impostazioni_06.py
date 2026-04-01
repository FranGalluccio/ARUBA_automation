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

def test_impostazioni_cestino(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Cestino (URL calcolato dopo il login per supportare prod-aruba)
    page.goto(get_app_base_url(page) + "/new/settings/home", timeout=20000)
    if not page.locator('button[title="Cestino"]').is_visible():
        page.locator('button[title="Messaggi e scrittura"]').click(force=True)
        page.locator('button[title="Cestino"]').first.wait_for(state="visible", timeout=5000)
    page.locator('button[title="Cestino"]').click(force=True)

    # Verifica che la sezione Cestino nelle impostazioni sia caricata:
    # il pannello delle impostazioni deve mostrare testo relativo alla svuotatura/eliminazione del cestino
    sezione_visibile = (
        page.get_by_text("Svuota cestino", exact=False).count() > 0 or
        page.get_by_text("eliminazione automatica", exact=False).count() > 0 or
        page.locator('[class*="trash-settings"], [class*="cestino-settings"]').count() > 0
    )
    assert sezione_visibile, "La sezione Cestino nelle impostazioni non si è caricata"

    # Verifica che ci sia almeno un'opzione di configurazione
    opzioni = page.locator('select, input[type="radio"], input[type="checkbox"], aru-input-choice').count()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert opzioni > 0, "Nessuna opzione di configurazione trovata nella sezione Cestino"
