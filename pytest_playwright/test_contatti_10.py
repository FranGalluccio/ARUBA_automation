import os
import json
import time
from datetime import datetime
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

    page.click("#contacts")
    page.locator('button[title="Tutti i contatti"], button[title="Tous les contacts"]').first.wait_for(state="visible", timeout=10000)

    # Crea un gruppo da eliminare
    group_name = f"Gruppo test {int(time.time())}"

    page.locator('button:has-text("Nuovo"), button:has-text("Nouveau")').first.click()
    # Seleziona "Gruppo" nel dialog (via JS per evitare il locator handler CDK)
    page.wait_for_timeout(500)
    page.evaluate("() => { const g = document.querySelector('#group, input[value=\"group\"]'); if (g) { g.click(); return; } for (const l of document.querySelectorAll('label')) { if (l.textContent.includes('Gruppo') || l.textContent.includes('Groupe')) { l.click(); return; } } }")
    page.wait_for_timeout(1000)
    page.evaluate("() => { for (const b of document.querySelectorAll('button')) { if (['Procedi', 'Procéder', 'Continuer'].includes(b.textContent.trim())) { b.click(); return; } } }")
    page.get_by_role("textbox", name="input field").wait_for(state="visible", timeout=5000)

    # Inserisci il nome del gruppo
    page.get_by_role("textbox", name="input field").fill(group_name)

    # Cerca e aggiungi almeno un contatto (se disponibile)
    try:
        search_box = page.get_by_role("textbox", name="input search")
        search_box.click()
        search_box.fill("test")
        page.get_by_role("checkbox").first.wait_for(state="visible", timeout=3000)
        cb = page.get_by_role("checkbox").first
        if cb.count() > 0:
            cb.click()
        page.locator('button:has-text("Aggiungi contatti"), button:has-text("Ajouter des contacts")').first.click()
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.wait_for(state="visible", timeout=3000)
    except Exception:
        pass

    page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

    try:
        # Verifica che il gruppo sia stato creato nella sidebar
        group_btn = page.locator(f'button[title="{group_name}"]').first
        group_btn.wait_for(state="visible", timeout=8000)
        assert group_btn.is_visible(), f"Il gruppo '{group_name}' non è visibile nella sidebar"

        # Tasto destro sul gruppo per il menu contestuale
        group_btn.click(button="right")
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_contatti_10_menu_{datetime.now():%H-%M-%S}.png"))

        # Cerca voci del menu contestuale
        menu_item_found = False
        for selector in [
            'aru-menu-item:has-text("Elimina"), button:has-text("Supprimer")',
            'button:has-text("Elimina gruppo"), button:has-text("Supprimer le groupe")',
            'button:has-text("Elimina"), button:has-text("Supprimer")',
            '[role="menuitem"]:has-text("Elimina"), button:has-text("Supprimer")',
            'li:has-text("Elimina"), button:has-text("Supprimer")',
        ]:
            try:
                item = page.locator(selector).first
                if item.is_visible():
                    item.click()
                    menu_item_found = True
                    break
            except Exception:
                pass

        assert menu_item_found, "Voce 'Elimina' non trovata nel menu contestuale del gruppo"

        # Conferma eliminazione
        try:
            confirm_btn = page.locator('.cdk-overlay-pane button:has-text("Elimina"), button:has-text("Supprimer")').first
            confirm_btn.wait_for(state="visible", timeout=3000)
            confirm_btn.click()
        except Exception:
            for confirm_sel in [
                'button[title="Si"], button[title="Oui"]', 'button:has-text("Sì")', 'button:has-text("Si")',
            ]:
                try:
                    btn = page.locator(confirm_sel).first
                    if btn.is_visible():
                        btn.click()
                        break
                except Exception:
                    pass

        # Aspetta che il gruppo scompaia
        page.locator(f'button[title="{group_name}"]').wait_for(state="hidden", timeout=5000)

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_contatti_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        # Verifica che il gruppo non sia più presente nella sidebar
        remaining = page.locator(f'button[title="{group_name}"]').count()
        assert remaining == 0, \
            f"Il gruppo '{group_name}' è ancora presente dopo l'eliminazione"

    finally:
        # Cleanup: elimina il gruppo se ancora presente
        try:
            group_btn = page.locator(f'button[title="{group_name}"]').first
            if group_btn.count() > 0:
                group_btn.click(button="right")
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
