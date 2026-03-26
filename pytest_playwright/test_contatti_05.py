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

    page.click("#contacts")
    page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=10000)

    # Crea un nuovo contatto da modificare
    unique_email = f"testmod_{int(time.time())}@{TEST_EMAIL_DOMAIN}"

    try:
        page.get_by_role("button", name="Nuovo", exact=True).click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill("Contatto")
        page.get_by_placeholder("Inserisci cognome").fill("DaModificare")
        page.get_by_placeholder("Inserisci email").fill(unique_email)
        page.get_by_role("button", name="Salva").click()

        # Attendi che il salvataggio si completi (toast o chiusura form)
        page.wait_for_timeout(2000)

        # Chiudi cookie banner se apparso dopo il salvataggio
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=2000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Cerca il contatto appena creato
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill("DaModificare")
        page.wait_for_timeout(1500)  # attendi che i risultati si aggiornino

        # Trova il contatto nella lista
        row = page.locator('div.frame-record-desktop').filter(has_text="DaModificare").first
        row.wait_for(state="visible", timeout=10000)

        # Apri il contatto in modifica.
        # Step 1: click singolo per aprire il pannello dettaglio a destra
        row.click()
        page.wait_for_timeout(1200)

        cognome_input = page.get_by_placeholder("Inserisci cognome")

        # Step 2: il pannello dettaglio si è aperto → clicca il pulsante "Modifica"
        # Usa filter(has_text=) che attraversa lo shadow DOM di aru-button.
        if not (cognome_input.count() > 0 and cognome_input.first.is_visible()):
            try:
                btn = page.locator('aru-button').filter(has_text="Modifica").first
                btn.wait_for(state="visible", timeout=5000)
                btn.click()
                page.wait_for_timeout(1000)
            except Exception:
                pass

        # Fallback: get_by_role e dblclick
        if not (cognome_input.count() > 0 and cognome_input.first.is_visible()):
            try:
                page.get_by_role("button", name="Modifica").first.click(timeout=3000)
                page.wait_for_timeout(1000)
            except Exception:
                try:
                    row.dblclick()
                    page.wait_for_timeout(1000)
                except Exception:
                    pass

        cognome_input.wait_for(state="visible", timeout=20000)
        cognome_input.click(click_count=3)
        cognome_input.fill("Modificato")

        # Salva
        page.get_by_role("button", name="Salva").click()

        # Verifica che il cognome aggiornato sia presente
        search2 = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search2.click(click_count=3)
        search2.fill("Modificato")

        result = page.locator('div.frame-record-desktop').filter(has_text="Modificato").first
        result.wait_for(state="visible", timeout=5000)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        assert result.is_visible(), "Il contatto modificato non è visibile"

    finally:
        # Cleanup: seleziona tutti i contatti ed elimina
        try:
            page.click("#contacts")
            page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=10000)
            page.locator('button[title="Tutti i contatti"]').first.click()
            page.wait_for_timeout(2000)
            page.locator('span.aru-input-checkbox__checkmark').first.wait_for(state="visible", timeout=5000)
            page.locator('span.aru-input-checkbox__checkmark').first.click(force=True)
            page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.wait_for(state="visible", timeout=5000)
            page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
            page.locator('.cdk-overlay-pane button:has-text("Elimina")').first.wait_for(state="visible", timeout=5000)
            page.locator('.cdk-overlay-pane button:has-text("Elimina")').first.click()
        except Exception:
            pass
