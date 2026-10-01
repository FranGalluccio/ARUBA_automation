import os
import json
from datetime import datetime
from base_pel import LoginPel, get_app_base_url
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
    # Login PEL
    LoginPel(page).login_pel(config)

    # Su PEL il link sidebar "Cestino" è un bottone shadow-DOM che non supera il
    # controllo di visibilità di Playwright (stesso problema riscontrato per
    # "Risposta automatica"): si naviga direttamente all'URL, confermato
    # cliccando manualmente dalla sidebar in debug.
    page.goto(get_app_base_url(page) + "/new/settings/messages-writing/empty-trash", timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.locator('h1').filter(has_text="Cestino").or_(
        page.locator('h1').filter(has_text="Corbeille")
    ).first.wait_for(state="visible", timeout=10000)

    # Verifica che la sezione Cestino nelle impostazioni sia caricata:
    # il pannello delle impostazioni deve mostrare testo relativo alla svuotatura/eliminazione del cestino
    sezione_visibile = (
        page.get_by_text("Svuota cestino", exact=False).count() > 0 or
        page.get_by_text("Vider la corbeille", exact=False).count() > 0 or
        page.get_by_text("eliminazione automatica", exact=False).count() > 0 or
        page.get_by_text("suppression automatique", exact=False).count() > 0 or
        page.get_by_text("automatiquement", exact=False).count() > 0 or
        page.locator('[class*="trash-settings"], [class*="cestino-settings"], aru-input-choice, select').count() > 0
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
