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

# --- Percorso importa messaggi ---
importa_messaggi = os.environ.get("IMPORTA_MESSAGGI", config.get("importa_messaggi"))

def test_messaggio_alta_priorita(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Messaggio alta priorità",  # oggetto del messaggio
        corpo="Test automatico invio messaggio PEC con Playwright",  # corpo del messaggio
        # destinatario_key non serve se usi il principale
)
    
    # Clicca pulsante altro
    page.locator('aru-button:has(aru-symbol[symbol="more"])').click()

    # Clicca alta priorità
    page.locator('aru-button#high-priority').click()
    
    time.sleep(1)
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()
    
     # Aspetta 8 secondi
    page.wait_for_timeout(8000)
    
    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()

    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    
    

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').nth(0).click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)
    
    # Seleziona il div contenitore
    header_info_div = page.locator('div.message-header-title-info.d-flex.flex-wrap.gap-2')

    # Verifica che contenga il simbolo "important"
    important_symbol = header_info_div.locator('aru-symbol[symbol="important"]')

    # Assert che sia presente e visibile
    expect(important_symbol).to_be_visible()      
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")