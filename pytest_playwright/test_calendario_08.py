import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, elimina_evento_pec
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

    ts = int(time.time())
    titolo_evento = f"evento tutto il giorno playwright {ts}"

    try:
        page.locator('[aria-label="Calendario"], [aria-label="Calendrier"], button[title="Calendario"], button[title="Calendrier"]').first.click()

        # Crea nuovo evento
        page.locator('button:has-text("Nuovo evento"), button:has-text("Nouvel événement")').first.click()
        titolo_input = page.locator('input[placeholder*=" titolo"], input[placeholder*=" titre"]').first
        titolo_input.wait_for(state="visible", timeout=8000)
        titolo_input.fill(titolo_evento)

        # Attiva flag "Giornata intera" - può essere checkbox, label o toggle
        allday_clicked = False
        for selector in [
            'button[title="Giornata intera"], button[title="Toute la journée"]',
            'input[type="checkbox"][name*="allday"]',
            'input[type="checkbox"][name*="full"]',
            'label:has-text("Giornata intera"), label:has-text("Toute la journée")',
            'aru-input-choice:has-text("Giornata intera"), aru-input-choice:has-text("Toute la journée")',
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
                    page.wait_for_timeout(300)
                    break
            except Exception:
                pass

        if allday_clicked:
            print("All-day toggle clicked")
            page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_08_allday_{datetime.now():%H-%M-%S}.png"))

        # Salva
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

        # Verifica che l'evento sia presente nel calendario
        page.locator('a, [class*="event"]').filter(has_text=titolo_evento).first.wait_for(
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
        elimina_evento_pec(page, "evento tutto il giorno playwright")
