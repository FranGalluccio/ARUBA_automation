import os
import json
import time
from datetime import datetime

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


def test_messaggio_alta_priorita(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test alta priorità playwright {ts}"

    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Test automatico invio messaggio PEC con Playwright",
    )

    # Clicca pulsante altro → alta priorità
    page.locator('aru-button:has(aru-symbol[symbol="more"])').click()
    page.locator('aru-button#high-priority').click()

    # Invia
    page.locator('span[title="Invia"]').click()

    # Aspetta ricezione, aggiorna e apri il primo messaggio
    page.wait_for_timeout(10000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(2000)
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=20000)

    # Verifica che il simbolo "important" sia visibile nel messaggio aperto
    important_symbol = page.locator('aru-symbol[symbol="important"]').first
    expect(important_symbol).to_be_visible()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")