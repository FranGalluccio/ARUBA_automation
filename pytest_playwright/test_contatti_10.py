import os
import json
from datetime import datetime
import time
from playwright.sync_api import sync_playwright
from base_pec import LoginPec
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_elimina_gruppo(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    time.sleep(2)
    page.click("#contacts")
    time.sleep(2)

    # Crea un gruppo da eliminare
    group_name = f"Gruppo test {int(time.time())}"

    page.get_by_role("button", name="Nuovo").click()
    # Seleziona "Gruppo" nel dialog
    try:
        page.locator("#group").check()
    except:
        try:
            page.locator('input[value="group"], label:has-text("Gruppo")').first.click()
        except:
            pass
    page.get_by_role("button", name="Procedi").click()
    time.sleep(1)

    # Inserisci il nome del gruppo
    page.get_by_role("textbox", name="input field").fill(group_name)

    # Cerca e aggiungi almeno un contatto (se disponibile)
    try:
        search_box = page.get_by_role("textbox", name="input search")
        search_box.click()
        search_box.fill("test")
        time.sleep(1)
        cb = page.get_by_role("checkbox").first
        if cb.count() > 0:
            cb.click()
        page.get_by_role("button", name="Aggiungi contatti").click()
        time.sleep(1)
    except:
        pass

    page.get_by_role("button", name="Salva").click()
    time.sleep(3)

    # Verifica che il gruppo sia stato creato nella sidebar
    group_btn = page.locator(f'button[title="{group_name}"]').first
    group_btn.wait_for(state="visible", timeout=8000)
    assert group_btn.is_visible(), f"Il gruppo '{group_name}' non è visibile nella sidebar"

    # Tasto destro sul gruppo per il menu contestuale
    group_btn.click(button="right")
    time.sleep(1)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_10_menu_{datetime.now():%H-%M-%S}.png"))

    # Cerca voci del menu contestuale
    menu_item_found = False
    for selector in [
        'aru-menu-item:has-text("Elimina")',
        'button:has-text("Elimina gruppo")',
        'button:has-text("Elimina")',
        '[role="menuitem"]:has-text("Elimina")',
        'li:has-text("Elimina")',
    ]:
        try:
            item = page.locator(selector).first
            if item.is_visible():
                item.click()
                menu_item_found = True
                time.sleep(1)
                break
        except:
            pass

    assert menu_item_found, "Voce 'Elimina' non trovata nel menu contestuale del gruppo"

    # Conferma eliminazione - la dialog mostra "Elimina" come pulsante di conferma nel CDK overlay
    time.sleep(1)
    try:
        confirm_btn = page.locator('.cdk-overlay-pane button:has-text("Elimina")').first
        confirm_btn.wait_for(state="visible", timeout=3000)
        confirm_btn.click()
    except Exception:
        # Fallback: prova altri selettori
        for confirm_sel in [
            'button[title="Si"]', 'button:has-text("Sì")', 'button:has-text("Si")',
        ]:
            try:
                btn = page.locator(confirm_sel).first
                if btn.is_visible():
                    btn.click()
                    break
            except Exception:
                pass
    time.sleep(3)

    # Verifica che il gruppo non sia più presente nella sidebar
    remaining = page.locator(f'button[title="{group_name}"]').count()
    assert remaining == 0, \
        f"Il gruppo '{group_name}' è ancora presente dopo l'eliminazione"

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_contatti_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
