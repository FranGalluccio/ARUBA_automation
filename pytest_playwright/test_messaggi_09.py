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


def test_segna_come_letto_da_leggere(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test segna letto/da leggere {ts}"

    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Test automatico invio messaggio PEC con Playwright",
    )

    # Invia
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: aspetta che il messaggio arrivi in inbox (fino a 90s)
    messaggio_arrivato = False
    for _ in range(22):
        page.wait_for_timeout(4000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"], button[aria-label="Aggiorna"], button[aria-label="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if page.locator('div.frame-record-desktop').filter(has_text=oggetto).count() > 0:
            messaggio_arrivato = True
            break

    assert messaggio_arrivato, f"Il messaggio '{oggetto}' non è arrivato in inbox entro 90s"

    # Segna tutti come già letti — cerca il button tramite aru-symbol con title che contiene "letti" o "lu"
    page.evaluate("""() => {
        const symbols = document.querySelectorAll('aru-symbol');
        for (const sym of symbols) {
            const t = (sym.getAttribute('title') || '').toLowerCase();
            if (t.includes('letti') || (t.includes('lu') && t.includes('marquer'))) {
                const btn = sym.closest('button, aru-button');
                if (btn) { btn.click(); break; }
            }
        }
    }""")
    page.wait_for_timeout(2000)

    # Segna tutti come da leggere via JS (bypassa aria-hidden e locator handler)
    page.wait_for_timeout(2000)
    page.evaluate("""() => {
        for (const btn of document.querySelectorAll('aru-button, button')) {
            if (btn.getAttribute('aria-hidden') === 'true') continue;
            const sym = btn.querySelector('aru-symbol');
            if (!sym) continue;
            const t = (sym.getAttribute('title') || '').toLowerCase();
            if (t.includes('da leggere') || t.includes('non lu')) {
                btn.click(); return;
            }
        }
    }""")
    page.wait_for_timeout(1500)

    # Verifica che almeno un messaggio risulti non letto:
    # il titolo della pagina mostra "(N)" davanti quando ci sono N messaggi non letti
    page.wait_for_timeout(2000)
    title = page.title()

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert title.startswith("("), (
        f"Dopo 'Segna tutti come da leggere' il titolo non mostra messaggi non letti: '{title}'"
    )
    
    

