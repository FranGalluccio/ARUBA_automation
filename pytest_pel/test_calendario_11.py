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


def test_evento_luogo_indirizzo(page):
    """Crea evento con tipo luogo 'Indirizzo' e verifica il salvataggio del campo location."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento luogo indirizzo pel {ts}"
    indirizzo = "Via Roma 1, Milano"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Il tipo luogo "Indirizzo" è il default — inserisce direttamente nel campo input luogo.
        # Il combobox "Indirizzo o link" usa opzioni custom non accessibili via role="option".
        # Cerca l'input testuale del campo location (il secondo input field nel form).
        luogo_input = None
        for sel in [
            "input[aria-label='input field']",
            "input[placeholder*='luogo']",
            "input[placeholder*='Luogo']",
            "input[placeholder*='Indirizzo']",
        ]:
            els = page.locator(sel)
            if els.count() > 0:
                # Prendi il secondo (il primo è di solito il titolo o un altro campo)
                idx = 1 if els.count() > 1 else 0
                luogo_input = els.nth(idx)
                break

        if luogo_input is None:
            luogo_input = page.locator("input[aria-label='input field']").first

        luogo_input.click()
        luogo_input.fill(indirizzo)
        page.wait_for_timeout(300)

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1000)

        # Apri l'evento e verifica che il luogo sia stato salvato
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )
        page.locator(".fc-event").filter(has_text=titolo).first.click()
        page.wait_for_timeout(1000)

        # Verifica il luogo nel popup dell'evento
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        assert page.get_by_text(indirizzo, exact=False).count() > 0, \
            f"Luogo '{indirizzo}' non trovato nel popup evento"
        print(f"test_calendario_11 PASSED — luogo: {indirizzo}")

    finally:
        elimina_evento_pel(page, titolo)
