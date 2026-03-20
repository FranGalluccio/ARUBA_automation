import os
import json
from datetime import datetime
from base_pel import LoginPel
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
    # Login PEL
    LoginPel(page).login_pel(config)

    # Apri menu account (username button apre dropdown con Esci)
    username = config["pel"]["username"].strip()
    try:
        page.locator(f'button[title="{username}"]').click(force=True, timeout=5000)
    except Exception:
        try:
            page.locator('button[title*="@"]').first.click(force=True, timeout=5000)
        except Exception:
            pass

    # Attendi che il bottone Esci sia visibile nel dropdown
    try:
        page.locator('button[title="Esci"]').wait_for(state="visible", timeout=5000)
    except Exception:
        pass

    # Clicca su Esci
    try:
        page.locator('button[title="Esci"]').click(force=True)
    except Exception:
        page.locator('button[title="Esci"]').evaluate("el => el.click()")

    # Aspetta che la navigazione verso la pagina di login completi
    page.wait_for_url(lambda url: "INBOX" not in url, timeout=15000)
    page.wait_for_load_state("load", timeout=15000)

    # Verifica che l'URL non contenga più INBOX
    assert "INBOX" not in page.url, \
        f"Il logout non ha reindirizzato alla pagina di login. URL attuale: {page.url}"

    # Verifica che il campo username sia visibile (siamo tornati al login)
    # Il form PEL usa name='text' per il campo username
    login_field = page.locator("input[name='text'], input[name='username'], input#username").first
    login_field.wait_for(state="visible", timeout=15000)
    expect(login_field).to_be_visible()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
