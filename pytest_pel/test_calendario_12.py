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


def _aggiungi_invitato(page, email):
    """Aggiunge un invitato tramite il campo 'Aggiungi gli invitati'."""
    inv_input = page.locator("input[placeholder*='invitat'], input[aria-label*='invitat']").first
    inv_input.wait_for(state="visible", timeout=5000)
    inv_input.fill(email)
    page.wait_for_timeout(800)
    page.keyboard.press("Enter")
    page.wait_for_timeout(600)


def _apri_evento_in_modifica(page, titolo):
    """
    Clicca sull'evento in calendario per aprire il popup/form di modifica.
    Espande a fullscreen se necessario. Restituisce True se aperto.
    """
    evento = page.locator(".fc-event").filter(has_text=titolo).first
    evento.wait_for(state="visible", timeout=8000)
    evento.click()
    page.wait_for_timeout(1000)

    # Se è già aperto in fullscreen (titolo "Modifica evento") siamo a posto
    if page.get_by_text("Modifica evento", exact=True).count() > 0:
        return True

    # Altrimenti cerca il pulsante Modifica nel popup
    for sel in [
        'button[aria-label*="Modifica"]', 'button[title*="Modifica"]',
        'button[aria-label*="modifica"]', 'button[title*="modifica"]',
        '[class*="edit"]', '[class*="pencil"]',
    ]:
        try:
            btn = page.locator(sel).first
            if btn.count() > 0 and btn.is_visible():
                btn.click()
                page.wait_for_timeout(1000)
                break
        except Exception:
            pass

    # Espandi a fullscreen
    try:
        page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
        page.wait_for_timeout(800)
    except Exception:
        pass

    return page.get_by_text("Modifica evento", exact=True).count() > 0 or \
           page.get_by_placeholder("Inserisci un titolo").count() > 0


def _rimuovi_invitato_dal_form(page, email):
    """
    Rimuove un invitato dal form evento.
    Prova più strategie: hover + click sul pulsante ×, aria-label, JS mirato.
    Restituisce True se la rimozione è riuscita.
    """
    email_lower = email.lower()

    # Strategy 1: chip/tag contenente l'email → pulsante figlio
    for chip_sel in [
        '[class*="chip"]', '[class*="tag"]', '[class*="attendee"]',
        '[class*="invit"]', '[class*="guest"]', 'li',
    ]:
        try:
            chips = page.locator(chip_sel).filter(has_text=email)
            if chips.count() > 0:
                chip = chips.first
                chip.hover()
                page.wait_for_timeout(300)
                close_btn = chip.locator(
                    'button, [role="button"], [class*="close"], [class*="remove"], '
                    '[class*="delete"], aru-symbol[symbol*="close"], aru-symbol[symbol*="delete"]'
                ).first
                if close_btn.count() > 0 and close_btn.is_visible():
                    close_btn.click()
                    page.wait_for_timeout(600)
                    return True
        except Exception:
            pass

    # Strategy 2: JS mirato — cerca il nodo di testo con l'email, risale al
    # contenitore più stretto e clicca il suo pulsante di rimozione.
    try:
        rimosso = page.evaluate(f"""() => {{
            const emailTarget = {repr(email_lower)};
            // Cerca i nodi foglia (span, div, td, p) che contengono *solo* l'email
            const leaves = Array.from(document.querySelectorAll(
                'span, div, td, p, label, small'
            ));
            for (const el of leaves) {{
                const txt = (el.textContent || '').trim().toLowerCase();
                if (!txt.includes(emailTarget)) continue;
                // Escludi contenitori troppo grandi (più di 200 char)
                if (txt.length > 200) continue;
                // Risali al row più stretto
                const row = el.closest('li, [class*="attendee"], [class*="invit"], [class*="chip"], [class*="tag"], [class*="guest"]') || el.parentElement || el;
                // Cerca un pulsante nel row (esclude i pulsanti della toolbar del form)
                const btns = row.querySelectorAll('button, [role="button"]');
                for (const btn of btns) {{
                    btn.click();
                    return true;
                }}
            }}
            return false;
        }}""")
        if rimosso:
            page.wait_for_timeout(600)
            return True
    except Exception:
        pass

    # Strategy 3: pulsante con aria-label di rimozione vicino all'email
    try:
        remove_btns = page.locator(
            'button[aria-label*="imuov"], button[aria-label*="emov"], '
            'button[aria-label*="liminat"], button[title*="imuov"]'
        )
        if remove_btns.count() > 0:
            remove_btns.first.click()
            page.wait_for_timeout(600)
            return True
    except Exception:
        pass

    return False


