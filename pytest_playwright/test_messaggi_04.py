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

def test_messaggio_importato(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Clicca su importa messaggi
    page.locator('button[title="Importa"]').click()
    
    # Intercetta il file chooser al click del bottone "Seleziona da dispositivo"
    with page.expect_file_chooser() as fc_info:
        page.locator('button[title="Seleziona da dispositivo"]').click()

    file_chooser = fc_info.value

    # Imposta il file da caricare
    file_chooser.set_files(importa_messaggi)

    # Attendi caricamento allegato
    page.wait_for_timeout(2000)
            
    # Piccola attesa per sicurezza
    time.sleep(1)
    
    # Clicca il bottone "Importa"
    page.locator('button[title="Importa"]').nth(1).click()
    
    
    time.sleep(1)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "1 nuovo messaggio da leggere" in toast.text_content()
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    

    
    