import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_login_credenziali_errate(page):
    # Vai alla pagina di login
    page.goto(config["pec"]["url"], timeout=30_000)
    page.wait_for_load_state("networkidle")

    # Accetta cookie (se presente)
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
    except:
        pass

    # Compila username con valore errato
    page.locator("input[name='username'], input#username, input[type='email']").first.fill("utente_inesistente@pec.it")

    # Compila password con valore errato
    page.locator("input[name='password'], input#password, input[type='password']").first.fill("PasswordErrata123!")

    # Clicca login
    page.locator("button[type='submit'], button:has-text('Login')").first.click()

    time.sleep(2)

    # Verifica che l'URL non contenga INBOX (login fallito, nessun redirect alla casella)
    assert "INBOX" not in page.url, f"Il login con credenziali errate ha avuto successo inaspettatamente. URL: {page.url}"

    # Verifica che il messaggio di errore sia visibile
    error_message = page.locator("div.errorWeb")
    expect(error_message).to_be_visible()
    assert "I dati inseriti non sono corretti" in error_message.inner_text()

    time.sleep(1)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")
