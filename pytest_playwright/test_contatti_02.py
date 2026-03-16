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


def test_aggiungere_nuovo_gruppo(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    time.sleep(1)
    # Aggiungere nuovo contatto
    page.locator("#contacts").click()
    time.sleep(1)
    
    group_name = f"Test automatico gruppo {__import__('time').time().__int__()}"

    page.get_by_role("button", name="Nuovo").click()
    page.locator("#group").check()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_role("textbox", name="input field").click()
    page.get_by_role("textbox", name="input field").fill(group_name)
    page.get_by_role("textbox", name="input search").click()
    page.get_by_role("checkbox", name="Test Automatico").first.click()
    page.get_by_role("button", name="Aggiungi contatti").click()
    time.sleep(1)
    page.get_by_role("button", name="Salva").click()

# usa la stessa variabile nell'assert
    expect(
        page.get_by_label("sidebar").get_by_role("button", name=group_name)
    ).to_be_visible()

    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")

    