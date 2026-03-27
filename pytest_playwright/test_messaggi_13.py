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


def test_risposta_a_tutti(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test risposta tutti playwright {ts}"

    # Invia messaggio a se stessi come base per il reply all
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

    # Rispondi a tutti
    page.locator('aru-symbol[title="Rispondi a tutti"]').first.click()
    page.locator("div[contenteditable='true']").first.wait_for(state="visible", timeout=5000)
    page.locator("div[contenteditable='true']").first.fill("Risposta a tutti automatica tramite Playwright")
    page.locator('span[title="Invia"]').click()

    # Verifica in Inviati che la risposta sia stata inviata con prefisso "Re:"
    # (Inviati si aggiorna immediatamente dopo l'invio, senza attendere la consegna)
    oggetto_reply = f"Re: {oggetto}"
    page.wait_for_timeout(2000)
    # Naviga a Inviati
    try:
        page.locator('button[title="Inviati"]').first.click(timeout=5000)
    except Exception:
        page.get_by_label("Inviati").first.click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=10000)

    msg_reply = page.locator('div.frame-record-desktop').filter(has_text=oggetto_reply)
    for _ in range(10):
        if msg_reply.count() > 0:
            break
        page.locator('aru-symbol[title="Aggiorna"]').click()
        page.wait_for_timeout(2000)
    assert msg_reply.count() > 0, f"'{oggetto_reply}' non trovata in Inviati dopo l'invio"
    msg_reply.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Verifica prefisso "Re:" nell'oggetto
    soggetto = page.locator("div.message-header-title-subject").inner_text().strip()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_13___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert "Re:" in soggetto, f"Oggetto inatteso (manca 'Re:'): {soggetto}"
