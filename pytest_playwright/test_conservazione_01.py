import os
import json
import pytest
from datetime import datetime
from base_pec import LoginPec
from playwright.sync_api import expect

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

CONSERVAZIONE_URL = config["pec"]["url"].rstrip("/") + "/new/messages/INBOX/CONSERVAZIONE"


def test_cartella_da_conservare(page):
    """Verifica la cartella 'Da conservare' nella sidebar:
    accessibilità, URL corretto, testo informativo sul versamento in conservazione.
    Skip se la feature non è disponibile nell'ambiente."""

    LoginPec(page).login_pec(config)

    # Dismetti overlay eventuale
    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Plus tard"), button:has-text("Non ora"), button:has-text("Pas maintenant"), button[aria-label="Chiudi"], [aria-label="Fermer"]').first.click(timeout=2000)
    except Exception:
        pass

    # --- Verifica disponibilità feature ---
    btn_conservazione = page.locator('button[title="Da conservare"], button[title="À conserver"]').first
    if not btn_conservazione.is_visible():
        pytest.skip("Feature 'Da conservare' non disponibile in questo ambiente")

    # --- Clicca "Da conservare" nella sidebar ---
    btn_conservazione.click(force=True)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(1000)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_conservazione_01_click_{datetime.now():%H-%M-%S}.png"))

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_conservazione_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    print(f"URL cartella Da conservare: {page.url}")

    # --- Verifica URL ---
    assert "CONSERVAZIONE" in page.url, \
        f"URL atteso contenere 'CONSERVAZIONE', trovato: {page.url}"

    # --- Verifica testo informativo ---
    testo_atteso = [
        "conservare",
        "conservazione",
        "versati in conservazione",
        "Impostazioni",
    ]
    page_text = page.content().lower()
    trovato = any(t.lower() in page_text for t in testo_atteso)
    assert trovato, "Testo informativo sulla conservazione non trovato nella pagina"

    # --- Verifica link/pulsante alle impostazioni conservazione ---
    impostazioni_btn = page.locator(
        'button:has-text("Impostazioni"), button:has-text("Paramètres"), a:has-text("Impostazioni"), button:has-text("Paramètres"), '
        '[title*="Impostazioni"], [aria-label*="Impostazioni"]'
    )
    # Il bottone "Impostazioni." (con punto) potrebbe essere fuori viewport ma presente nel DOM
    assert impostazioni_btn.count() > 0, \
        "Pulsante/link alle impostazioni di conservazione non trovato"
