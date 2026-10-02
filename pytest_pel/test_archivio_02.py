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


def test_filtro_archivio(page):
    """Verifica il filtro 'Letti' nella cartella Archivio (tab aru-chip,
    stesso componente già usato in In arrivo — vedi test_messaggi_18).

    Sostituisce il precedente test_archivio_messaggio_inviato, che
    presupponeva di poter configurare 'Archivia tutti i messaggi' da
    Impostazioni > Archivio: pagina che non esiste su PEL Domini e che su
    PEL Staff risultava comunque non attiva sull'account di test (skip
    sistematico, nessuna copertura reale). L'archivio su PEL Domini è in
    sola lettura ("L'archivio in scrittura non è abilitato"): non si può
    quindi verificare l'arrivo di un messaggio appena inviato, ma si può
    verificare che l'interfaccia della cartella (filtri) funzioni
    correttamente sui messaggi già presenti."""
    LoginPel(page).login_pel(config)

    assert _click_waffle_menu(page), "Impossibile aprire il menu a 9 puntini (Servizi)"

    archivio_btn = page.get_by_text("Archivio", exact=True).first
    try:
        archivio_btn.wait_for(state="visible", timeout=5000)
    except Exception:
        pytest.skip("Feature 'Archivio' non disponibile su questa casella")
    archivio_btn.click(force=True)
    page.wait_for_timeout(2500)

    filtro_letti = page.locator('.aru-chip:has-text("Letti"), [class*="chip"]:has-text("Letti")').first
    assert filtro_letti.is_visible(), "Il filtro 'Letti' non è visibile nella cartella Archivio"

    filtro_letti.click(force=True)
    page.wait_for_timeout(1500)

    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    assert "mail_quickFilter" in page.url, (
        f"Il filtro 'Letti' non risulta applicato nell'Archivio (URL: {page.url})"
    )
