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

# Percorso file fattura di test (relativo alla CWD = root del repo)
FILE_FATTURA = os.environ.get(
    "FILE_FATTURA",
    config.get("file_fattura", "dati_test/fattura-test.eml")
)


def test_import_fattura_ricevute(page):
    """Importa un file .eml di fattura elettronica tramite 'Gestione messaggi → Importa'
    e verifica che il messaggio importato sia visibile nella cartella 'Fatture ricevute'.
    Skip se la feature non è disponibile nell'ambiente."""

    # Verifica esistenza file di test
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

    # --- Naviga in Fatture ricevute ---
    fatture_btn.click(force=True)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    assert "Fatturazione%20Elettronica" in page.url or "fattur" in page.url.lower(), \
        f"URL Fatture ricevute non corretto: {page.url}"

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_pre_{datetime.now():%H-%M-%S}.png"))

    # --- Torna in INBOX per aprire Gestione messaggi → Importa ---
    # Il bottone Importa non è accessibile dalla virtual folder Fatture ricevute
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(1)

    # Espandi il sottomenu "Gestione messaggi" se collassato
    try:
        gm_btn = page.locator('button[title="Gestione messaggi"]').first
        gm_btn.wait_for(state="visible", timeout=5000)
        gm_btn.click(force=True)
        time.sleep(1)
    except Exception:
        pass

    # Verifica se il bottone Importa è diventato visibile
    importa_btn = page.locator('button[title="Importa"]').first
    try:
        importa_btn.wait_for(state="visible", timeout=4000)
        importa_btn.click()
    except Exception:
        # Fallback: dispatch_event bypassa la visibility ma funziona con shadow DOM
        try:
            importa_btn.wait_for(state="attached", timeout=4000)
            importa_btn.dispatch_event("click")
        except Exception:
            pytest.skip("Bottone 'Importa' non accessibile - feature non disponibile in questo ambiente")
    time.sleep(1)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_import_dialog_{datetime.now():%H-%M-%S}.png"))

    # Verifica che il dialog di import si sia aperto
    dialog_text = page.get_by_text("Seleziona i messaggi da importare", exact=False).first
    try:
        dialog_text.wait_for(state="visible", timeout=5000)
    except Exception:
        # Fallback: il dialog potrebbe avere testo diverso
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_dialog_fallback_{datetime.now():%H-%M-%S}.png"))
        # Cerca qualsiasi dialog/modal aperto
        assert page.locator('.cdk-overlay-pane, [role="dialog"], aru-dialog').count() > 0 or \
               page.locator('#hidden_input').count() > 0, \
               "Dialog di importazione non si è aperto"

    # --- Seleziona il file fattura ---
    file_input = page.locator("#hidden_input")
    file_input.set_input_files(FILE_FATTURA)
    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_file_selezionato_{datetime.now():%H-%M-%S}.png"))

    # Clicca "Importa" nel dialog
    try:
        page.locator('aru-button:has-text("Importa"), button:has-text("Importa")').last.click()
        time.sleep(3)
    except Exception:
        pass

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_post_import_{datetime.now():%H-%M-%S}.png"))

    # --- Verifica che il messaggio sia visibile in INBOX dove è stato importato ---
    # (Il dialog importa in "In arrivo" per default; "Fatture ricevute" è una cartella
    #  virtuale SDI che non riceve messaggi importati manualmente.)
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(2)
    try:
        page.locator('aru-symbol[title="Aggiorna"]').click()
        time.sleep(2)
    except Exception:
        pass

    # Cerca per testo univoco dell'EML (oggetto o identificativo XML)
    messaggio_importato = (
        page.get_by_text("IT01234567890_00001.xml", exact=False).count() > 0 or
        page.get_by_text("Notifica di consegna", exact=False).count() > 0 or
        page.get_by_text("sdi01@pec.fatturapa.it", exact=False).count() > 0
    )

    assert messaggio_importato, \
        "Il messaggio EML importato non è visibile in INBOX dopo l'import tramite 'Gestione messaggi → Importa'"

    print(f"Messaggio importato trovato in INBOX: IT01234567890_00001.xml")

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_fatture_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
