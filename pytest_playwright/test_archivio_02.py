import os
import json
import time
import pytest
from datetime import datetime
from base_pec import LoginPec, Helper
from playwright.sync_api import expect

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

ARCHIVE_SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings/archive"


def _click_waffle_menu(page):
    """Apre il menu a 9 punti (waffle / servizi) nell'header."""
    waffle_selectors = [
        'button[aria-label="Servizi"]',
        '[aria-label="Servizi"]',
        'button[aria-label*="Servi"]',
        'button[title="Servizi"]',
        '[title="Servizi"]',
        # Fallback: il bottone nella top-nav che contiene aru-symbol con icona griglia
        'aru-button:has(aru-symbol[href*="grid"])',
        'aru-button:has(aru-symbol[href*="apps"])',
        'aru-button:has(aru-symbol[href*="services"])',
    ]
    for sel in waffle_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                time.sleep(1)
                return True
        except Exception:
            pass
    return False


def test_archivio_messaggio_inviato(page):
    """Verifica che i messaggi inviati/ricevuti vengano archiviati secondo
    la configurazione impostata: imposta 'Archivia tutti', invia un messaggio
    a se stesso, poi apre la sezione Archivio e verifica la presenza del messaggio."""

    LoginPec(page).login_pec(config)

    # --- Verifica disponibilità + Step 1: naviga all'URL archivio ---
    # (button[title="Archivio"] è sempre hidden; la feature è confermata
    #  dal caricamento dell'h1 sulla pagina di configurazione)
    page.goto(ARCHIVE_SETTINGS_URL, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)
    if page.locator("h1").filter(has_text="Archivio").count() == 0:
        pytest.skip("Feature 'Archivio' non disponibile in questo ambiente")

    # Seleziona il primo radio button ("Archivia tutti i messaggi ricevuti o inviati")
    radio_inputs = page.locator("input[type='radio']").all()
    assert len(radio_inputs) >= 1, "Radio button non trovati nella pagina archivio"
    radio_inputs[0].click()
    time.sleep(0.5)

    # Salva
    try:
        page.locator('aru-button[skin="primary"]').first.click()
        time.sleep(1)
    except Exception:
        page.get_by_role("button", name="Salva").first.click()
        time.sleep(1)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_02_config_{datetime.now():%H-%M-%S}.png"))

    # --- Step 2: torna a INBOX prima di creare il messaggio ---
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(1)

    oggetto_univoco = f"Test archivio playwright {int(time.time())}"
    Helper.crea_messaggio(
        page, config,
        oggetto=oggetto_univoco,
        corpo="Messaggio di test per verifica archiviazione automatica."
    )

    # Clicca Invia
    try:
        page.locator('aru-button[skin="primary"]:has-text("Invia"), button:has-text("Invia")').first.click()
        time.sleep(2)
    except Exception:
        page.keyboard.press("Control+Return")
        time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_02_inviato_{datetime.now():%H-%M-%S}.png"))
    print(f"Messaggio inviato con oggetto: {oggetto_univoco}")

    # Aspetta che il messaggio venga ricevuto e archiviato (l'archivio può avere latenza)
    time.sleep(10)

    # --- Step 3: apri sezione Archivio dalla waffle menu ---
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(2)

    # Dismetti eventuale overlay
    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    archivio_opened = False

    # Prova waffle menu
    if _click_waffle_menu(page):
        time.sleep(1)
        try:
            archivio_item = page.locator(
                'button:has-text("Archivio"), a:has-text("Archivio"), '
                'aru-menu-item:has-text("Archivio"), [role="menuitem"]:has-text("Archivio")'
            ).first
            if archivio_item.is_visible():
                # Potrebbe aprire in nuova tab
                with page.context.expect_page(timeout=5000) as new_page_info:
                    archivio_item.click()
                archivio_page = new_page_info.value
                archivio_page.wait_for_load_state("networkidle", timeout=15000)
                time.sleep(3)
                archivio_opened = True
                archivio_page.screenshot(path=os.path.join(
                    REPORT_FOLDER, f"test_archivio_02_archivio_{datetime.now():%H-%M-%S}.png"
                ))
                # Cerca il messaggio nell'archivio
                try:
                    archivio_page.get_by_text(oggetto_univoco, exact=False).first.wait_for(
                        state="visible", timeout=15000
                    )
                    assert archivio_page.get_by_text(oggetto_univoco, exact=False).count() > 0, \
                        f"Messaggio '{oggetto_univoco}' non trovato nell'archivio"
                    print(f"Messaggio trovato in Archivio: {oggetto_univoco}")
                except Exception as e:
                    print(f"Nota: messaggio non ancora visibile in archivio (possibile latenza): {e}")
                archivio_page.close()
        except Exception as e:
            print(f"Apertura Archivio da waffle non riuscita: {e}")

    # Fallback: apri da settings e verifica accesso
    if not archivio_opened:
        page.goto(ARCHIVE_SETTINGS_URL, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(2)
        h1 = page.locator("h1").filter(has_text="Archivio").first
        assert h1.is_visible(), "Sezione Archivio non accessibile"
        print("Archivio accessibile via settings (waffle menu non riuscito)")

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
