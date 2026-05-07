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
    page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=10000)

    ts = int(time.time())
    nome_test = f"EmailTest{ts}"
    email_contatto = f"emailtest_{ts}@{TEST_EMAIL_DOMAIN}"

    try:
        # Crea un contatto con email per il test
        page.locator('button:has-text("Nuovo"), button:has-text("Nouveau")').first.click()
        page.wait_for_timeout(1500)
        page.locator('button:has-text("Procedi"), button:has-text("Procéder"), button:has-text("Continuer"), button:has-text("Suivant")').first.click(force=True)
        page.wait_for_timeout(1000)
        page.locator('input[placeholder*=" nome"], input[placeholder*="rénom"]').first.fill(nome_test, force=True)
        page.locator('input[placeholder*="cognome"], input[placeholder*="famille"]').first.fill("Contact", force=True)
        page.locator('input[placeholder*="email"]').first.fill(email_contatto, force=True)
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click(force=True)

        # Cerca il contatto
        search = page.locator('input[placeholder*="Cerca tra i contatti"], input[placeholder*="contacts"]').first
        search.click()
        search.fill(nome_test)

        row = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
        row.wait_for(state="visible", timeout=8000)

        # Hover per rivelare i pulsanti di azione
        row.hover()
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_09_hover_{datetime.now():%H-%M-%S}.png"))

        def compose_open():
            page.wait_for_timeout(1000)
            return page.evaluate("""() => {
                if (document.querySelector('span[title="Invia"], span[title="Envoyer"]')) return true;
                for (const btn of document.querySelectorAll('button')) {
                    const t = btn.textContent.trim();
                    if (t === 'Envoyer' || t === 'Invia') return true;
                }
                const html = document.body.innerHTML || '';
                if (html.includes('Nouveau message') || html.includes('Nuovo messaggio')) return true;
                for (const el of document.querySelectorAll('*')) {
                    if (el.shadowRoot) {
                        const sh = el.shadowRoot;
                        if (sh.innerHTML.includes('Nouveau message') || sh.innerHTML.includes('Nuovo messaggio')) return true;
                        for (const b of sh.querySelectorAll('button')) {
                            const t = b.textContent.trim();
                            if (t === 'Envoyer' || t === 'Invia') return true;
                        }
                    }
                }
                return false;
            }""")

        email_clicked = False

        # Attempt 1: click the first action icon (envelope) visible on row hover
        row.hover()
        page.wait_for_timeout(500)
        try:
            action_icon = row.locator('aru-button, button').filter(
                has=page.locator('aru-symbol')
            ).first
            action_icon.click(force=True)
            page.wait_for_timeout(2000)
            email_clicked = compose_open()
        except Exception:
            pass

        # Attempt 2: iterate webmail-actions-buttons or generic action buttons
        if not email_clicked:
            for btn_sel in ['webmail-actions-buttons aru-button', 'aru-button']:
                try:
                    btns = row.locator(btn_sel).all()
                    for btn in btns[:4]:
                        btn.click(force=True)
                        page.wait_for_timeout(2000)
                        if compose_open():
                            email_clicked = True
                            break
                    if email_clicked:
                        break
                except Exception:
                    pass

        # Attempt 3: mailto link
        if not email_clicked:
            try:
                mailto_link = row.locator('a[href*="mailto"], a[href*="pec"]').first
                if mailto_link.count() > 0:
                    mailto_link.click(force=True)
                    page.wait_for_timeout(2000)
                    email_clicked = compose_open()
            except Exception:
                pass

        # Attempt 4: toolbar button after checkbox selection
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

        # Final check after longer wait (compose might open slowly)
        if not email_clicked:
            page.wait_for_timeout(3000)
            email_clicked = compose_open()

        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        assert email_clicked, "Impossibile aprire la finestra di composizione email dal contatto"

        # Chiudi il dialog senza inviare
        try:
            page.locator('button[title="Chiudi"], [title="Fermer"], button[title="Fermer"]').last.click(force=True)
            page.wait_for_timeout(500)
            page.locator('button[title="Si"], button[title="Oui"], button:has-text("Sì")').first.click(timeout=2000)
        except Exception:
            try:
                page.keyboard.press("Escape")
            except Exception:
                pass

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
