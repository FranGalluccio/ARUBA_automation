import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso importa messaggi ---
importa_messaggi = os.environ.get("IMPORTA_MESSAGGI", config.get("importa_messaggi"))

def test_cartella(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Clicca su nuova cartella
    page.locator('span[title="Crea nuova cartella"]').click()
    
    nome_cartella = "Test automatico playwright"
    # Compila nome cartella
    page.locator('input[placeholder="Nome cartella"]').fill(nome_cartella)
    
    # Clicca su salva
    page.locator('span[title="Salva"]').click()
    
    time.sleep(1)

    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "La cartella è stata creata." in toast.text_content()
    
    page.locator(f'button[title="{nome_cartella}"]').click(button="right")
    
    time.sleep(1)
    
    page.locator('button:has-text("Modifica cartella")').click()
    
    # Modifica nome cartella
    nuovo_nome_cartella = "Test automatico playwright - Modificata"
    page.locator('input[aria-label="input field"]').fill(nuovo_nome_cartella)
    
    # Clicca su salva
    page.locator('span[title="Salva"]').click()
    
    time.sleep(2)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "La cartella è stata modificata." in toast.text_content()
    
    time.sleep(1) 
    # Clicca con tasto destro sulla cartella modificata
    page.locator(f'button[title="{nuovo_nome_cartella}"]').click(button="right")
    
    time.sleep(1)
    # Clicca su modifica cartella
    page.locator('button:has-text("Elimina cartella")').click()
    
    # Clicca su elimina
    page.locator('span[title="Elimina"]').click()
    
    time.sleep(1)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "La cartella è stata eliminata." in toast.text_content()
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")

    

    
    
    


   



