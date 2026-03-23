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
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_creazione_invio_evento(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"evento test auto invito {ts}"

    try:
        # Crea nuovo evento
        page.get_by_role("button", name="Calendario").click()
        page.locator("button").filter(has_text="Nuovo evento").click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
        page.get_by_role("button", name="Salva").click()
        page.locator("a").filter(has_text=titolo_evento).first.wait_for(state="visible", timeout=15000)
        page.locator("a").filter(has_text=titolo_evento).first.click()
        # Modifica evento
        page.get_by_role("button", name="Modifica").wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Modifica").click()
        page.locator('input[aria-label="input chosen"]').nth(1).wait_for(state="visible", timeout=5000)
        page.locator('input[aria-label="input chosen"]').nth(1).fill(config["destinatari"]["destinatario_principale"])
        page.get_by_role("textbox", name="input chosen").press("Enter")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="Salva").click()
        page.wait_for_timeout(1000)
        try:
            page.get_by_role("button", name="Invia").first.click(timeout=10000)
        except Exception:
            pass
        # Vai alla posta in arrivo
        page.locator("#messages").get_by_label("Messaggi").click()
        page.wait_for_timeout(5000)
        # Aggiorna la posta
        page.locator('aru-symbol[title="Aggiorna"]').click()
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
        # Cleanup: annulla evento con invitati tramite 3 puntini → Annulla evento
        try:
            page.get_by_role("button", name="Calendario").click()
            page.get_by_role("button", name="Eventi").wait_for(state="visible", timeout=5000)
            page.get_by_role("button", name="Eventi").click(force=True)
            page.wait_for_timeout(1500)
            for _ in range(20):
                ev = page.get_by_text("evento test auto invito", exact=False).first
                if ev.count() == 0:
                    break
                ev.click()
                page.wait_for_timeout(1500)
                # Clicca i 3 puntini nell'header del popup evento
                try:
                    page.locator('button:has(aru-symbol[symbol="dots-separator"])').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # Clicca "Annulla evento" dal menu a tendina
                try:
                    page.locator('button[title="Annulla evento"]').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # Eventuale conferma
                try:
                    page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                    page.wait_for_timeout(1500)
                    try:
                        toast = page.locator("div.aru-toast__message").first
                        if toast.is_visible():
                            print(f"Toast eliminazione: {toast.text_content()}")
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                except Exception:
                    pass
                page.get_by_role("button", name="Eventi").click(force=True)
                page.wait_for_timeout(1500)
        except Exception:
            pass
