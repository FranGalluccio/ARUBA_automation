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

def test_etichetta(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Clicca su nuova cartella
    page.locator('span[title="Nuova etichetta"]').click()
    
    nome_etichetta = "Test etichetta lavoro"
    time.sleep(1)
    # Compila nome etichetta
    page.locator("input[placeholder='Es. Lavoro']").fill(nome_etichetta)
    time.sleep(1)
    # Salva nuova etichetta
    page.get_by_role("button", name="Salva").click()
    time.sleep(1)
    
    chiudi = page.get_by_role("button", name="Chiudi")

    try:
        chiudi.wait_for(state="visible", timeout=3000)
        chiudi.click()
    except Exception:
        pass

    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(1)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su etichetta
    page.locator('button:has(aru-symbol[title="Etichetta"])').nth(0).click()
    
    time.sleep(1)

    # Seleziona etichetta lavoro
    page.locator('aru-chosen-closed[inputgroupinputs*="Test etichetta lavoro"]').click()
    time.sleep(1)
    # Applica etichetta
    page.evaluate('''() => {
    const btn = document.querySelector('button[title="Applica"]');
    btn?.click();
}''')
    
    # Clicca con tasto destro sull'etichetta creata
    page.locator(f'button[title="{nome_etichetta}"]').click(button="right")
    
    # Elimina etichetta
    page.locator('button:has-text("Elimina etichetta")').click()
    
    # Conferma elimina etichetta
    page.locator('button[title="Si"]').click()
    time.sleep(1)
    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").first
    expect(toast).to_be_visible()
    assert "L'etichetta è stata eliminata." in toast.text_content()
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_08___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
    
    
    






