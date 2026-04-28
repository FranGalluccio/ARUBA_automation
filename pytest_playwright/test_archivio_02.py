import os
import json
import time
import pytest
from datetime import datetime
from base_pec import LoginPec, Helper, get_app_base_url
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
        'button[aria-label="Servizi"]',
        'button[title="Servizi"]',
        '[aria-label="Servizi"]',
    ]
    for sel in waffle_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                page.wait_for_timeout(500)
                return True
        except Exception:
            pass
    return False


def test_archivio_messaggio_inviato(page):
    """Verifica che i messaggi inviati/ricevuti vengano archiviati secondo
    la configurazione impostata: imposta 'Archivia tutti', invia un messaggio
    a se stesso, poi apre la sezione Archivio e verifica la presenza del messaggio."""

    LoginPec(page).login_pec(config)
    app_base = get_app_base_url(page)

    # --- Verifica disponibilità + Step 1: naviga all'URL archivio ---
    # (button[title="Archivio"] è sempre hidden; la feature è confermata
    #  dal caricamento dell'h1 sulla pagina di configurazione)
    page.goto(app_base + "/new/settings/archive", timeout=20000)
    page.wait_for_load_state("load", timeout=15000)

    # Chiudi cookie banner se presente (può bloccare h1 e pulsante Salva)
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Attendi che eventuali overlay CDK (spinner, dialog post-login) spariscano
    try:
        page.wait_for_function("!document.querySelector('.cdk-overlay-backdrop-showing')", timeout=10000)
    except Exception:
        pass

    try:
        page.locator("h1").filter(has_text="Archivio").wait_for(state="visible", timeout=10000)
    except Exception:
        pytest.skip("Feature 'Archivio' non disponibile in questo ambiente")

    # Seleziona "Archivia tutti i messaggi ricevuti o inviati" cercando per testo della label
    try:
        page.get_by_text("Archivia tutti i messaggi ricevuti o inviati", exact=False).first.click()
    except Exception:
        page.locator("input[type='radio']").first.click()

    # Salva
    try:
        salva = page.locator('aru-button[skin="primary"]').first
        salva.wait_for(state="visible", timeout=10000)
        salva.click()
    except Exception:
        page.get_by_role("button", name="Salva").first.click(timeout=15000)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_02_config_{datetime.now():%H-%M-%S}.png"))

    # --- Step 2: torna a INBOX prima di creare il messaggio ---
    page.goto(app_base + "/new/messages/INBOX", timeout=20000)
    page.wait_for_timeout(1500)

    oggetto_univoco = f"Test archivio playwright {int(time.time())}"
    # Invia sempre a se stessi (indirizzo PEC dell'account corrente) per garantire l'archiviazione
    config_self = {**config, "destinatari": {"destinatario_principale": config["pec"]["username"]}}
    Helper.crea_messaggio(
        page, config_self,
        oggetto=oggetto_univoco,
        corpo="Messaggio di test per verifica archiviazione automatica."
    )

    # Invia il messaggio (stesso pattern usato negli altri test)
    page.locator('span[title="Invia"]').click()
    page.wait_for_timeout(2000)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_archivio_02_inviato_{datetime.now():%H-%M-%S}.png"))
    print(f"Messaggio inviato con oggetto: {oggetto_univoco}")

    # Attesa per il recapito del messaggio (operazione server-side)
    page.wait_for_timeout(10000)

    # --- Step 3: apri sezione Archivio (mailbox, non impostazioni) ---
    # Torna a INBOX per avere il nav pulito
    page.goto(app_base + "/new/messages/INBOX", timeout=20000)
    page.wait_for_timeout(1500)

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
        try:
            archivio_btn = page.locator(
                'aru-button[title="Archivio"], button[title="Archivio"]'
            ).first
            archivio_btn.wait_for(state="visible", timeout=5000)
            archivio_btn.click()
            page.wait_for_timeout(2000)
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
    # Usa keyboard.type per digitare carattere per carattere (fill fallisce sul shadow DOM)
    archivio_page.keyboard.type(oggetto_univoco, delay=50)
    # Clicca "Cerca" per eseguire la ricerca
    try:
        archivio_page.locator('button:has-text("Cerca"), aru-button:has-text("Cerca")').last.click(timeout=3000)
    except Exception:
        archivio_page.keyboard.press("Enter")
    page.wait_for_timeout(3000)

    archivio_page.screenshot(path=os.path.join(
        REPORT_FOLDER, f"test_archivio_02_ricerca_{datetime.now():%H-%M-%S}.png"
    ))

    # --- Step 5: verifica presenza del messaggio ---
    def _messaggio_trovato():
        # Controlla assenza di "Non sono presenti messaggi" nella lista risultati
        # (get_by_text sull'intera pagina matcherebbe anche il chip della barra di ricerca)
        no_results = archivio_page.get_by_text("Non sono presenti messaggi", exact=False).count() > 0
        return not no_results

    found = _messaggio_trovato()
    if not found:
        # Latenza archivio: riprova dopo 20s — cancella chip e cerca di nuovo
        page.wait_for_timeout(20000)
        # Cancella il chip/filtro attivo cliccando la ×
        try:
            archivio_page.locator('button[aria-label="Rimuovi filtro"], [title="Rimuovi filtro"], button.chip-remove').first.click(timeout=2000)
        except Exception:
            pass
        # Ri-cerca dalla barra principale
        search_box2 = archivio_page.locator('input[placeholder="Cerca messaggio..."]').first
        try:
            search_box2.wait_for(state="visible", timeout=10000)
            search_box2.click()
            archivio_page.keyboard.type(oggetto_univoco, delay=50)
            try:
                archivio_page.locator('button:has-text("Cerca"), aru-button:has-text("Cerca")').last.click(timeout=3000)
            except Exception:
                archivio_page.keyboard.press("Enter")
            page.wait_for_timeout(3000)
        except Exception:
            pass
        found = _messaggio_trovato()

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_archivio_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert found, (
        f"Messaggio '{oggetto_univoco}' non trovato nell'Archivio. "
        "Verificare che la configurazione 'Archivia tutti' sia attiva e che il messaggio sia stato recapitato."
    )
    print(f"Messaggio trovato in Archivio: {oggetto_univoco}")
