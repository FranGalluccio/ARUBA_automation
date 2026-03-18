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


def test_evento_tutto_il_giorno(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    try:
        time.sleep(1)
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)

        # Crea nuovo evento
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        time.sleep(1)
        page.get_by_placeholder("Inserisci un titolo").fill("evento tutto il giorno playwright")

        # Attiva flag "Giornata intera" - può essere checkbox, label o toggle
        allday_clicked = False
        for selector in [
            'button[title="Giornata intera"]',
            'input[type="checkbox"][name*="allday"]',
            'input[type="checkbox"][name*="full"]',
            'label:has-text("Giornata intera")',
            'aru-input-choice:has-text("Giornata intera")',
            '[class*="allday"]',
            '[class*="all-day"]',
            '[class*="full-day"]',
            'input[type="checkbox"]',  # first checkbox in the dialog
        ]:
            try:
                el = page.locator(selector).first
                if el.count() > 0:
                    el.click(force=True)
                    allday_clicked = True
                    time.sleep(0.5)
                    break
            except Exception:
                pass

        if allday_clicked:
            print("All-day toggle clicked")
            page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_08_allday_{datetime.now():%H-%M-%S}.png"))

        # Salva
        page.get_by_role("button", name="Salva").click()
        time.sleep(1)

        # Verifica che l'evento sia presente nel calendario
        page.locator('a, [class*="event"]').filter(has_text="evento tutto il giorno playwright").first.wait_for(
            state="visible", timeout=8000
        )

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    finally:
        # Cleanup: elimina l'evento (eseguito anche in caso di fallimento)
        try:
            page.get_by_role("button", name="Calendario").click()
            time.sleep(1)
            page.get_by_role("button", name="Eventi").click()
            time.sleep(2)
            while True:
                ev = page.locator('a, [class*="event"]').filter(has_text="evento tutto il giorno playwright").first
                if ev.count() == 0:
                    break
                ev.click()
                time.sleep(2)
                try:
                    page.locator('button:has(aru-symbol[title="Elimina"]), button[title="Elimina"], aru-button[title="Elimina"]').first.click(timeout=3000)
                except Exception:
                    page.get_by_role("button", name="Elimina").first.click()
                time.sleep(1)
                try:
                    page.get_by_role("button", name="Sì").first.click(timeout=2000)
                    time.sleep(1)
                except Exception:
                    pass
                time.sleep(1)
        except Exception:
            pass
