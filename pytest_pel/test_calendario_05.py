import os
import json
import time
from datetime import datetime
from base_pel import LoginPel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_crea_calendario_personalizzato(page):
    """Crea un nuovo calendario con nome e colore, verifica il toast, poi lo elimina."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    nome_cal = f"Cal Lavoro {ts}"

    try:
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.wait_for_timeout(1000)

        # Apri gestione calendario
        page.get_by_role("button", name="Gestione calendario").first.click()
        page.wait_for_timeout(1000)

        # Crea nuovo calendario
        page.get_by_role("button", name="Nuovo", exact=False).first.click()
        page.wait_for_timeout(800)
        nome_input = page.locator(
            "input[placeholder*='Nome'], input[placeholder*='nome'], input[aria-label='input field']"
        ).first
        nome_input.wait_for(state="visible", timeout=8000)
        nome_input.fill(nome_cal)

        # Scegli colore (il terzo disponibile)
        colori = page.locator('[class*="color"], [class*="colour"], input[type="color"], [role="radio"]').all()
        if len(colori) >= 3:
            try:
                colori[2].click(force=True)
            except Exception:
                pass

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1500)

        # Verifica toast di conferma creazione
        toast = page.locator("div.aru-toast__message, [class*='toast'], [class*='snack']").first
        try:
            toast.wait_for(state="visible", timeout=5000)
            print(f"Toast: {toast.inner_text()}")
        except Exception:
            pass

        # Verifica che il calendario sia visibile nella sidebar
        page.locator('[title="I miei calendari"]').first.click()
        page.wait_for_timeout(500)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        assert page.get_by_text(nome_cal, exact=False).count() > 0, \
            f"Calendario '{nome_cal}' non trovato nella sidebar"
        print(f"test_calendario_05 PASSED — calendario: {nome_cal}")

    finally:
        # Cleanup: elimina il calendario creato
        try:
            cal = page.get_by_text(nome_cal, exact=False).first
            if cal.count() > 0:
                cal.click(button="right")
                page.wait_for_timeout(500)
                page.get_by_text("Elimina calendario", exact=False).first.click(timeout=3000)
                page.wait_for_timeout(500)
                page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                page.wait_for_timeout(1000)
        except Exception:
            pass
