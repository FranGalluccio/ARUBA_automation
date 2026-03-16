import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
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

# --- Percorso allegato ---
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


def test_scarica_allegato_ricevuto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia messaggio con allegato a se stessi
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Scarica allegato",
        corpo="Messaggio con allegato da scaricare",
        path_allegato=file_allegato,
    )
    page.locator('span[title="Invia"]').click()

    # Aspetta consegna
    page.wait_for_timeout(8000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)

    # Apri messaggio
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.wait_for_load_state("domcontentloaded")
    assert "external-message" in new_page.url

    # Clicca sull'allegato
    nome_file = os.path.basename(file_allegato)
    new_page.locator(f'button[title="{nome_file}"]').click()
    time.sleep(1)

    # Scarica l'allegato
    with new_page.expect_download() as download_info:
        new_page.locator('text="Scarica"').first.click()

    download = download_info.value
    download_path = os.path.join(REPORT_FOLDER, f"allegato_scaricato_{datetime.now():%Y-%m-%d_%H-%M-%S}_{nome_file}")
    download.save_as(download_path)

    # Verifica che il file sia stato scaricato
    assert os.path.exists(download_path), f"Il file non è stato scaricato: {download_path}"
    assert os.path.getsize(download_path) > 0, "Il file scaricato è vuoto"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_20___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)
    print(f"File scaricato in: {download_path}")
    print(f"Screenshot salvato in: {screenshot_path}")
