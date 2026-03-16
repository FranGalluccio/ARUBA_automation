import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings"


def test_risposta_automatica(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Avvisi e report (sotto accordion "Messaggi e scrittura")
    page.goto(SETTINGS_URL + "/home", timeout=20000)
    time.sleep(2)
    # Espandi l'accordion "Messaggi e scrittura" se necessario
    if not page.locator('button[title="Avvisi e report"]').is_visible():
        page.locator('button[title="Messaggi e scrittura"]').first.click(force=True)
        time.sleep(2)
    page.locator('button[title="Avvisi e report"]').click(force=True)
    time.sleep(3)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_impostazioni_04_pre_{datetime.now():%H-%M-%S}.png"))

    # Verifica che la pagina Avvisi e report sia caricata
    page.locator('h1, aru-tab-group, aru-table, [class*="alert"], [class*="notification"]').first.wait_for(state="visible", timeout=8000)
    assert page.locator('h1, aru-tab-group, aru-table, [class*="alert"], [class*="notification"]').first.is_visible(), \
        "La pagina Avvisi e report non si è caricata"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
