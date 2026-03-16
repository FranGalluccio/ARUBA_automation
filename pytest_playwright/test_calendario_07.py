import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_naviga_periodi_calendario(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.get_by_role("button", name="Calendario").click()
    time.sleep(1)

    # Leggi il testo dell'header corrente (mini-calendar sidebar: "Marzo 2026")
    header = page.locator('div.vanilla-calendar-header__content, [class*="calendar-header"]').first
    header.wait_for(state="visible", timeout=5000)
    header_iniziale = header.inner_text().strip()
    print(f"Header iniziale: '{header_iniziale}'")

    # Naviga al mese/periodo successivo
    page.locator('button[title="Next"]').click()
    time.sleep(1)
    header_successivo = header.inner_text().strip()
    print(f"Header dopo Next: '{header_successivo}'")
    assert header_iniziale != header_successivo, \
        f"L'header non è cambiato dopo click su Next: '{header_iniziale}' vs '{header_successivo}'"

    # Naviga indietro
    page.locator('button[title="Prev"]').click()
    time.sleep(1)
    header_tornato = header.inner_text().strip()
    print(f"Header dopo Prev: '{header_tornato}'")
    assert header_tornato == header_iniziale, \
        f"L'header non è tornato a quello iniziale: '{header_tornato}' != '{header_iniziale}'"

    # Vai alla settimana corrente con "Oggi" (può essere disabilitato se già su oggi)
    try:
        page.locator('button[title="Oggi"]').click(force=True)
        time.sleep(1)
    except:
        pass

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
