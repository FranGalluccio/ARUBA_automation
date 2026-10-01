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

def test_risposta_automatica(page):
    # Login PEL
    LoginPel(page).login_pel(config)

    # Su PEL non esiste l'accordion "Avvisi e report" presente su PEC: "Risposta
    # automatica" è raggiungibile direttamente via URL (stesso namespace di
    # Firme e Regole messaggi), confermato navigando manualmente dalla sidebar.
    page.goto(get_app_base_url(page) + "/new/settings/messages-writing/automatic-reply", timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_impostazioni_04_pre_{datetime.now():%H-%M-%S}.png"))

    # Verifica che la pagina Risposta automatica sia caricata
    risposta_header = page.locator('h1').filter(has_text="Risposta automatica").or_(
        page.locator('h1').filter(has_text="Réponse automatique")
    ).first
    risposta_header.wait_for(state="visible", timeout=8000)
    avvisi_loaded = risposta_header.is_visible()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert avvisi_loaded, "La pagina Risposta automatica non si è caricata"
