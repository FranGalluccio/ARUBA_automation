import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


def test_messaggio_con_allegato(page):
    # Login PEC
    LoginPec(page).login_pec()

    # Creare messaggio con allegato
    Helper.crea_messaggio(
        page,
        "francescoconservazione@pec.it",
        "Test automatico con Playwright - Invio allegati",
        "Test automatico invio messaggio PEC con Playwright",
        file_allegato
    )
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()

     # Aspetta 8 secondi
    page.wait_for_timeout(8000)
    
    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()
    
    time.sleep(2)

    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Verifica pagina esterna
    assert "external-message" in new_page.url

    # Clicca sull’allegato usando il nome dinamico
    new_page.locator(f'button[title="{os.path.basename(file_allegato)}"]').click()
    
    # Mostra anteprima
    new_page.locator('text="Mostra anteprima"').first.click()
    
    # Aspetta 5 secondi prima dello screenshot
    time.sleep(5)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
