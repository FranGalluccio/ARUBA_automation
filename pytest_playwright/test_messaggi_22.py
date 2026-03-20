import os
import json
from datetime import datetime
import time
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


def test_verifica_cartella_inviati(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    oggetto_inviato = f"Test automatico con Playwright - Verifica inviati {int(time.time())}"

    # Invia un messaggio
    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto_inviato,
        corpo="Corpo del messaggio per verifica cartella inviati",
    )
    page.locator('span[title="Invia"]').click()

    # Aspetta toast conferma
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "Il messaggio è stato inviato" in toast.text_content()

    # Apri cartella Inviati
    page.locator('button[title="Inviati"]').click()

    # Verifica che ci siano messaggi nella cartella Inviati
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)
    assert page.locator('div.frame-record-desktop').count() > 0, "Nessun messaggio trovato nella cartella Inviati"

    # Apri il primo messaggio e verifica che l'oggetto corrisponda
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)
    oggetto_visibile = page.locator("div.message-header-title-subject").inner_text().strip()
    assert oggetto_inviato in oggetto_visibile, f"Oggetto inatteso: {oggetto_visibile}"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_22___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
