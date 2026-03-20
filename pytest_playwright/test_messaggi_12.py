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


def test_invio_messaggio_semplice(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Invio semplice",
        corpo="Corpo del messaggio semplice senza allegati",
    )

    # Invia
    page.locator('span[title="Invia"]').click()

    # Aspetta toast di conferma
    toast = page.locator("div.aru-toast__message").first
    toast.wait_for(state="visible", timeout=8000)
    expect(toast).to_be_visible()
    assert "Il messaggio è stato inviato" in toast.text_content()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_12___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
