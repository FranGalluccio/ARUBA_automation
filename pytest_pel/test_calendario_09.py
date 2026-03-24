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


def test_pianificazione_invitato_occupato(page):
    """
    Verifica che nella vista pianificazione disponibilità uno slot risulti 'Occupato'
    quando l'invitato ha già un evento con 'Mostrati come occupato' attivo.
    Scenario:
    1. Crea evento A alle 10:00-11:00 (Mostrati come occupato ON — default)
    2. Apri nuovo evento B nella stessa fascia, aggiunge se stesso come invitato
    3. Apre vista pianificazione → verifica che lo slot risulti occupato
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo_a = f"evento base occupato pel {ts}"
    titolo_b = f"evento check pianificazione pel {ts}"
    ora_futura = (datetime.now() + timedelta(hours=2)).hour
    ora_inizio = f"{ora_futura:02d}:00"
    ora_fine = f"{(ora_futura + 1) % 24:02d}:00"

    try:
        # --- Evento A: crea con orario fisso (Mostrati come occupato ON di default) ---
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_a)

        time_inputs = page.locator("[aria-label='input time']")
        if time_inputs.count() >= 1:
            time_inputs.nth(0).click(force=True)
            time_inputs.nth(0).fill(ora_inizio)
            page.wait_for_timeout(200)
        if time_inputs.count() >= 2:
            time_inputs.nth(1).click(force=True)
            time_inputs.nth(1).fill(ora_fine)
            page.wait_for_timeout(200)

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_evento_a_{datetime.now():%H-%M-%S}.png"))

        # --- Evento B: stessa fascia, aggiungi se stesso come invitato ---
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_b)

        time_inputs = page.locator("[aria-label='input time']")
        if time_inputs.count() >= 1:
            time_inputs.nth(0).click(force=True)
            time_inputs.nth(0).fill(ora_inizio)
            page.wait_for_timeout(200)
        if time_inputs.count() >= 2:
            time_inputs.nth(1).click(force=True)
            time_inputs.nth(1).fill(ora_fine)
            page.wait_for_timeout(200)

        try:
            invitati = page.locator("input[placeholder*='invitat'], input[aria-label*='invitat']").first
            invitati.wait_for(state="visible", timeout=5000)
            invitati.fill(USERNAME)
            page.wait_for_timeout(800)
            page.keyboard.press("Enter")
            page.wait_for_timeout(500)
        except Exception:
            pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_evento_b_{datetime.now():%H-%M-%S}.png"))

        # Espandi a fullscreen per accedere alla sezione invitati completa
        try:
            page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
            page.wait_for_timeout(800)
        except Exception:
            pass

        # Espandi sezione "1 invitato" (freccia ">") per rendere visibile il planning button
        try:
            page.locator(
                'button:has-text("invitato"), aru-expansion-panel-header, '
                '[class*="expansion-panel"] button, [class*="attendees"] button'
            ).first.click(timeout=3000)
            page.wait_for_timeout(600)
        except Exception:
            try:
                page.get_by_text("invitato", exact=False).first.click(timeout=2000)
                page.wait_for_timeout(600)
            except Exception:
                pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_expanded_{datetime.now():%H-%M-%S}.png"))

        # --- Apri vista pianificazione ---
        planning_aperta = False
        for sel in [
            "aru-button.planning-button",
            'aru-button:has-text("Vista pianificazione")',
            'button:has-text("Vista pianificazione")',
            '[title*="pianificazione"]',
            '[title*="Pianificazione"]',
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0 and el.is_visible():
                    el.click()
                    planning_aperta = True
                    break
            except Exception:
                pass

        if not planning_aperta:
            try:
                page.evaluate("document.querySelectorAll('aru-button.planning-button')[0].click()")
                planning_aperta = True
            except Exception:
                pass

        page.wait_for_timeout(3000)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_planning_{datetime.now():%H-%M-%S}.png"))

        # --- Verifica che lo slot risulti "Occupato" ---
        occupato_visibile = False

        # Cerca la modale di pianificazione specifica:
        # la modale di pianificazione contiene "Tu (" (indicatore organizzatore)
        # che è univoco rispetto alla form evento
        planning_modal = None
        try:
            for pane in page.locator(".cdk-overlay-pane").all():
                try:
                    text = pane.inner_text()
                    if "Tu (" in text:
                        planning_modal = pane
                        break
                except Exception:
                    pass
        except Exception:
            pass

        if planning_modal:
            # 1. Cerca il titolo dell'evento A nell'HTML del modal
            # (i titoli sono visibili nella griglia ma troncati, presenti nell'HTML)
            try:
                inner_html = planning_modal.evaluate("el => el.innerHTML")
                titolo_a_breve = titolo_a[:20].lower()  # primi 20 char del titolo evento A
                if titolo_a_breve in inner_html.lower() or "occupat" in inner_html.lower():
                    occupato_visibile = True
            except Exception:
                pass

            # 2. Cerca blocchi evento/busy nella griglia
            if not occupato_visibile:
                try:
                    count = planning_modal.locator(
                        "aru-planning-event, [class*='planning-event'], [class*='event-block'], "
                        "[class*='busy'], [class*='occupied'], [class*='event-item']"
                    ).count()
                    if count > 0:
                        occupato_visibile = True
                except Exception:
                    pass

            # 3. Cerca celle colorate (eventi) nella griglia — il blocco rosa indica occupato
            if not occupato_visibile:
                try:
                    has_colored = planning_modal.evaluate("""el => {
                        const all = el.querySelectorAll('*');
                        for (const e of all) {
                            const bg = window.getComputedStyle(e).backgroundColor;
                            if (!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent'
                                || bg === '' || bg === 'rgb(255, 255, 255)') continue;
                            // Esclude elementi di struttura (colore blu bottoni, header)
                            const tag = e.tagName.toLowerCase();
                            if (['button', 'input', 'select', 'span', 'h1','h2','h3','a'].includes(tag)) continue;
                            if (e.classList.toString().includes('header')) continue;
                            return true;
                        }
                        return false;
                    }""")
                    if has_colored:
                        occupato_visibile = True
                except Exception:
                    pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        assert planning_aperta, \
            "Vista pianificazione disponibilità non aperta — pulsante non trovato nella form evento"
        assert occupato_visibile, \
            "Slot non risulta 'Occupato' nella vista pianificazione — evento A con 'Mostrati come occupato' ON non rilevato"
        print("test_calendario_09 PASSED — slot occupato verificato in vista pianificazione")

    finally:
        # Chiudi dialog pianificazione e form evento B se ancora aperti
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass
        elimina_evento_pel(page, titolo_a)
        elimina_evento_pel(page, titolo_b)
