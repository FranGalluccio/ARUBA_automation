import os
import json
from playwright.sync_api import Page
from base_pec import LoginPec
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
FILE_ICS = os.path.abspath(config["calendario_import"])
assert os.path.exists(FILE_ICS), f"File ICS non trovato: {FILE_ICS}"


def test_import_export_calendario(page: Page):
    # --- Login PEC ---
    LoginPec(page).login_pec(config)
    page.wait_for_load_state("load")

    try:
        # --- Vai al calendario ---
        page.get_by_role("button", name="Calendario").click()
        page.wait_for_load_state("load")

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

        # Re-apri il sidebar del calendario (l'import chiude il pannello laterale)
        page.get_by_role("button", name="Calendario").first.click()
        page.wait_for_timeout(1000)

        # Screenshot dopo import
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_04_post_import_{datetime.now():%H-%M-%S}.png"))

        # --- Esporta calendario ---
        # Click "Esporta" nella sidebar → apre dialog "Esporta calendario"
        export_triggered = False
        page.get_by_role("button", name="Esporta").first.wait_for(state="visible", timeout=8000)
        page.get_by_role("button", name="Esporta").first.click(timeout=5000)
        page.wait_for_timeout(500)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_04_export_dialog_{datetime.now():%H-%M-%S}.png"))

        # Imposta periodo breve: solo il mese corrente
        try:
            oggi = datetime.now()
            inizio = oggi.replace(day=1).strftime("%d/%m/%Y")
            fine = oggi.strftime("%d/%m/%Y")
            date_input = page.locator('.cdk-overlay-pane input[type="text"], .cdk-overlay-pane input').first
            date_input.triple_click()
            date_input.fill(f"{inizio} - {fine}")
            page.wait_for_timeout(300)
        except Exception:
            pass

        # Caso 1: dialog aperto → clicca "Esporta" nel dialog per avviare il download
        try:
            with page.expect_download(timeout=10000) as download_info:
                page.locator('.cdk-overlay-pane button:has-text("Esporta")').first.click(timeout=5000)
            download_info.value
            export_triggered = True
        except Exception:
            pass

        # Caso 2: download già partito senza dialog (fallback)
        if not export_triggered:
            try:
                with page.expect_download(timeout=5000) as download_info2:
                    page.keyboard.press("Escape")
                download_info2.value
                export_triggered = True
            except Exception:
                pass

        assert export_triggered, "L'esportazione del calendario non ha prodotto un download"

        # Screenshot finale
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_04___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    finally:
        # --- Cleanup: elimina eventi importati (eseguito anche in caso di fallimento) ---
        try:
            page.get_by_role("button", name="Calendario").click()
            page.get_by_role("button", name="Eventi").wait_for(state="visible", timeout=5000)
            page.get_by_role("button", name="Eventi").click()
            page.wait_for_timeout(1500)
            for _ in range(20):
                ev = page.locator('a, [class*="event"]').filter(has_text="test").first
                if ev.count() == 0:
                    break
                ev.click()
                page.wait_for_timeout(1500)
                try:
                    page.locator('button:has(aru-symbol[symbol="dots-separator"])').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                try:
                    page.locator('button[title="Annulla evento"]').first.click(timeout=3000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                # Step extra per eventi ricorrenti: Tutti gli eventi → Ok
                try:
                    page.get_by_role("radio", name="Tutti gli eventi").check(timeout=2000)
                    page.wait_for_timeout(300)
                    page.get_by_role("button", name="Ok").first.click(timeout=2000)
                    page.wait_for_timeout(500)
                except Exception:
                    pass
                try:
                    page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                    page.wait_for_timeout(1500)
                    try:
                        toast = page.locator("div.aru-toast__message").first
                        if toast.is_visible():
                            print(f"Toast eliminazione: {toast.text_content()}")
                    except Exception:
                        pass
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(300)
                except Exception:
                    pass
                page.get_by_role("button", name="Eventi").click(force=True)
                page.wait_for_timeout(1500)
        except Exception:
            pass
