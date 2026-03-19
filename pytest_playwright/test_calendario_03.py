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

# --- Percorso allegato dinamico ---
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


def test_creazione_invio_evento(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"evento test auto invito {ts}"

    try:
        time.sleep(1)

        # Crea nuovo evento
        page.get_by_role("button", name="Calendario").click()
        page.locator("button").filter(has_text="Nuovo evento").click()
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)
        page.locator("a").filter(has_text=titolo_evento).first.wait_for(state="visible", timeout=15000)
        page.locator("a").filter(has_text=titolo_evento).first.click()
        # Modifica evento
        time.sleep(1)
        page.get_by_role("button", name="Modifica").click()
        time.sleep(1)
        page.locator('input[aria-label="input chosen"]').nth(1).fill(config["destinatari"]["destinatario_principale"])
        time.sleep(1)
        page.get_by_role("textbox", name="input chosen").press("Enter")
        time.sleep(2)
        page.get_by_role("button", name="Salva").click()
        time.sleep(2)
        try:
            page.get_by_role("button", name="Invia").first.click(timeout=10000)
        except Exception:
            pass
        # Vai alla posta in arrivo
        page.locator("#messages").get_by_label("Messaggi").click()
        time.sleep(5)
        # Aggiorna la posta
        page.locator('aru-symbol[title="Aggiorna"]').click()
        time.sleep(2)
        # Aspetta che almeno un record sia visibile
        page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

        # Clicca sul primo record
        page.locator('div.frame-record-desktop').first.click()

        # Aspetta che il contenuto della mail sia visibile
        page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

        # Percorso screenshot dinamico
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    finally:
        # Cleanup: elimina evento (eseguito anche in caso di fallimento)
        try:
            page.get_by_role("button", name="Calendario").click()
            time.sleep(1)
            page.get_by_role("button", name="Eventi").click(force=True)
            time.sleep(2)
            for _ in range(5):
                ev = page.get_by_text(titolo_evento, exact=False).first
                if ev.count() == 0:
                    break
                ev.click()
                time.sleep(2)
                try:
                    page.get_by_role("button", name="Annulla evento").first.click(timeout=3000)
                    time.sleep(1)
                except Exception:
                    pass
                try:
                    page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                    time.sleep(2)
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                except Exception:
                    pass
                page.get_by_role("button", name="Eventi").click(force=True)
                time.sleep(2)
        except Exception:
            pass
