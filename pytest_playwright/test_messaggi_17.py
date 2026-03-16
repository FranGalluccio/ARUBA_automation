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


def test_ricerca_messaggi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia un messaggio con oggetto univoco da cercare
    oggetto_univoco = f"Test ricerca playwright {int(time.time())}"
    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto_univoco,
        corpo="Corpo del messaggio per test ricerca",
    )
    page.locator('span[title="Invia"]').click()

    # Aspetta consegna
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)

    # Usa la barra di ricerca (input con classe aru-input-search__chosen__input-editable)
    search_input = page.locator('input.aru-input-search__chosen__input-editable, input[placeholder*="Cerca messaggio"]').first
    search_input.wait_for(state="visible", timeout=5000)
    search_input.click()
    time.sleep(0.5)
    search_input.fill(oggetto_univoco)
    time.sleep(0.5)
    page.keyboard.press("Enter")
    time.sleep(3)

    # Verifica che almeno un risultato sia presente
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)
    count = page.locator('div.frame-record-desktop').count()
    assert count > 0, f"Nessun risultato trovato per la ricerca: {oggetto_univoco}"

    time.sleep(1)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_17___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
