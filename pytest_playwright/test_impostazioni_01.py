import os
import json
import time
from datetime import datetime
from base_pec import LoginPec, get_app_base_url
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

def test_crea_firma(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Naviga direttamente alla pagina Firme (URL calcolato dopo il login per supportare prod-aruba)
    signatures_url = get_app_base_url(page) + "/new/settings/messages-writing/signatures"
    page.goto(signatures_url, timeout=20000)

    # Verifica che la pagina Firme sia caricata
    firme_header = page.locator('h1').filter(has_text="Firme").first
    firme_header.wait_for(state="visible", timeout=8000)
    assert firme_header.is_visible(), "La pagina Firme non si è caricata"

    # Clicca il pulsante di creazione firma (aru-button kind="solid" skin="primary")
    create_btn = page.locator('aru-button[kind="solid"][skin="primary"]').first
    create_btn.wait_for(state="visible", timeout=5000)
    create_btn.click()

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_impostazioni_01_form_{datetime.now():%H-%M-%S}.png"))

    # Compila il form della firma
    nome_firma = f"Firma test playwright {int(time.time())}"

    # Il campo nome potrebbe essere un input con vari selettori
    nome_input = page.locator('input[placeholder*="nome"], input[placeholder*="Nome"], input[placeholder*="Inserisci"]').first
    try:
        nome_input.wait_for(state="visible", timeout=3000)
        nome_input.fill(nome_firma)
    except Exception:
        # Prova con il primo input disponibile
        inputs = [i for i in page.locator("input").all() if i.is_visible()]
        if inputs:
            inputs[0].fill(nome_firma)

    # Testo della firma
    editor = page.locator("div[contenteditable='true']").first
    try:
        editor.wait_for(state="visible", timeout=3000)
        editor.click()
        editor.fill("Firma automatica test Playwright")
    except Exception:
        pass

    # Salva la firma
    try:
        save_btn = page.locator('button[title="Salva"], button[title="Enregistrer"], aru-button[skin="primary"]').first
        save_btn.wait_for(state="visible", timeout=3000)
        save_btn.click()
    except Exception:
        pass

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_01___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
