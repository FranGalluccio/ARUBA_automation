import os
import json
from datetime import datetime
import time
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


def test_salva_e_usa_modello(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    oggetto_modello = f"Modello playwright {int(time.time())}"

    # Crea un messaggio e salvalo come modello
    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto_modello,
        corpo="Corpo del modello di test",
    )

    # Accetta eventuali cookie che potrebbero bloccare i click
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=2000)
        time.sleep(1)
    except Exception:
        pass

    # Salva come modello usando il menu a tendina accanto al pulsante Invia
    page.locator("#new-message\\.save-menu").click(force=True)
    time.sleep(1)
    page.locator('button[title="Salva come modello"]').click()
    time.sleep(1)

    # Chiudi il dialog del messaggio (pulsante Chiudi nella toolbar del compose)
    try:
        page.locator('button[title="Chiudi"]').last.click(force=True)
        time.sleep(1)
    except Exception:
        pass

    # Se compare dialog di conferma chiusura, conferma
    try:
        page.locator('button[title="Si"], button:has-text("Sì"), button:has-text("Si")').first.click(timeout=2000)
        time.sleep(1)
    except Exception:
        pass

    # Apri la cartella Modelli e verifica che il modello sia presente
    page.locator('button[title="Modelli"]').click()
    time.sleep(1)
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    # Verifica che il modello salvato con il nome univoco sia visibile nella lista
    modello_row = page.locator('div.frame-record-desktop').filter(has_text=oggetto_modello).first
    assert modello_row.is_visible(), f"Il modello '{oggetto_modello}' non è visibile nella cartella Modelli"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_21___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
