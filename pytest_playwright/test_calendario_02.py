import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper
from playwright.sync_api import Playwright, sync_playwright, expect


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


def test_creazione_modifica_evento(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    time.sleep(2)
    
    # Crea nuovo evento
    page.get_by_role("button", name="Calendario").click()
    page.get_by_role("button", name="Nuovo evento").click()
    page.get_by_placeholder("Inserisci un titolo").fill("evento test automatico")
    page.get_by_role("button", name="Salva").click()
    time.sleep(2)
    page.locator("a").filter(has_text="evento test automatico").click()
    page.get_by_role("button", name="Modifica").click()
    time.sleep(2)
    page.get_by_placeholder("Inserisci un titolo").click()
    time.sleep(1)
    page.get_by_placeholder("Inserisci un titolo").fill("")
    page.get_by_placeholder("Inserisci un titolo").fill("evento test automatico modificato")
    time.sleep(2)
    page.get_by_role("button", name="Salva").click()
    
        
    time.sleep(2)
    
        # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    time.sleep(2)
    
    # Elimina evento
    page.get_by_role("button", name="Eventi").click()
    page.get_by_role("button", name="evento test automatico modificato").first.click()
    page.get_by_role("button", name="Annulla evento").click()
    page.get_by_role("button", name="Elimina").click()