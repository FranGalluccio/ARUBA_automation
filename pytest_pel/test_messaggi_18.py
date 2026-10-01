import os
import json
from datetime import datetime

from base_pel import LoginPel, HelperPel
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_filtri_inbox(page):
    # Login PEL
    LoginPel(page).login_pel(config)

    # Aspetta che i messaggi siano visibili
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    # Su PEL il filtro inbox è una fila di tab aru-chip ("Tutti", "Letti", "Da leggere"),
    # non un componente dropdown aru-input-select come su PEC. Nota: un selettore
    # generico su "Letti" matcherebbe anche il bottone toolbar "Segna tutti come
    # già letti" (stessa sottostringa) — serve scoping sulla classe aru-chip.
    filtro_letti = page.locator('.aru-chip:has-text("Letti"), [class*="chip"]:has-text("Letti")').first
    assert filtro_letti.is_visible(), "Il filtro 'Letti' non è visibile nella lista messaggi"

    filtro_letti.click(force=True)
    page.wait_for_timeout(1500)

    # Screenshot dopo il filtro applicato
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_18___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Verifica che il filtro sia stato applicato: l'URL riflette il quick-filter attivo
    assert "mail_quickFilter" in page.url, (
        f"Il filtro 'Letti' non risulta applicato (URL: {page.url})"
    )
