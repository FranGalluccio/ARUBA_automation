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


def test_evento_luogo_link(page):
    """
    Crea evento con un URL come luogo e verifica che venga salvato.
    (Il campo 'Indirizzo o link' accetta sia indirizzi fisici sia URL meeting.)
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento luogo link pel {ts}"
    url_meeting = "https://meet.example.com/test-room"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Inserisci URL direttamente nel campo luogo (no combobox navigation — il tipo default funziona)
        luogo_input = None
        for sel in [
            "input[aria-label='input field']",
            "input[placeholder*='luogo']",
            "input[placeholder*='Luogo']",
            "input[placeholder*='Indirizzo']",
        ]:
            els = page.locator(sel)
            if els.count() > 0:
                idx = 1 if els.count() > 1 else 0
                luogo_input = els.nth(idx)
                break

        if luogo_input is None:
            luogo_input = page.locator("input[aria-label='input field']").first

        luogo_input.click()
        luogo_input.fill(url_meeting)
        page.wait_for_timeout(300)

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1000)

        # Apri l'evento e verifica che l'URL sia stato salvato
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )
        page.locator(".fc-event").filter(has_text=titolo).first.click()
        page.wait_for_timeout(1000)

        # Verifica l'URL nel popup evento
        assert page.get_by_text("meet.example.com", exact=False).count() > 0 or \
               page.get_by_text(url_meeting, exact=False).count() > 0, \
            f"URL meeting '{url_meeting}' non trovato nel popup evento"

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_12___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_12 PASSED — luogo link: {url_meeting}")

    finally:
        elimina_evento_pel(page, titolo)
