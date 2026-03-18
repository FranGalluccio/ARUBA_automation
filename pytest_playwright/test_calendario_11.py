import os
import json
from datetime import datetime
import time
from base_pec import LoginPec
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_eliminazione_evento_ricorrente(page):
    """Verifica che l'eliminazione di un evento ricorrente con opzione 'Tutti gli eventi'
    rimuova tutti i occorrenze dal calendario."""
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"evento elimina ricorrente playwright {ts}"

    try:
        time.sleep(1)
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)

        # Crea nuovo evento ricorrente
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        time.sleep(1)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo_evento)

        # Imposta ripetizione (stessa procedura di test_calendario_01)
        page.get_by_role("combobox", name="Non ripetere").click()
        page.get_by_role("button", name="Personalizza...").click()
        page.get_by_role("radio", name="Dopo").check()
        time.sleep(1)
        page.get_by_role("dialog") \
            .filter(has_text="Personalizza") \
            .filter(has=page.locator("button", has_text="Salva")) \
            .last \
            .get_by_role("button", name="Salva") \
            .click()
        time.sleep(1)

        # Salva evento
        page.get_by_role("button", name="Salva").click()
        time.sleep(3)

        # Vai alla vista Eventi
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)
        page.get_by_role("button", name="Eventi").click(force=True)
        time.sleep(3)

        # Verifica che l'evento esista
        assert page.get_by_text(titolo_evento, exact=False).count() > 0, \
            f"Evento ricorrente '{titolo_evento}' non trovato dopo la creazione"

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_pre_delete_{datetime.now():%H-%M-%S}.png"))

        # Clicca sull'evento per aprire il popup
        page.get_by_text(titolo_evento, exact=False).first.click()
        time.sleep(2)

        # Clicca "Annulla evento" — apre il dialog "Elimina evento ricorrente"
        page.get_by_role("button", name="Annulla evento").first.click(timeout=5000)
        time.sleep(1)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_dialog_{datetime.now():%H-%M-%S}.png"))

        # Verifica che appaia il dialog con le opzioni di eliminazione
        dialog_visible = (
            page.get_by_text("Elimina evento ricorrente", exact=False).is_visible() or
            page.get_by_role("radio", name="Tutti gli eventi").is_visible()
        )
        assert dialog_visible, "Dialog 'Elimina evento ricorrente' non apparso"

        # Seleziona "Tutti gli eventi"
        page.get_by_role("radio", name="Tutti gli eventi").check(timeout=5000)
        time.sleep(0.5)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_11_tutti_gli_eventi_{datetime.now():%H-%M-%S}.png"))

        # Conferma eliminazione
        page.get_by_role("button", name="Ok").first.click()
        time.sleep(3)

        # Gestione eventuale conferma aggiuntiva
        try:
            page.get_by_role("button", name="Elimina").first.click(timeout=3000)
            time.sleep(2)
        except Exception:
            pass

        # Screenshot dopo eliminazione
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_11___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

        # Verifica che l'evento sia stato eliminato completamente
        page.get_by_role("button", name="Calendario").click()
        time.sleep(1)
        page.get_by_role("button", name="Eventi").click(force=True)
        time.sleep(3)

        count_dopo = page.get_by_text(titolo_evento, exact=False).count()
        assert count_dopo == 0, (
            f"L'evento ricorrente '{titolo_evento}' è ancora presente ({count_dopo} occorrenze) "
            "dopo l'eliminazione con 'Tutti gli eventi'"
        )
        print("Eliminazione evento ricorrente con 'Tutti gli eventi': OK")

    finally:
        # Cleanup: elimina l'evento se non già eliminato
        try:
            page.get_by_role("button", name="Calendario").click()
            time.sleep(1)
            page.get_by_role("button", name="Eventi").click(force=True)
            time.sleep(2)
            while True:
                ev = page.get_by_text(titolo_evento, exact=False).first
                if ev.count() == 0:
                    break
                ev.click()
                time.sleep(2)
                try:
                    page.get_by_role("button", name="Annulla evento").first.click(timeout=3000)
                    time.sleep(1)
                except Exception:
                    pass
                try:
                    page.get_by_role("radio", name="Tutti gli eventi").check(timeout=2000)
                    time.sleep(0.5)
                    page.get_by_role("button", name="Ok").first.click(timeout=2000)
                    time.sleep(2)
                except Exception:
                    pass
                try:
                    page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                    time.sleep(2)
                except Exception:
                    pass
                try:
                    page.keyboard.press("Escape")
                    time.sleep(0.5)
                except Exception:
                    pass
                page.get_by_role("button", name="Eventi").click(force=True)
                time.sleep(2)
        except Exception:
            pass
