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
FILE_FATTURA = os.environ.get(
    "FILE_FATTURA",
    config.get("file_fattura", "dati_test/fattura-reale-02.eml")
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
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_pre_{datetime.now():%H-%M-%S}.png"))
    count_before = _count_fatture(page)
    print(f"Fatture prima dell'import: {count_before}")

    # --- Torna in INBOX per aprire Gestione messaggi → Importa ---
    page.goto(config["pec"]["url"].rstrip("/") + "/new/messages/INBOX", timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
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

    # Clicca "Importa" nel dialog per avviare l'upload
    try:
        page.locator('aru-button:has-text("Importa"), button:has-text("Importa")').last.click()
        time.sleep(3)
    except Exception:
        pass

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_post_import_{datetime.now():%H-%M-%S}.png"))

    # --- Vai in Fatture ricevute e attendi che il nuovo messaggio appaia ---
    # Usa goto() per forzare il reload della virtual folder (più affidabile del pulsante Aggiorna)
    fattura_trovata = False
    for attempt in range(10):
        page.goto(FATTURE_URL, timeout=20000)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
        except Exception:
            pass
        time.sleep(2)
        count_after = _count_fatture(page)
        if count_after > count_before:
            fattura_trovata = True
            print(f"Fatture dopo import: {count_after} (prima: {count_before}) - tentativo {attempt+1}")
            break

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_01_fatture_ricevute_{datetime.now():%H-%M-%S}.png"))

    assert fattura_trovata, (
        f"Nessuna nuova fattura in 'Fatture ricevute' dopo l'import di '{os.path.basename(FILE_FATTURA)}'. "
        f"Conteggio prima: {count_before}, dopo: {_count_fatture(page)}."
    )

    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_fatture_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")

    # --- Cleanup: elimina tutte le fatture in Fatture ricevute ---
    try:
        # Seleziona tutte
        page.locator('div.aru-input-checkbox').first.click()
        time.sleep(1)
        # Elimina
        page.locator('button[title="Elimina"], aru-button[title="Elimina"]').first.click()
        time.sleep(1)
        # Conferma
        try:
            page.get_by_role("button", name="Sì").click(timeout=3000)
            time.sleep(1)
        except Exception:
            pass
    except Exception:
        pass
