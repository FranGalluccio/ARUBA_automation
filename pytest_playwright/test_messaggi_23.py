import os
import json
import time
from datetime import datetime
from base_pec import LoginPec, Helper
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_ricevuta_accettazione(page):
    """Verifica che dopo l'invio di un messaggio PEC arrivi la Ricevuta di Accettazione (RA)."""
    LoginPec(page).login_pec(config)

    # Invia messaggio a se stesso con oggetto univoco
    ts = int(time.time())
    oggetto = f"Test RA {ts}"
    Helper.crea_messaggio(
        page, config,
        oggetto=oggetto,
        corpo="Test automatico ricevuta di accettazione PEC",
    )
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Vai alla inbox e aggiorna con polling attivo (RA può tardare su ambienti lenti)
    page.wait_for_timeout(5000)
    page.locator("#messages").locator('[aria-label="Messaggi"], [aria-label="Messages"]').first.first.click()
    page.wait_for_timeout(5000)

    # Mostra le ricevute — obbligatorio, senza questo le ricevute non compaiono mai
    # IT: "Mostra ricevute" / FR: "Afficher les reçus"
    try:
        mostra_btn = page.get_by_text("Mostra ricevute", exact=True).or_(
            page.get_by_text("Afficher les reçus", exact=True)
        ).first
        mostra_btn.wait_for(state="visible", timeout=5000)
        mostra_btn.click(force=True)
        page.wait_for_timeout(2000)
    except Exception:
        pass

    # Polling fino a 90s per la RA
    found_ra = False
    for _ in range(18):
        page.wait_for_timeout(5000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(2000)
        # Riprova mostra ricevute se necessario
        try:
            mostra_btn = page.get_by_text("Mostra ricevute", exact=True).or_(
                page.get_by_text("Afficher les reçus", exact=True)
            ).first
            mostra_btn.wait_for(state="visible", timeout=1000)
            mostra_btn.click(force=True)
            page.wait_for_timeout(1000)
        except Exception:
            pass
        if page.locator(
            'div.frame-record-desktop:has(aru-symbol[title="Ricevuta di accettazione"], aru-symbol[title="Accusé de réception"])'
        ).filter(has_text=oggetto).count() > 0:
            found_ra = True
            break

    # Apri la ricevuta in nuova finestra e verifica il tipo (evita falsi positivi da icona)
    body_ok = False
    if found_ra:
        ra_row = page.locator(
            'div.frame-record-desktop:has(aru-symbol[title="Ricevuta di accettazione"], aru-symbol[title="Accusé de réception"])'
        ).filter(has_text=oggetto).first
        ra_row.click()

        # Apri in nuova finestra
        apri_btn = page.locator('aru-symbol[title="Apri in una nuova finestra"], aru-symbol[title="Ouvrir dans une nouvelle fenêtre"]').first
        apri_btn.wait_for(state="visible", timeout=10000)
        with page.expect_popup() as popup_info:
            apri_btn.click()
        new_page = popup_info.value
        new_page.wait_for_load_state("networkidle", timeout=15000)
        new_page.wait_for_timeout(1000)

        # Il tipo di ricevuta è nel shadow DOM di aru-text#pecMessage
        pec_label = new_page.evaluate(
            "() => document.querySelector('aru-text#pecMessage')?.shadowRoot?.textContent?.trim() || ''"
        )
        body_ok = "Ricevuta di accettazione" in pec_label or "Accusé de réception" in pec_label or "accettazione" in pec_label.lower() or "réception" in pec_label.lower()
        new_page.close()

        assert body_ok, (
            f"La ricevuta non è di tipo 'Ricevuta di accettazione'. "
            f"Tipo trovato: {pec_label!r}"
        )

    # Nascondi nuovamente le ricevute per non interferire con i test successivi
    # IT: "Nascondi ricevute" / FR: "Masquer les accusés"
    try:
        nascondi_btn = page.get_by_text("Nascondi ricevute", exact=True).or_(
            page.get_by_text("Masquer les accusés", exact=True)
        ).first
        nascondi_btn.wait_for(state="visible", timeout=3000)
        nascondi_btn.click(force=True)
        page.wait_for_timeout(1000)
    except Exception:
        pass

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_23___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path)

    assert found_ra, (
        f"Ricevuta di Accettazione (RA) non trovata dopo invio messaggio '{oggetto}'. "
        "Il sistema PEC potrebbe non star generando le ricevute correttamente."
    )
    print(f"Screenshot salvato in: {screenshot_path}")
