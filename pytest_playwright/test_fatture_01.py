import os
import json
import time
import pytest
from datetime import datetime
from base_pec import LoginPec

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# File con X-Fattura-PA: Yes (da sdi20@pec.fatturapa.it)
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FILE_FATTURA = os.environ.get(
    "FILE_FATTURA",
    os.path.join(_project_root, config.get("file_fattura", "dati_test/fattura-reale-02.eml"))
)

FATTURE_URL = config["pec"]["url"].rstrip("/") + "/new/messages/ArubaVrtSearch/Fatturazione%20Elettronica"


def _count_fatture(page):
    """Conta le righe visibili in Fatture ricevute."""
    return page.locator('div.frame-record-desktop').count()


def test_import_fattura_ricevute(page):
    """Importa un file .eml di fattura elettronica (X-Fattura-PA: Yes) tramite
    'Gestione messaggi → Importa' e verifica che appaia in 'Fatture ricevute'.
    Skip se la feature non è disponibile nell'ambiente."""

    assert os.path.exists(FILE_FATTURA), \
        f"File fattura di test non trovato: {FILE_FATTURA}"

    LoginPec(page).login_pec(config)

    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    # --- Verifica disponibilità feature ---
    fatture_btn = page.locator('button[title="Fatture ricevute"]').first
    if not fatture_btn.is_visible():
        pytest.skip("Feature 'Fatture ricevute' non disponibile in questo ambiente")

    # --- Naviga in Fatture ricevute e conta messaggi prima dell'import ---
    page.goto(FATTURE_URL, timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_pre_{datetime.now():%H-%M-%S}.png"))
    count_before = _count_fatture(page)
    print(f"Fatture prima dell'import: {count_before}")

    # --- Torna in INBOX per aprire Gestione messaggi → Importa ---
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    time.sleep(1)

    # Espandi "Gestione messaggi" se collassato
    try:
        gm_btn = page.locator('button[title="Gestione messaggi"]').first
        gm_btn.wait_for(state="visible", timeout=5000)
        gm_btn.click(force=True)
        time.sleep(1)
    except Exception:
        pass

    # Clicca "Importa"
    importa_btn = page.locator('button[title="Importa"]').first
    try:
        importa_btn.wait_for(state="visible", timeout=4000)
        importa_btn.click()
    except Exception:
        try:
            importa_btn.wait_for(state="attached", timeout=4000)
            importa_btn.dispatch_event("click")
        except Exception:
            pytest.skip("Bottone 'Importa' non accessibile - feature non disponibile in questo ambiente")
    time.sleep(1)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_import_dialog_{datetime.now():%H-%M-%S}.png"))

    # Verifica che il dialog si sia aperto
    try:
        page.get_by_text("Seleziona i messaggi da importare", exact=False).first.wait_for(state="visible", timeout=5000)
    except Exception:
        assert page.locator('.cdk-overlay-pane, [role="dialog"], aru-dialog').count() > 0 or \
               page.locator('#hidden_input').count() > 0, \
               "Dialog di importazione non si è aperto"

    # --- Seleziona il file fattura ---
    file_input = page.locator("#hidden_input")
    file_input.set_input_files(FILE_FATTURA)
    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_file_selezionato_{datetime.now():%H-%M-%S}.png"))

    # Clicca "Importa" nel dialog per avviare l'upload (non il bottone sidebar già cliccato)
    # get_by_role pierces shadow DOM; prendiamo l'ultimo bottone "Importa" visibile
    time.sleep(1)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_before_confirm_{datetime.now():%H-%M-%S}.png"))
    try:
        all_importa = page.get_by_role("button", name="Importa", exact=True).all()
        clicked = False
        for btn in reversed(all_importa):
            try:
                if btn.is_visible():
                    btn.click()
                    clicked = True
                    break
            except Exception:
                pass
        if not clicked:
            # Fallback JS: clicca l'ultimo bottone Importa nel DOM
            page.evaluate("""() => {
                const btns = [...document.querySelectorAll('button, aru-button')];
                const importa = btns.filter(b => b.textContent.trim().includes('Importa'));
                if (importa.length > 0) importa[importa.length - 1].click();
            }""")
    except Exception:
        pass
    time.sleep(5)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_post_import_{datetime.now():%H-%M-%S}.png"))

    # --- Vai in Fatture ricevute e attendi che il nuovo messaggio appaia ---
    page.goto(FATTURE_URL, timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    fattura_trovata = False
    for attempt in range(20):
        count_after = _count_fatture(page)
        if count_after > count_before:
            fattura_trovata = True
            print(f"Fatture dopo import: {count_after} (prima: {count_before}) - tentativo {attempt+1}")
            break
        # A metà polling ricarica la pagina per forzare aggiornamento (utile in CI)
        if attempt == 9:
            page.goto(FATTURE_URL, timeout=20000)
            try:
                page.wait_for_load_state("load", timeout=10000)
            except Exception:
                pass
            time.sleep(2)
        else:
            time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_fatture_ricevute_{datetime.now():%H-%M-%S}.png"))

    assert fattura_trovata, (
        f"Nessuna nuova fattura in 'Fatture ricevute' dopo l'import di '{os.path.basename(FILE_FATTURA)}'. "
        f"Conteggio prima: {count_before}, dopo: {_count_fatture(page)}."
    )

    # --- Apri la fattura e clicca "Visualizza fattura" ---
    prima_riga = page.locator('div.frame-record-desktop').first
    prima_riga.click()
    time.sleep(2)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_dettaglio_{datetime.now():%H-%M-%S}.png"))

    # Clicca "Visualizza fattura" — può aprire una nuova tab
    pages_before = len(page.context.pages)
    page.locator('button:has-text("Visualizza fattura"), aru-button:has-text("Visualizza fattura")').first.click()
    time.sleep(3)

    pages_after = page.context.pages

    if len(pages_after) > pages_before:
        viewer_page = pages_after[-1]
        try:
            viewer_page.wait_for_load_state("load", timeout=15000)
            time.sleep(2)
        except Exception:
            pass
        viewer_url = viewer_page.url
        assert viewer_url and viewer_url not in ("about:blank", ""), \
            f"La nuova tab aperta da 'Visualizza fattura' è vuota (url: {viewer_url})"
        viewer_page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_visualizza_{datetime.now():%H-%M-%S}.png"))
    else:
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_visualizza_{datetime.now():%H-%M-%S}.png"))
        assert page.locator('iframe, [class*="viewer"], [class*="preview"], [class*="pdf"]').count() > 0, \
            "Visualizza fattura non ha aperto una nuova tab né un viewer nella pagina"
    print("Visualizza fattura: OK")

    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_fatture_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # --- Torna alla lista Fatture ricevute per il cleanup ---
    # Chiudi la tab del viewer se aperta
    if len(pages_after) > pages_before:
        try:
            pages_after[-1].close()
        except Exception:
            pass
    # Naviga nuovamente alla lista per uscire dalla visualizzazione dettaglio
    page.goto(FATTURE_URL, timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    # --- Cleanup: elimina tutte le fatture (2 passaggi) ---
    ELIMINA_BTN = (
        'button:has(aru-symbol[title="Elimina"]), '
        'aru-button:has(aru-symbol[title="Elimina"]), '
        'button[title="Elimina"]'
    )
    ELIMINA_DEF = (
        'button:has-text("Elimina definitivamente"), '
        'aru-button:has-text("Elimina definitivamente")'
    )
    try:
        # Step 1: seleziona → Elimina (sposta nel Cestino)
        page.locator('div.aru-input-checkbox').first.click()
        time.sleep(1)
        page.locator(ELIMINA_BTN).first.click()
        time.sleep(2)
        try:
            page.get_by_role("button", name="Sì").click(timeout=2000)
            time.sleep(2)
        except Exception:
            pass

        # Step 2: ri-seleziona → Elimina definitivamente (toolbar) → conferma dialog
        if page.locator('div.frame-record-desktop').count() > 0:
            # Clicca checkbox solo se il bottone "Elimina definitivamente" non è già visibile
            if not page.locator(ELIMINA_DEF).first.is_visible():
                page.locator('div.aru-input-checkbox').first.click()
                time.sleep(1)
            # Clicca "Elimina definitivamente" nel toolbar
            page.locator(ELIMINA_DEF).first.click()
            time.sleep(2)
            # Clicca "Elimina definitivamente" nel dialog di conferma
            page.locator(ELIMINA_DEF).last.click(timeout=5000)
            time.sleep(2)
    except Exception:
        pass
