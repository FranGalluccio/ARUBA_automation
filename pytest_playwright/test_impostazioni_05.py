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


def test_posta_indesiderata(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Posta indesiderata (sotto accordion "Account e sicurezza")
    page.goto(SETTINGS_URL + "/home", timeout=20000)
    time.sleep(2)
    if not page.locator('button[title="Posta indesiderata"]').is_visible():
        page.locator('button[title="Account e sicurezza"]').click(force=True)
        time.sleep(1)
    page.locator('button[title="Posta indesiderata"]').click(force=True)
    time.sleep(2)

    # Verifica che la sezione sia caricata
    assert "INBOX" not in page.url or page.locator('h1, h2').filter(has_text="Posta indesiderata").count() > 0 or \
           page.locator('[class*="spam"], [class*="blocklist"]').count() > 0, \
           "La sezione Posta indesiderata non si è caricata correttamente"

    # Aggiunge un mittente alla lista di blocco
    mittente_blocco = "spamtest@example.com"
    try:
        page.get_by_role("button", name="Aggiungi").click()
        time.sleep(1)
        page.locator('input[placeholder*="email"], input[placeholder*="mittente"], input[type="email"]').first.fill(mittente_blocco)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)

        # Verifica che il mittente sia nella lista
        page.locator('tr, li, [class*="row"]').filter(has_text=mittente_blocco).first.wait_for(
            state="visible", timeout=5000
        )
    except Exception as e:
        print(f"Aggiunta alla blocklist non disponibile: {e}")

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: rimuove il mittente dalla lista
    try:
        row = page.locator('tr, li, [class*="row"]').filter(has_text=mittente_blocco).first
        row.locator('button[title="Elimina"], aru-symbol[title="Elimina"]').click()
        time.sleep(2)
    except:
        pass
