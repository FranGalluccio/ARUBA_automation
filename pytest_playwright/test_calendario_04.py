import os
import json
from playwright.sync_api import Page
from base_pec import LoginPec, elimina_evento_pec, dismiss_overlay
from datetime import datetime


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Path file calendario (.ics) ---
FILE_ICS = os.path.normpath(os.path.join(os.path.dirname(os.path.dirname(CONFIG_FILE)), config["calendario_import"]))
assert os.path.exists(FILE_ICS), f"File ICS non trovato: {FILE_ICS}"


def test_import_export_calendario(page: Page):
    # --- Login PEC ---
    LoginPec(page).login_pec(config)
    page.wait_for_load_state("load")

    try:
        # --- Vai al calendario ---
        page.get_by_role("button", name="Calendario").click()
        page.wait_for_load_state("load")

        # Chiudi cookie banner se presente (blocca click su Importa)
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # --- Importa calendario (.ics) ---
        page.get_by_role("button", name="Importa").first.click()
        page.locator("#hidden_input").wait_for(state="attached", timeout=5000)
        page.locator("#hidden_input").set_input_files(FILE_ICS)

        # Conferma import: click JS sul bottone "Importa" nel dialog (testo esatto)
        page.evaluate("""() => {
            const btns = [...document.querySelectorAll('button')];
            const btn = btns.find(b => b.textContent.trim() === 'Importa');
            if (btn) btn.click();
        }""")
        page.wait_for_timeout(3000)

        # Chiudi dialog se ancora aperto
        if page.locator('.cdk-overlay-pane').count() > 0:
            try:
                page.locator('button').filter(has_text="Annulla").last.click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass

        page.wait_for_timeout(1000)

        # Reload per ripristinare il sidebar del calendario (si chiude dopo il file dialog)
        page.reload()
        page.wait_for_load_state("load")
        page.wait_for_timeout(2000)

        # Chiudi cookie banner e overlay CDK se riapparsi dopo reload
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=2000)
            page.wait_for_timeout(500)
        except Exception:
            pass
        dismiss_overlay(page)

        # Screenshot dopo import
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_04_post_import_{datetime.now():%H-%M-%S}.png"))

        # --- Esporta calendario ---
        # Click sidebar "Esporta" → apre dialog "Esporta calendario"
        esporta_btn = page.get_by_role("button", name="Esporta").first
        esporta_btn.wait_for(state="visible", timeout=15000)
        esporta_btn.click(timeout=5000)

        # Aspetta che il dialog sia visibile
        dialog = page.locator('.cdk-overlay-pane button').filter(has_text="Esporta").first
        dialog.wait_for(state="visible", timeout=5000)

        # Screenshot finale (dialog esporta visibile)
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        # Clicca "Esporta" nel dialog; l'app può avviare il download tramite blob URL
        # (Playwright non sempre cattura i download da blob), quindi verifichiamo
        # che il dialog si chiuda come indicatore che l'export è stato avviato.
        try:
            with page.expect_download(timeout=8000) as download_info:
                dialog.click(timeout=5000)
            download_info.value
            print("Export: download catturato da Playwright")
        except Exception:
            # Dialog si chiude = export avviato (blob download non intercettabile)
            page.wait_for_timeout(2000)
            assert page.locator('.cdk-overlay-pane button').filter(has_text="Annulla").count() == 0, \
                "Il dialog 'Esporta calendario' è ancora aperto dopo il click su Esporta"
            print("Export: dialog chiuso, export avviato (download via blob)")

    finally:
        elimina_evento_pec(page, "test")
