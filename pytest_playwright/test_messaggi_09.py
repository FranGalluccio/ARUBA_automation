import os
import json
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
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    try:
     # Segna come già letti
        page.locator('button:has(aru-symbol[title="Segna tutti come già letti"])').nth(0).click()
    except Exception:
        page.locator('button:has(aru-symbol[title="Segna tutti come già letti"])').nth(0).click()

    # Segna come da leggere
    page.wait_for_timeout(1000)
    try:
        page.locator('button:has(aru-symbol[title="Segna tutti come da leggere"])').nth(0).click()
    except Exception:
        page.locator('button:has(aru-symbol[title="Segna tutti come da leggere"])').nth(0).click()

    # Verifica che l'azione "Segna tutti come da leggere" abbia avuto effetto:
    # ci devono essere messaggi non letti (badge/indicatore unread) nella inbox
    page.wait_for_timeout(1000)
    unread_count = page.locator(
        '[class*="unread"], [class*="not-read"], aru-badge, '
        'div.frame-record-desktop[class*="unread"], '
        'div.frame-record-desktop-row-content[class*="unread"]'
    ).count()
    assert unread_count > 0, (
        "Dopo 'Segna tutti come da leggere' non sono stati trovati messaggi non letti nella inbox"
    )

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    
    

