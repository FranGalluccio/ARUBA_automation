import os
import json
from datetime import datetime
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

def test_messaggio_in_bozza(page):
    # Login PEC
    LoginPec(page).login_pec(config)
    
    Helper.crea_messaggio(
        page,
        config,
        oggetto="Test automatico con Playwright - Messaggio in bozza",
        corpo="Test automatico invio messaggio PEC con Playwright",
        destinatario_key="destinatario_principale"  # opzionale, default già principale
)
    
    # Clicca e salva bozza
    page.locator("#new-message\\.save-menu").wait_for(state="visible", timeout=5000)
    page.locator("#new-message\\.save-menu").click()
    page.locator("#save-draft").click()
    
    # Chiudi finestra messaggio
    page.locator('#message-dialog aru-symbol[symbol="close"]').click(force=True)

    # Gestisci popup "Salva in bozze?" — usa evaluate() per bypassare il locator handler.
    # I testi Si/No sono nel shadow template (light DOM vuoto), ordine: [0]=X, [1]=Si, [2]=No.
    page.wait_for_selector('.cdk-overlay-pane:has-text("Salva in bozze"), .cdk-overlay-pane:has-text("Sauvegarder")', timeout=8000)
    page.evaluate("""() => {
        for (const pane of document.querySelectorAll('.cdk-overlay-pane')) {
            if (!pane.textContent.includes('Salva in bozze') && !pane.textContent.includes('Sauvegarder')) continue;
            const aruBtns = pane.querySelectorAll('aru-button');
            const siBtn = aruBtns[1];
            if (!siBtn) return;
            const inner = siBtn.shadowRoot && siBtn.shadowRoot.querySelector('button');
            if (inner) {
                inner.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true, composed: true}));
            } else {
                siBtn.dispatchEvent(new MouseEvent('click', {bubbles: true, cancelable: true}));
            }
            return;
        }
    }""")
    # Attendi chiusura compose + backdrop
    try:
        page.wait_for_function("!document.querySelector('.cdk-overlay-backdrop-showing')", timeout=8000)
    except Exception:
        page.wait_for_timeout(2000)

    # Apri bozze (force=True per bypassare eventuale backdrop residuo)
    page.locator('button[title="Bozze"], button[title="Brouillons"], [title="Bozze"], [title="Brouillons"]').click(force=True)
    
    # Aspetta che almeno un record sia visibile
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=15000)

    # Clicca sul primo record
    page.locator('div.frame-record-desktop').first.click()
    
    # Trova il pulsante "Invia" e cliccalo
    page.locator('span[title="Invia"], span[title="Envoyer"]').wait_for(state="visible", timeout=10000)
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Verifica toast di conferma invio
    toast = page.locator("div.aru-toast__message").filter(has_text="Il messaggio è stato inviato").or_(
        page.locator("div.aru-toast__message").filter(has_text="envoyé")
    ).first
    expect(toast).to_be_visible()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    toast_text = toast.text_content()
    assert "Il messaggio è stato inviato" in toast_text or "envoyé" in toast_text.lower(), \
        f"Toast di conferma invio non trovato: {toast_text!r}"
    
    
    
    
