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
        """Clicca il pulsante '...' nella toolbar; Escape prima per chiudere overlay residui."""
        page.keyboard.press("Escape")
        page.wait_for_timeout(300)
        for sel in [
            'button:has(aru-symbol[title="Altro"])',
            'button:has(aru-symbol[title="Plus"])',
            'button[title="Altro"]',
            'button[title="Plus"]',
            'svg[title="Altro"]',
            'svg[title="Plus"]',
        ]:
            try:
                loc = page.locator(sel).first
                if loc.count() > 0 and loc.is_visible():
                    loc.click(force=True)
                    return
            except Exception:
                pass
        raise Exception("Pulsante Altro/Plus non trovato")

    def _click_menu_item(nth):
        """Clicca l'nth menu item nel pannello Altro (slot o CDK overlay)."""
        page.wait_for_timeout(1000)
        for sel in [
            'aru-menu[slot="panelNoDropdown"] >> aru-menu-item',
            '.cdk-overlay-container aru-menu-item',
            '.cdk-overlay-pane aru-menu-item',
            '[role="menuitem"]',
        ]:
            try:
                loc = page.locator(sel)
                if loc.count() > nth and loc.nth(nth).is_visible():
                    loc.nth(nth).click(force=True)
                    return
            except Exception:
                pass
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"debug_menu_{nth}_{datetime.now():%H-%M-%S}.png"))
        raise Exception(f"Menu item {nth} non trovato/visibile")

    # Seleziona e aggiungi ai preferiti
    _seleziona_prime_due(page)
    _clicca_altro(page)
    _click_menu_item(0)
    page.wait_for_timeout(1000)

    # Seleziona e rimuovi dai preferiti
    _seleziona_prime_due(page)
    _clicca_altro(page)
    _click_menu_item(0)
    page.wait_for_timeout(1000)

    # Seleziona e aggiungi in evidenza
    _seleziona_prime_due(page)
    _clicca_altro(page)
    _click_menu_item(1)
    page.wait_for_timeout(1000)

    # Seleziona e rimuovi da in evidenza
    _seleziona_prime_due(page)
    _clicca_altro(page)
    _click_menu_item(1)

    # Verifica toast di conferma che i messaggi non sono più in evidenza
    toast = page.locator("div.aru-toast__message").filter(has_text="in evidenza").or_(
        page.locator("div.aru-toast__message").filter(has_text="évidence")
    ).first
    toast.wait_for(state="visible", timeout=8000)
    assert toast.is_visible(), "Nessun toast di conferma per la rimozione da 'In evidenza'"
    toast_text = toast.text_content()
    assert "in evidenza" in toast_text.lower() or "évidence" in toast_text.lower(), \
        f"Toast non contiene il testo atteso: '{toast_text}'"
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
