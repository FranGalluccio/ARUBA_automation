import os
import json
import time
import pytest
from datetime import datetime, timedelta
from base_pel import LoginPel, elimina_evento_pel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

SALA = os.environ.get("PEL_SALA_RIUNIONI", config.get("sala_riunioni", ""))


def _imposta_orario(page, ora_inizio, ora_fine):
    time_inputs = page.locator("[aria-label='input time']")
    if time_inputs.count() >= 1:
        time_inputs.nth(0).click(force=True)
        time_inputs.nth(0).fill(ora_inizio)
        page.wait_for_timeout(200)
    if time_inputs.count() >= 2:
        time_inputs.nth(1).click(force=True)
        time_inputs.nth(1).fill(ora_fine)
        page.wait_for_timeout(200)


def _espandi_fullscreen(page):
    try:
        page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
        page.wait_for_timeout(800)
    except Exception:
        pass


def _aggiungi_sala(page, nome_sala):
    """
    Inserisce il nome della sala riunioni nel form evento (fullscreen).
    Restituisce True se il campo è stato trovato e compilato, False altrimenti.
    """
    selectors = [
        'input[placeholder*="sala"], input[placeholder*="Sala"]',
        'input[placeholder*="riunion"]',
        'input[placeholder*="Aggiungi sala"]',
        'input[placeholder*="Aggiungi luogo"], input[placeholder*="luogo"]',
        'input[placeholder*="location"], input[placeholder*="Location"]',
        '[formcontrolname*="room"] input',
        '[formcontrolname*="location"] input',
        '[formcontrolname*="luogo"] input',
        'aru-input-autocomplete input',
    ]

    for sel in selectors:
        try:
            inputs = page.locator(sel).all()
            for el in inputs:
                if not el.is_visible():
                    continue
                el.click()
                el.fill(nome_sala)
                page.wait_for_timeout(1200)
                # Accetta il suggerimento dropdown se appare
                try:
                    suggestion = page.locator(
                        f'[class*="dropdown"] [class*="option"], '
                        f'[role="option"], '
                        f'[class*="autocomplete"] li'
                    ).filter(has_text=nome_sala).first
                    if suggestion.count() > 0 and suggestion.is_visible():
                        suggestion.click()
                        page.wait_for_timeout(500)
                    else:
                        page.keyboard.press("Enter")
                        page.wait_for_timeout(500)
                except Exception:
                    page.keyboard.press("Enter")
                    page.wait_for_timeout(500)
                return True
        except Exception:
            continue

    return False


def test_conflitto_sala_riunioni(page):
    """
    Verifica che non sia possibile prenotare la stessa sala riunioni
    per due eventi sovrapposti nello stesso orario.

    Scenario:
    1. Crea Evento A con sala R alle HH:00-HH+1:00
    2. Crea Evento B con stessa sala R allo stesso orario
    3. Verifica che il sistema segnali il conflitto (toast / warning / form bloccato)
    """
    if not SALA:
        pytest.skip(
            "Nessuna sala riunioni configurata — imposta 'sala_riunioni' in config.json "
            "o la variabile d'ambiente PEL_SALA_RIUNIONI"
        )

    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo_a = f"sala test A pel {ts}"
    titolo_b = f"sala test B pel {ts}"
    ora_futura = (datetime.now() + timedelta(hours=3)).hour
    ora_inizio = f"{ora_futura:02d}:00"
    ora_fine = f"{(ora_futura + 1) % 24:02d}:00"

    try:
        # ------------------------------------------------------------------ #
        # Evento A — prenota sala R                                           #
        # ------------------------------------------------------------------ #
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_a)
        _imposta_orario(page, ora_inizio, ora_fine)
        _espandi_fullscreen(page)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_form_a_{datetime.now():%H-%M-%S}.png"))

        sala_trovata = _aggiungi_sala(page, SALA)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_sala_a_{datetime.now():%H-%M-%S}.png"))

        if not sala_trovata:
            pytest.skip(
                f"Campo sala riunioni non trovato nel form evento — "
                f"verifica i selettori in _aggiungi_sala() o controlla gli screenshot"
            )

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1500)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_salvato_a_{datetime.now():%H-%M-%S}.png"))

        # ------------------------------------------------------------------ #
        # Evento B — stessa sala, stesso orario                              #
        # ------------------------------------------------------------------ #
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_b)
        _imposta_orario(page, ora_inizio, ora_fine)
        _espandi_fullscreen(page)

        _aggiungi_sala(page, SALA)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_sala_b_{datetime.now():%H-%M-%S}.png"))

        # Prova a salvare — deve apparire un errore/conflitto
        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(2000)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_dopo_salva_b_{datetime.now():%H-%M-%S}.png"))

        # ------------------------------------------------------------------ #
        # Verifica conflitto                                                  #
        # ------------------------------------------------------------------ #
        conflitto_rilevato = False

        # 1. Toast con parole chiave di conflitto
        parole_conflitto = ["occupata", "prenotata", "conflict", "non disponibile", "già occupata"]
        for parola in parole_conflitto:
            try:
                if page.locator(
                    "div.aru-toast__message, [class*='toast'], [class*='snack'], "
                    "[class*='alert'], [class*='error-message']"
                ).filter(has_text=parola).count() > 0:
                    conflitto_rilevato = True
                    break
            except Exception:
                pass

        # 2. Testo di errore/warning visibile nel form o nella pagina
        if not conflitto_rilevato:
            for parola in parole_conflitto:
                try:
                    if page.get_by_text(parola, exact=False).count() > 0:
                        conflitto_rilevato = True
                        break
                except Exception:
                    pass

        # 3. Il form è ancora aperto e il titolo dell'evento B è ancora nel campo
        #    (significa che il salvataggio è stato bloccato)
        if not conflitto_rilevato:
            try:
                titolo_input = page.get_by_placeholder("Inserisci un titolo")
                if titolo_input.count() > 0 and titolo_input.is_visible():
                    val = titolo_input.input_value()
                    if titolo_b in val:
                        conflitto_rilevato = True
            except Exception:
                pass

        # 4. Indicatore di validazione rosso/invalido sul campo sala
        if not conflitto_rilevato:
            try:
                if page.locator(
                    '[class*="error"], [class*="invalid"], [class*="conflict"], '
                    'input.ng-invalid, [class*="field-error"]'
                ).count() > 0:
                    conflitto_rilevato = True
            except Exception:
                pass

        page.screenshot(
            path=os.path.join(REPORT_FOLDER, f"test_calendario_11___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"),
            full_page=True
        )

        assert conflitto_rilevato, (
            f"FAIL: nessun conflitto rilevato — l'Evento B sembra salvato con la sala '{SALA}' "
            f"già prenotata dall'Evento A alle {ora_inizio}-{ora_fine}. "
            f"Controlla gli screenshot in {REPORT_FOLDER}"
        )
        print(f"test_calendario_11 PASSED — conflitto sala '{SALA}' rilevato alle {ora_inizio}-{ora_fine}")

    finally:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
            page.get_by_role("button", name="Annulla").first.click(timeout=2000)
        except Exception:
            pass
        elimina_evento_pel(page, titolo_a)
        elimina_evento_pel(page, titolo_b)
