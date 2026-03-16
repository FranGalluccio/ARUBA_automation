import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper
import time

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso rubrica da importare ---
file_rubrica = os.environ.get("RUBRICA_IMPORT", config.get("rubrica_import"))


def test_importa_contatti(page):
    """Importa la rubrica CSV nella PEC"""
    # Login PEC
    LoginPec(page).login_pec(config)

    # Apri la rubrica
    page.locator("#contacts").click()
    page.wait_for_timeout(1000)

    # Clicca sul bottone "Importa" per aprire il dialog di import
    page.locator('span[aria-label="Importa"]').click()
    page.wait_for_timeout(1000)

    # Carica il file CSV da importare
    file_input = page.locator('input[type="file"]')
    file_input.set_input_files(file_rubrica)
    page.wait_for_timeout(1000)

    # Dopo il caricamento del file, clicca sul pulsante Importa per confermare
    page.get_by_role("button", name="Importa", exact=True).click()
    page.wait_for_timeout(2000)
    
    time.sleep(1)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    assert toast.is_visible()
    assert "I contatti sono stati importati." in toast.text_content()

    # Screenshot finale per debug
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot import rubrica salvato in: {screenshot_path}")
