import os
import json
from datetime import datetime
from base_pec import LoginPec, Helper
from playwright.sync_api import sync_playwright, expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_creazione_calendario(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Crea nuovo calendario
    page.locator('button:has-text("Calendario"), button:has-text("Calendrier")').first.click()
    page.get_by_role("button", name="Nuovo calendario").click()
    page.get_by_role("textbox", name="input field").wait_for(state="visible", timeout=5000)
    page.get_by_role("textbox", name="input field").click()
    page.get_by_role("textbox", name="input field").fill("Lavoro")
    page.locator("aru-webmail-input-color").get_by_role("button").click()
    page.locator(".aru-webmail-color-dot").first.click()
    page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()
    # Verifica creazione calendario — aspetta la toast (scompare rapidamente)
    toast = page.locator("div.aru-toast__message").first
    toast.wait_for(state="visible", timeout=8000)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_calendario_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert "Il calendario è stato creato." in toast.text_content()

    # Cleanup: elimina calendario creato
    try:
        page.get_by_role("checkbox", name="Lavoro").first.wait_for(state="visible", timeout=5000)
        page.get_by_role("checkbox", name="Lavoro").first.click(button="right")
        page.locator('[role="menuitem"]:has-text("Elimina"), [role="menuitem"]:has-text("Supprimer")').first.wait_for(state="visible", timeout=3000)
        page.locator('[role="menuitem"]:has-text("Elimina"), [role="menuitem"]:has-text("Supprimer")').first.click()
        page.locator('button:has-text("Sì"), button:has-text("Oui")').first.wait_for(state="visible", timeout=3000)
        page.locator('button:has-text("Sì"), button:has-text("Oui")').first.click()
    except Exception:
        pass
