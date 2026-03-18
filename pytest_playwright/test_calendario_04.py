import os
import json
from playwright.sync_api import Page
from base_pec import LoginPec
import time
from datetime import datetime



# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


# --- Carica config.json ---
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_FILE = os.path.join(BASE_DIR, "config.json")

with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)


# --- Path file calendario (.ics) ---
FILE_ICS = os.path.abspath(config["calendario_import"])
assert os.path.exists(FILE_ICS), f"File ICS non trovato: {FILE_ICS}"


def test_import_export_calendario(page: Page):
    # --- Login PEC ---
    LoginPec(page).login_pec(config)
    page.wait_for_load_state("networkidle")

    try:
        # --- Vai al calendario ---
        page.get_by_role("button", name="Calendario").click()
        page.wait_for_load_state("networkidle")

        # --- Crea nuovo evento ---
        page.get_by_role("button", name="Nuovo evento").click()
        page.get_by_placeholder("Inserisci un titolo").fill("import export calendario")
        page.get_by_role("button", name="Salva").click()

        time.sleep(1)

        # --- Importa calendario (.ics) ---
        page.get_by_role("button", name="Importa").first.click()
        time.sleep(1)
        page.locator("#hidden_input").set_input_files(FILE_ICS)
        time.sleep(1)

        # Conferma import: prende l'ultimo "Importa" visibile (quello nel dialog, non la sidebar)
        try:
            all_importa = page.get_by_role("button", name="Importa").all()
            for btn in reversed(all_importa):
                try:
                    if btn.is_visible():
                        btn.click()
                        break
                except Exception:
                    pass
        except Exception:
            pass

        time.sleep(2)

        # Percorso screenshot dinamico
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)

        print(f"Screenshot salvato in: {screenshot_path}")

        # --- Esporta calendario ---
        export_triggered = False
        # Step 1: apri dialog esporta
        page.get_by_role("button", name="Esporta").first.click(timeout=5000)
        time.sleep(1)
        # Step 2: conferma esporta nel dialog (se c'è) oppure il download parte già
        try:
            with page.expect_download(timeout=8000) as download_info:
                try:
                    page.get_by_role("button", name="Esporta").last.click(timeout=3000)
                except Exception:
                    pass
            download_info.value
            export_triggered = True
        except Exception:
            # Fallback: click destro sul calendario in sidebar
            try:
                with page.expect_download(timeout=8000) as download_info2:
                    page.locator('[aria-label="Personale"], [title="Personale"], input[type="checkbox"]').first.click(button="right")
                    time.sleep(1)
                    page.get_by_role("menuitem", name="Esporta").click()
                    time.sleep(1)
                download_info2.value
                export_triggered = True
            except Exception:
                pass

        # Check for success toast if no download was detected
        if not export_triggered:
            toast_visible = page.locator(
                'div.aru-toast__message, [class*="toast"], [class*="success"]'
            ).count() > 0
            assert toast_visible, (
                "L'esportazione del calendario non ha prodotto né un download né un toast di conferma"
            )

    finally:
        # --- Cleanup: elimina eventi (eseguito anche in caso di fallimento) ---
        try:
            page.get_by_role("button", name="Calendario").click()
            time.sleep(1)
            page.get_by_role("button", name="Eventi").click()
            time.sleep(2)
            while True:
                ev = page.locator('a, [class*="event"]').filter(has_text="import export calendario").first
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
