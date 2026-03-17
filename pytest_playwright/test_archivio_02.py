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
        'aru-button:has(aru-symbol[symbol="services2"])',
        'button:has(aru-symbol[symbol="services2"])',
        'button[aria-label="Servizi"]',
        'button[title="Servizi"]',
        '[aria-label="Servizi"]',
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
    time.sleep(30)

    # --- Step 3: apri sezione Archivio (mailbox, non impostazioni) ---
    # Torna a INBOX per avere il nav pulito
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=15000)
    except Exception:
        pass
    time.sleep(2)

    # Dismetti eventuale overlay
    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    # Apri Archivio: prima prova il link diretto nel top-nav,
    # poi waffle menu (stesso tab, NON nuova tab)
    archivio_page = page  # di default lavoriamo sulla stessa pagina

    archivio_opened = False

    # Apri waffle menu (symbol="services2"), poi clicca Archivio (diventa visibile dopo apertura)
    if _click_waffle_menu(page):
        time.sleep(2)  # attendi apertura pannello waffle
        try:
            archivio_btn = page.locator(
                'aru-button[title="Archivio"], button[title="Archivio"]'
            ).first
            archivio_btn.wait_for(state="visible", timeout=5000)
            archivio_btn.click()
            try:
                page.wait_for_load_state("networkidle", timeout=15000)
            except Exception:
                pass
            time.sleep(3)
            archivio_opened = True
        except Exception as e:
            print(f"Click Archivio da waffle fallito: {e}")

    assert archivio_opened, "Impossibile aprire la sezione Archivio dal waffle menu"

    archivio_page.screenshot(path=os.path.join(
        REPORT_FOLDER, f"test_archivio_02_archivio_{datetime.now():%H-%M-%S}.png"
    ))

    # --- Step 4: cerca il messaggio nella barra di ricerca dell'archivio ---
    # Dismetti eventuale overlay/cookie
    try:
        archivio_page.locator('button:has-text("Accetta tutti"), button:has-text("Ricordarmelo"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    search_box = archivio_page.locator('input[placeholder="Cerca messaggio..."]').first
    search_box.wait_for(state="visible", timeout=15000)
    search_box.click()
    time.sleep(1)
    search_box.fill(oggetto_univoco)
    time.sleep(1)
    # Prova a cliccare il filtro "Oggetto" per restringere la ricerca
    try:
        archivio_page.locator('button:has-text("Oggetto"), [role="button"]:has-text("Oggetto")').first.click(timeout=2000)
        time.sleep(0.5)
    except Exception:
        pass
    # Clicca "Cerca" se disponibile, altrimenti premi Enter
    try:
        archivio_page.locator('button:has-text("Cerca"), aru-button:has-text("Cerca")').last.click(timeout=3000)
    except Exception:
        archivio_page.keyboard.press("Enter")
    time.sleep(5)

    archivio_page.screenshot(path=os.path.join(
        REPORT_FOLDER, f"test_archivio_02_ricerca_{datetime.now():%H-%M-%S}.png"
    ))

    # --- Step 5: verifica presenza del messaggio ---
    def _messaggio_trovato():
        return (
            archivio_page.get_by_text(oggetto_univoco, exact=False).count() > 0
            or oggetto_univoco in archivio_page.content()
        )

    found = _messaggio_trovato()
    if not found:
        # Latenza archivio: riprova dopo 20s cercando di nuovo
        time.sleep(20)
        search_box.click()
        time.sleep(1)
        search_box.fill("")
        search_box.fill(oggetto_univoco)
        time.sleep(1)
        try:
            archivio_page.locator('button:has-text("Cerca"), aru-button:has-text("Cerca")').last.click(timeout=3000)
        except Exception:
            archivio_page.keyboard.press("Enter")
        time.sleep(5)
        found = _messaggio_trovato()

    assert found, (
        f"Messaggio '{oggetto_univoco}' non trovato nell'Archivio. "
        "Verificare che la configurazione 'Archivia tutti' sia attiva e che il messaggio sia stato recapitato."
    )
    print(f"Messaggio trovato in Archivio: {oggetto_univoco}")

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
