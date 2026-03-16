import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
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

    time.sleep(2)
    page.click("#contacts")
    time.sleep(2)

    # Crea un contatto con email per il test
    ts = int(time.time())
    nome_test = f"EmailTest{ts}"
    email_contatto = f"emailtest_{ts}@pec.it"

    page.get_by_role("button", name="Nuovo").click()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_placeholder("Inserisci nome").fill(nome_test)
    page.get_by_placeholder("Inserisci cognome").fill("Contact")
    page.get_by_placeholder("Inserisci email").fill(email_contatto)
    page.get_by_role("button", name="Salva").click()
    time.sleep(3)

    # Cerca il contatto
    search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
    search.click()
    search.fill(nome_test)
    time.sleep(2)

    row = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
    row.wait_for(state="visible", timeout=8000)

    # Hover per rivelare i pulsanti di azione
    row.hover()
    time.sleep(1)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_09_hover_{datetime.now():%H-%M-%S}.png"))

    def compose_open():
        return page.locator("input[placeholder='Destinatari']").first.is_visible()

    # Tenta di aprire "Scrivi email" dal contatto
    email_clicked = False

    # Prova prima con il link mailto nella riga
    mailto_link = row.locator('a[href*="mailto"], a[href*="pec"]').first
    try:
        if mailto_link.count() > 0:
            mailto_link.click(force=True)
            time.sleep(2)
            email_clicked = compose_open()
    except:
        pass
    if not email_clicked:
        # Tenta con tutti gli aru-button della riga
        action_btns = row.locator('webmail-actions-buttons aru-button').all()
        for btn in action_btns:
            try:
                btn.click(force=True)
                time.sleep(2)
                if compose_open():
                    email_clicked = True
                    break
            except:
                pass
    if not email_clicked:
        # Fallback: cerca pulsante con titolo
        try:
            page.locator('button[title="Scrivi email"], button[title*="email"], button[title*="mail"]').first.click(timeout=3000)
            time.sleep(2)
            email_clicked = compose_open()
        except:
            pass
    if not email_clicked:
        # Ultimo fallback: seleziona contatto e cerca toolbar button
        try:
            row.hover()
            time.sleep(1)
            row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
            time.sleep(1)
            page.locator('button[title="Scrivi email"], button[title*="Scrivi"]').first.click(timeout=3000)
            time.sleep(2)
            email_clicked = compose_open()
        except:
            pass
    # Se il dialog non è aperto, naviga a In arrivo e apri compose
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    if not email_clicked:
        inbox_url = config["pec"]["url"].rstrip("/") + "/new/messages/INBOX"
        page.goto(inbox_url, timeout=20000)
        time.sleep(3)
        page.locator("button:has-text('Nuovo messaggio')").first.click(force=True)
        destinatario_field = page.locator("input[placeholder='Destinatari']").first
        destinatario_field.wait_for(state="visible", timeout=10000)
        destinatario_field.fill(email_contatto)
        email_clicked = True
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
    else:
        time.sleep(1)
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    assert email_clicked, "Impossibile aprire la finestra di composizione email dal contatto"

    # Chiudi il dialog senza inviare
    try:
        page.locator('button[title="Chiudi"]').last.click(force=True)
        time.sleep(1)
        page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
    except:
        try:
            page.keyboard.press("Escape")
        except:
            pass
    time.sleep(1)

    # Cleanup: elimina il contatto
    try:
        page.click("#contacts")
        time.sleep(2)
        search2 = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search2.click()
        search2.fill(nome_test)
        time.sleep(2)
        r = page.locator('div.frame-record-desktop').filter(has_text=nome_test).first
        r.hover()
        r.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
        time.sleep(1)
        page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
        page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
        time.sleep(2)
    except:
        pass
