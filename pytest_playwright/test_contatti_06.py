import os
import json
import time
from datetime import datetime
from base_pec import LoginPec
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


def test_elimina_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    page.click("#contacts")
    page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=10000)

    # Crea un contatto da eliminare
    unique_email = f"testelimina_{int(time.time())}@{TEST_EMAIL_DOMAIN}"
    cognome = f"DaEliminare{int(time.time())}"

    try:
        page.locator('button:has-text("Nuovo"), button:has-text("Nouveau")').first.click()
        page.locator('button:has-text("Procedi"), button:has-text("Procéder"), button:has-text("Continuer")').first.evaluate("el => el.click()")
        page.locator('input[placeholder*=" nome"], input[placeholder*="prénom"]').first.fill("Contatto")
        page.locator('input[placeholder*="cognome"], input[placeholder*="famille"]').first.fill(cognome)
        page.locator('input[placeholder*="email"]').first.fill(unique_email)
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

        # Cerca il contatto appena creato
        search = page.locator('input[placeholder*="Cerca tra i contatti"], input[placeholder*="contacts"]').first
        search.click()
        search.fill(cognome)

        row = page.locator('div.frame-record-desktop').filter(has_text=cognome).first
        row.wait_for(state="visible", timeout=5000)

        row.hover()
        row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)

        # Clicca Elimina dalla toolbar
        elimina_btn = page.locator('aru-symbol[title="Elimina"], aru-symbol[title="Supprimer"], button[title="Elimina"]').first
        elimina_btn.wait_for(state="visible", timeout=5000)
        elimina_btn.click()

        # Screenshot per diagnostica
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_06_del_{datetime.now():%H-%M-%S}.png"))

        # Conferma nella dialog
        page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.wait_for(state="visible", timeout=5000)
        page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.click()

        # Aspetta che la lista si aggiorni dopo l'eliminazione
        try:
            page.locator('.cdk-overlay-backdrop').wait_for(state="hidden", timeout=3000)
        except Exception:
            pass
        try:
            row.wait_for(state="hidden", timeout=5000)
        except Exception:
            pass

        search2 = page.locator('input[placeholder*="Cerca tra i contatti"], input[placeholder*="contacts"]').first
        search2.click(force=True)
        search2.fill(cognome)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        assert page.locator('div.frame-record-desktop').filter(has_text=cognome).count() == 0, \
            f"Il contatto '{cognome}' è ancora presente dopo l'eliminazione"

    finally:
        # Cleanup: seleziona tutti i contatti ed elimina (safety net)
        try:
            page.click("#contacts")
            page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=5000)
            page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.click()
            page.wait_for_timeout(2000)
            page.locator('span.aru-input-checkbox__checkmark').first.wait_for(state="visible", timeout=5000)
            page.locator('span.aru-input-checkbox__checkmark').first.click(force=True)
            page.locator('aru-symbol[title="Elimina"], aru-symbol[title="Supprimer"], button[title="Elimina"]').first.click()
            page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.wait_for(state="visible", timeout=5000)
            page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.click()
        except Exception:
            pass
