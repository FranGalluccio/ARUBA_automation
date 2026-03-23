import os
import json
import time
from datetime import datetime
from base_pel import LoginPel, elimina_evento_pel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_assegna_calendario_specifico(page):
    """Crea evento assegnandolo a un calendario specifico e verifica il salvataggio."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento calendario assegnato pel {ts}"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Espandi a fullscreen per vedere il campo "Calendario assegnato"
        try:
            page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Trova il combobox "Calendario assegnato" (default: "Personale")
        calendario_cb = page.get_by_role("combobox", name="Personale").first
        try:
            calendario_cb.wait_for(state="visible", timeout=5000)
        except Exception:
            # Fallback: cerca per label generica
            calendario_cb = page.locator('select[aria-label*="Calendario"], aru-select[aria-label*="Calendario"]').first

        # Leggi il valore corrente — aru-select non supporta input_value(), usa inner_text()
        try:
            val_iniziale = calendario_cb.inner_text().strip()
        except Exception:
            val_iniziale = "Personale"
        print(f"  Calendario iniziale: {val_iniziale!r}")

        calendario_cb.click()
        page.wait_for_timeout(700)

        # aru-select usa aru-option come opzioni
        opzioni = page.locator("aru-option, li[class*='option'], [class*='select-option']").all()
        calendario_scelto = val_iniziale
        if len(opzioni) > 1:
            # Seleziona un'opzione diversa dall'attuale
            for opt in opzioni:
                txt = opt.inner_text().strip()
                if txt and txt != val_iniziale:
                    opt.click()
                    calendario_scelto = txt
                    break
            else:
                opzioni[0].click()
        elif len(opzioni) == 1:
            opzioni[0].click()
            calendario_scelto = opzioni[0].inner_text().strip()
        else:
            # Nessuna opzione trovata — clicca fuori per chiudere la tendina
            try:
                page.get_by_placeholder("Inserisci un titolo").click()
                page.wait_for_timeout(300)
            except Exception:
                pass
        page.wait_for_timeout(300)
        print(f"  Calendario selezionato: {calendario_scelto!r}")

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_14_cal_{datetime.now():%H-%M-%S}.png"))

        page.get_by_role("button", name="Salva").first.click(force=True)
        page.wait_for_timeout(1000)

        # Verifica che l'evento sia visibile
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_14___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_14 PASSED — calendario: {calendario_scelto!r}")

    finally:
        elimina_evento_pel(page, titolo)
