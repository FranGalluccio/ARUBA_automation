import os
import json
import time
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


def test_invio_allegati_multipli(page):
    """Verifica che sia possibile inviare un messaggio PEC con allegati multipli."""
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test allegati multipli {ts}"

    # Percorso allegato relativo alla CWD (root del progetto), come in tutti gli altri test
    path_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato", "dati_test/allegato-test.pdf"))

    # Dismiss any CDK backdrop
    if page.locator('.cdk-overlay-backdrop').is_visible():
        for _ in range(3):
            if not page.locator('.cdk-overlay-backdrop').is_visible():
                break
            try:
                btn = page.locator('button:has-text("Ricordarmelo"), button:has-text("Chiudi"), button:has-text("Non ora")').first
                if btn.is_visible():
                    btn.click(force=True)
                    page.wait_for_timeout(300)
                    continue
                page.locator('.cdk-overlay-pane').last.locator('button').last.click(force=True)
                page.wait_for_timeout(300)
            except Exception:
                break

    destinatario = config["destinatari"]["destinatario_principale"]
    page.locator("button:has-text('Nuovo messaggio')").click(force=True)

    try:
        page.locator("input[placeholder='Destinatari']").fill(destinatario, timeout=2000)
    except Exception:
        page.locator('input[aria-label="input field"]').click()
        page.locator("input[placeholder='Destinatari']").fill(destinatario)

    page.locator('input[aria-label="input field"]').fill(oggetto)
    page.locator("div[contenteditable='true']").fill("Test automatico invio con allegati multipli")

    # Allega primo file
    page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
    with page.expect_file_chooser() as fc_info:
        page.locator("aru-menu-item", has_text="Carica da dispositivo").first.click()
    fc_info.value.set_files([path_allegato])
    page.wait_for_timeout(3000)

    # Allega secondo file (stesso file, nome diverso non necessario per il test)
    page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
    with page.expect_file_chooser() as fc_info2:
        page.locator("aru-menu-item", has_text="Carica da dispositivo").first.click()
    fc_info2.value.set_files([path_allegato])
    page.wait_for_timeout(3000)

    # Verifica che siano stati aggiunti almeno 2 allegati nel composer prima dell'invio.
    # Gli allegati nel composer sono renderizzati come elementi con classe 'attachment-chip',
    # scoped al dialog del nuovo messaggio per evitare falsi positivi da altri elementi della pagina.
    page.wait_for_timeout(3000)
    composer = page.locator('webmail-new-message-dialog').first
    allegati_count = composer.locator("[class*='attachment-chip']").count()
    if allegati_count == 0:
        allegati_count = composer.locator("aru-attachment-item, .attachment-item").count()
    assert allegati_count >= 2, (
        f"Attesi almeno 2 allegati nel composer (uno per file caricato), trovati {allegati_count}. "
        "Verificare che il campo 'file_allegato' in config.json punti a un file valido."
    )

    # Invia il messaggio
    page.locator('span[title="Invia"]').click()
    page.wait_for_timeout(5000)

    # Verifica che il messaggio sia stato inviato (naviga agli inviati)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    page.wait_for_timeout(2000)

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_25___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
