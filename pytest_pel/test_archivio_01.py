import os
import json
import pytest
from datetime import datetime
from base_pel import LoginPel
from playwright.sync_api import expect

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def _click_waffle_menu(page):
    """Apre il menu a 9 punti (waffle / servizi) nell'header."""
    waffle_selectors = [
        'aru-button:has(aru-symbol[symbol="services2"])',
        'button:has(aru-symbol[symbol="services2"])',
        'button[aria-label="Servizi"], [aria-label="Services"]',
        'button[title="Servizi"], button[title="Services"]',
        '[aria-label="Servizi"], [aria-label="Services"]',
    ]
    for sel in waffle_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click(force=True)
                page.wait_for_timeout(1500)
                return True
        except Exception:
            pass
    return False


def test_cartella_archivio_accessibile(page):
    """Verifica che la cartella Archivio (menu a 9 puntini) sia raggiungibile
    e si carichi correttamente.

    Sostituisce il precedente test_configurazione_archivio, che verificava
    la pagina di CONFIGURAZIONE delle regole di archiviazione (Impostazioni
    > Archivio): quella pagina non esiste su PEL Domini (conferma utente) e
    su PEL Staff fa comunque skip perché non attiva sull'account di test —
    nessuna delle due varianti dava copertura reale. La cartella Archivio
    stessa invece esiste sempre ed è navigabile da menu, anche quando non è
    configurabile (su PEL Domini è in sola lettura: "L'archivio in
    scrittura non è abilitato")."""
    LoginPel(page).login_pel(config)

    assert _click_waffle_menu(page), "Impossibile aprire il menu a 9 puntini (Servizi)"

    archivio_btn = page.get_by_text("Archivio", exact=True).first
    try:
        archivio_btn.wait_for(state="visible", timeout=5000)
    except Exception:
        pytest.skip("Feature 'Archivio' non disponibile su questa casella")
    archivio_btn.click(force=True)
    page.wait_for_timeout(2500)

    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    assert "archive" in page.url.lower(), \
        f"La navigazione alla cartella Archivio non è riuscita (URL: {page.url})"

    # Verifica che la pagina sia effettivamente renderizzata (non la pagina
    # bianca da crash): deve essere presente almeno la fila di filtri
    # "Tutti/Letti/Da leggere" o un messaggio informativo sull'archivio.
    contenuto_caricato = (
        page.get_by_text("Tutti", exact=True).count() > 0
        or page.get_by_text("archivio", exact=False).count() > 0
        or page.get_by_text("Non sono presenti messaggi", exact=False).count() > 0
    )
    assert contenuto_caricato, "La cartella Archivio non si è caricata correttamente"
