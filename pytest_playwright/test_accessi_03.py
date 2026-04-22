import os
import json
import pytest
from datetime import datetime
from base_pec import LoginPec, get_app_base_url, dismiss_overlay

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

def test_form_supervisore360(page):
    """Verifica la sezione Supervisore360: apertura del form di aggiunta delega,
    presenza del campo email/delegato.
    Non invia il form per evitare side-effect reali.
    Skip se la feature non è disponibile nell'ambiente."""

    LoginPec(page).login_pec(config)
    app_base = get_app_base_url(page)

    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    # --- Verifica disponibilità feature ---
    page.goto(app_base + "/new/settings/home", timeout=20000)
    page.wait_for_load_state("load", timeout=15000)

    try:
        if not page.locator('button[title="Accessi altri account"]').is_visible():
            page.locator('button[title="Account e sicurezza"]').first.click(force=True)
            page.locator('button[title="Accessi altri account"]').first.wait_for(state="visible", timeout=5000)
    except Exception:
        pass

    accessi_btn = page.locator('button[title="Accessi altri account"]').first
    if not accessi_btn.is_visible():
        pytest.skip("Feature 'Accessi altri account' non disponibile in questo ambiente")

    # --- Naviga alla panoramica tramite click sul bottone (goto diretto reindirizza a INBOX) ---
    dismiss_overlay(page)
    accessi_btn.click(force=True)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(1500)

    # --- Verifica che Supervisore360 sia presente nella panoramica ---
    supervisore_in_overview = (
        page.get_by_text("Supervisore360", exact=False).count() > 0 or
        page.get_by_text("Supervisore 360", exact=False).count() > 0 or
        page.locator('[title*="Supervisore"]').count() > 0 or
        page.locator('[aria-label*="Supervisore"]').count() > 0
    )
    if not supervisore_in_overview:
        if "bnl" in page.url.lower():
            pytest.skip("Feature 'Supervisore360' non disponibile su BNL")
        assert False, "Supervisore360 non trovato nella pagina 'Accessi altri account'"

    # --- Naviga a Supervisore360 ---
    supervisore_nav = page.locator('[title*="Supervisore"], [aria-label*="Supervisore"]').first
    if supervisore_nav.count() > 0:
        supervisore_nav.click(force=True)
        page.wait_for_timeout(1000)
    else:
        if "bnl" in page.url.lower():
            pytest.skip("Nessun percorso verso Supervisore360 su BNL")
        assert False, "Nessun percorso verso Supervisore360 trovato"

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_accessi_03_supervisore_{datetime.now():%H-%M-%S}.png"))

    content = page.content().lower()
    assert "supervisore" in content or "supervisor" in content or "delega" in content, \
        "Pagina Supervisore360 non caricata correttamente"

    # --- Cerca pulsante per aggiungere nuova delega ---
    aggiungi_selectors = [
        'button:has-text("Delega supervisore")',
        'aru-button:has-text("Delega supervisore")',
        'button:has-text("Aggiungi")',
        'aru-button:has-text("Aggiungi")',
        'button:has-text("Nuova delega")',
        'button:has-text("Nuovo")',
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
        pytest.skip("Pulsante 'Aggiungi delega' per Supervisore360 non trovato — feature forse non attiva")

    # --- Clicca Aggiungi e verifica apertura form ---
    aggiungi_btn.click(force=True)
    try:
        page.locator('.cdk-overlay-pane').first.wait_for(state="visible", timeout=5000)
    except Exception:
        page.wait_for_timeout(1000)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_accessi_03_form_{datetime.now():%H-%M-%S}.png"))

    # Verifica form/dialog aperto con campo email supervisore
    form_selectors = [
        'input[type="email"]',
        'input[placeholder*="email" i]',
        'input[placeholder*="supervisore" i]',
        'input[placeholder*="delega" i]',
        'aru-input',
        'input[type="text"]',
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

    # Screenshot finale (form ancora aperto)
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_accessi_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert form_found, "Form di aggiunta Supervisore360 non si è aperto"

    # --- Chiudi senza inviare ---
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
                break
        except Exception:
            pass
    else:
        page.keyboard.press("Escape")
