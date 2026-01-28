import os
import json
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec


# --- Leggi config.json ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", BASE_DIR)
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso file allegato (.ics) ---
FILE_ICS = os.path.join(TEST_FOLDER, "Personale.ics")


def test_import_export_calendario(page):
    # --- Login PEC ---
    LoginPec(page).login_pec(config)
    page.wait_for_load_state("networkidle")

    # --- Vai al calendario ---
    page.get_by_role("button", name="Calendario").click()
    page.wait_for_timeout(500)

    # --- Crea nuovo evento ---
    page.get_by_role("button", name="Nuovo evento").click()
    page.get_by_placeholder("Inserisci un titolo").fill("import export calendario")
    page.get_by_role("button", name="Salva").click()
    page.wait_for_timeout(500)

# --- Esporta evento ---
    page.get_by_role("button", name="Esporta").click()

    with page.expect_download() as download_info:
        page.get_by_role("button", name="Esporta").click()

    download = download_info.value
    download.save_as(FILE_ICS)


    # --- Importa evento ---
    page.get_by_role("button", name="Importa").click()
    page.get_by_role("button", name="Importa file").click()

    # INPUT FILE NASCOSTO
    page.locator("#hidden_input").set_input_files(FILE_ICS)

    page.get_by_role("button", name="Importa", exact=True).click()
    page.wait_for_timeout(1000)

    # --- Verifica presenza primo evento e cleanup ---
    page.get_by_role("row", name="import export calendario").locator("a").nth(1).click()
    page.get_by_role("button", name="Annulla evento").click()
    page.get_by_role("button", name="Elimina").click()
    
    time.sleep(5)
    # --- Verifica presenza evento e cleanup ---
    page.get_by_role("row", name="import export calendario").first.locator("a").click()
    page.get_by_role("button", name="Annulla evento").click()
    page.get_by_role("button", name="Elimina").click()