def _gestisci_dialogo_notifica(page):
    """Gestisce il dialogo 'Vuoi informare gli invitati?' cliccando 'Non inviare'."""
    try:
        btn = page.get_by_role("button", name="Non inviare").first
        if btn.count() > 0 and btn.is_visible():
            btn.click()
            page.wait_for_timeout(800)
            return True
    except Exception:
        pass
    return False


def test_invitati_aggiungi_rimuovi(page):
    """
    Crea un evento con 2 invitati, poi riapre in modifica e rimuove il primo.

    Scenario:
    1. Crea evento con invitato_1 e invitato_2 → Invia
    2. Riapre dal calendario → form di modifica (fullscreen)
    3. Verifica che entrambi gli invitati siano presenti
    4. Rimuove invitato_1 tramite il pulsante ×
    5. Verifica che nel form rimanga solo invitato_2
    6. Salva e gestisce il dialogo di notifica
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento 2 invitati pel {ts}"
    invitato_1 = config["destinatari"]["destinatario_principale"]
    invitato_2 = config["destinatari"]["destinatario_secondario"]

    try:
        # ------------------------------------------------------------------ #
        # Step 1: Crea evento con 2 invitati                                 #
        # ------------------------------------------------------------------ #
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        _aggiungi_invitato(page, invitato_1)
        _aggiungi_invitato(page, invitato_2)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_12_invitati_{datetime.now():%H-%M-%S}.png"))

        page.get_by_role("button", name="Invia").first.wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Invia").first.click()
        page.wait_for_timeout(2000)

        # ------------------------------------------------------------------ #
        # Step 2: Riapri in modifica dal calendario                          #
        # ------------------------------------------------------------------ #
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.wait_for_timeout(1500)
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(state="visible", timeout=8000)

        aperto = _apri_evento_in_modifica(page, titolo)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_12_modifica_{datetime.now():%H-%M-%S}.png"))
        assert aperto, f"Impossibile aprire il form di modifica per '{titolo}'"

        # ------------------------------------------------------------------ #
        # Step 3: Verifica che entrambi gli invitati siano presenti          #
        # ------------------------------------------------------------------ #
        assert page.get_by_text(invitato_1, exact=False).count() > 0, \
            f"Invitato 1 '{invitato_1}' non trovato nel form di modifica"
        assert page.get_by_text(invitato_2, exact=False).count() > 0, \
            f"Invitato 2 '{invitato_2}' non trovato nel form di modifica"

        # ------------------------------------------------------------------ #
        # Step 4: Rimuovi invitato_1                                         #
        # ------------------------------------------------------------------ #
        rimosso = _rimuovi_invitato_dal_form(page, invitato_1)
        assert rimosso, f"Impossibile trovare il pulsante × per rimuovere '{invitato_1}'"

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_12_rimosso_{datetime.now():%H-%M-%S}.png"))

        # ------------------------------------------------------------------ #
        # Step 5: Verifica nel form (prima di salvare)                       #
        # Controlla solo nella lista invitati, non nell'intera pagina,
        # perché l'email dell'organizzatore può comparire anche altrove.
        # ------------------------------------------------------------------ #
        inv1_nella_lista = page.evaluate(f"""() => {{
            const email = {repr(invitato_1)};
            const rows = Array.from(document.querySelectorAll(
                'li, [class*="attendee"], [class*="invit"], [class*="guest"]'
            ));
            return rows.some(el => (el.textContent || '').toLowerCase().includes(email.toLowerCase()));
        }}""")
        assert not inv1_nella_lista, \
            f"Invitato 1 '{invitato_1}' è ancora nella lista invitati dopo la rimozione"

        inv2_nella_lista = page.evaluate(f"""() => {{
            const email = {repr(invitato_2)};
            const rows = Array.from(document.querySelectorAll(
                'li, [class*="attendee"], [class*="invit"], [class*="guest"]'
            ));
            return rows.some(el => (el.textContent || '').toLowerCase().includes(email.toLowerCase()));
        }}""")
        assert inv2_nella_lista, \
            f"Invitato 2 '{invitato_2}' è stato rimosso per errore"

        page.screenshot(path=os.path.join(REPORT_FOLDER,
            f"test_calendario_12___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_12 PASSED — '{invitato_1}' rimosso, '{invitato_2}' ancora presente")

        # ------------------------------------------------------------------ #
        # Step 6: Salva e gestisci dialogo notifica                          #
        # ------------------------------------------------------------------ #
        for btn_name in ["Invia", "Salva"]:
            try:
                btn = page.get_by_role("button", name=btn_name).first
                if btn.count() > 0 and btn.is_visible():
                    btn.click()
                    page.wait_for_timeout(1500)
                    break
            except Exception:
                pass

        # Dialogo "Vuoi informare gli invitati?" → Non inviare
        _gestisci_dialogo_notifica(page)

    finally:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass
        elimina_evento_pel(page, titolo)
