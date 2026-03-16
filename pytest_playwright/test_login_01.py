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


def test_logout(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)

    # Apri menu account (force=True bypassa il div che intercetta i pointer events nel web component)
    page.locator(f'button[title="{config["pec"]["username"]}"]').click(force=True)

    time.sleep(1)

    # Clicca su Esci
    page.locator('button[title="Esci"]').click(force=True)

    # Aspetta che la navigazione verso la pagina di login completi
    page.wait_for_url(lambda url: "INBOX" not in url, timeout=15000)
    page.wait_for_load_state("networkidle", timeout=15000)

    # Verifica che l'URL non contenga più INBOX (siamo usciti dalla casella)
    assert "INBOX" not in page.url, f"Il logout non ha reindirizzato alla pagina di login. URL attuale: {page.url}"

    # Verifica che il campo username sia visibile (siamo tornati al login)
    login_field = page.locator("input[name='username'], input#username, input[type='email']").first
    expect(login_field).to_be_visible()

    time.sleep(1)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
