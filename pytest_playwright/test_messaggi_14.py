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


def test_elimina_messaggio(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    # Invia un messaggio a se stessi per avere un messaggio da eliminare
    Helper.crea_messaggio(
        page,
        config,
        oggetto=f"Test elimina playwright {ts}",
        corpo="Questo messaggio verrà eliminato nel test",
    )
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: aspetta consegna e apri il messaggio specifico per oggetto (fino a 80s)
    oggetto_msg = f"Test elimina playwright {ts}"
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto_msg)
    for _ in range(20):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"], button[aria-label="Aggiorna"], button[aria-label="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    assert msg.count() > 0, f"Messaggio '{oggetto_msg}' non trovato in inbox entro 80s"
    msg.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Clicca Elimina
    page.locator('aru-symbol[title="Elimina"], aru-symbol[title="Supprimer"]').first.click()
    page.wait_for_timeout(2000)

    # Verifica: il messaggio eliminato è nel Cestino (cerca per oggetto specifico)
    page.locator('button[title="Cestino"], button[title="Corbeille"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)
    msg_cestino = page.locator('div.frame-record-desktop').filter(has_text=oggetto_msg)
    testo_primo = msg_cestino.first.inner_text() if msg_cestino.count() > 0 else ""

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_14___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert str(ts) in testo_primo, f"Messaggio eliminato (ts={ts}) non trovato nel Cestino. Trovato: {testo_primo!r}"
