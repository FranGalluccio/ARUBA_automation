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

def test_etichetta(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Clicca su nuova etichetta
    page.locator('span[title="Nuova etichetta"], span[title="Nouvelle étiquette"]').first.click()

    nome_etichetta = "Test etichetta lavoro"
    # Compila nome etichetta
    page.locator("input[placeholder*='Lavoro'], input[placeholder*='Travail'], input[placeholder*='label'], input[placeholder*='tichetta']").first.wait_for(state="visible", timeout=5000)
    page.locator("input[placeholder*='Lavoro'], input[placeholder*='Travail'], input[placeholder*='label'], input[placeholder*='tichetta']").first.fill(nome_etichetta)
    # Salva nuova etichetta
    page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

    chiudi = page.locator('button:has-text("Chiudi"), button:has-text("Fermer")').first

    try:
        chiudi.wait_for(state="visible", timeout=3000)
        chiudi.click()
    except Exception:
        pass

    # Seleziona i messaggi (hover per renderli visibili)
    page.locator('div.frame-record-desktop').nth(0).hover()
    page.wait_for_timeout(300)
    page.locator('div.aru-input-checkbox').nth(1).click(force=True)
    page.wait_for_timeout(500)
    page.locator('div.frame-record-desktop').nth(1).hover()
    page.wait_for_timeout(300)
    page.locator('div.aru-input-checkbox').nth(2).click(force=True)

    # Clicca su etichetta
    page.locator('button:has(aru-symbol[title="Etichetta"])').nth(0).click()
    page.locator('aru-chosen-closed[inputgroupinputs*="Test etichetta lavoro"]').wait_for(state="visible", timeout=5000)

    # Seleziona etichetta lavoro
    page.locator('aru-chosen-closed[inputgroupinputs*="Test etichetta lavoro"]').click()
    page.wait_for_timeout(500)
    # Applica etichetta
    page.evaluate('''() => {
    const btn = document.querySelector('button[title="Applica"]') || document.querySelector('button[title="Appliquer"]');
    btn?.click();
}''')

    # Clicca con tasto destro sull'etichetta creata
    page.locator(f'button[title="{nome_etichetta}"]').click(button="right")

    # Elimina etichetta
    page.locator('button:has-text("Elimina etichetta"), button:has-text("Supprimer l\'étiquette")').wait_for(state="visible", timeout=5000)
    page.locator('button:has-text("Elimina etichetta"), button:has-text("Supprimer l\'étiquette")').click()

    # Conferma elimina etichetta
    page.locator('button[title="Si"], button[title="Oui"]').click()

    # Verifica toast di conferma eliminazione etichetta
    toast = page.locator("div.aru-toast__message").filter(has_text="etichetta").or_(
        page.locator("div.aru-toast__message").filter(has_text="étiquette")
    ).first
    expect(toast).to_be_visible()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    toast_text = toast.text_content()
    assert "etichetta" in toast_text.lower() or "étiquette" in toast_text.lower(), \
        f"Toast eliminazione etichetta non trovato: {toast_text!r}"
