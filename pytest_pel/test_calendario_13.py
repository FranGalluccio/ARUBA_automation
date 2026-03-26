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


def _naviga_vista_settimana(page):
    """Assicura di essere in vista Settimana nel calendario."""
    page.get_by_role("button", name="Calendario", exact=True).click()
    page.wait_for_timeout(1000)
    try:
        page.get_by_role("button", name="Settimana", exact=True).click(timeout=3000)
        page.wait_for_timeout(800)
    except Exception:
        pass


def _crea_evento_semplice(page, titolo, ora_inizio="10:00", ora_fine="11:00"):
    """
    Crea un evento semplice senza invitati.
    Usa il mini-form inline, poi espande in fullscreen per impostare l'orario,
    infine salva con il pulsante Salva.
    """
    # Apri form nuovo evento
    clicked = page.evaluate("""() => {
        for (const btn of document.querySelectorAll('button')) {
            const txt = btn.textContent.trim();
            if (txt.includes('Nuovo evento') && !btn.closest('.cdk-overlay-container')) {
                btn.click();
                return true;
            }
        }
        return false;
    }""")
    if not clicked:
        page.get_by_role("button", name="Nuovo evento", exact=True).click(force=True)

    page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=10000)
    page.get_by_placeholder("Inserisci un titolo").fill(titolo)

    # Imposta orario
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
    page.wait_for_timeout(2000)


def _drag_evento(page, titolo, target_date_str):
    """
    Trascina l'evento <titolo> nella colonna del giorno <target_date_str> (YYYY-MM-DD).
    Usa mouse.move() a passi per permettere a FullCalendar di rilevare il drag.
    Restituisce True se l'operazione ha avuto successo (nessuna eccezione).
    """
    # Trova l'evento nella griglia del calendario
    evento = page.locator(".fc-event").filter(has_text=titolo).first
    evento.wait_for(state="visible", timeout=8000)
    src_box = evento.bounding_box()
    assert src_box, f"Impossibile ottenere il bounding box dell'evento '{titolo}'"

    # Trova la colonna di destinazione
    tgt_col = page.locator(f".fc-timegrid-col[data-date='{target_date_str}']").first
    if tgt_col.count() == 0:
        # Fallback: day-grid
        tgt_col = page.locator(f".fc-day[data-date='{target_date_str}']").first
    tgt_col.wait_for(state="visible", timeout=5000)
    tgt_box = tgt_col.bounding_box()
    assert tgt_box, f"Impossibile trovare la colonna per la data '{target_date_str}'"

    # Coordinate sorgente: centro dell'evento
    src_x = src_box["x"] + src_box["width"] / 2
    src_y = src_box["y"] + src_box["height"] / 2

    # Coordinate destinazione: stessa riga oraria, colonna target
    tgt_x = tgt_box["x"] + tgt_box["width"] / 2
    tgt_y = src_y  # mantieni la stessa posizione verticale (orario invariato)

    # Drag lento: necessario per FullCalendar
    page.mouse.move(src_x, src_y)
    page.wait_for_timeout(300)
    page.mouse.down()
    page.wait_for_timeout(500)  # breve pausa prima di iniziare il movimento

    steps = 25
    for i in range(1, steps + 1):
        x = src_x + (tgt_x - src_x) * i / steps
        y = src_y + (tgt_y - src_y) * i / steps
        page.mouse.move(x, y)
        page.wait_for_timeout(30)

    page.wait_for_timeout(600)
    page.mouse.up()
    page.wait_for_timeout(2500)
    return True


