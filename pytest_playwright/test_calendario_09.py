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


def test_evento_con_promemoria(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.get_by_role("button", name="Calendario").click()
    time.sleep(1)

    # Crea nuovo evento
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    time.sleep(1)
    page.get_by_placeholder("Inserisci un titolo").fill("evento con promemoria playwright")

    # Aggiungi promemoria - apre un dialog con "Salva" e "Annulla"
    page.locator('button[title="Aggiungi promemoria"]').click()
    time.sleep(1)

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
        time.sleep(0.5)
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
    time.sleep(1)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_after_dialog_save_{datetime.now():%H-%M-%S}.png"))

    # Aspetta che il dialog si chiuda
    try:
        page.locator('.cdk-overlay-backdrop').wait_for(state="hidden", timeout=8000)
    except Exception:
        pass
    time.sleep(2)

    # Ora salva l'evento (il "Salva" nel pannello laterale del form evento)
    page.get_by_role("button", name="Salva").first.click(force=True)
    # Attendi la toast di conferma salvataggio (scompare rapidamente)
    try:
        page.locator("div.aru-toast__message").wait_for(state="visible", timeout=8000)
    except Exception:
        time.sleep(3)
    time.sleep(1)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_after_event_save_{datetime.now():%H-%M-%S}.png"))

    # Vai alla vista "Events" per trovare l'evento più facilmente
    try:
        page.get_by_role("button", name="Eventi").click(force=True)
        time.sleep(5)
    except Exception:
        pass

    # Verifica che l'evento sia presente
    evento_trovato = page.get_by_text("evento con promemoria playwright", exact=False).count() > 0

    assert evento_trovato, "L'evento con promemoria non è stato trovato nel calendario"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: elimina l'evento
    try:
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)
        page.get_by_role("button", name="Eventi").click()
        time.sleep(2)
        while True:
            ev = page.locator('a, [class*="event"]').filter(has_text="evento con promemoria playwright").first
            if ev.count() == 0:
                break
            ev.click()
            time.sleep(1)
            page.get_by_role("button", name="Annulla evento").first.click()
            time.sleep(1)
            page.get_by_role("button", name="Elimina").first.click()
            time.sleep(2)
    except Exception:
        pass
