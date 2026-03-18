import os
import json
from datetime import datetime
import time
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

    # Garantisce almeno 2 messaggi in inbox
    for i in range(2):
        Helper.crea_messaggio(
            page, config,
            oggetto=f"Test preferiti {int(time.time())}_{i}",
            corpo="Test automatico preferiti e pinnati",
        )
        page.locator('span[title="Invia"]').click()
        page.wait_for_timeout(4000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    time.sleep(2)

    count = page.locator('div.frame-record-desktop').count()
    assert count >= 2, f"Inbox ha solo {count} messaggi — impossibile testare preferiti/pinnati"

    # Seleziona i primi 2 messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(1)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Aggiungi ai preferiti
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    
    time.sleep(1)
    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(1)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Rimuovi dai preferiti
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    
    time.sleep(1)
    # Seleziona tutti i messaggi
    page.locator('div.aru-input-checkbox').nth(1).click()
    time.sleep(1)
    page.locator('div.aru-input-checkbox').nth(2).click()
    
    # Clicca su altro
    page.locator('svg[title="Altro"]').click()
    
    # Aggiungi in evidenza
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).click()
    
    time.sleep(1)

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
    
    time.sleep(1)
    # Verifica toast di conferma che i messaggi non sono più in evidenza
    toast = page.locator("div.aru-toast__message").first
    assert toast.is_visible(), "Nessun toast di conferma per la rimozione da 'In evidenza'"
    assert " messaggi non sono più in evidenza." in toast.text_content(), \
        f"Toast non contiene il testo atteso: '{toast.text_content()}'"
    # Verifica che i messaggi non abbiano più la classe/attributo di evidenza
    highlighted = page.locator(
        'div.frame-record-desktop[class*="highlight"], '
        'div.frame-record-desktop[class*="evidenza"], '
        'div.frame-record-desktop[class*="flagged"]'
    ).count()
    assert highlighted == 0, (
        f"Trovati {highlighted} messaggi ancora marcati come 'in evidenza' dopo la rimozione"
    )
    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")