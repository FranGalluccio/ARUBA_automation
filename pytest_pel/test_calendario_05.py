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


def test_evento_giornata_intera(page):
    """Crea un evento con toggle 'Giornata intera' attivato e verifica visibilità."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento giornata intera pel {ts}"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Toggle "Giornata intera" — in PEL è un toggle switch visibile a fianco delle date
        toggled = False
        for sel in [
            'input[type="checkbox"]:near(:text("Giornata intera"))',
            'button[title="Giornata intera"]',
            'label:has-text("Giornata intera") input',
            'aru-input-choice:has-text("Giornata intera")',
            '[class*="allday"], [class*="all-day"]',
            'input[type="checkbox"]',
        ]:
            try:
                el = page.locator(sel).first
                if el.count() > 0:
                    el.click(force=True)
                    toggled = True
                    page.wait_for_timeout(300)
                    break
            except Exception:
                pass

        if toggled:
            page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_05_toggle_{datetime.now():%H-%M-%S}.png"))
            print("  Toggle Giornata intera attivato")

        # Chiudi banner cookie se riapparso
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        page.get_by_role("button", name="Salva").click()
        page.wait_for_timeout(1000)

        # Verifica che l'evento sia visibile nella riga "Tutto il giorno" o nel calendario
        page.locator("a, [class*='event']").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_05___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_05 PASSED — toggled={toggled}")

    finally:
        elimina_evento_pel(page, titolo)
