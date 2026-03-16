import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_risposta_a_tutti(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia messaggio a se stessi come base per il reply all
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Originale per reply all",
        corpo="Corpo del messaggio originale",
    )
    page.locator('span[title="Invia"]').click()

    # Aspetta consegna
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)

    # Apri primo record
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Clicca Rispondi a tutti
    page.locator('aru-symbol[title="Rispondi a tutti"]').first.click()

    # Aspetta apertura form risposta
    page.locator("div[contenteditable='true']").first.wait_for(state="visible", timeout=5000)
    page.locator("div[contenteditable='true']").first.fill("Risposta a tutti automatica tramite Playwright")

    # Invia risposta
    page.locator('span[title="Invia"]').click()

    # Aspetta consegna risposta
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)

    # Apri il messaggio di risposta ricevuto
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Verifica prefisso "Re:" nell'oggetto
    oggetto = page.locator("div.message-header-title-subject").inner_text().strip()
    assert "Re:" in oggetto, f"Oggetto inatteso (manca 'Re:'): {oggetto}"

    time.sleep(2)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_13___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
