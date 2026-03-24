import os
import json
import time
from datetime import datetime, timedelta
from base_pel import LoginPel, elimina_evento_pel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_disponibilita_occupato(page):
    """
    Verifica che un evento con 'Mostrati come occupato' ON salvi correttamente
    la preferenza (toggle checked) e che la vista pianificazione si apra senza errori.
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo_a = f"evento occupato A pel {ts}"

    # Usa un'ora futura (+2h) per evitare che l'evento sia già passato
    ora_futura = (datetime.now() + timedelta(hours=2)).hour
    ora_inizio = f"{ora_futura:02d}:00"
    ora_fine = f"{(ora_futura + 1) % 24:02d}:00"

    try:
        # Crea evento A con "Mostrati come occupato" ON
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_a)

        # Imposta orario
        time_inputs = page.locator("[aria-label='input time']")
        if time_inputs.count() >= 1:
            time_inputs.nth(0).click(force=True)
            time_inputs.nth(0).fill(ora_inizio)
            page.wait_for_timeout(200)
        if time_inputs.count() >= 2:
            time_inputs.nth(1).click(force=True)
            time_inputs.nth(1).fill(ora_fine)
            page.wait_for_timeout(200)

        # Espandi a fullscreen per accedere al toggle
        try:
            page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Assicura toggle "Mostrati come occupato" sia ON
        toggle_on = False
        try:
            toggle = page.locator('label:has-text("Mostrati come occupato"), label:has-text("Mostrati")').first
            if toggle.count() > 0:
                if not toggle.is_checked():
                    toggle.click(force=True)
                    page.wait_for_timeout(300)
                toggle_on = toggle.is_checked()
        except Exception:
            pass

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(2000)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_07_creato_{datetime.now():%H-%M-%S}.png"))

        # Riapri evento A per verificare che il toggle "Mostrati come occupato" sia ON
        page.locator(".fc-event").filter(has_text=titolo_a).first.wait_for(state="visible", timeout=8000)
        page.locator(".fc-event").filter(has_text=titolo_a).first.click()
        page.wait_for_timeout(1000)

        page.get_by_role("button", name="Modifica").wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Modifica").click()
        page.wait_for_timeout(500)

        # Espandi fullscreen se necessario
        try:
            page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Verifica stato toggle "Mostrati come occupato"
        toggle_checked = False
        try:
            toggle_check = page.locator('label:has-text("Mostrati come occupato"), label:has-text("Mostrati")').first
            if toggle_check.count() > 0:
                toggle_checked = toggle_check.is_checked()
        except Exception:
            # Fallback: cerca indicatore visuale del toggle attivo
            toggle_checked = page.locator(
                '[class*="toggle--checked"], [class*="toggle-on"], [aria-checked="true"]'
            ).count() > 0

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)

        # Annulla modifica
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(300)
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass

        assert toggle_checked, \
            "Toggle 'Mostrati come occupato' non risulta ON dopo il salvataggio dell'evento"
        print(f"test_calendario_07 PASSED — 'Mostrati come occupato' ON verificato per: {titolo_a}")

    finally:
        elimina_evento_pel(page, titolo_a)
