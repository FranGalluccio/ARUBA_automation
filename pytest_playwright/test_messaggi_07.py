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
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw

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
        page.locator('span[title="Invia"], span[title="Envoyer"]').click()
        page.wait_for_timeout(4000)
    page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    count = page.locator('div.frame-record-desktop').count()
    assert count >= 2, f"Inbox ha solo {count} messaggi — impossibile testare preferiti/pinnati"

    def _seleziona_prime_due(page):
        """Seleziona le prime 2 righe tramite hover + force click su checkbox."""
        for i in range(2):
            row_content = page.locator('div.frame-record-desktop-row-content').nth(i)
            row_content.scroll_into_view_if_needed()
            row_content.hover()
            page.wait_for_timeout(600)
            row_content.locator('div.aru-input-checkbox').first.click(force=True)
            page.wait_for_timeout(600)

    def _clicca_altro(page):
        """Clicca il pulsante Altro nella toolbar (attende visibilità)."""
        altro_btn = page.locator('svg[title="Altro"]').first
        altro_btn.wait_for(state="visible", timeout=10000)
        altro_btn.click()

    # Seleziona e aggiungi ai preferiti
    _seleziona_prime_due(page)
    _clicca_altro(page)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).wait_for(state="visible", timeout=5000)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    page.wait_for_timeout(1000)

    # Seleziona e rimuovi dai preferiti
    _seleziona_prime_due(page)
    _clicca_altro(page)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).wait_for(state="visible", timeout=5000)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(0).click()
    page.wait_for_timeout(1000)

    # Seleziona e aggiungi in evidenza
    _seleziona_prime_due(page)
    _clicca_altro(page)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).wait_for(state="visible", timeout=5000)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).click()
    page.wait_for_timeout(1000)

    # Seleziona e rimuovi da in evidenza
    _seleziona_prime_due(page)
    _clicca_altro(page)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).wait_for(state="visible", timeout=5000)
    page.locator('aru-menu[slot="panelNoDropdown"] >> aru-menu-item').nth(1).click()

    # Verifica toast di conferma che i messaggi non sono più in evidenza
    toast = page.locator("div.aru-toast__message").filter(has_text="non sono più in evidenza").first
    toast.wait_for(state="visible", timeout=8000)
    assert toast.is_visible(), "Nessun toast di conferma per la rimozione da 'In evidenza'"
    assert " messaggi non sono più in evidenza." in toast.text_content(), \
        f"Toast non contiene il testo atteso: '{toast.text_content()}'"
    # Verifica che i messaggi non abbiano più la classe/attributo di evidenza
    highlighted = page.locator(
        'div.frame-record-desktop[class*="highlight"], '
        'div.frame-record-desktop[class*="evidenza"], '
        'div.frame-record-desktop[class*="flagged"]'
    ).count()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert highlighted == 0, (
        f"Trovati {highlighted} messaggi ancora marcati come 'in evidenza' dopo la rimozione"
    )
