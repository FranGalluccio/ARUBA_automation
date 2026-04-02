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


def test_ricevuta_consegna(page):
    """Verifica che dopo l'invio di un messaggio PEC arrivi la Ricevuta di Consegna (RD)."""
    LoginPec(page).login_pec(config)

    # Invia messaggio a se stesso con oggetto univoco
    ts = int(time.time())
    oggetto = f"Test RD {ts}"
    Helper.crea_messaggio(
        page, config,
        oggetto=oggetto,
        corpo="Test automatico ricevuta di consegna PEC",
    )
    page.locator('span[title="Invia"]').click()

    # Vai alla inbox e aggiorna con polling attivo (RD richiede più tempo della RA)
    page.wait_for_timeout(5000)
    page.locator("#messages").get_by_label("Messaggi").first.click()
    page.wait_for_timeout(5000)

    # Mostra le ricevute se il banner è presente
    try:
        mostra_btn = page.locator('button:has-text("Mostra ricevute")').first
        if mostra_btn.is_visible():
            mostra_btn.click()
            page.wait_for_timeout(2000)
    except Exception:
        pass

    # Polling fino a 120s per la RD (più lenta della RA)
    found_rd = False
    for _ in range(20):
        page.wait_for_timeout(6000)
        page.locator('aru-symbol[title="Aggiorna"]').click()
        page.wait_for_timeout(2000)
        # Riprova mostra ricevute se necessario
        try:
            mostra_btn = page.locator('button:has-text("Mostra ricevute")').first
            if mostra_btn.is_visible():
                mostra_btn.click()
                page.wait_for_timeout(1000)
        except Exception:
            pass
        if page.locator(
            'div.frame-record-desktop:has(aru-symbol[title="Ricevuta di consegna"])'
        ).filter(has_text=oggetto).count() > 0:
            found_rd = True
            break

    # Apri la ricevuta in nuova finestra e verifica il tipo (evita falsi positivi da icona)
    body_ok = False
    if found_rd:
        rd_row = page.locator(
            'div.frame-record-desktop:has(aru-symbol[title="Ricevuta di consegna"])'
        ).filter(has_text=oggetto).first
        rd_row.click()

        # Apri in nuova finestra
        apri_btn = page.locator('aru-symbol[title="Apri in una nuova finestra"]').first
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
        body_ok = "consegna" in pec_label.lower()
        new_page.close()

        assert body_ok, (
            f"La ricevuta non contiene 'consegna'. "
            f"Tipo trovato: {pec_label!r}"
        )

    # Nascondi nuovamente le ricevute per non interferire con i test successivi
    try:
        nascondi_btn = page.locator('button:has-text("Nascondi ricevute")').first
        if nascondi_btn.is_visible():
            nascondi_btn.click()
            page.wait_for_timeout(1000)
    except Exception:
        pass

    screenshot_path = os.path.join(
        REPORT_FOLDER, f"test_messaggi_24___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)

    assert found_rd, (
        f"Ricevuta di Consegna (RD) non trovata dopo invio messaggio '{oggetto}'. "
        "Il sistema PEC potrebbe non star generando le ricevute di consegna correttamente."
    )
    print(f"Screenshot salvato in: {screenshot_path}")
