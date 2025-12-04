import os
import json
from datetime import datetime
from playwright.sync_api import Playwright, sync_playwright, expect
from base_pec import LoginPec, Helper
import time


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


def test_esporta_contatti(page):
    # Login PEC
    LoginPec(page).login_pec()

    time.sleep(2)
    # Apertura rubrica
    page.locator("#contacts").click()
    page.wait_for_timeout(1000)

    time.sleep(2)
    # Attendi il download
    with page.expect_download() as download_info:
        page.get_by_role("button", name="Esporta").click()
        page.get_by_role("combobox", name="Esporta rubrica in vCard").click()
        page.get_by_role("button", name="Esporta rubrica in CSV").click()
        page.get_by_role("button", name="Esporta rubrica").click()
        time.sleep(2)

    download = download_info.value

    # Percorso del file scaricato
    download_path = os.path.join(
        REPORT_FOLDER,
        f"rubrica_{datetime.now():%Y-%m-%d_%H-%M-%S}.csv"
    )

    download.save_as(download_path)

    # Verifica effettiva del file
    assert os.path.exists(download_path), "Il file CSV NON è stato scaricato!"

    time.sleep(2)
    # Screenshot (per debug)
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"File scaricato in: {download_path}")
    print(f"Screenshot salvato in: {screenshot_path}")
