import os
import json
from datetime import datetime
from playwright.sync_api import sync_playwright, expect
from base_pec import LoginPec, Helper


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


def test_esporta_contatti(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Apertura rubrica
    page.locator("#contacts").click()
    page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=10000)

    # Apri dialog esporta con click trusted
    try:
        page.get_by_role("button", name="Esporta").click()
    except Exception:
        page.get_by_role("button", name="Exporter").click()

    # Aspetta che il dialog "Esporta rubrica" sia aperto
    page.locator('.cdk-overlay-pane').last.wait_for(state="visible", timeout=8000)
    page.wait_for_timeout(500)

    # Click diretto su "Esporta rubrica" per avviare il download (no combobox format, non esiste)
    with page.expect_download() as download_info:
        page.locator('.cdk-overlay-pane').last.locator(
            'button:has-text("Esporta rubrica"), '
            'button:has-text("Exporter le carnet"), '
            'button:has-text("Exporter")'
        ).first.click(force=True)

    download = download_info.value

    # Percorso del file scaricato
    download_path = os.path.join(
        REPORT_FOLDER,
        f"rubrica_{datetime.now():%Y-%m-%d_%H-%M-%S}.csv"
    )

    download.save_as(download_path)

    # Screenshot (per debug)
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"File scaricato in: {download_path}")
    print(f"Screenshot salvato in: {screenshot_path}")
    # Verifica effettiva del file
    assert os.path.exists(download_path), "Il file CSV NON è stato scaricato!"
