import os
import json
import time
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


def test_invio_messaggio_con_cc(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test CC playwright {ts}"
    destinatario = config["destinatari"]["destinatario_principale"]

    # Apri nuovo messaggio
    page.locator("button:has-text('Nuovo messaggio'), button:has-text('Nouveau message')").click()

    # Compila destinatario principale
    to_input = page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").first
    to_input.wait_for(state="visible", timeout=5000)
    to_input.fill(destinatario)
    to_input.press("Enter")

    # Aggiungi CC
    page.locator('button[title="CC"], button[title="Cc"]').first.click()
    page.wait_for_timeout(1000)
    cc_destinatario = config["destinatari"].get("destinatario_secondario", destinatario)
    cc_inputs = page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").all()
    cc_input = cc_inputs[-1] if len(cc_inputs) >= 2 else page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").first
    cc_input.fill(cc_destinatario)

    # Compila oggetto e corpo
    page.locator('input[aria-label="input field"]').fill(oggetto)
    page.locator("div[contenteditable='true']").fill("Corpo del messaggio con CC")

    # Invia
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Aspetta toast di conferma invio (timeout più lungo per SMB)
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible(timeout=15000)
    toast_text = toast.text_content()

    # Aspetta ricezione, aggiorna e apri il primo messaggio
    page.wait_for_timeout(10000)
    page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
    page.wait_for_timeout(2000)
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
    # Il testo del toast varia per ambiente (IT/FR)
    assert any(kw in toast_text.lower() for kw in [
        "inviato", "envoyé", "sent", "succès", "success"
    ]), f"Toast invio inatteso: '{toast_text}'"
