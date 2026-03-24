import os
import json
import pytest
from datetime import datetime
from base_pec import LoginPec

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings/home"
LEGGI_FATTURE_URL = config["pec"]["url"].rstrip("/") + "/new/settings/read-invoices"


def test_leggi_fatture_settings(page):
    """Verifica la sezione 'Leggi fatture' nelle impostazioni:
    accessibilità pagina, presenza h1, contenuto informativo sul cassetto fiscale.
    Skip se la feature non è disponibile nell'ambiente."""

    LoginPec(page).login_pec(config)

    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    # --- Verifica disponibilità feature (check da settings home) ---
    page.goto(SETTINGS_URL, timeout=20000)
    page.wait_for_load_state("load", timeout=15000)

    # Espandi accordion "Account e sicurezza" se necessario
    try:
        if not page.locator('button[title="Leggi fatture"]').is_visible():
            page.locator('button[title="Account e sicurezza"]').first.click(force=True)
            page.locator('button[title="Leggi fatture"]').first.wait_for(state="visible", timeout=5000)
    except Exception:
        pass

    leggi_fatture_btn = page.locator('button[title="Leggi fatture"]').first
    if not leggi_fatture_btn.is_visible():
        pytest.skip("Feature 'Leggi fatture' non disponibile in questo ambiente")

    # --- Naviga alla pagina Leggi fatture ---
    leggi_fatture_btn.click(force=True)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_fatture_02_pagina_{datetime.now():%H-%M-%S}.png"))

    # Verifica URL
    assert "read-invoices" in page.url or "fattur" in page.url.lower() or \
           "leggi" in page.url.lower(), \
        f"URL 'Leggi fatture' non corretto: {page.url}"

    # --- Verifica h1 ---
    h1 = page.locator("h1").filter(has_text="Leggi fatture").first
    h1.wait_for(state="visible", timeout=8000)

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_fatture_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    print(f"URL Leggi fatture: {page.url}")
    assert h1.is_visible(), "h1 'Leggi fatture' non visibile"

    # --- Verifica contenuto informativo ---
    content = page.content().lower()
    keywords = ["fattur", "cassetto fiscale", "fatturazione", "invoice"]
    assert any(k in content for k in keywords), \
        "Contenuto informativo sulla fatturazione non trovato nella pagina"
