import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper
from playwright.sync_api import sync_playwright, expect


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

TEST_EMAIL_DOMAIN = config.get("test_email_domain", "pec.it")


def test_aggiungere_nuovo_contatto(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    time.sleep(1)
    # Aggiungere nuovo contatto
  # email unica per ogni run
    unique_email = f"testautomatico_{int(time.time())}@{TEST_EMAIL_DOMAIN}"

    page.click("#contacts")
    time.sleep(1)
    page.get_by_role("button", name="Nuovo").click()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_placeholder("Inserisci nome").click()
    page.get_by_placeholder("Inserisci nome").fill("Test")
    page.get_by_placeholder("Inserisci cognome").click()
    page.get_by_placeholder("Inserisci cognome").fill("Automatico")
    page.get_by_placeholder("Inserisci email").click()
    page.get_by_placeholder("Inserisci email").fill(unique_email)
    page.get_by_role("button", name="Salva").click()
    time.sleep(2)

    # Verifica che il contatto sia stato creato (cerca per email univoca)
    search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
    search.click()
    search.fill(unique_email)
    time.sleep(1)
    row = page.locator('div.frame-record-desktop').filter(has_text="Test").first
    assert row.is_visible(), f"Contatto con email '{unique_email}' non trovato dopo il salvataggio"

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: elimina il contatto creato
    try:
        row.hover()
        row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
        time.sleep(1)
        page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
        page.get_by_role("button", name="Sì").first.click(timeout=2000)
        time.sleep(1)
    except Exception:
        pass
