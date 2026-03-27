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


def test_risposta_messaggio(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test risposta playwright {ts}"

    # Invia un messaggio a se stessi per avere qualcosa a cui rispondere
    Helper.crea_messaggio(page, config, oggetto=oggetto, corpo="Corpo del messaggio originale")
    page.locator('span[title="Invia"]').click()

    # Polling: cerca il messaggio originale per oggetto (fino a 80s)
    msg_orig = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(20):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"]').click()
        page.wait_for_timeout(1000)
        if msg_orig.count() > 0:
            break
    assert msg_orig.count() > 0, f"Messaggio originale '{oggetto}' non trovato in inbox entro 80s"
    msg_orig.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Rispondi
    page.locator('aru-symbol[title="Rispondi"]').first.click()
    page.locator("div[contenteditable='true']").first.wait_for(state="visible", timeout=5000)
    page.locator("div[contenteditable='true']").first.fill("Risposta automatica tramite Playwright")
    page.locator('span[title="Invia"]').click()

    # Polling: cerca la risposta Re: per oggetto specifico (fino a 120s)
    oggetto_reply = f"Re: {oggetto}"
    msg_reply = page.locator('div.frame-record-desktop').filter(has_text=oggetto_reply)
    for _ in range(30):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"]').click()
        page.wait_for_timeout(1000)
        if msg_reply.count() > 0:
            break
    assert msg_reply.count() > 0, f"Risposta '{oggetto_reply}' non trovata in inbox entro 120s"
    msg_reply.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Verifica prefisso "Re:" nell'oggetto
    soggetto = page.locator("div.message-header-title-subject").inner_text().strip()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_11___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert "Re:" in soggetto, f"Oggetto inatteso: {soggetto}"
