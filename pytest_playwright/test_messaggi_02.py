import os
import json
from datetime import datetime

from base_pec import LoginPec, Helper

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

def test_messaggio_inoltrato(page):
    # Login PEC
    LoginPec(page).login_pec(config)

 # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()
    
    # Clicca su inoltra
    page.locator('aru-symbol[title="Inoltra"]').first.click()
    
 # Prendi il destinatario dal config (usa la chiave principale)
    destinatario = config["destinatari"]["destinatario_principale"]

    # Fallback stabile: seleziona SOLO il campo destinatario
    destinatario_input = page.locator("input[placeholder='Destinatari']")
    try:
        destinatario_input.fill(destinatario)
    except Exception:
        page.locator('input[aria-label="input field"]').click()
        destinatario_input.fill(destinatario)

    # Compila oggetto e corpo
    page.locator('input[aria-label="input field"]').fill("Test automatico con Playwright - Inoltro messaggio")
    page.locator("div[contenteditable='true']").fill("Corpo del messaggio inoltrato")
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()
    
     # Aspetta 8 secondi
    page.wait_for_timeout(8000)
    
    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()

    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)
    
    # Prende il testo dell'oggetto dal messaggio aperto
    oggetto = page.locator("div.message-header-title-subject").inner_text().strip()

    # Confronto
    assert "Test automatico" in oggetto, f"Oggetto inatteso: {oggetto}"
    
    page.wait_for_timeout(2000)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    
    
    