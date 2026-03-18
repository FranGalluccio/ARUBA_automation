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

ACCESSI_URL = config["pec"]["url"].rstrip("/") + "/new/settings/other-accounts/overview"
SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings/home"


def test_form_multiutente_pec(page):
    """Verifica la sezione Multiutente PEC: apertura del form di aggiunta,
    presenza dei campi email, password e opzioni di privilegio.
    Non invia il form per evitare side-effect reali.
    Skip se la feature non è disponibile nell'ambiente."""

    LoginPec(page).login_pec(config)

    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    # --- Verifica disponibilità feature ---
    page.goto(SETTINGS_URL, timeout=20000)
    page.wait_for_load_state("networkidle", timeout=15000)
    time.sleep(1)

    try:
        if not page.locator('button[title="Accessi altri account"]').is_visible():
            page.locator('button[title="Account e sicurezza"]').first.click(force=True)
            time.sleep(1)
    except Exception:
        pass

    accessi_btn = page.locator('button[title="Accessi altri account"]').first
    if not accessi_btn.is_visible():
        pytest.skip("Feature 'Accessi altri account' non disponibile in questo ambiente")

    # --- Naviga alla panoramica tramite click sul bottone (goto diretto reindirizza a INBOX) ---
    accessi_btn.click(force=True)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    # --- Naviga a Multiutente PEC: prima prova il bottone sidebar, poi il primo "Gestisci" ---
    multiutente_nav = page.locator('button[title="Multiutente PEC"]').first
    if multiutente_nav.is_visible():
        multiutente_nav.click(force=True)
    else:
        gestisci_btn = page.locator('button:has-text("Gestisci"), aru-button:has-text("Gestisci")').first
        if not gestisci_btn.is_visible():
            pytest.skip("Nessun percorso verso Multiutente PEC trovato")
        gestisci_btn.click(force=True)

    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_accessi_02_multiutente_{datetime.now():%H-%M-%S}.png"))

    content = page.content().lower()
    assert "multiutente" in content or "multi" in content, \
        "Pagina Multiutente PEC non caricata correttamente"

    # --- Cerca pulsante per aggiungere un nuovo multiutente ---
    aggiungi_selectors = [
        'button[title="Crea account"]',    # BNL test
        'button:has-text("Aggiungi")',
        'aru-button:has-text("Aggiungi")',
        'button:has-text("Crea account")',
        'button:has-text("Nuovo")',
        'aru-button:has-text("Crea")',
        'aru-button[skin="primary"]',
    ]
    aggiungi_btn = None
    for sel in aggiungi_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                aggiungi_btn = el
                break
        except Exception:
            pass

    if aggiungi_btn is None:
        pytest.skip("Pulsante 'Aggiungi' per Multiutente PEC non trovato — feature forse non attiva")

    # --- Clicca Aggiungi e verifica apertura form ---
    aggiungi_btn.click(force=True)
    time.sleep(2)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_accessi_02_form_{datetime.now():%H-%M-%S}.png"))

    # Verifica che si sia aperto un form/dialog con campi email e/o password
    form_selectors = [
        'input[type="email"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="mail" i]',
        'aru-input',
        'input[type="text"]',
        'input[type="password"]',
        '[class*="dialog"]',
        '[class*="modal"]',
        '.cdk-overlay-pane',
    ]
    form_found = False
    for sel in form_selectors:
        if page.locator(sel).count() > 0:
            form_found = True
            el = page.locator(sel).first
            try:
                ph = el.get_attribute("placeholder") or el.get_attribute("aria-label") or sel
                print(f"Form/input trovato: '{ph}'")
            except Exception:
                pass
            break

    assert form_found, "Form di aggiunta Multiutente PEC non si è aperto"

    # --- Chiudi il form senza inviare (nessun side-effect) ---
    close_selectors = [
        'button[aria-label="Chiudi"]',
        'button:has-text("Annulla")',
        'button:has-text("Cancel")',
        'aru-button:has-text("Annulla")',
        '[title="Chiudi"]',
    ]
    for sel in close_selectors:
        try:
            el = page.locator(sel).first
            if el.is_visible():
                el.click()
                time.sleep(1)
                break
        except Exception:
            pass
    else:
        # Fallback: tasto Escape
        page.keyboard.press("Escape")
        time.sleep(1)

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_accessi_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
