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


def test_contatto_preferito(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    page.click("#contacts")
    page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=10000)

    ts = int(time.time())
    nome_pref = f"Preferito{ts}"
    unique_email = f"pref_{ts}@{TEST_EMAIL_DOMAIN}"

    try:
        page.locator('button:has-text("Nuovo"), button:has-text("Nouveau")').first.click()
        page.wait_for_timeout(1500)
        page.locator('button:has-text("Procedi"), button:has-text("Procéder"), button:has-text("Continuer"), button:has-text("Suivant")').first.click(force=True)
        page.wait_for_timeout(1000)
        page.locator('input[placeholder*=" nome"], input[placeholder*="rénom"]').first.fill(nome_pref, force=True)
        page.locator('input[placeholder*="cognome"], input[placeholder*="famille"]').first.fill("Test", force=True)
        page.locator('input[placeholder*="email"]').first.fill(unique_email, force=True)
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click(force=True)

        # Cerca il contatto
        search = page.locator('input[placeholder*="Cerca tra i contatti"], input[placeholder*="contacts"]').first
        search.click()
        search.fill(nome_pref)

        row = page.locator('div.frame-record-desktop').filter(has_text=nome_pref).first
        row.wait_for(state="visible", timeout=8000)

        row.hover()
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_08_hover_{datetime.now():%H-%M-%S}.png"))

        # Clicca il pulsante stella/preferiti
        star_btn = row.locator('button:has(aru-symbol[symbol="star-regular-big"])').first
        star_btn.wait_for(state="visible", timeout=5000)
        star_btn.click(force=True)

        # Attendi che il server registri il preferito (verifica cambio icona stella)
        try:
            row.locator('button:has(aru-symbol[symbol="star-big"])').first.wait_for(state="visible", timeout=5000)
        except Exception:
            page.wait_for_timeout(3000)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        # Verifica in "Contatti preferiti"
        page.locator('button[title="Contatti preferiti"], button[title="Contacts favoris"]').first.click()
        try:
            page.locator('div.frame-record-desktop').filter(has_text=nome_pref).first.wait_for(state="visible", timeout=10000)
        except Exception:
            pass
        assert page.locator('div.frame-record-desktop').filter(has_text=nome_pref).count() > 0, \
            f"Il contatto '{nome_pref}' non trovato in Contatti preferiti dopo averlo aggiunto"

    finally:
        # Cleanup: seleziona tutti i contatti ed elimina
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
