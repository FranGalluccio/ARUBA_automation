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


def test_scrivi_email_da_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.click("#contacts")
    time.sleep(1)

    ts = int(time.time())
    nome_test = f"EmailTest{ts}"
    email_contatto = f"emailtest_{ts}@pec.it"

    try:
        # Crea un contatto con email per il test
        page.get_by_role("button", name="Nuovo").click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill(nome_test)
        page.get_by_placeholder("Inserisci cognome").fill("Contact")
        page.get_by_placeholder("Inserisci email").fill(email_contatto)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)

        # Cerca il contatto
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill(nome_test)
        time.sleep(1)

        row = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
        row.wait_for(state="visible", timeout=8000)

        # Hover per rivelare i pulsanti di azione
        row.hover()
        time.sleep(1)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_09_hover_{datetime.now():%H-%M-%S}.png"))

        def compose_open():
            try:
                crea_dialog = page.locator('text="Crea contatto, gruppo, rubrica"').first
                if crea_dialog.is_visible():
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
            except Exception:
                pass
            return page.locator('span[title="Invia"]').count() > 0

        email_clicked = False

        mailto_link = row.locator('a[href*="mailto"], a[href*="pec"]').first
        try:
            if mailto_link.count() > 0:
                mailto_link.click(force=True)
                time.sleep(1)
                email_clicked = compose_open()
        except Exception:
            pass
        if not email_clicked:
            action_btns = row.locator('webmail-actions-buttons aru-button').all()
            for btn in action_btns:
                try:
                    btn.click(force=True)
                    time.sleep(1)
                    if compose_open():
                        email_clicked = True
                        break
                except Exception:
                    pass
        if not email_clicked:
            try:
                page.locator('button[title="Scrivi email"], button[title*="email"], button[title*="mail"]').first.click(timeout=3000)
                time.sleep(1)
                email_clicked = compose_open()
            except Exception:
                pass
        if not email_clicked:
            try:
                row.hover()
                time.sleep(1)
                row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
                time.sleep(1)
                page.locator('button[title="Scrivi email"], button[title*="Scrivi"]').first.click(timeout=3000)
                time.sleep(1)
                email_clicked = compose_open()
            except Exception:
                pass

        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        time.sleep(1)
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        assert email_clicked, "Impossibile aprire la finestra di composizione email dal contatto"

        # Chiudi il dialog senza inviare
        try:
            page.locator('button[title="Chiudi"]').last.click(force=True)
            time.sleep(1)
            page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
        except Exception:
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass
        time.sleep(1)

    finally:
        # Cleanup: elimina il contatto (eseguito anche in caso di fallimento)
        try:
            page.click("#contacts")
            time.sleep(1)
            search2 = page.locator('input[placeholder*="Cerca tra i contatti"]').first
            search2.click()
            search2.fill(nome_test)
            time.sleep(1)
            r = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
            if r.count() > 0:
                r.hover()
                r.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
                time.sleep(1)
                page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
                page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
                time.sleep(1)
        except Exception:
            pass
