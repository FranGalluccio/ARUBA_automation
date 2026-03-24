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


def test_evento_con_promemoria(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"evento con promemoria playwright {ts}"

    try:
        page.get_by_role("button", name="Calendario").click()

        # Crea nuovo evento
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)

        # Aggiungi promemoria - apre un dialog con "Salva" e "Annulla"
        page.locator('button[title="Aggiungi promemoria"]').click()
        page.wait_for_timeout(500)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_reminder_{datetime.now():%H-%M-%S}.png"))

        # Verifica che il dialog promemoria si sia aperto
        promemoria_dialog = page.locator('[role="dialog"], .cdk-overlay-pane, [class*="dialog"]').first
        try:
            promemoria_dialog.wait_for(state="visible", timeout=5000)
            print("Dialog promemoria aperto")
        except Exception:
            pass

        # Conta aru-input-select nella dialog (verifica che il promemoria sia configurabile)
        count_after = page.locator('aru-input-select').count()
        print(f"aru-input-select after adding promemoria: {count_after}")
        assert count_after > 0, "Nessun elemento di promemoria trovato"

        # Inserisci l'email nel campo "Invia email a"
        try:
            page.locator('input[placeholder="Indirizzo email"]').first.fill(config["pec"]["username"])
            page.wait_for_timeout(300)
        except Exception:
            pass

        # Salva il promemoria nella dialog - usa l'ultimo pane (topmost overlay)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_before_dialog_save_{datetime.now():%H-%M-%S}.png"))
        dialog_salva = page.locator('.cdk-overlay-pane').last.locator('button:has-text("Salva")').first
        try:
            dialog_salva.wait_for(state="visible", timeout=5000)
            dialog_salva.click()
        except Exception:
            page.locator('button:has-text("Salva")').last.click(force=True)
        page.wait_for_timeout(500)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_after_dialog_save_{datetime.now():%H-%M-%S}.png"))

        # Aspetta che il dialog si chiuda
        try:
            page.locator('.cdk-overlay-backdrop').wait_for(state="hidden", timeout=8000)
        except Exception:
            pass
        page.wait_for_timeout(1000)

        # Ora salva l'evento (il "Salva" nel pannello laterale del form evento)
        page.get_by_role("button", name="Salva").first.click(force=True)
        # Attendi la toast di conferma salvataggio (scompare rapidamente)
        try:
            page.locator("div.aru-toast__message").wait_for(state="visible", timeout=10000)
        except Exception:
            page.wait_for_timeout(5000)
        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_after_event_save_{datetime.now():%H-%M-%S}.png"))

        # Vai alla vista "Events" per trovare l'evento più facilmente
        try:
            page.get_by_role("button", name="Calendario").click()
            page.get_by_role("button", name="Eventi").wait_for(state="visible", timeout=5000)
            page.get_by_role("button", name="Eventi").click(force=True)
            page.wait_for_timeout(8000)
        except Exception:
            pass

        # Verifica che l'evento sia presente nella vista Events
        evento_trovato = page.get_by_text(titolo_evento, exact=False).count() > 0

        # Fallback: cerca via barra di ricerca del calendario
        if not evento_trovato:
            try:
                search = page.locator(
                    'input[placeholder*="Cerca nel calendario"], '
                    'input[placeholder*="Cerca calendario"], '
                    'input[placeholder*="Cerca"]'
                ).first
                search.wait_for(state="visible", timeout=5000)
                search.click()
                search.fill(titolo_evento)
                page.keyboard.press("Enter")
                for _ in range(10):
                    if page.get_by_text(titolo_evento, exact=False).count() > 0:
                        evento_trovato = True
                        break
                    page.wait_for_timeout(1000)
            except Exception:
                pass

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        assert evento_trovato, f"L'evento con promemoria '{titolo_evento}' non è stato trovato nel calendario"

    finally:
        elimina_evento_pec(page, "evento con promemoria playwright")
