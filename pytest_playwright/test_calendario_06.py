import os
import json
from datetime import datetime
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


def test_cambio_vista_calendario(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    page.locator('[aria-label="Calendario"], [aria-label="Calendrier"], button[title="Calendario"], button[title="Calendrier"]').first.click()
    page.locator('button[title="Giorno"]').wait_for(state="visible", timeout=8000)

    # Screenshot finale (calendario visibile con tutti i bottoni vista)
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Vista Giorno
    page.locator('button[title="Giorno"]').click()
    page.wait_for_timeout(500)
    assert page.locator('button[title="Giorno"]').is_visible(), "Bottone 'Giorno' non visibile"
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_06_giorno_{datetime.now():%H-%M-%S}.png"))

    # Vista Mese
    page.locator('button[title="Mese"]').click()
    page.wait_for_timeout(500)
    assert page.locator('button[title="Mese"]').is_visible(), "Bottone 'Mese' non visibile"
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_06_mese_{datetime.now():%H-%M-%S}.png"))

    # Vista Lista eventi
    page.locator('button[title="Eventi"]').click()
    page.wait_for_timeout(500)
    assert page.locator('button[title="Eventi"]').is_visible(), "Bottone 'Eventi' non visibile"
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_06_eventi_{datetime.now():%H-%M-%S}.png"))

    # Torna alla vista Settimana (default)
    page.locator('button[title="Settimana"]').click()
    page.wait_for_timeout(500)
