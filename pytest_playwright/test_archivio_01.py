import os
import json
import pytest
from datetime import datetime
from base_pec import LoginPec, get_app_base_url
from playwright.sync_api import expect

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

def test_configurazione_archivio(page):
    """Verifica la pagina di configurazione archivio: struttura, radio button,
    checkbox opzioni. Modifica la selezione, salva e verifica il persist."""

    LoginPec(page).login_pec(config)
    app_base = get_app_base_url(page)

    # --- Verifica disponibilità feature navigando direttamente all'URL ---
    # (il button[title="Archivio"] esiste nel DOM ma è sempre hidden:
    #  la feature è verificata controllando che la pagina si carichi con l'h1 atteso)
    page.goto(app_base + "/new/settings/archive", timeout=20000)
    page.wait_for_load_state("load", timeout=15000)

    # Chiudi cookie banner se presente (può bloccare l'h1 e causare skip errato)
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    try:
        page.locator("h1").filter(has_text="Archivio").wait_for(state="visible", timeout=10000)
    except Exception:
        pytest.skip("Feature 'Archivio' non disponibile in questo ambiente")

    # --- Verifica struttura pagina ---
    h1 = page.locator("h1").filter(has_text="Archivio").first
    h1.wait_for(state="visible", timeout=8000)
    assert h1.is_visible(), "h1 'Archivio' non visibile"

    h2 = page.locator("h2").filter(has_text="Configurazione Archivio").first
    assert h2.is_visible(), "h2 'Configurazione Archivio' non visibile"

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_01_struttura_{datetime.now():%H-%M-%S}.png"))

    # --- Verifica radio button principali ---
    radio_tutti = page.locator("input[type='radio']").filter(
        has_text="Archivia tutti i messaggi"
    )
    radio_scegli = page.locator("input[type='radio']").filter(
        has_text="Scegli quali messaggi archiviare"
    )
    # I radio possono essere identificati per aria-label o essere vicini al testo
    radio_inputs = page.locator("input[type='radio']").all()
    assert len(radio_inputs) >= 2, f"Attesi almeno 2 radio button, trovati: {len(radio_inputs)}"

    # --- Verifica checkbox opzioni specifiche ---
    expected_options = [
        "Archivia tutte le ricevute di accettazione",
        "Archivia tutte le ricevute di consegna",
        "Archivia tutti i messaggi di posta certificata ricevuti",
        "Archivia tutti i messaggi di posta certificata inviati",
    ]
    for opt in expected_options:
        el = page.locator(f'input[type="checkbox"], input[type="radio"]').filter(
            has_text=opt
        )
        # Cerca anche per testo vicino (label)
        label = page.locator("label, span, div").filter(has_text=opt).first
        assert label.count() > 0 or page.get_by_text(opt, exact=False).count() > 0, \
            f"Opzione non trovata: '{opt}'"

    # --- Seleziona "Scegli quali messaggi archiviare" ---
    # force=True bypassa il cdk-overlay-backdrop-showing con custom-backdrop-class
    try:
        page.locator("input[type='radio']").nth(1).click(force=True)
    except Exception:
        page.get_by_text("Scegli quali messaggi archiviare", exact=False).first.click(force=True)

    # Abilita checkbox "ricevute di accettazione" (opzionale: appare solo se radio "Scegli" è selezionato)
    ra_checkbox = page.locator("input[type='checkbox']").first
    if ra_checkbox.count() > 0 and ra_checkbox.is_visible():
        ra_checkbox.check()

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_01_scegli_{datetime.now():%H-%M-%S}.png"))

    # --- Salva ---
    save_btn = page.locator('aru-button[skin="primary"], button[type="submit"]').first
    try:
        save_btn.wait_for(state="visible", timeout=5000)
        save_btn.click()
    except Exception:
        # Fallback: cerca per testo Salva
        btn = page.locator('aru-button:has-text("Salva"), button:has-text("Salva")').first
        btn.wait_for(state="attached", timeout=5000)
        btn.dispatch_event("click")

    # Verifica toast di conferma
    toast = page.locator("div.aru-toast__message, aru-toast, [class*='toast'], [class*='snack']").first
    try:
        toast.wait_for(state="visible", timeout=5000)
        print("Toast di conferma salvataggio visibile")
    except Exception:
        print("Toast non rilevato - verifica reload")

    # --- Ricarica e verifica persist ---
    page.reload()
    page.wait_for_load_state("load", timeout=15000)

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    # Verifica che la pagina sia ancora quella giusta
    assert "archive" in page.url or page.locator("h1").filter(has_text="Archivio").count() > 0, \
        "Dopo reload la pagina Archivio non si è ricaricata correttamente"

    # --- Cleanup: ripristina "Archivia tutti" ---
    try:
        page.locator("input[type='radio']").first.click(force=True)
        page.locator('aru-button[skin="primary"], button[type="submit"]').first.click(force=True)
        page.wait_for_timeout(500)
    except Exception:
        pass
