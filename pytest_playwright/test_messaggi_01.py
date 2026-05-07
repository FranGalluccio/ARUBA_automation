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
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Aspetta ricezione del messaggio con allegato (poll per oggetto)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(20):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    assert msg.count() > 0, f"Messaggio '{oggetto}' non trovato in inbox entro 80s"
    msg.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"], aru-symbol[title="Ouvrir dans une nouvelle fenêtre"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.set_viewport_size({"width": 1280, "height": 900})
    new_page.wait_for_load_state("networkidle", timeout=15000)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Verifica pagina esterna
    assert "external-message" in new_page.url

    # Aspetta che il bottone allegato sia visibile (selettori multipli per versioni diverse)
    nome_allegato = os.path.basename(file_allegato)
    attachment_loc = new_page.locator(
        f'[title="{nome_allegato}"], '
        f'button:has-text("{nome_allegato}"), '
        f'[aria-label="{nome_allegato}"], '
        f'span:has-text("{nome_allegato}")'
    ).first
    attachment_loc.wait_for(state="visible", timeout=30000)
    attachment_loc.click()

    # Mostra anteprima (button may be outside viewport in FR layout)
    _preview_btn = new_page.locator(
        'button:has-text("Mostra anteprima"), button:has-text("Aperçu"), button:has-text("Afficher")'
    ).or_(new_page.get_by_text("Mostra anteprima", exact=False)).or_(
        new_page.get_by_text("Aperçu", exact=False)
    ).first
    _preview_btn.evaluate("el => el.click()")
    new_page.wait_for_timeout(2000)
