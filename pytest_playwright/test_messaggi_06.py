import os
import json
from datetime import datetime
import time
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

def test_ripristino_messaggi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia 2 messaggi a se stesso per garantire che il Cestino abbia elementi
    for i in range(2):
        Helper.crea_messaggio(
            page, config,
            oggetto=f"Test ripristino {int(time.time())}_{i}",
            corpo="Test automatico ripristino messaggi",
        )
        page.locator('span[title="Invia"]').click()
        page.wait_for_timeout(3000)

    # Sposta i messaggi nel Cestino (seleziona i 2 appena inviati)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)
    page.locator('div.aru-input-checkbox').nth(1).click()
    page.wait_for_timeout(500)
    page.locator('div.aru-input-checkbox').nth(2).click()
    page.wait_for_timeout(500)
    page.locator(
        'button:has(aru-symbol[title="Elimina"]), aru-button:has(aru-symbol[title="Elimina"])'
    ).first.click()
    page.wait_for_timeout(1000)
    try:
        page.get_by_role("button", name="Sì").click(timeout=2000)
        page.wait_for_timeout(1000)
    except Exception:
        pass

    # Apri cestino
    page.locator('button[title="Cestino"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    count = page.locator('div.frame-record-desktop').count()
    assert count >= 2, f"Cestino ha solo {count} messaggi — impossibile testare il ripristino"

    # Seleziona i primi 2 messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    page.wait_for_timeout(500)
    page.locator('div.aru-input-checkbox').nth(2).click()
    page.wait_for_timeout(500)

    # Clicca su sposta
    page.locator('svg[title="Sposta"]').click()

    # Sposta in arrivo
    page.locator("aru-webmail-menu-item[webmailmenuopener]").locator("span:has-text('In arrivo')").click()

    # Verifica toast di conferma ripristino
    toast = page.locator("div.aru-toast__message").filter(has_text="I messaggi selezionati sono stati spostati in In arrivo").first
    toast.wait_for(state="visible", timeout=8000)
    assert "I messaggi selezionati sono stati spostati in In arrivo" in toast.text_content()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
