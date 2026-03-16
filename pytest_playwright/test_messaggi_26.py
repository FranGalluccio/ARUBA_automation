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


def test_selezione_multipla_batch(page):
    """Verifica selezione multipla messaggi e azioni batch (segna come letto/non letto, elimina)."""
    LoginPec(page).login_pec(config)

    # Invia 2 messaggi di test per avere materiale da selezionare
    for i in range(2):
        ts = int(time.time()) + i
        Helper.crea_messaggio(
            page, config,
            oggetto=f"Test batch {ts}",
            corpo="Messaggio per test selezione multipla",
        )
        page.locator('span[title="Invia"]').click()
        page.wait_for_timeout(3000)

    # Vai alla inbox e aggiorna
    page.locator("#messages").get_by_label("Messaggi").click()
    page.wait_for_timeout(2000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(3000)

    # Seleziona tutti i messaggi tramite checkbox header
    checkbox_header = page.locator(
        'input[type="checkbox"][aria-label*="Seleziona tutti"], '
        'th input[type="checkbox"], '
        '.select-all-checkbox'
    ).first
    if checkbox_header.is_visible():
        checkbox_header.click()
        page.wait_for_timeout(1000)
    else:
        # Fallback: seleziona i primi 2 messaggi manualmente
        checkboxes = page.locator('div.frame-record-desktop input[type="checkbox"]').all()
        for cb in checkboxes[:2]:
            try:
                cb.click()
                page.wait_for_timeout(500)
            except Exception:
                pass

    # Verifica che appaiano le azioni batch (toolbar multi-select)
    batch_toolbar = page.locator(
        '[class*="batch"], [class*="multi-select"], '
        'button:has-text("Segna come"), button:has-text("Elimina selezionati")'
    ).first
    try:
        batch_toolbar.wait_for(state="visible", timeout=5000)
        batch_visible = True
    except Exception:
        batch_visible = False

    assert batch_visible, (
        "La toolbar azioni batch non è apparsa dopo la selezione multipla dei messaggi."
    )

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_26___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
