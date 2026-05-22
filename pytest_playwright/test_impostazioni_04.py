import os
import json
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

def test_risposta_automatica(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Vai alle impostazioni → Avvisi e report (URL calcolato dopo il login per supportare prod-aruba)
    page.goto(get_app_base_url(page) + "/new/settings/home", timeout=20000)
    # Espandi l'accordion "Messaggi e scrittura" se necessario
    if not page.locator('button[title="Avvisi e report"], button[title="Alertes et rapports"], button[title="Notifications et rapports"]').is_visible():
        _accordion = page.locator(
            'button[title="Messaggi e scrittura"], button[title="Messages et rédaction"]'
        ).or_(page.locator('button').filter(has_text="Messaggi e scrittura")).or_(
            page.locator('button').filter(has_text="Messages et")
        ).first
        _accordion.click(force=True)
        page.locator('button[title="Avvisi e report"], button[title="Alertes et rapports"], button[title="Notifications et rapports"]').first.wait_for(state="visible", timeout=5000)
    page.locator('button[title="Avvisi e report"], button[title="Alertes et rapports"], button[title="Notifications et rapports"]').click(force=True)

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_impostazioni_04_pre_{datetime.now():%H-%M-%S}.png"))

    # Verifica che la pagina Avvisi e report sia caricata controllando elementi specifici di questa sezione
    page.locator('aru-tab-group, aru-table').first.wait_for(state="visible", timeout=8000)
    avvisi_loaded = (
        page.get_by_role("heading", name="Avvisi e report").count() > 0 or
        page.locator('aru-tab-group, aru-table').first.is_visible()
    )

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_impostazioni_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert avvisi_loaded, "La pagina Avvisi e report non si è caricata"
