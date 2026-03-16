import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
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


def test_elimina_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(2)
    page.click("#contacts")
    time.sleep(2)

    # Crea un contatto da eliminare
    unique_email = f"testelimina_{int(time.time())}@pec.it"
    cognome = f"DaEliminare{int(time.time())}"

    page.get_by_role("button", name="Nuovo").click()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_placeholder("Inserisci nome").fill("Contatto")
    page.get_by_placeholder("Inserisci cognome").fill(cognome)
    page.get_by_placeholder("Inserisci email").fill(unique_email)
    page.get_by_role("button", name="Salva").click()
    time.sleep(3)

    # Cerca il contatto appena creato
    search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
    search.click()
    search.fill(cognome)
    time.sleep(2)

    # Seleziona il contatto tramite checkbox (stessa tecnica usata nel cleanup di test_contatti_07)
    row = page.locator('div.frame-record-desktop').filter(has_text=cognome).first
    row.wait_for(state="visible", timeout=5000)

    row.hover()
    time.sleep(0.5)
    row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
    time.sleep(1)

    # Clicca Elimina dalla toolbar
    elimina_btn = page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first
    elimina_btn.wait_for(state="visible", timeout=5000)
    elimina_btn.click()
    time.sleep(1)

    # Screenshot per diagnostica
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_06_del_{datetime.now():%H-%M-%S}.png"))

    # Conferma nella dialog "Elimina contatti" → clicca il pulsante "Elimina" nel CDK overlay pane
    confirm_btn = page.locator('.cdk-overlay-pane button:has-text("Elimina")').first
    confirm_btn.wait_for(state="visible", timeout=3000)
    confirm_btn.click()
    time.sleep(3)

    # Verifica che il contatto non sia più presente
    # Aspetta che eventuali backdrop spariscano
    try:
        page.locator('.cdk-overlay-backdrop').wait_for(state="hidden", timeout=3000)
    except Exception:
        pass
    time.sleep(1)
    # Pulisci la ricerca e ricerca di nuovo
    search2 = page.locator('input[placeholder*="Cerca tra i contatti"]').first
    search2.click(force=True)
    time.sleep(0.5)
    search2.fill(cognome)
    time.sleep(2)

    assert page.locator('div.frame-record-desktop').filter(has_text=cognome).count() == 0, \
        f"Il contatto '{cognome}' è ancora presente dopo l'eliminazione"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
