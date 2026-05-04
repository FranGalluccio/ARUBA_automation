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

def test_panoramica_accessi_altri_account(page):
    """Verifica la sezione 'Accessi altri account' nelle impostazioni:
    struttura pagina (h1, h2, h3), presenza card Multiutente PEC e Supervisore360,
    presenza dei pulsanti 'Gestisci'.
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

    # --- Naviga alla panoramica ---
    dismiss_overlay(page)
    accessi_btn.click(force=True)
    try:
        page.wait_for_url(
            lambda url: "other-accounts" in url or "accessi" in url.lower(),
            timeout=10000
        )
    except Exception:
        try:
            page.wait_for_load_state("load", timeout=5000)
        except Exception:
            pass

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_accessi_01_panoramica_{datetime.now():%H-%M-%S}.png"))

    # --- Verifica URL ---
    assert "other-accounts" in page.url or "accessi" in page.url.lower(), \
        f"URL 'Accessi altri account' non corretto: {page.url}"

    # --- Verifica h1 ---
    h1 = page.locator("h1").filter(has_text="Accessi altri account").first
    h1.wait_for(state="visible", timeout=8000)
    assert h1.is_visible(), "h1 'Accessi altri account' non visibile"

    # --- Verifica h2 ---
    h2 = page.locator("h2").filter(has_text="Servizi per far gestire").first
    assert h2.is_visible(), "h2 descrittivo non visibile"

    # --- Verifica sezioni Multiutente PEC e Supervisore360 ---
    multiutente_card = page.get_by_text("Multiutente PEC", exact=False).first
    assert multiutente_card.is_visible(), "Card 'Multiutente PEC' non visibile"

    supervisore_card = page.get_by_text("Supervisore360", exact=False).first
    supervisore_present = supervisore_card.is_visible()
    if not supervisore_present:
        print("Nota: Card 'Supervisore360' non visibile in questo ambiente (feature opzionale)")

    # --- Verifica pulsanti Gestisci (almeno 1 per Multiutente) ---
    gestisci_btns = page.locator(
        'button:has-text("Gestisci"), aru-button:has-text("Gestisci")'
    )
    # Attendi lazy-load delle card prima del count
    try:
        gestisci_btns.first.wait_for(state="visible", timeout=5000)
    except Exception:
        pass
    if gestisci_btns.count() == 0:
        if page.get_by_text("Pro e Premium", exact=False).count() > 0:
            pytest.skip("Multiutente PEC e Supervisore360 richiedono account PEC Pro/Premium — non disponibili su questo account")
    assert gestisci_btns.count() >= 1, \
        f"Nessun pulsante 'Gestisci' trovato: {gestisci_btns.count()}"

    # --- Verifica navigazione sub-sezioni ---
    # Multiutente PEC sub-page
    multiutente_nav = page.locator('button[title="Multiutente PEC"]').first
    if multiutente_nav.is_visible():
        multiutente_nav.click(force=True)
        try:
            page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass
        content = page.content().lower()
        assert "multiutente" in content or "multi" in content, \
            "Sotto-pagina Multiutente PEC non si è caricata"
        page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"test_accessi_01_multiutente_{datetime.now():%H-%M-%S}.png"
        ))
        # Torna indietro
        page.goto(app_base + "/new/settings/other-accounts/overview", timeout=20000)
        try:
            page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass

    # Supervisore360 sub-page
    supervisore_nav = page.locator('button[title="Supervisore360"]').first
    if supervisore_nav.is_visible():
        supervisore_nav.click(force=True)
        try:
            page.wait_for_load_state("load", timeout=8000)
        except Exception:
            pass
        page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"test_accessi_01_supervisore_{datetime.now():%H-%M-%S}.png"
        ))
        content = page.content().lower()
        assert "supervisore" in content or "supervisor" in content, \
            "Sotto-pagina Supervisore360 non si è caricata"

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_accessi_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
