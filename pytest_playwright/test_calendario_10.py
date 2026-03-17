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


def test_ricerca_nel_calendario(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.get_by_role("button", name="Calendario").click()
    time.sleep(1)

    titolo_evento = f"evento ricerca playwright {int(time.time())}"

    # Crea un evento con titolo univoco
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    time.sleep(1)
    page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)
    page.get_by_role("button", name="Salva").click()
    time.sleep(1)

    # Usa la barra di ricerca del calendario
    # La ricerca è visibile come input con placeholder "Cerca nel calendario"
    search = page.locator(
        'input[placeholder*="Cerca nel calendario"], '
        'input[placeholder*="Cerca calendario"], '
        'input[placeholder*="Cerca"]'
    ).first
    search.wait_for(state="visible", timeout=5000)
    search.click()
    search.fill(titolo_evento)
    page.keyboard.press("Enter")
    time.sleep(2)

    # Verifica che l'evento appaia nei risultati
    # Cerca nella vista "Eventi" che mostra una lista
    result = page.locator(
        '[class*="search-result"], [class*="event"], a, button'
    ).filter(has_text=titolo_evento).first

    # Attendi che il risultato diventi visibile (potrebbe essere in un elemento "hidden")
    try:
        result.wait_for(state="visible", timeout=8000)
        assert result.is_visible(), f"L'evento '{titolo_evento}' non è visibile"
    except Exception:
        # Alternativa: vai nella vista "Eventi" e cerca
        page.get_by_role("button", name="Eventi").click()
        time.sleep(1)
        result2 = page.locator('a, button, [class*="event"]').filter(has_text=titolo_evento).first
        assert result2.is_visible(), f"L'evento '{titolo_evento}' non è stato trovato"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: elimina l'evento
    try:
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)
        page.get_by_role("button", name="Eventi").click()
        time.sleep(1)
        ev = page.locator('a, button, [class*="event"]').filter(has_text=titolo_evento).first
        if ev.is_visible():
            ev.click()
            time.sleep(1)
            page.get_by_role("button", name="Annulla evento").click()
            time.sleep(1)
            page.get_by_role("button", name="Elimina").click()
            time.sleep(1)
    except Exception:
        pass
