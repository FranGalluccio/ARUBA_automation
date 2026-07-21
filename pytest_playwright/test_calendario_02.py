import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper, elimina_evento_pec
from playwright.sync_api import sync_playwright, expect


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


def test_creazione_modifica_evento(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_base = f"evento test automatico {ts}"
    titolo_modificato = f"evento test automatico modificato {ts}"

    # Crea nuovo evento
    page.locator('#calendar, [aria-label="Calendario"], [aria-label="Calendrier"], button[title="Calendario"], button[title="Calendrier"]').first.click()
    page.locator('button:has-text("Nuovo evento"), button:has-text("Nouvel événement")').first.click()
    titolo_input = page.locator('input[placeholder*=" titolo"], input[placeholder*=" titre"]').first
    titolo_input.wait_for(state="visible", timeout=8000)
    titolo_input.fill(titolo_base)
    page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()
    page.locator("a").filter(has_text=titolo_base).filter(has_not_text="modificato").first.wait_for(state="visible", timeout=8000)
    page.locator("a").filter(has_text=titolo_base).filter(has_not_text="modificato").first.click()
    page.locator('button:has-text("Modifica"), button:has-text("Modifier")').first.wait_for(state="visible", timeout=5000)
    page.locator('button:has-text("Modifica"), button:has-text("Modifier")').first.click()
    titolo_input = page.locator('input[placeholder*=" titolo"], input[placeholder*=" titre"]').first
    titolo_input.wait_for(state="visible", timeout=5000)
    titolo_input.click()
    titolo_input.fill("")
    titolo_input.fill(titolo_modificato)
    page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

    # Verifica toast di conferma salvataggio modifica evento
    toast = page.locator("div.aru-toast__message").first
    toast.wait_for(state="visible", timeout=8000)
    toast_text = toast.text_content()
    assert "evento è stato salvato" in toast_text.lower() or "evento è stato modificato" in toast_text.lower() \
        or "enregistr" in toast_text.lower(), \
        f"Toast di conferma salvataggio evento non trovato: {toast_text!r}"

    try:
        page.wait_for_timeout(1000)
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
    finally:
        elimina_evento_pec(page, "evento test automatico")
