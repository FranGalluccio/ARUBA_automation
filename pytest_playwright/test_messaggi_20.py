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
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: cerca il messaggio specifico per oggetto (non il primo in assoluto)
    # 40 iterazioni * ~4s = ~160s per ambienti lenti (SMB con inbox piena)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(40):
        page.wait_for_timeout(3000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    msg.first.click(timeout=15000)
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"], aru-symbol[title="Ouvrir dans une nouvelle fenêtre"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.set_viewport_size({"width": 1280, "height": 900})
    new_page.wait_for_load_state("domcontentloaded")
    new_page.wait_for_load_state("load")
    assert "external-message" in new_page.url

    # Clicca sull'allegato (selettori multipli per versioni diverse)
    nome_file = os.path.basename(file_allegato)
    attachment_btn = new_page.locator(
        f'[title="{nome_file}"], '
        f'button:has-text("{nome_file}"), '
        f'[aria-label="{nome_file}"], '
        f'span:has-text("{nome_file}")'
    ).first
    attachment_btn.wait_for(state="visible", timeout=30000)
    attachment_btn.click(force=True)
    new_page.wait_for_timeout(1000)

    # Scarica l'allegato — IT: "Scarica" / FR: "Télécharger"
    # The download button is in a CDK overlay dropdown. The inner shadow DOM button has wrong
    # bounding box coords, so we locate the CDK pane (regular DOM) and click via mouse.click().
    # Route interception forces Content-Disposition: attachment so Chrome downloads the PDF.
    download_path = os.path.join(REPORT_FOLDER, f"allegato_scaricato_{datetime.now():%Y-%m-%d_%H-%M-%S}_{nome_file}")

    def _force_attachment(route):
        url = route.request.url.lower()
        if any(k in url for k in ['.pdf', 'download', 'attach', 'allegat', '/file']):
            resp = route.fetch()
            headers = dict(resp.headers)
            headers['content-disposition'] = f'attachment; filename="{nome_file}"'
            route.fulfill(response=resp, headers=headers)
        else:
            route.continue_()

    # Find the dropdown/overlay panel position via JS (regular DOM, no shadow piercing needed)
    coords = new_page.evaluate("""() => {
        // Look for CDK overlay pane or dropdown menu that opened
        const selectors = ['.cdk-overlay-pane', '[role="menu"]', '[role="listbox"]', '.dropdown-menu'];
        for (const sel of selectors) {
            for (const el of document.querySelectorAll(sel)) {
                const rect = el.getBoundingClientRect();
                if (rect.width > 50 && rect.height > 30 && rect.y >= 0 && rect.y < window.innerHeight) {
                    // Click on the first item (Télécharger/Scarica) — top 30% of panel
                    return {x: rect.x + rect.width / 2, y: rect.y + rect.height * 0.3};
                }
            }
        }
        // Fallback: first visible aru-button element
        for (const el of document.querySelectorAll('aru-button')) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 10 && rect.height > 10 && rect.y > 0 && rect.y < window.innerHeight) {
                return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2};
            }
        }
        return null;
    }""")
    print(f"Download button coords via overlay: {coords}")

    new_page.route('**', _force_attachment)
    try:
        with new_page.expect_download(timeout=30000) as download_info:
            if coords:
                new_page.mouse.click(coords['x'], coords['y'])
            else:
                new_page.locator('button[title="Scarica"], button[title="Télécharger"]').first.click(force=True)
        download = download_info.value
        download.save_as(download_path)
    finally:
        new_page.unroute('**', _force_attachment)

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
