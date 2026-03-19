import os
import json
from datetime import datetime
import time
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

    time.sleep(1)
    page.click("#contacts")
    time.sleep(1)

    ts = int(time.time())
    nome_pref = f"Preferito{ts}"
    unique_email = f"pref_{ts}@{TEST_EMAIL_DOMAIN}"

    try:
        page.get_by_role("button", name="Nuovo").click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill(nome_pref)
        page.get_by_placeholder("Inserisci cognome").fill("Test")
        page.get_by_placeholder("Inserisci email").fill(unique_email)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)

        # Cerca il contatto
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill(nome_pref)
        time.sleep(1)

        row = page.locator('div.frame-record-desktop').filter(has_text=nome_pref).first
        row.wait_for(state="visible", timeout=8000)

        row.hover()
        time.sleep(1)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_08_hover_{datetime.now():%H-%M-%S}.png"))

        # Clicca il pulsante stella/preferiti
        star_btn = row.locator('button:has(aru-symbol[symbol="star-regular-big"])').first
        star_btn.wait_for(state="visible", timeout=5000)
        star_btn.click(force=True)
        time.sleep(2)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        # Verifica in "Contatti preferiti"
        page.locator('button[title="Contatti preferiti"]').first.click()
        time.sleep(3)
        try:
            page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)
        except Exception:
            pass
        assert page.locator('div.frame-record-desktop').filter(has_text=nome_pref).count() > 0, \
            f"Il contatto '{nome_pref}' non trovato in Contatti preferiti dopo averlo aggiunto"

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
