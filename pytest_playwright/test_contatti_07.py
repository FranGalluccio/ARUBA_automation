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


def test_ricerca_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.click("#contacts")
    time.sleep(1)

    # Crea un contatto con nome univoco per la ricerca
    nome_univoco = f"RicercaTest{int(time.time())}"
    unique_email = f"ricerca_{int(time.time())}@{TEST_EMAIL_DOMAIN}"

    try:
        page.get_by_role("button", name="Nuovo").click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill(nome_univoco)
        page.get_by_placeholder("Inserisci cognome").fill("Playwright")
        page.get_by_placeholder("Inserisci email").fill(unique_email)
        page.get_by_role("button", name="Salva").click()
        time.sleep(1)

        # Usa la barra di ricerca
        search = page.locator('input[placeholder*="Cerca tra i contatti"], input[placeholder*="Cerca"]').first
        search.click()
        search.fill(nome_univoco)
        time.sleep(1)

        # Verifica che il contatto sia visibile nei risultati
        result = page.locator('div.frame-record-desktop, [class*="contact-row"]').filter(has_text=nome_univoco).first
        result.wait_for(state="visible", timeout=8000)
        assert result.is_visible(), f"Il contatto '{nome_univoco}' non è stato trovato nella ricerca"

        time.sleep(1)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
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
