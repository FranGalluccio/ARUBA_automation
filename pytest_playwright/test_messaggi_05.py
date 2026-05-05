import os
import json
import time
from datetime import datetime

from base_pec import LoginPec, Helper
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_cartella(page):
    ts = int(time.time())
    nome_cartella = f"Test cartella playwright {ts}"
    nuovo_nome_cartella = f"Test cartella playwright modificata {ts}"

    # Login PEC
    LoginPec(page).login_pec(config)

    try:
        # Clicca su nuova cartella
        page.locator('span[title="Crea nuova cartella"]').click()

        # Compila nome cartella
        page.locator('input[placeholder="Nome cartella"]').wait_for(state="visible", timeout=5000)
        page.locator('input[placeholder="Nome cartella"]').fill(nome_cartella)

        # Salva usando il bottone nel dialog overlay
        page.locator('.cdk-overlay-pane button:has-text("Salva"), .cdk-overlay-pane button:has-text("Enregistrer")').first.click()

        # Verifica toast di conferma creazione (wait senza filter — il toast è veloce)
        toast = page.locator("div.aru-toast__message").first
        toast.wait_for(state="visible", timeout=8000)
        assert "La cartella è stata creata." in toast.text_content()

        # Rinomina cartella via tasto destro
        page.locator(f'button[title="{nome_cartella}"]').wait_for(state="visible", timeout=5000)
        page.locator(f'button[title="{nome_cartella}"]').click(button="right")
        page.locator('button:has-text("Modifica cartella"), button:has-text("Modifier le dossier")').wait_for(state="visible", timeout=5000)
        page.locator('button:has-text("Modifica cartella"), button:has-text("Modifier le dossier")').click()

        # Modifica nome cartella
        page.locator('input[aria-label="input field"]').wait_for(state="visible", timeout=5000)
        page.locator('input[aria-label="input field"]').fill(nuovo_nome_cartella)

        # Salva modifica
        page.locator('.cdk-overlay-pane button:has-text("Salva"), .cdk-overlay-pane button:has-text("Enregistrer")').first.click()

        # Verifica toast di conferma modifica
        toast = page.locator("div.aru-toast__message").filter(has_text="La cartella è stata modificata.").first
        expect(toast).to_be_visible()

        # Screenshot
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_messaggi_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")
        assert "La cartella è stata modificata." in toast.text_content()

    finally:
        # Cleanup: elimina la cartella (con nome originale o modificato)
        for nome in [nuovo_nome_cartella, nome_cartella]:
            try:
                btn = page.locator(f'button[title="{nome}"]').first
                if btn.count() > 0 and btn.is_visible():
                    btn.click(button="right")
                    page.locator('button:has-text("Elimina cartella"), button:has-text("Supprimer le dossier")').wait_for(state="visible", timeout=3000)
                    page.locator('button:has-text("Elimina cartella"), button:has-text("Supprimer le dossier")').click()
                    page.locator('span[title="Elimina"], span[title="Supprimer"]').click()
                    page.wait_for_timeout(500)
            except Exception:
                pass
