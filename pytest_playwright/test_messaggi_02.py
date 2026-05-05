import os
import json
import time
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

    # Oggetto univoco per identificare il messaggio inoltrato
    ts = int(time.time())
    oggetto_inoltro = f"Test inoltro playwright {ts}"

    # Aspetta che almeno un record sia visibile e apri il primo
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()

    # Clicca su Inoltra
    page.locator('aru-symbol[title="Inoltra"]').first.click()

    # Compila destinatario
    destinatario = config["destinatari"]["destinatario_principale"]
    destinatario_input = page.locator("input[placeholder='Destinatari']")
    try:
        destinatario_input.fill(destinatario)
    except Exception:
        page.locator('input[aria-label="input field"]').click()
        destinatario_input.fill(destinatario)

    # Oggetto univoco
    page.locator('input[aria-label="input field"]').fill(oggetto_inoltro)
    page.locator("div[contenteditable='true']").fill("Corpo del messaggio inoltrato")

    # Invia
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: cerca il messaggio inoltrato per oggetto (non aprire il primo in assoluto)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto_inoltro)
    for _ in range(30):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    assert msg.count() > 0, f"Messaggio inoltrato '{oggetto_inoltro}' non trovato in inbox entro 120s"
    msg.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Verifica oggetto
    oggetto = page.locator("div.message-header-title-subject").inner_text().strip()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert oggetto_inoltro in oggetto, f"Oggetto inatteso: {oggetto}"
