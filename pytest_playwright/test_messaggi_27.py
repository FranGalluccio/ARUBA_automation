import os
import json
import time
from datetime import datetime
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

TEST_EXTERNAL_EMAIL = config.get("test_external_email", "test@gmail.com")


def test_anomalia_invio_non_pec(page):
    """Verifica che l'invio a un indirizzo non-PEC generi una ricevuta di anomalia."""
    LoginPec(page).login_pec(config)

    # Dismiss any CDK backdrop
    if page.locator('.cdk-overlay-backdrop').is_visible():
        for _ in range(3):
            if not page.locator('.cdk-overlay-backdrop').is_visible():
                break
            try:
                btn = page.locator('button:has-text("Ricordarmelo"), button:has-text("Plus tard"), button:has-text("Chiudi"), button:has-text("Non ora"), button:has-text("Pas maintenant")').first
                if btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(300)
                    continue
                page.locator('.cdk-overlay-pane').last.locator('button').last.click(force=True)
                page.wait_for_timeout(300)
            except Exception:
                break

    ts = int(time.time())
    oggetto = f"Test anomalia non-PEC {ts}"

    # Apri nuovo messaggio con destinatario non-PEC
    page.locator("button:has-text('Nuovo messaggio'), button:has-text('Nouveau message')").click(force=True)
    try:
        page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").fill(TEST_EXTERNAL_EMAIL, timeout=2000)
    except Exception:
        page.locator('input[aria-label="input field"]').click()
        page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").fill(TEST_EXTERNAL_EMAIL)

    page.locator('input[aria-label="input field"]').fill(oggetto)
    page.locator("div[contenteditable='true']").fill("Test automatico anomalia PEC - destinatario non-PEC")

    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Attendi eventuale avviso di anomalia nella UI
    page.wait_for_timeout(5000)

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_27___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    # Cerca avviso/errore sincrono nella UI: alert, toast, testo "anomalia"
    avviso_ui = page.locator('[role="alert"], .alert, aru-toast, .error-message').first
    has_anomalia_text = page.get_by_text("anomalia", exact=False).first.is_visible()

    # Se la UI mostra un avviso sincrono il test passa subito
    if avviso_ui.is_visible() or has_anomalia_text:
        print("Avviso anomalia mostrato nella UI.")
        print(f"Screenshot salvato in: {screenshot_path}")
        return

    # Altrimenti controlla la inbox: la ricevuta di anomalia arriva come messaggio
    page.locator("#messages").locator('[aria-label="Messaggi"], [aria-label="Messages"]').first.click()
    page.wait_for_timeout(3000)
    page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"], button[aria-label="Aggiorna"], button[aria-label="Actualiser"]').click()
    page.wait_for_timeout(3000)

    frames = page.locator('div.frame-record-desktop').all()
    found_anomalia = False
    for frame in frames:
        try:
            text = frame.inner_text().lower()
            if "anomalia" in text or "non-pec" in text or "non pec" in text:
                found_anomalia = True
                break
        except Exception:
            pass

    page.screenshot(path=screenshot_path, full_page=True)

    assert found_anomalia, (
        f"Ricevuta di Anomalia non trovata dopo invio a indirizzo non-PEC (oggetto: '{oggetto}'). "
        "Il sistema PEC dovrebbe notificare quando il destinatario non è una casella PEC certificata."
    )
    print(f"Screenshot salvato in: {screenshot_path}")
