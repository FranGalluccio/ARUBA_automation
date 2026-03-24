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


def test_evento_con_invitati(page):
    """Crea evento con invitato, invia l'invito e verifica la ricezione in inbox."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento pel invito {ts}"
    invitato = config["destinatari"]["destinatario_principale"]

    try:
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Aggiungi invitato
        inv_input = page.locator("input[placeholder='Aggiungi gli invitati']").first
        inv_input.wait_for(state="visible", timeout=5000)
        inv_input.fill(invitato)
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        # Con invitati il pulsante diventa "Invia"
        send_btn = page.get_by_role("button", name="Invia").first
        send_btn.wait_for(state="visible", timeout=5000)
        send_btn.click()
        page.wait_for_timeout(2000)

        # Verifica che l'evento sia visibile in calendario (salvato correttamente)
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.wait_for_timeout(1500)
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        assert page.locator(".fc-event").filter(has_text=titolo).count() > 0, \
            f"Evento con invitato '{titolo}' non trovato in calendario dopo invio"
        print(f"test_calendario_03 PASSED — invito inviato per: {titolo}")

    finally:
        elimina_evento_pel(page, titolo)
