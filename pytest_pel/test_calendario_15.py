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

USERNAME = config["pel"]["username"]


def _crea_evento(page, titolo, ora_inizio, ora_fine, mostrati_occupato=True):
    """Crea un evento PEL con opzione 'Mostrati come occupato'."""
    page.get_by_role("button", name="Calendario", exact=True).click()
    page.get_by_role("button", name="Nuovo evento", exact=True).click()
    page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
    page.get_by_placeholder("Inserisci un titolo").fill(titolo)

    # Imposta orario inizio
    time_inputs = page.locator("[aria-label='input time']")
    if time_inputs.count() >= 1:
        time_inputs.nth(0).click(force=True)
        time_inputs.nth(0).fill(ora_inizio)
        page.wait_for_timeout(200)
    if time_inputs.count() >= 2:
        time_inputs.nth(1).click(force=True)
        time_inputs.nth(1).fill(ora_fine)
        page.wait_for_timeout(200)

    # Espandi a fullscreen per vedere "Mostrati come occupato"
    try:
        page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
        page.wait_for_timeout(500)
    except Exception:
        pass

    # Toggle "Mostrati come occupato"
    try:
        toggle = page.locator('aru-toggle:near(:text("Mostrati come occupato")), input[type="checkbox"]:near(:text("Mostrati come occupato"))').first
        is_checked = toggle.is_checked() if toggle.count() > 0 else None
        if mostrati_occupato and is_checked is False:
            toggle.click(force=True)
            page.wait_for_timeout(300)
        elif not mostrati_occupato and is_checked is not False:
            # Disattiva se attivo di default
            if is_checked:
                toggle.click(force=True)
                page.wait_for_timeout(300)
    except Exception:
        pass

    page.get_by_role("button", name="Salva").first.click()
    page.wait_for_timeout(1500)


def test_disponibilita_occupato(page):
    """
    Verifica che un evento con 'Mostrati come occupato' ON renda lo slot occupato
    nella vista di pianificazione disponibilità.
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo_a = f"evento occupato A pel {ts}"
    titolo_b = f"evento occupato B pel {ts}"

    # Orario fisso domani alle 10:00-11:00
    domani = (datetime.now() + timedelta(days=1)).strftime("%d/%m/%Y")
    ora_inizio = "10:00"
    ora_fine = "11:00"

    try:
        # ---- Evento A: Mostrati come occupato ON ----
        _crea_evento(page, titolo_a, ora_inizio, ora_fine, mostrati_occupato=True)

        # ---- Evento B: stessa data/ora, aggiungi se stesso come invitato ----
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_b)

        # Imposta stesso orario
        time_inputs = page.locator("[aria-label='input time']")
        if time_inputs.count() >= 1:
            time_inputs.nth(0).click(force=True)
            time_inputs.nth(0).fill(ora_inizio)
            page.wait_for_timeout(200)
        if time_inputs.count() >= 2:
            time_inputs.nth(1).click(force=True)
            time_inputs.nth(1).fill(ora_fine)
            page.wait_for_timeout(200)

        # Aggiungi se stesso come invitato
        try:
            invitati = page.locator("input[placeholder*='invitat'], input[aria-label*='invitat']").first
            invitati.wait_for(state="visible", timeout=5000)
            invitati.fill(USERNAME)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
        except Exception:
            pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_15_invitato_{datetime.now():%H-%M-%S}.png"))

        # Apri vista pianificazione disponibilità (usa .first — ci sono 2 planning-button)
        overlay_prima = page.locator(".cdk-overlay-pane").count()
        try:
            page.locator("aru-button.planning-button").first.click(force=True, timeout=5000)
        except Exception:
            try:
                page.evaluate("document.querySelectorAll('aru-button.planning-button')[0].click()")
            except Exception:
                pass
        page.wait_for_timeout(2500)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_15_planning_{datetime.now():%H-%M-%S}.png"))

        # Verifica presenza indicatore "Occupato" nella griglia di pianificazione.
        # Usa exact=True per evitare falsi positivi da titoli eventi come "evento occupato A".
        # Cerca anche indicatori CSS specifici della modal di pianificazione.
        overlay_panes = page.locator(".cdk-overlay-pane").all()
        occupato_visibile = False
        for pane in overlay_panes:
            try:
                if pane.get_by_text("Occupato", exact=True).count() > 0:
                    occupato_visibile = True
                    break
                if pane.locator("[class*='busy'], [class*='occupied'], [class*='unavailable']").count() > 0:
                    occupato_visibile = True
                    break
            except Exception:
                pass
        # Fallback: cerca in tutta la pagina solo testo esatto "Occupato"
        if not occupato_visibile:
            occupato_visibile = page.get_by_text("Occupato", exact=True).count() > 0

        assert occupato_visibile, \
            "Slot non risulta 'Occupato' nella vista pianificazione nonostante evento A con 'Mostrati come occupato' ON"

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_15___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print("test_calendario_15 PASSED — slot correttamente marcato come Occupato")

        # Chiudi dialog pianificazione e annulla evento B (non salvato)
        page.keyboard.press("Escape")
        page.wait_for_timeout(500)
        try:
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass

    finally:
        elimina_evento_pel(page, titolo_a)
        elimina_evento_pel(page, titolo_b)
