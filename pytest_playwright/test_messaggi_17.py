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
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Aspetta consegna (CI può essere più lento)
    page.wait_for_timeout(15000)
    page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"], button[aria-label="Aggiorna"], button[aria-label="Actualiser"]').click()
    page.wait_for_timeout(2000)

    # Usa la barra di ricerca (input con classe aru-input-search__chosen__input-editable)
    search_input = page.locator('input.aru-input-search__chosen__input-editable, input[placeholder*="Cerca messaggio"]').first
    search_input.wait_for(state="visible", timeout=5000)
    search_input.click()
    page.wait_for_timeout(300)
    search_input.fill(oggetto_univoco)
    page.wait_for_timeout(300)
    page.keyboard.press("Enter")

    # Verifica che almeno un risultato sia presente (retry se latenza server)
    try:
        page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=15000)
    except Exception:
        # Riprova la ricerca una volta
        page.wait_for_timeout(10000)
        search_input2 = page.locator('input.aru-input-search__chosen__input-editable, input[placeholder*="Cerca messaggio"]').first
        if search_input2.is_visible():
            search_input2.click()
            search_input2.fill(oggetto_univoco)
            page.keyboard.press("Enter")
        page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=15000)
    count = page.locator('div.frame-record-desktop').count()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_17___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert count > 0, f"Nessun risultato trovato per la ricerca: {oggetto_univoco}"
