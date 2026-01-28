import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec, Helper

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

def test_messaggi_preferiti_pinnati(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(2)
    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(2)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Aggiungi ai preferiti
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    
    time.sleep(2)
    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(2)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Rimuovi dai preferiti
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    
    time.sleep(2)
    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(2)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Aggiungi in evidenza
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).click()
    
    time.sleep(2)

    # Passa sopra la prima riga (hover) e poi clicca sul checkbox
    page.locator('div.frame-record-desktop-row-content').nth(0).hover()
    page.locator('div.frame-record-desktop-row-content').nth(0).locator('div.aru-input-checkbox').click(force=True)

    # Passa sopra la seconda riga (hover) e poi clicca sul checkbox
    page.locator('div.frame-record-desktop-row-content').nth(1).hover()
    page.locator('div.frame-record-desktop-row-content').nth(1).locator('div.aru-input-checkbox').click(force=True)
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Rimuovi da in evidenza
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).click()
    
    time.sleep(2)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    assert toast.is_visible()
    assert " messaggi non sono più in evidenza." in toast.text_content()
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")