import os
import json
import time
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

# --- Percorso allegato ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_scarica_allegato_ricevuto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test scarica allegato playwright {ts}"

    # Invia messaggio con allegato a se stessi
    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Messaggio con allegato da scaricare",
        path_allegato=file_allegato,
    )
    page.locator('span[title="Invia"]').click()

    # Polling: cerca il messaggio specifico per oggetto (non il primo in assoluto)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(20):
        page.wait_for_timeout(3000)
        page.locator('aru-symbol[title="Aggiorna"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    msg.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.wait_for_load_state("domcontentloaded")
    new_page.wait_for_load_state("load")
    assert "external-message" in new_page.url

    # Clicca sull'allegato
    nome_file = os.path.basename(file_allegato)
    attachment_btn = new_page.locator(f'button[title="{nome_file}"]')
    attachment_btn.wait_for(state="visible", timeout=15000)
    attachment_btn.click()

    # Scarica l'allegato
    with new_page.expect_download() as download_info:
        new_page.locator('text="Scarica"').first.click()

    download = download_info.value
    download_path = os.path.join(REPORT_FOLDER, f"allegato_scaricato_{datetime.now():%Y-%m-%d_%H-%M-%S}_{nome_file}")
    download.save_as(download_path)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_20___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)
    print(f"File scaricato in: {download_path}")
    print(f"Screenshot salvato in: {screenshot_path}")
    # Verifica che il file sia stato scaricato
    assert os.path.exists(download_path), f"Il file non è stato scaricato: {download_path}"
    assert os.path.getsize(download_path) > 0, "Il file scaricato è vuoto"
