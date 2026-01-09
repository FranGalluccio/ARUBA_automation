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

def test_messaggio_con_allegato_drive(page):
    # Login PEC
    LoginPec(page).login_pec()

    # Creare messaggio con allegato
    Helper.crea_messaggio(
        page,
        "francescoconservazione@pec.it",
        "Test automatico con Playwright - Invio allegati drive",
        "Test automatico invio messaggio PEC con Playwright"
    )
    
    # Apri menu allegati
    page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
    menu_item = page.locator("aru-menu-item", has_text="Carica da Aruba Drive").first
    
    # Controlla che il tasto carica da Aruba Drive sia visibile e cliccabile
    assert menu_item.is_visible(), "L'opzione 'Carica da Aruba Drive' non è visibile, controlla se aruba drive è collegato"
    assert menu_item.is_enabled(), "L'opzione 'Carica da Aruba Drive' non è cliccabile, controlla se aruba drive è collegato"
    
    # Carica da dispositivo
    page.locator("aru-menu-item", has_text="Carica da Aruba Drive").first.click()
    
    # Prendi il container/modale della lista dei file
    container = page.locator("div.h-100.d-flex.flex-column.overflow-x-hidden.overflow-y-auto.change-thumb")

    # Clicca il primo file nella lista (se presente)
    container.locator("div.row.h-64.small-border.cursor-pointer").first.click()

    # Prendi il container della modale "Allega da Aruba Drive"
    modal = page.locator("div#attachment-list")

# Clicca il primo checkbox dentro la modale
    modal.locator("aru-input-choice[type='checkbox'] >> nth=1").click()
    
    # Allega un file
    page.locator("button[title='Allega 1 file']").click()
    
    # Attesa prima di inviare il messaggio
    time.sleep(5)
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"]').click()
    
    # Aspetta 8 secondi
    page.wait_for_timeout(8000)
    
    # Aggiorna la posta
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)


    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    time.sleep(2)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()

    # Aspetta che il contenuto della mail sia visibile
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.wait_for_load_state("domcontentloaded")

    # Verifica pagina esterna
    assert "external-message" in new_page.url

    # Prendi il nome del file dal tooltip
    file_name = page.locator("aru-tooltip span.button-tooltip strong").first.inner_text()
    
    # Clicca sul bottone corrispondente usando il title
    new_page.locator(f'button[title="{file_name}"]').click()

    # Seleziona il pulsante
    button = new_page.locator('text="Mostra anteprima"').first
    # Assert prima di cliccare
    assert button.is_visible(), "Il pulsante 'Mostra anteprima' non è visibile"
    assert button.is_enabled(), "Il pulsante 'Mostra anteprima' non è cliccabile"
    
    # Mostra anteprima
    new_page.locator('text="Mostra anteprima"').first.click()
    
     # Aspetta 5 secondi prima dello screenshot
    time.sleep(5)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")