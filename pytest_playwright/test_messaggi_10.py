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


def test_messaggio_alta_priorita(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test alta priorità playwright {ts}"

    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Test automatico invio messaggio PEC con Playwright",
    )

    # Clicca pulsante altro → alta priorità
    page.locator('aru-button:has(aru-symbol[symbol="more"])').click()
    page.locator('aru-button#high-priority').click()

    # Invia
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: cerca il messaggio specifico per oggetto (non il primo in assoluto)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(20):
        page.wait_for_timeout(3000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    msg.first.click()
    page.locator('div.message-content-body').wait_for(state="visible", timeout=20000)

    # Verifica che esista un indicatore di alta priorità scansionando tutti gli aru-symbol via JS
    found_priority = page.evaluate("""() => {
        const symbols = Array.from(document.querySelectorAll('aru-symbol'));
        return symbols.some(el => {
            const symbol = (el.getAttribute('symbol') || '').toLowerCase();
            const title = (el.getAttribute('title') || '').toLowerCase();
            const name = (el.getAttribute('name') || '').toLowerCase();
            return symbol.includes('import') || symbol.includes('high') || symbol.includes('prior') ||
                   title.includes('import') || title.includes('alta') || title.includes('prior') ||
                   name.includes('import') || name.includes('high') || name.includes('prior');
        });
    }""")

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert found_priority, "Nessun indicatore di alta priorita trovato nel messaggio (aru-symbol con attributi importan*/high*/prior*/alta*)"