import os
import json
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

# --- Percorso importa messaggi ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("IMPORTA_MESSAGGI", config.get("importa_messaggi"))
importa_messaggi = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw

def test_messaggio_importato(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Chiudi cookie banner se presente
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Clicca su importa messaggi
    page.locator('button[title="Importa"], button[title="Importer"]').first.click()

    # Imposta il file direttamente sull'input nascosto (bypass CDK overlay backdrop)
    hidden = page.locator('#hidden_input, input[type="file"]').first
    try:
        hidden.set_input_files(importa_messaggi)
    except Exception:
        # Fallback: intercetta file chooser tramite click sul bottone
        with page.expect_file_chooser() as fc_info:
            page.locator('button[title="Seleziona da dispositivo"], button[title*="appareil"], button[title*="Sélectionner"], button[title*="Choisir"]').first.evaluate("el => el.click()")
        file_chooser = fc_info.value
        file_chooser.set_files(importa_messaggi)

    # Attendi caricamento allegato
    page.wait_for_timeout(2000)
    page.locator('button[title="Importa"], button[title="Importer"]').nth(1).wait_for(state="visible", timeout=5000)

    # Clicca il bottone "Importa"
    page.locator('button[title="Importa"], button[title="Importer"]').nth(1).click()

    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    toast_text = toast.text_content()
    assert "nuovo messaggio" in toast_text or "nouveau message" in toast_text.lower(), \
        f"Toast importazione non trovato: {toast_text!r}"
    

    
    