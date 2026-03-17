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


def test_ricevuta_consegna(page):
    """Verifica che dopo l'invio di un messaggio PEC arrivi la Ricevuta di Consegna (RD)."""
    LoginPec(page).login_pec(config)

    # Invia messaggio a se stesso con oggetto univoco
    ts = int(time.time())
    oggetto = f"Test RD {ts}"
    Helper.crea_messaggio(
        page, config,
        oggetto=oggetto,
        corpo="Test automatico ricevuta di consegna PEC",
    )
    page.locator('span[title="Invia"]').click()

    # Vai alla inbox e aggiorna (la RD richiede più tempo della RA)
    page.wait_for_timeout(5000)
    page.locator("#messages").get_by_label("Messaggi").first.click()
    page.wait_for_timeout(50000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(5000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(3000)

    # Mostra le ricevute se il banner è presente (in alcuni ambienti sono nascoste per default)
    try:
        mostra_btn = page.locator('button:has-text("Mostra ricevute")').first
        if mostra_btn.is_visible():
            mostra_btn.click()
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # Cerca la RC tramite l'icona aru-symbol con title="Ricevuta di consegna"
    # e filtra per il soggetto univoco del messaggio inviato
    found_rd = page.locator(
        'div.frame-record-desktop:has(aru-symbol[title="Ricevuta di consegna"])'
    ).filter(has_text=oggetto).count() > 0

    # Nascondi nuovamente le ricevute per non interferire con i test successivi
    try:
        nascondi_btn = page.locator('button:has-text("Nascondi ricevute")').first
        if nascondi_btn.is_visible():
            nascondi_btn.click()
            page.wait_for_timeout(1000)
    except Exception:
        pass

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_24___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    assert found_rd, (
        f"Ricevuta di Consegna (RD) non trovata dopo invio messaggio '{oggetto}'. "
        "Il sistema PEC potrebbe non star generando le ricevute di consegna correttamente."
    )
    print(f"Screenshot salvato in: {screenshot_path}")
