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


def test_scrivi_email_da_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    page.click("#contacts")
    page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=10000)

    ts = int(time.time())
    nome_test = f"EmailTest{ts}"
    email_contatto = f"emailtest_{ts}@{TEST_EMAIL_DOMAIN}"

    try:
        # Crea un contatto con email per il test
        page.get_by_role("button", name="Nuovo", exact=True).click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill(nome_test)
        page.get_by_placeholder("Inserisci cognome").fill("Contact")
        page.get_by_placeholder("Inserisci email").fill(email_contatto)
        page.get_by_role("button", name="Salva").click()

        # Cerca il contatto
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill(nome_test)

        row = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
        row.wait_for(state="visible", timeout=8000)

        # Hover per rivelare i pulsanti di azione
        row.hover()
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_09_hover_{datetime.now():%H-%M-%S}.png"))

        def compose_open():
            try:
                crea_dialog = page.locator('text="Crea contatto, gruppo, rubrica"').first
                if crea_dialog.is_visible():
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(500)
            except Exception:
                pass
            return page.locator('span[title="Invia"]').count() > 0

        email_clicked = False

        mailto_link = row.locator('a[href*="mailto"], a[href*="pec"]').first
        try:
            if mailto_link.count() > 0:
                mailto_link.click(force=True)
                page.wait_for_timeout(1000)
                email_clicked = compose_open()
        except Exception:
            pass
        if not email_clicked:
            action_btns = row.locator('webmail-actions-buttons aru-button').all()
            for btn in action_btns:
                try:
                    btn.click(force=True)
                    page.wait_for_timeout(1000)
                    if compose_open():
                        email_clicked = True
                        break
                except Exception:
                    pass
        if not email_clicked:
            try:
                page.locator('button[title="Scrivi email"], button[title*="email"], button[title*="mail"]').first.click(timeout=3000)
                page.wait_for_timeout(1000)
                email_clicked = compose_open()
            except Exception:
                pass
        if not email_clicked:
            try:
                row.hover()
                row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
                page.wait_for_timeout(500)
                page.locator('button[title="Scrivi email"], button[title*="Scrivi"]').first.click(timeout=3000)
                page.wait_for_timeout(1000)
                email_clicked = compose_open()
            except Exception:
                pass

        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        assert email_clicked, "Impossibile aprire la finestra di composizione email dal contatto"

        # Chiudi il dialog senza inviare
        try:
            page.locator('button[title="Chiudi"]').last.click(force=True)
            page.wait_for_timeout(500)
            page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
        except Exception:
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass

    finally:
        # Cleanup: seleziona tutti i contatti ed elimina
        try:
            page.click("#contacts")
            page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=5000)
            page.locator('button[title="Tutti i contatti"]').first.click()
            page.wait_for_timeout(2000)
            page.locator('span.aru-input-checkbox__checkmark').first.wait_for(state="visible", timeout=5000)
            page.locator('span.aru-input-checkbox__checkmark').first.click(force=True)
            page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
            page.locator('.cdk-overlay-pane button:has-text("Elimina")').first.wait_for(state="visible", timeout=5000)
            page.locator('.cdk-overlay-pane button:has-text("Elimina")').first.click()
        except Exception:
            pass
