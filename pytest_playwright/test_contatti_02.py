import os
import json
import time
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

TEST_EMAIL_DOMAIN = config.get("test_email_domain", "pec.it")


def test_aggiungere_nuovo_gruppo(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    page.locator("#contacts").click()
    page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=10000)

    ts = int(time.time())
    group_name = f"Test automatico gruppo {ts}"
    contact_name = f"GruppoContact{ts}"

    try:
        # Crea un contatto temporaneo da aggiungere al gruppo
        page.get_by_role("button", name="Nuovo", exact=True).click()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_placeholder("Inserisci nome").fill(contact_name)
        page.get_by_placeholder("Inserisci email").fill(f"gruppocontact_{ts}@{TEST_EMAIL_DOMAIN}")
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()
        page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

        # Crea il gruppo
        page.get_by_role("button", name="Nuovo", exact=True).click()
        page.locator("#group").check()
        page.get_by_role("button", name="Procedi").click()
        page.get_by_role("textbox", name="input field").click()
        page.get_by_role("textbox", name="input field").fill(group_name)
        page.get_by_role("textbox", name="input search").click()
        page.get_by_role("textbox", name="input search").fill(contact_name)
        page.get_by_role("checkbox", name=contact_name).first.wait_for(state="visible", timeout=5000)
        page.get_by_role("checkbox", name=contact_name).first.click()
        page.locator('button:has-text("Aggiungi contatti"), button:has-text("Ajouter des contacts")').first.click()
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.wait_for(state="visible", timeout=5000)
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

        # Percorso screenshot dinamico
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        expect(
            page.get_by_label("sidebar").get_by_role("button", name=group_name)
        ).to_be_visible()

    finally:
        # Cleanup: elimina il gruppo creato
        try:
            group_btn = page.locator(f'button[title="{group_name}"]').first
            if group_btn.count() > 0:
                group_btn.click(button="right")
                page.locator('aru-menu-item:has-text("Elimina"), button:has-text("Supprimer"), button:has-text("Elimina gruppo"), button:has-text("Supprimer le groupe"), button:has-text("Elimina"), button:has-text("Supprimer"), [role="menuitem"]:has-text("Elimina"), button:has-text("Supprimer")').first.wait_for(state="visible", timeout=3000)
                for sel in [
                    'aru-menu-item:has-text("Elimina"), button:has-text("Supprimer")',
                    'button:has-text("Elimina gruppo"), button:has-text("Supprimer le groupe")',
                    'button:has-text("Elimina"), button:has-text("Supprimer")',
                    '[role="menuitem"]:has-text("Elimina"), button:has-text("Supprimer")',
                ]:
                    item = page.locator(sel).first
                    if item.is_visible():
                        item.click()
                        break
                for confirm_sel in [
                    '.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")',
                    'button[title="Si"], button[title="Oui"]', 'button:has-text("Sì")',
                ]:
                    try:
                        btn = page.locator(confirm_sel).first
                        if btn.is_visible():
                            btn.click()
                            break
                    except Exception:
                        pass
        except Exception:
            pass

        # Cleanup: seleziona tutti i contatti ed elimina
        try:
            page.locator("#contacts").click()
            page.locator('button[title="Tutti i contatti"]').first.wait_for(state="visible", timeout=5000)
            page.locator('button[title="Tutti i contatti"]').first.click()
            page.wait_for_timeout(2000)
            page.locator('span.aru-input-checkbox__checkmark').first.wait_for(state="visible", timeout=5000)
            page.locator('span.aru-input-checkbox__checkmark').first.click(force=True)
            page.locator('aru-symbol[title="Elimina"], aru-symbol[title="Supprimer"], button[title="Elimina"]').first.click()
            try:
                page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.wait_for(state="visible", timeout=5000)
                page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first.click()
            except Exception:
                page.locator('button[title="Si"], button[title="Oui"], button:has-text("Sì")').first.click(timeout=2000)
        except Exception:
            pass
