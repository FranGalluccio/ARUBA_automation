import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper
from playwright.sync_api import sync_playwright, expect
import locale

# Forza locale italiana (necessaria per mesi in italiano)
locale.setlocale(locale.LC_TIME, "it_IT")

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


def test_creazione_evento_ricorrente(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"nuovo evento ricorrente playwright {ts}"

    # Crea nuovo evento ricorrente
    page.get_by_role("button", name="Calendario").click()
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
    page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
    page.get_by_role("combobox", name="Non ripetere").click()
    page.get_by_role("button", name="Personalizza...").click()
    page.get_by_role("radio", name="Dopo").check()
    page.wait_for_timeout(500)
    page.get_by_role("dialog") \
    .filter(has_text="Personalizza") \
    .filter(has=page.locator("button", has_text="Salva")) \
    .last \
    .get_by_role("button", name="Salva") \
    .click()

    page.wait_for_timeout(500)
    page.get_by_role("button", name="Salva").click()

    try:
        page.wait_for_timeout(1000)
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
    finally:
        # Cleanup: elimina evento ricorrente (eseguito anche in caso di fallimento)
        try:
            page.get_by_role("button", name="Calendario").click()
            page.get_by_role("button", name="Eventi").wait_for(state="visible", timeout=5000)
            page.get_by_role("button", name="Eventi").click(force=True)
            page.wait_for_timeout(1500)
            for _ in range(20):
                ev = page.get_by_text("nuovo evento ricorrente playwright", exact=False).first
                if ev.count() == 0:
                    break
                ev.click()
                page.wait_for_timeout(1500)
                # 1. Apri menu 3 puntini
                try:
                    page.locator('button:has(aru-symbol[symbol="dots-separator"])').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # 2. Annulla evento dal menu
                try:
                    page.locator('button[title="Annulla evento"]').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # 3. Dialog ricorrente: seleziona "Tutti gli eventi" → Ok
                try:
                    page.get_by_role("radio", name="Tutti gli eventi").check(timeout=2000)
                    page.wait_for_timeout(300)
                    page.get_by_role("button", name="Ok").first.click(timeout=2000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # 4. Dialog conferma: Elimina
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
