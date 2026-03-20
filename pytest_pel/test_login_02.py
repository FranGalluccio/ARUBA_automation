import os
import json
from datetime import datetime
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

TEST_NONEXISTENT_EMAIL = config.get("test_nonexistent_email", "utente_inesistente@pec.it")
TEST_INVALID_PASSWORD = config.get("test_invalid_password", "PasswordErrata123!")


def test_login_credenziali_errate(page):
    # Vai alla pagina di login
    page.goto(config["pel"]["url"], timeout=30_000)

    # Accetta cookie prima che blocchi il form
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=5000)
    except Exception:
        pass

    # Aspetta che il campo username sia visibile (caricamento asincrono)
    username_input = page.locator("input[name='text'], input[name='username'], input#username, input[type='email']").first
    username_input.wait_for(state="visible", timeout=15_000)

    # Compila username con valore errato
    username_input.fill(TEST_NONEXISTENT_EMAIL)

    # Compila password con valore errato
    page.locator("input[name='password'], input[type='password']").first.fill(TEST_INVALID_PASSWORD)

    # Clicca login (il bottone è un web component aru-button, non un button standard)
    page.locator("aru-button[skin='primary']").first.click()

    # Aspetta risposta del server
    page.wait_for_timeout(3000)

    # Verifica che l'URL non contenga INBOX (login fallito)
    assert "INBOX" not in page.url, \
        f"Il login con credenziali errate ha avuto successo inaspettatamente. URL: {page.url}"

    # Verifica che il form di login sia ancora visibile (siamo rimasti sulla pagina di login)
    login_form = page.locator("input[name='text'], input[name='username']").first
    login_form.wait_for(state="visible", timeout=10000)
    expect(login_form).to_be_visible()

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
