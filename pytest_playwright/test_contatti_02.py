import os
import json
from datetime import datetime
import time
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
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


def test_aggiungere_nuovo_gruppo(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(1)
    page.locator("#contacts").click()
    time.sleep(1)

    ts = int(time.time())
    group_name = f"Test automatico gruppo {ts}"
    contact_name = f"GruppoContact{ts}"

    # Crea un contatto temporaneo da aggiungere al gruppo
    page.get_by_role("button", name="Nuovo").click()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_placeholder("Inserisci nome").fill(contact_name)
    page.get_by_placeholder("Inserisci email").fill(f"gruppocontact_{ts}@pec.it")
    page.get_by_role("button", name="Salva").click()
    time.sleep(2)

    # Crea il gruppo
    page.get_by_role("button", name="Nuovo").click()
    page.locator("#group").check()
    page.get_by_role("button", name="Procedi").click()
    page.get_by_role("textbox", name="input field").click()
    page.get_by_role("textbox", name="input field").fill(group_name)
    page.get_by_role("textbox", name="input search").click()
    page.get_by_role("textbox", name="input search").fill(contact_name)
    time.sleep(1)
    page.get_by_role("checkbox", name=contact_name).first.click()
    page.get_by_role("button", name="Aggiungi contatti").click()
    time.sleep(1)
    page.get_by_role("button", name="Salva").click()

# usa la stessa variabile nell'assert
    expect(
        page.get_by_label("sidebar").get_by_role("button", name=group_name)
    ).to_be_visible()

    
    time.sleep(1)
    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    print(f"Screenshot salvato in: {screenshot_path}")

    # Cleanup: elimina il gruppo creato
    try:
        group_btn = page.locator(f'button[title="{group_name}"]').first
        group_btn.click(button="right")
        time.sleep(1)
        for sel in ['button:has-text("Elimina gruppo")', 'button:has-text("Elimina")', '[role="menuitem"]:has-text("Elimina")']:
            item = page.locator(sel).first
            if item.is_visible():
                item.click()
                time.sleep(1)
                break
        try:
            page.get_by_role("button", name="Sì").click(timeout=2000)
            time.sleep(1)
        except Exception:
            pass
    except Exception:
        pass

    # Cleanup: elimina il contatto temporaneo
    try:
        search = page.locator('input[placeholder*="Cerca tra i contatti"]').first
        search.click()
        search.fill(contact_name)
        time.sleep(1)
        row = page.locator('div.frame-record-desktop').filter(has_text=contact_name).first
        row.hover()
        row.locator('aru-input-choice, input[type="checkbox"]').first.click(force=True)
        time.sleep(1)
        page.locator('aru-symbol[title="Elimina"], button[title="Elimina"]').first.click()
        page.get_by_role("button", name="Sì").first.click(timeout=2000)
        time.sleep(1)
    except Exception:
        pass
