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

    # Login a due step su domini "Aruba Mail" generici: il campo password
    # appare solo dopo aver cliccato "Prosegui"/"Continua" sul solo username
    # (stesso comportamento gestito in base_pel.LoginPel.login_pel).
    password_input = page.locator("input[name='password'], input[type='password']")
    if password_input.count() == 0:
        prosegui_btn = page.locator('button:has-text("Prosegui"), button:has-text("Continua")').first
        prosegui_btn.click()
        password_input.first.wait_for(state="visible", timeout=15_000)

    # Compila password con valore errato
    password_input.first.fill(TEST_INVALID_PASSWORD)

    # Clicca login. Selettore allineato a base_pel.LoginPel.login_pel: su PEL
    # Domini (SSO/Keycloak, form a step unico) il bottone "Accedi" non è un
    # aru-button[skin='primary'] come su PEL Staff, serve il fallback.
    accedi_btn = page.locator("button[title='Accedi']").first
    if accedi_btn.count() == 0:
        accedi_btn = page.locator("button[type='submit'], button:has-text('Login'), button:has-text('Accedi'), aru-button[skin='primary']").first
    accedi_btn.click()

    # Aspetta risposta del server
    page.wait_for_timeout(3000)

    # Verifica che l'URL non contenga INBOX (login fallito)
    assert "INBOX" not in page.url, \
        f"Il login con credenziali errate ha avuto successo inaspettatamente. URL: {page.url}"

    # Verifica che il form di login sia ancora visibile (siamo rimasti sulla pagina di login).
    # Dopo credenziali errate l'app torna allo step 1 (solo email): stesso
    # selettore completo usato per username_input, altrimenti il campo
    # email (type='email', senza name='text'/'username') non viene trovato.
    login_form = page.locator("input[name='text'], input[name='username'], input#username, input[type='email']").first
    login_form.wait_for(state="visible", timeout=10000)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    expect(login_form).to_be_visible()
