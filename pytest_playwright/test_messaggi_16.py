import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper, get_app_base_url
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_copia_messaggio_in_cartella(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Crea una cartella di destinazione
    nome_cartella = "Test copia playwright"
    page.locator('span[title="Crea nuova cartella"]').click()
    folder_input = page.locator('input[placeholder="Nome cartella"]')
    folder_input.wait_for(state="visible", timeout=5000)
    folder_input.fill(nome_cartella)
    # Salva la cartella cliccando il pulsante "Salva" nel CDK overlay pane
    page.locator('.cdk-overlay-pane button:has-text("Salva")').first.click()
    # Aspetta che il dialog si chiuda
    try:
        page.locator('.cdk-overlay-backdrop').wait_for(state="hidden", timeout=5000)
    except Exception:
        pass
    page.wait_for_timeout(500)
    # Naviga direttamente all'inbox per bypassare eventuali backdrop residui
    inbox_url = get_app_base_url(page) + "/new/messages/INBOX"
    page.goto(inbox_url, timeout=20000)
    page.wait_for_load_state("load")

    ts = int(time.time())
    # Invia un messaggio a se stessi
    Helper.crea_messaggio(
        page,
        config,
        oggetto=f"Test copia playwright {ts}",
        corpo="Questo messaggio verrà copiato in una cartella",
    )
    page.locator('span[title="Invia"]').click(force=True)

    # Aspetta consegna
    page.wait_for_timeout(10000)
    page.locator('aru-symbol[title="Aggiorna"]').click(force=True)

    # Apri il messaggio
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)
    page.locator('div.frame-record-desktop').first.click(force=True)
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Clicca Copia
    page.locator('aru-symbol[title="Copia"]').first.click(force=True)
    page.wait_for_timeout(500)

    # Clicca il pulsante della cartella nel dropdown (nth(1) = Content area = dropdown item)
    page.locator(f'button[title="{nome_cartella}"]').nth(1).wait_for(state="visible", timeout=5000)
    page.locator(f'button[title="{nome_cartella}"]').nth(1).click(force=True)
    page.wait_for_timeout(500)

    # Verifica toast (non bloccante)
    try:
        toast = page.locator("div.aru-toast__message").first
        if toast.is_visible():
            print(f"Toast: {toast.text_content()}")
    except Exception:
        pass

    # Verifica: il messaggio è presente nella cartella di destinazione
    page.locator(f'button[title="{nome_cartella}"]').first.click(force=True)
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_16___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert page.locator('div.frame-record-desktop').count() > 0, "La copia del messaggio non è stata trovata nella cartella"

    # Verifica: il messaggio è ancora presente in In arrivo (non rimosso)
    page.locator('button[title="In arrivo"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=5000)

    # Cleanup: elimina la cartella
    page.locator(f'button[title="{nome_cartella}"]').first.click(button="right")
    page.locator('button:has-text("Elimina cartella")').wait_for(state="visible", timeout=5000)
    page.locator('button:has-text("Elimina cartella")').click()
    page.locator('span[title="Elimina"]').click()
