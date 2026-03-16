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


def test_invio_messaggio_con_cc(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    destinatario = config["destinatari"]["destinatario_principale"]

    # Apri nuovo messaggio
    page.locator("button:has-text('Nuovo messaggio')").click()
    time.sleep(1)

    # Compila destinatario principale
    to_input = page.locator("input[placeholder='Destinatari']").first
    to_input.wait_for(state="visible", timeout=5000)
    to_input.fill(destinatario)
    # Press Enter/Tab per confermare il destinatario come chip
    to_input.press("Enter")
    time.sleep(0.5)

    # Aggiungi CC (dopo click sul bottone CC, appare un nuovo input Destinatari)
    page.locator('button[title="CC"]').click()
    time.sleep(1)
    cc_destinatario = config["destinatari"].get("destinatario_secondario", destinatario)
    # Ora ci sono 2 input Destinatari, il secondo è il CC
    cc_inputs = page.locator("input[placeholder='Destinatari']").all()
    if len(cc_inputs) >= 2:
        cc_input = cc_inputs[-1]  # prendi l'ultimo (il CC appena aggiunto)
    else:
        cc_input = page.locator("input[placeholder='Destinatari']").first
    cc_input.fill(cc_destinatario)

    # Compila oggetto e corpo
    page.locator('input[aria-label="input field"]').fill("Test automatico con Playwright - Messaggio con CC")
    page.locator("div[contenteditable='true']").fill("Corpo del messaggio con CC")

    # Invia
    page.locator('span[title="Invia"]').click()

    # Aspetta toast di conferma
    time.sleep(2)
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "Il messaggio è stato inviato" in toast.text_content()

    # Aspetta consegna e verifica il messaggio ricevuto mostra CC
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(1)

    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_19___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
