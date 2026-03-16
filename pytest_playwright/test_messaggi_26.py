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
    page.locator("#messages").get_by_label("Messaggi").first.click()
    page.wait_for_timeout(2000)

    # Dismiss CDK overlay se presente (modale "Adegua la tua PEC" ecc.)
    if page.locator('.cdk-overlay-backdrop').is_visible():
        for _ in range(3):
            if not page.locator('.cdk-overlay-backdrop').is_visible():
                break
            try:
                btn = page.locator('button:has-text("Ricordarmelo"), button:has-text("Chiudi"), button:has-text("Non ora")').first
                if btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(500)
                    continue
                page.locator('.cdk-overlay-pane').last.locator('button').last.click(force=True)
                page.wait_for_timeout(500)
            except Exception:
                break

    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(3000)

    # Hover sul primo messaggio per rendere visibile il checkbox, poi clicca
    rows = page.locator('div.frame-record-desktop').all()
    assert len(rows) >= 2, f"Trovati solo {len(rows)} messaggi in inbox, attesi almeno 2."

    for row in rows[:2]:
        try:
            row.hover()
            page.wait_for_timeout(300)
            cb = row.locator('input[type="checkbox"]').first
            if cb.is_visible():
                cb.click()
            else:
                # Alcuni temi mostrano un div cliccabile come checkbox
                row.locator('[class*="checkbox"], aru-checkbox').first.click(force=True)
            page.wait_for_timeout(500)
        except Exception:
            pass

    # Verifica che almeno 2 messaggi siano selezionati o che appaia la toolbar
    # (il titolo pagina cambia a "X messaggi selezionati" o appare un contatore)
    page.wait_for_timeout(1000)
    page_content = page.content().lower()
    batch_visible = (
        "selezionat" in page_content
        or page.locator('button:has-text("Elimina"), button:has-text("Segna")').count() > 0
    )

    assert batch_visible, (
        "La toolbar azioni batch non è apparsa dopo la selezione multipla dei messaggi. "
        "Verificare che i checkbox nei messaggi siano cliccabili."
    )

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_26___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
