import os
import json
from datetime import datetime
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


def test_storico_accessi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Storico accessi (sotto accordion "Account e sicurezza")
    page.goto(SETTINGS_URL + "/home", timeout=20000)
    if not page.locator('button[title="Storico accessi"]').is_visible():
        page.locator('button[title="Account e sicurezza"]').click(force=True)
        page.locator('button[title="Storico accessi"]').first.wait_for(state="visible", timeout=5000)
    page.locator('button[title="Storico accessi"]').click(force=True)

    # Storico accessi si apre in una nuova scheda/finestra (link esterno)
    # Verifica che il bottone/link sia visibile e cliccabile
    storico_btn = page.locator('button[title="Storico accessi"], a[title="Storico accessi"], button:has-text("Apri"), a:has-text("Apri")').first
    expect(storico_btn).to_be_visible()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
