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

    # Dismiss overlay pre-esistente (es. banner "Adegua la tua PEC")
    try:
        page.locator('button:has-text("Plus tard"), button:has-text("Ricordarmelo"), button:has-text("Non ora")').first.click(timeout=2000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Clicca su importa messaggi con force (evita blocco da backdrop residuo)
    page.locator('button[title="Importa"], button[title="Importer"], [title="Importa"], [title="Importer"]').first.click(force=True)
    page.wait_for_timeout(1000)

    # Il dialog di importazione apre un CDK overlay con backdrop.
    # set_input_files su #hidden_input scatena il locator handler 60+ volte.
    # Fix: intercetta il file chooser cliccando il pulsante DENTRO il pane con force=True.
    try:
        with page.expect_file_chooser(timeout=15000) as fc_info:
            page.locator(
                '.cdk-overlay-pane button[title*="Seleziona"], '
                '.cdk-overlay-pane button[title*="appareil"], '
                '.cdk-overlay-pane button[title*="Sélectionner"], '
                '.cdk-overlay-pane button[title*="Choisir"], '
                '.cdk-overlay-pane button[title*="Dispositivo"]'
            ).first.click(force=True)
        file_chooser = fc_info.value
        file_chooser.set_files(importa_messaggi)
    except Exception:
        # Fallback: input[type="file"] dentro il pane
        hidden = page.locator('.cdk-overlay-pane input[type="file"], #hidden_input, input[type="file"]').first
        hidden.set_input_files(importa_messaggi)

    # Attendi che il file sia pronto nel dialog (upload preview)
    page.wait_for_timeout(3000)
    page.locator('button[title="Importa"], button[title="Importer"], [title="Importa"], [title="Importer"]').nth(1).wait_for(state="visible", timeout=10000)

    # Clicca il bottone "Importa" di conferma nel dialog
    page.locator('button[title="Importa"], button[title="Importer"], [title="Importa"], [title="Importer"]').nth(1).click(force=True)

    # Attendi che il caricamento in background termini, poi verifica toast
    # Il file può richiedere alcuni secondi per essere processato lato server
    page.wait_for_timeout(3000)
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible(timeout=15000)

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
    

    
    