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

# --- Percorso importa messaggi ---
importa_messaggi = os.environ.get("IMPORTA_MESSAGGI", config.get("importa_messaggi"))

def test_segna_come_letto_da_leggere(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Segna come letto e da leggere",  # oggetto del messaggio
        corpo="Test automatico invio messaggio PEC con Playwright",  # corpo del messaggio
        # destinatario_key non serve se usi il principale
)
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()

     # Aspetta 8 secondi
    page.wait_for_timeout(8000)
    
    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()
    
    time.sleep(2)
    
    try:
     # Segna come da leggere
        page.locator('button:has(aru-symbol[title="Segna tutti come già letti"])').nth(0).click()
    except:
        page.locator('button:has(aru-symbol[title="Segna come già letti"])').nth(0).click()

    time.sleep(2)
    
    # Segna come da leggere
    try:
        page.locator('button:has(aru-symbol[title="Segna tutti come da leggere"])').nth(0).click()
    except:
        page.locator('button:has(aru-symbol[title="Segna come da leggere"])').nth(0).click()
    
    # Assert per verificare che il pulsante "Segna tutti come da leggere" sia visibile e cliccabile
    button = page.locator('button:has(aru-symbol[title="Segna tutti come da leggere"])').nth(0)
    assert button.is_visible(), "Il pulsante 'Segna tutti come da leggere' non è visibile"
    assert button.is_enabled(), "Il pulsante 'Segna tutti come da leggere' non è cliccabile"
    
    time.sleep(2)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    
    