def _evento_nella_colonna(page, titolo, target_date_str):
    """
    Verifica che l'evento sia nella colonna del giorno target.
    Controlla che il bounding box dell'evento sia sovrapposto alla colonna target.
    """
    evento = page.locator(".fc-event").filter(has_text=titolo).first
    if evento.count() == 0:
        return False, "Evento non trovato nel calendario"

    evento_box = evento.bounding_box()
    if not evento_box:
        return False, "Bounding box evento non disponibile"

    tgt_col = page.locator(f".fc-timegrid-col[data-date='{target_date_str}']").first
    if tgt_col.count() == 0:
        tgt_col = page.locator(f".fc-day[data-date='{target_date_str}']").first
    if tgt_col.count() == 0:
        return False, f"Colonna target '{target_date_str}' non trovata"

    tgt_box = tgt_col.bounding_box()
    if not tgt_box:
        return False, "Bounding box colonna target non disponibile"

    # L'evento è nella colonna se il suo centro X è compreso nei limiti della colonna
    evento_center_x = evento_box["x"] + evento_box["width"] / 2
    col_left = tgt_box["x"]
    col_right = tgt_box["x"] + tgt_box["width"]
    in_col = col_left <= evento_center_x <= col_right

    return in_col, (
        f"Centro X evento={evento_center_x:.0f}, "
        f"colonna [{col_left:.0f} - {col_right:.0f}]"
    )


def test_sposta_evento_drag(page):
    """
    Crea un evento semplice oggi, poi lo trascina in un altro giorno della
    stessa settimana tramite drag-and-drop. Verifica che dopo il drag l'evento
    si trovi effettivamente nel giorno di destinazione.

    Scenario:
    1. Crea evento oggi alle 10:00-11:00
    2. Naviga alla vista Settimana
    3. Trascina l'evento sul giorno target (oggi + 2 giorni)
    4. Verifica che l'evento sia nel giorno target (tramite bounding box)
    5. Cleanup
    """
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento drag pel {ts}"

    oggi = datetime.now()
    # Giorno destinazione: scegli ±2 giorni rimanendo nella stessa settimana
    # (la vista Aruba mostra Lun-Dom, sabato e domenica inclusi).
    # Se siamo da mercoledì in poi → vai indietro di 2; altrimenti avanti di 2.
    if oggi.weekday() >= 2:  # mer, gio, ven, sab, dom
        target_dt = oggi - timedelta(days=2)
    else:                     # lun, mar
        target_dt = oggi + timedelta(days=2)
    target_date_str = target_dt.strftime("%Y-%m-%d")

    try:
        # ------------------------------------------------------------------ #
        # Step 1: Naviga al calendario, vista settimana, crea evento         #
        # ------------------------------------------------------------------ #
        _naviga_vista_settimana(page)
        _crea_evento_semplice(page, titolo, "10:00", "11:00")

        # ------------------------------------------------------------------ #
        # Step 2: Torna alla vista settimana e verifica che l'evento esista  #
        # ------------------------------------------------------------------ #
        _naviga_vista_settimana(page)
        page.wait_for_timeout(1000)

        evento = page.locator(".fc-event").filter(has_text=titolo).first
        evento.wait_for(state="visible", timeout=8000)

        page.screenshot(path=os.path.join(REPORT_FOLDER,
            f"test_calendario_13_pre_drag_{datetime.now():%H-%M-%S}.png"))

        # Registra la posizione originale (colonna sorgente)
        src_box_before = evento.bounding_box()
        src_center_x = src_box_before["x"] + src_box_before["width"] / 2

        # ------------------------------------------------------------------ #
        # Step 3: Drag-and-drop verso il giorno target                       #
        # ------------------------------------------------------------------ #
        print(f"[INFO] Trascino '{titolo}' -> {target_date_str}")
        _drag_evento(page, titolo, target_date_str)

        page.screenshot(path=os.path.join(REPORT_FOLDER,
            f"test_calendario_13_post_drag_{datetime.now():%H-%M-%S}.png"))

        # ------------------------------------------------------------------ #
        # Step 4: Verifica che l'evento sia nel giorno target                #
        # ------------------------------------------------------------------ #
        in_col, dettaglio = _evento_nella_colonna(page, titolo, target_date_str)

        page.screenshot(path=os.path.join(REPORT_FOLDER,
            f"test_calendario_13___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)

        assert in_col, (
            f"L'evento '{titolo}' non risulta nella colonna '{target_date_str}' dopo il drag. "
            f"Dettaglio: {dettaglio}"
        )
        print(f"test_calendario_13 PASSED — evento spostato a {target_date_str} ({dettaglio})")

    finally:
        try:
            page.keyboard.press("Escape")
            page.wait_for_timeout(400)
        except Exception:
            pass
        elimina_evento_pel(page, titolo)
