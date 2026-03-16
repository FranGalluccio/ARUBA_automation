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


def test_ricevuta_accettazione(page):
    """Verifica che dopo l'invio di un messaggio PEC arrivi la Ricevuta di Accettazione (RA)."""
    LoginPec(page).login_pec(config)

    # Invia messaggio a se stesso con oggetto univoco
    ts = int(time.time())
    oggetto = f"Test RA {ts}"
    Helper.crea_messaggio(
        page, config,
        oggetto=oggetto,
        corpo="Test automatico ricevuta di accettazione PEC",
    )
    page.locator('span[title="Invia"]').click()

    # Vai alla inbox e aggiorna (la RA arriva entro pochi secondi)
    page.wait_for_timeout(5000)
    page.locator("#messages").get_by_label("Messaggi").first.click()
    page.wait_for_timeout(15000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(3000)

    # Cerca la RA nell'inbox: contiene "accettazione" nel testo del messaggio
    frames = page.locator('div.frame-record-desktop').all()
    found_ra = False
    for frame in frames:
        try:
            text = frame.inner_text().lower()
            if "accettazione" in text:
                found_ra = True
                break
        except Exception:
            pass

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_23___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    assert found_ra, (
        f"Ricevuta di Accettazione (RA) non trovata dopo invio messaggio '{oggetto}'. "
        "Il sistema PEC potrebbe non star generando le ricevute correttamente."
    )
    print(f"Screenshot salvato in: {screenshot_path}")
