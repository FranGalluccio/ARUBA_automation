import os
import json
from datetime import datetime
import time
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


def test_elimina_messaggio(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia un messaggio a se stessi per avere un messaggio da eliminare
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Da eliminare",
        corpo="Questo messaggio verrà eliminato nel test",
    )
    page.locator('span[title="Invia"]').click()

    # Aspetta consegna
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(1)

    # Apri il messaggio
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Clicca Elimina
    page.locator('aru-symbol[title="Elimina"]').first.click()
    time.sleep(2)

    # Verifica: apri il cestino e verifica che il messaggio sia presente
    page.locator('button[title="Cestino"]').click()
    time.sleep(1)
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    # Verifica che ci sia almeno un messaggio nel cestino
    count = page.locator('div.frame-record-desktop').count()
    assert count > 0, "Il messaggio eliminato non è stato trovato nel cestino"

    time.sleep(1)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_14___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
