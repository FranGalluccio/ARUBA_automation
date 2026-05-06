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

def test_storico_accessi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Naviga direttamente alla pagina Storico accessi (URL stabile per IT e FR)
    app_base = get_app_base_url(page)
    page.goto(app_base + "/new/settings/account-security/access-history", timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    # Verifica che la navigazione alla pagina Storico accessi sia riuscita
    assert "access-history" in page.url or "account-security" in page.url, \
        f"Pagina Storico accessi non raggiunta: {page.url}"
