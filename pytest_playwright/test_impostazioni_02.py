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


def test_riquadro_di_lettura(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Home (dove si trova il riquadro di lettura)
    page.goto(SETTINGS_URL + "/home", timeout=20000)
    time.sleep(2)

    # Verifica che le 3 opzioni di riquadro siano visibili
    opzione_destra = page.locator('button, label, [class*="reading-pane"], [class*="layout"]').filter(has_text="A destra").first
    opzione_basso = page.locator('button, label, [class*="reading-pane"], [class*="layout"]').filter(has_text="In basso").first
    opzione_espandi = page.locator('button, label, [class*="reading-pane"], [class*="layout"]').filter(has_text="Espandi").first

    expect(opzione_destra).to_be_visible()
    expect(opzione_basso).to_be_visible()
    expect(opzione_espandi).to_be_visible()

    # Cambia a "In basso"
    opzione_basso.click()
    time.sleep(2)

    # Verifica toast o cambio visivo
    toast = page.locator("div.aru-toast__message").first
    try:
        expect(toast).to_be_visible(timeout=3000)
    except:
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
    time.sleep(2)
