import os
import json
import time
from datetime import datetime
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

SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings"


def test_regole_messaggi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Regole messaggi (sotto accordion "Messaggi e scrittura")
    page.goto(SETTINGS_URL + "/home", timeout=20000)
    # Espandi l'accordion "Messaggi e scrittura" se necessario
    if not page.locator('button[title="Regole messaggi"]').is_visible():
        page.locator('button[title="Messaggi e scrittura"]').first.click(force=True)
        page.locator('button[title="Regole messaggi"]').first.wait_for(state="visible", timeout=5000)
    page.locator('button[title="Regole messaggi"]').click(force=True)

    # Verifica che la pagina Regole messaggi sia caricata
    page.locator('h1, [class*="filter"], [class*="rule"]').first.wait_for(state="visible", timeout=8000)

    # Clicca "Nuova regola" - cerchiamo tutti i pulsanti aru-button visibili
    create_btn = page.locator('aru-button[kind="solid"][skin="primary"]').first
    create_btn.wait_for(state="visible", timeout=8000)
    create_btn.click(force=True)

    # Verifica che il form di creazione regola si sia aperto
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_impostazioni_03_form_{datetime.now():%H-%M-%S}.png"))

    # Il form è aperto: verifica che siano presenti label o placeholder specifici del form regola
    form_visible = (
        page.locator('[placeholder*="Nome regola"], [placeholder*="regola"], [label*="Nome regola"]').count() > 0 or
        page.get_by_text("Nome regola", exact=False).count() > 0 or
        page.get_by_text("Condizioni", exact=False).count() > 0 or
        page.get_by_text("Azioni", exact=False).count() > 0
    )
    assert form_visible, "Il form di creazione regola non si è aperto"

    # Compila nome regola se c'è un input disponibile
    nome_regola = f"Regola test playwright {int(time.time())}"
    for inp in page.locator("input").all():
        try:
            if inp.is_visible():
                inp.fill(nome_regola)
                break
        except Exception:
            pass

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: elimina la regola
    try:
        row = page.locator('[class*="rule"], [class*="regola"], tr, li').filter(has_text=nome_regola).first
        row.locator('button[title="Elimina"], aru-symbol[title="Elimina"]').click()
        page.locator('button[title="Si"], button:has-text("Sì"), button:has-text("Si")').first.click(timeout=2000)
    except Exception:
        pass
