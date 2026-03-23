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


def test_creazione_modifica_evento(page):
    """Crea un evento, lo modifica (cambia titolo) e verifica l'aggiornamento."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo_base = f"evento pel auto {ts}"
    titolo_modificato = f"evento pel auto modificato {ts}"

    try:
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_base)
        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1500)

        # Apri l'evento appena creato
        page.locator(".fc-event").filter(has_text=titolo_base).first.wait_for(
            state="visible", timeout=8000
        )
        page.locator(".fc-event").filter(has_text=titolo_base).first.click()
        page.get_by_role("button", name="Modifica").wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Modifica").click()

        # Modifica il titolo
        titolo_input = page.get_by_placeholder("Inserisci un titolo")
        titolo_input.wait_for(state="visible", timeout=5000)
        titolo_input.fill(titolo_modificato)
        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1500)

        # Verifica che il titolo aggiornato sia visibile
        page.locator(".fc-event").filter(has_text=titolo_modificato).first.wait_for(
            state="visible", timeout=8000
        )

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_02 PASSED — titolo modificato: {titolo_modificato}")

    finally:
        elimina_evento_pel(page, f"evento pel auto {ts}")
