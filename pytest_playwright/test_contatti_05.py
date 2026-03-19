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

TEST_EMAIL_DOMAIN = config.get("test_email_domain", "pec.it")


def test_modifica_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.click("#contacts")
    time.sleep(1)

    # Crea un nuovo contatto da modificare
    unique_email = f"testmod_{int(time.time())}@{TEST_EMAIL_DOMAIN}"

    try:
        page.get_by_role("button", name="Nuovo").click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill("Contatto")
        page.get_by_placeholder("Inserisci cognome").fill("DaModificare")
        page.get_by_placeholder("Inserisci email").fill(unique_email)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)

        # Cerca il contatto appena creato
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill("DaModificare")
        time.sleep(1)

        # Trova il contatto nella lista
        row = page.locator('div.frame-record-desktop').filter(has_text="DaModificare").first
        row.wait_for(state="visible", timeout=8000)

        # Hover per far apparire il checkbox e selezionarlo
        row.hover()
        time.sleep(0.5)
        row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
        time.sleep(1)

        # Cerca pulsante Modifica nella toolbar (appare quando si seleziona 1 contatto)
        # oppure tenta doppio click sul contatto per aprire l'editor
        try:
            modifica_btn = page.locator('button[title="Modifica"], aru-symbol[title="Modifica"]').first
            modifica_btn.wait_for(state="visible", timeout=3000)
            modifica_btn.click()
        except Exception:
            # Fallback: doppio click sulla riga per aprire edit
            row.dblclick()

        time.sleep(1)

        # Modifica il cognome
        cognome_input = page.get_by_placeholder("Inserisci cognome")
        cognome_input.wait_for(state="visible", timeout=5000)
        cognome_input.click(click_count=3)
        cognome_input.fill("Modificato")

        # Salva
        page.get_by_role("button", name="Salva").click()
        time.sleep(1)

        # Verifica che il cognome aggiornato sia presente
        search2 = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search2.click(click_count=3)
        search2.fill("Modificato")
        time.sleep(1)

        result = page.locator('div.frame-record-desktop').filter(has_text="Modificato").first
        result.wait_for(state="visible", timeout=5000)
        assert result.is_visible(), "Il contatto modificato non è visibile"

        time.sleep(1)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    finally:
        # Cleanup: seleziona tutti i contatti ed elimina
        try:
            page.click("#contacts")
            time.sleep(1)
            page.locator('button[title="Tutti i contatti"]').first.click()
            time.sleep(1)
            page.locator('span.aru-input-checkbox__checkmark').first.click(force=True)
            time.sleep(0.5)
            page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
            time.sleep(0.5)
            page.locator('.cdk-overlay-pane button:has-text("Elimina")').first.click(timeout=3000)
            time.sleep(1)
        except Exception:
            pass
