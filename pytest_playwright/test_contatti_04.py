import os
import csv
import json
from datetime import datetime
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper
import time

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso rubrica da importare ---
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_rubrica_rel = os.environ.get("RUBRICA_IMPORT", config.get("rubrica_import", "dati_test/rubrica.csv"))
file_rubrica = os.path.join(_project_root, _rubrica_rel) if not os.path.isabs(_rubrica_rel) else _rubrica_rel


def _get_imported_names():
    """Leggi i nomi (firstname + lastname) dal CSV di rubrica per il cleanup."""
    names = []
    try:
        with open(file_rubrica, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                fname = row.get("firstname", "").strip()
                lname = row.get("lastname", "").strip()
                if fname or lname:
                    names.append(f"{fname} {lname}".strip())
    except Exception:
        pass
    return names


def test_importa_contatti(page):
    """Importa la rubrica CSV nella PEC"""
    # Login PEC
    LoginPec(page).login_pec(config)

    # Apri la rubrica
    page.locator("#contacts").click()
    page.wait_for_timeout(1000)

    try:
        # Clicca sul bottone "Importa" per aprire il dialog di import
        page.locator('span[aria-label="Importa"]').click()
        page.wait_for_timeout(1000)

        # Carica il file CSV da importare
        file_input = page.locator('input[type="file"]')
        file_input.set_input_files(file_rubrica)
        page.wait_for_timeout(1000)

        # Dopo il caricamento del file, clicca sul pulsante Importa per confermare
        page.get_by_role("button", name="Importa", exact=True).click()
        page.wait_for_timeout(2000)

        time.sleep(1)
        # Verifica toast di conferma invio
        toast = page.locator("div.aru-toast__message").first
        assert toast.is_visible()
        assert "I contatti sono stati importati." in toast.text_content()

        # Screenshot finale per debug
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot import rubrica salvato in: {screenshot_path}")

    finally:
        # Cleanup: elimina i contatti importati
        imported_names = _get_imported_names()
        for name in imported_names:
            try:
                search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
                search.click(click_count=3)
                search.fill(name)
                time.sleep(1)
                r = page.locator('div.frame-record-desktop').filter(has_text=name).first
                if r.count() > 0:
                    r.hover()
                    r.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
                    time.sleep(1)
                    page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
                    try:
                        page.locator('button[title="Si"], button:has-text("Sì")').first.click(timeout=2000)
                    except Exception:
                        pass
                    time.sleep(1)
            except Exception:
                pass
