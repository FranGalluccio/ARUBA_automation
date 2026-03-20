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


def test_risposta_messaggio(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia un messaggio a se stessi per avere qualcosa a cui rispondere
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Messaggio originale per reply",
        corpo="Corpo del messaggio originale",
    )

    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()

    # Aspetta 8 secondi per la consegna
    page.wait_for_timeout(8000)

    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()

    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Cerca il messaggio inviato per soggetto (non il primo in assoluto)
    oggetto_originale = "Test automatico con Playwright - Messaggio originale per reply"
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto_originale).first
    if msg.count() == 0:
        msg = page.locator('div.frame-record-desktop').first
    msg.click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Clicca su Rispondi
    page.locator('aru-symbol[title="Rispondi"]').first.click()

    # Aspetta che il campo corpo sia pronto (la finestra di risposta si apre)
    page.locator("div[contenteditable='true']").first.wait_for(state="visible", timeout=5000)

    # Scrivi il testo di risposta
    page.locator("div[contenteditable='true']").first.fill("Risposta automatica tramite Playwright")

    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()

    # Aspetta 8 secondi per la consegna della risposta
    page.wait_for_timeout(8000)

    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()

    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Cerca il messaggio di risposta per prefisso "Re:"
    reply_msg = page.locator('div.frame-record-desktop').filter(has_text="Re:").first
    if reply_msg.count() == 0:
        reply_msg = page.locator('div.frame-record-desktop').first
    reply_msg.click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Verifica che l'oggetto contenga il prefisso "Re:"
    oggetto = page.locator("div.message-header-title-subject").inner_text().strip()
    assert "Re:" in oggetto, f"Oggetto inatteso: {oggetto}"

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_11___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
