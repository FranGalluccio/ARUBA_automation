import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper, elimina_evento_pec, dismiss_overlay, get_app_base_url
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_creazione_invio_evento(page, browser):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    titolo_evento = f"evento test auto invito {ts}"

    try:
        # Crea nuovo evento
        page.locator('#calendar, [aria-label="Calendario"], [aria-label="Calendrier"], button[title="Calendario"], button[title="Calendrier"]').first.click()
        page.locator('button:has-text("Nuovo evento"), button:has-text("Nouvel événement")').first.click()
        titolo_input = page.locator('input[placeholder*=" titolo"], input[placeholder*=" titre"]').first
        titolo_input.wait_for(state="visible", timeout=8000)
        titolo_input.fill(titolo_evento)
        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()
        page.locator("a").filter(has_text=titolo_evento).first.wait_for(state="visible", timeout=15000)
        page.locator("a").filter(has_text=titolo_evento).first.click()
        # Modifica evento
        page.locator('button:has-text("Modifica"), button:has-text("Modifier")').first.wait_for(state="visible", timeout=5000)
        page.locator('button:has-text("Modifica"), button:has-text("Modifier")').first.click()
        invitati_input = page.locator('input[placeholder*="nvitat"], input[placeholder*="nvité"]').first
        invitati_input.wait_for(state="visible", timeout=5000)
        invitati_input.fill(config["destinatari"]["destinatario_principale"])
        page.keyboard.press("Enter")
        page.wait_for_timeout(1000)

        # Invita anche il partecipante secondario (se diverso dal principale)
        destinatario_secondario = config["destinatari"].get("destinatario_secondario")
        if destinatario_secondario and destinatario_secondario != config["destinatari"]["destinatario_principale"]:
            invitati_input.fill(destinatario_secondario)
            page.keyboard.press("Enter")
            page.wait_for_timeout(1000)

        page.locator('button:has-text("Salva"), button:has-text("Enregistrer")').first.click()

        # Verifica toast di conferma salvataggio evento
        toast = page.locator("div.aru-toast__message").first
        toast.wait_for(state="visible", timeout=8000)
        toast_text = toast.text_content()
        assert "evento è stato salvato" in toast_text.lower() or "evento è stato modificato" in toast_text.lower() \
            or "enregistr" in toast_text.lower(), \
            f"Toast di conferma salvataggio evento non trovato: {toast_text!r}"

        page.wait_for_timeout(1000)
        try:
            page.locator('button:has-text("Invia"), button:has-text("Envoyer"), [aria-label="Invia"], [aria-label="Envoyer"]').first.first.click(timeout=10000)
            page.wait_for_timeout(3000)
        except Exception:
            pass
        # Chiudi overlay rimasti dopo l'invio (es. conferma invio inviti)
        dismiss_overlay(page)
        page.wait_for_timeout(2000)
        # Naviga direttamente alla inbox (goto previene redirect del flusso calendario)
        inbox_url = get_app_base_url(page) + "/new/messages/INBOX"
        page.goto(inbox_url, wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(3000)
        # Workaround bug app: "Nascondi ricevute" nasconde anche messaggi normali.
        # Clicca "Mostra ricevute" se visibile per ripristinare la vista completa.
        try:
            mostra_btn = page.locator('button:has-text("Mostra ricevute"), button:has-text("Afficher")').first
            if mostra_btn.is_visible(timeout=2000):
                mostra_btn.click(force=True)
                page.wait_for_timeout(2000)
        except Exception:
            pass
        # Aggiorna la posta
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(5000)
        # Aspetta che almeno un record sia visibile
        page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=15000)

        # Clicca sul primo record
        page.locator('div.frame-record-desktop').first.click()

        # Aspetta che il contenuto della mail sia visibile (20s per CI FR lenta)
        page.locator('div.message-content-body').wait_for(state="visible", timeout=20000)

        # --- Verifica lato destinatario: seconda pagina con account separato (cliente07) ---
        pec_secondario_config = config.get("pec_secondario") or {}
        if destinatario_secondario and pec_secondario_config.get("password"):
            context2 = browser.new_context(viewport={"width": 1920, "height": 1080}, ignore_https_errors=True)
            page2 = context2.new_page()
            try:
                config_secondario = {**config, "pec": config["pec_secondario"]}
                LoginPec(page2).login_pec(config_secondario)
                inbox_url_2 = get_app_base_url(page2) + "/new/messages/INBOX"
                page2.goto(inbox_url_2, wait_until="domcontentloaded", timeout=30000)
                page2.wait_for_timeout(3000)

                # L'email di invito può impiegare qualche secondo ad arrivare: polling con refresh
                invito_arrivato = False
                for _ in range(12):
                    page2.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
                    page2.wait_for_timeout(5000)
                    if page2.get_by_text(titolo_evento, exact=False).count() > 0:
                        invito_arrivato = True
                        break
                assert invito_arrivato, \
                    f"Invito all'evento '{titolo_evento}' non arrivato nella inbox del destinatario secondario"

                page2.screenshot(
                    path=os.path.join(REPORT_FOLDER, f"test_calendario_03_destinatario___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"),
                    full_page=True
                )
                print("Invito all'evento trovato nella inbox del destinatario secondario")

                # Apri l'invito e accetta (riquadro "Parteciperai?" -> Si/Forse/No, primo bottone = Si)
                page2.get_by_text(titolo_evento, exact=False).first.click()
                page2.locator('div.message-content-body').wait_for(state="visible", timeout=20000)
                page2.locator('aru-button[aru-id="msg-dtl-body-event-current-btn-0"]').first.click(timeout=5000)
                page2.wait_for_timeout(3000)
                print("Invito accettato dal destinatario secondario")

                # Verifica che l'evento sia quello corretto nel Calendario del destinatario secondario
                # (stesso titolo e organizzatore tra i partecipanti, non solo un titolo omonimo)
                page2.locator('#calendar, [aria-label="Calendario"], [aria-label="Calendrier"], button[title="Calendario"], button[title="Calendrier"]').first.click()
                page2.wait_for_timeout(2000)
                for ev_name in ["Eventi", "Événements", "Agenda", "Events"]:
                    try:
                        btn = page2.get_by_role("button", name=ev_name)
                        btn.wait_for(state="visible", timeout=3000)
                        btn.click(force=True)
                        break
                    except Exception:
                        pass
                page2.wait_for_timeout(2000)
                evento_calendario = page2.get_by_text(titolo_evento, exact=False).first
                evento_calendario.wait_for(state="visible", timeout=10000)
                evento_calendario.click()
                page2.wait_for_timeout(1500)
                expect(page2.get_by_text(config["pec"]["username"], exact=False).first).to_be_visible(timeout=8000)
                print("Evento corretto trovato nel calendario del destinatario secondario (organizzatore verificato tra i partecipanti)")
                page2.keyboard.press("Escape")
                page2.wait_for_timeout(500)

                # Verifica lato organizzatore (page resta aperta insieme a page2): deve arrivare
                # la mail di notifica accettazione prima di chiudere il secondo contesto.
                accettazione_arrivata = False
                for _ in range(6):
                    page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
                    page.wait_for_timeout(5000)
                    righe = page.locator('div.frame-record-desktop').all_inner_texts()
                    if any(titolo_evento in r and ("ccettat" in r.lower() or "accepté" in r.lower()) for r in righe):
                        accettazione_arrivata = True
                        break
                assert accettazione_arrivata, \
                    f"Mail di accettazione dell'evento '{titolo_evento}' non arrivata nella inbox dell'organizzatore"
                print("Mail di accettazione ricevuta dall'organizzatore")
            finally:
                context2.close()

        # Percorso screenshot dinamico
        screenshot_path = os.path.join(
            REPORT_FOLDER,
            f"test_calendario_03___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
        )
        page.screenshot(path=screenshot_path, full_page=True)
        print(f"Screenshot salvato in: {screenshot_path}")

    finally:
        elimina_evento_pec(page, "evento test auto invito")
