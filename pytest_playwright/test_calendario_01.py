import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper
from playwright.sync_api import sync_playwright, expect
from datetime import datetime
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

    time.sleep(1)

    # Crea nuovo evento ricorrente
    page.get_by_role("button", name="Calendario").click()
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
    #page.get_by_role("textbox", name="input date").first.click()
    #page.get_by_text("Gennaio 2026").click()
    #page.locator("#event-dialog").get_by_text("Gennaio").click()
    #page.locator("#event-dialog").get_by_text("28").click()
    page.get_by_role("combobox", name="Non ripetere").click()
    page.get_by_role("button", name="Personalizza...").click()
    page.get_by_role("radio", name="Dopo").check()
    time.sleep(1)
    page.get_by_role("dialog") \
    .filter(has_text="Personalizza") \
    .filter(has=page.locator("button", has_text="Salva")) \
    .last \
    .get_by_role("button", name="Salva") \
    .click()

    time.sleep(1)
    page.get_by_role("button", name="Salva").click()

    try:
        time.sleep(1)
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        time.sleep(1)
    finally:
        # Cleanup: elimina evento ricorrente (eseguito anche in caso di fallimento)
        try:
            page.get_by_role("button", name="Calendario").click()
            time.sleep(1)
            page.get_by_role("button", name="Eventi").click(force=True)
            time.sleep(2)
            for _ in range(20):
                ev = page.get_by_text("nuovo evento ricorrente playwright", exact=False).first
                if ev.count() == 0:
                    break
                ev.click()
                time.sleep(2)
                # 1. Apri menu 3 puntini
                try:
                    page.locator('button:has(aru-symbol[symbol="dots-separator"])').first.click(timeout=3000)
                    time.sleep(1)
                except Exception:
                    pass
                # 2. Annulla evento dal menu
                try:
                    page.locator('button[title="Annulla evento"]').first.click(timeout=3000)
                    time.sleep(1)
                except Exception:
                    pass
                # 3. Dialog ricorrente: seleziona "Tutti gli eventi" → Ok
                try:
                    page.get_by_role("radio", name="Tutti gli eventi").check(timeout=2000)
                    time.sleep(0.5)
                    page.get_by_role("button", name="Ok").first.click(timeout=2000)
                    time.sleep(1)
                except Exception:
                    pass
                # 3. Dialog conferma: Elimina
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