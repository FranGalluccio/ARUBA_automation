import os
import json
import time
from datetime import datetime

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


def test_messaggio_con_allegato(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test allegato playwright {ts}"

    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Test automatico invio messaggio PEC con Playwright",
        path_allegato=file_allegato,
    )

    # Invia
    page.locator('span[title="Invia"]').click()

    # Aspetta ricezione, aggiorna e apri il primo messaggio
    page.wait_for_timeout(10000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(2000)
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.wait_for_load_state("networkidle", timeout=15000)

    # Verifica pagina esterna
    assert "external-message" in new_page.url

    # Aspetta che il bottone allegato sia visibile
    nome_allegato = os.path.basename(file_allegato)
    new_page.locator(f'button[title="{nome_allegato}"]').wait_for(state="visible", timeout=15000)
    new_page.locator(f'button[title="{nome_allegato}"]').click()

    # Mostra anteprima
    new_page.locator('text="Mostra anteprima"').first.click()
    new_page.wait_for_timeout(2000)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
