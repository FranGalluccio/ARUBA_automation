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
    page.goto(config["pec"]["url"], timeout=30_000)
    page.wait_for_load_state("load")

    # Accetta cookie (se presente)
    try:
        page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
    except Exception:
        pass

    # Compila username con valore errato
    page.locator("input[name='username'], input#username, input[type='email']").first.fill(TEST_NONEXISTENT_EMAIL)

    # Compila password con valore errato
    page.locator("input[name='password'], input#password, input[type='password']").first.fill(TEST_INVALID_PASSWORD)

    # Clicca login
    page.locator("button[type='submit'], button:has-text('Login')").first.click()

    # Attendi che la pagina risponda (errore o redirect)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    # Verifica che l'URL non contenga INBOX (login fallito, nessun redirect alla casella)
    assert "INBOX" not in page.url, f"Il login con credenziali errate ha avuto successo inaspettatamente. URL: {page.url}"

    # Verifica che il messaggio di errore sia visibile
    # - Aruba test: div.errorWeb
    # - Keycloak (SMB prod): #input-error, div.alert-error, .pf-c-alert, span[class*="feedback"]
    # Aruba test: div.errorWeb
    # Keycloak standard: #input-error, .pf-c-alert__description, div[aria-live='polite']
    # SMB Keycloak (layout francese): span.px-2 dentro #kc-content-wrapper
    error_selectors = [
        "div.errorWeb",
        "#input-error",
        "span#input-error",
        "div.alert-error",
        "[class*='alert-error']",
        "[class*='kc-feedback']",
        "[class*='login-alert']",
        ".pf-c-alert__description",
        "div[aria-live='polite']:not(:empty)",
        # Keycloak SMB (con #kc-content-wrapper) e main PEC (span.px-2 standalone)
        "#kc-content-wrapper span.px-2",
        "span.px-2",
    ]
    error_message = None
    for sel in error_selectors:
        el = page.locator(sel).first
        if el.count() > 0 and el.is_visible():
            error_message = el
            break

    assert error_message is not None, "Nessun messaggio di errore login trovato nella pagina"

    err_text = error_message.inner_text()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_login_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert any(kw in err_text.lower() for kw in [
        "dati inseriti", "details", "incorrect", "not correct",
        "correttamente", "invalid", "non valid", "errat", "credenziali",
        # francese (SMB Keycloak)
        "informations", "saisies", "incorrectes", "verifier", "reessayer",
    ]), f"Messaggio di errore login inatteso: '{err_text}'"
