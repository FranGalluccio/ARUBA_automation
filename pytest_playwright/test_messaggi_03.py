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

def test_messaggio_in_bozza(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Messaggio in bozza",
        corpo="Test automatico invio messaggio PEC con Playwright",
        destinatario_key="destinatario_principale"  # opzionale, default già principale
)
    
    # Clicca e salva bozza
    page.locator("#new-message\\.save-menu").wait_for(state="visible", timeout=5000)
    page.locator("#new-message\\.save-menu").click()
    page.locator("#save-draft").click()
    
    # Chiudi finestra messaggio
    page.locator('#message-dialog aru-symbol[symbol="close"]').click(force=True)
    
    # Gestisci popup di conferma chiusura senza salvataggio
    page.locator('button[title="Si"]').click()

    # Apri bozze
    page.locator('button[title="Bozze"]').click()
    
    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').wait_for(state="visible", timeout=10000)
    page.locator('span[title="Invia"]').click()

    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").filter(has_text="Il messaggio è stato inviato").first
    expect(toast).to_be_visible()
    assert "Il messaggio è stato inviato" in toast.text_content()
    
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    
    
    
    
