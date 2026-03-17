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


def test_creazione_calendario(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    time.sleep(1)
    
    # Crea nuovo calendario
    page.get_by_role("button", name="Calendario").click()
    page.get_by_role("button", name="Nuovo calendario").click()
    page.get_by_role("textbox", name="input field").click()
    page.get_by_role("textbox", name="input field").fill("Lavoro")
    page.locator("aru-webmail-input-color").get_by_role("button").click()
    page.locator(".aru-webmail-color-dot").first.click()
    page.get_by_role("button", name="Salva").click()
    # Verifica creazione calendario — aspetta la toast (scompare rapidamente)
    toast = page.locator("div.aru-toast__message").first
    toast.wait_for(state="visible", timeout=8000)
    assert "Il calendario è stato creato." in toast.text_content()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    
    # Elimina calendario creato
    time.sleep(2)
    page.get_by_role("checkbox", name="Lavoro").first.click(button="right")
    page.get_by_role("menuitem", name="Elimina").click()
    page.get_by_role("button", name="Sì").click()
    # Verifica eliminazione calendario
    toast = page.locator("div.aru-toast__message").first
    toast.wait_for(state="visible", timeout=8000)
    assert "Il calendario è stato eliminato." in toast.text_content()
    time.sleep(1)
    


    
    