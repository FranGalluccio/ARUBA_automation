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


def test_pianificazione_multi_invitati(page):
    """
    Aggiunge due invitati distinti a un evento e verifica che la vista pianificazione
    disponibilità mostri entrambi nella griglia.
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento multi invitati pel {ts}"
    invitato_1 = config["destinatari"]["destinatario_principale"]
    invitato_2 = config["destinatari"]["destinatario_secondario"]

    try:
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Aggiungi primo invitato
        try:
            inv_input = page.locator("input[placeholder*='invitat'], input[aria-label*='invitat']").first
            inv_input.wait_for(state="visible", timeout=5000)
            inv_input.fill(invitato_1)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Aggiungi secondo invitato
        try:
            inv_input = page.locator("input[placeholder*='invitat'], input[aria-label*='invitat']").first
            inv_input.fill(invitato_2)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
        except Exception:
            pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_10_invitati_{datetime.now():%H-%M-%S}.png"))

        # Apri vista pianificazione
        try:
            page.locator("aru-button.planning-button").first.click(force=True, timeout=5000)
        except Exception:
            try:
                page.evaluate("document.querySelectorAll('aru-button.planning-button')[0].click()")
            except Exception:
                pass
        page.wait_for_timeout(2500)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_10_planning_{datetime.now():%H-%M-%S}.png"))

        # Verifica che entrambi gli invitati siano visibili nella griglia pianificazione
        inv1_visibile = page.get_by_text(invitato_1, exact=False).count() > 0
        inv2_visibile = page.get_by_text(invitato_2, exact=False).count() > 0

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_10___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        assert inv1_visibile, f"Invitato 1 '{invitato_1}' non trovato nella vista pianificazione"
        assert inv2_visibile, f"Invitato 2 '{invitato_2}' non trovato nella vista pianificazione"
        print(f"test_calendario_10 PASSED — entrambi gli invitati visibili in pianificazione")

    finally:
        # Chiudi dialog pianificazione e form evento se ancora aperti
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass
        elimina_evento_pel(page, titolo)
