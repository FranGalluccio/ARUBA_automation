import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper, elimina_evento_pec
from playwright.sync_api import sync_playwright, expect
import locale

# Forza locale italiana (necessaria per mesi in italiano)
locale.setlocale(locale.LC_TIME, "it_IT")

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_creazione_evento_ricorrente(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"nuovo evento ricorrente playwright {ts}"

    # Crea nuovo evento ricorrente
    page.get_by_role("button", name="Calendario").click()
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
    page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
    page.get_by_role("combobox", name="Non ripetere").click()
    page.get_by_role("button", name="Personalizza...").click()
    page.get_by_role("radio", name="Dopo").check()
    page.wait_for_timeout(500)
    page.get_by_role("dialog") \
    .filter(has_text="Personalizza") \
    .filter(has=page.locator("button", has_text="Salva")) \
    .last \
    .get_by_role("button", name="Salva") \
    .click()

    page.wait_for_timeout(500)
    page.get_by_role("button", name="Salva").click()

    try:
        page.wait_for_timeout(1000)
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
    finally:
        elimina_evento_pec(page, "nuovo evento ricorrente playwright")
