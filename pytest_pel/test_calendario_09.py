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


def test_evento_con_promemoria(page):
    """Crea un evento con promemoria e-mail e verifica che venga salvato."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento promemoria pel {ts}"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Chiudi banner cookie se presente
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Link "Aggiungi promemoria" nel pannello destro (fullscreen) o come link/button
        try:
            page.get_by_text("Aggiungi promemoria").first.click(timeout=5000)
        except Exception:
            page.locator('[title="Aggiungi promemoria"]').first.click(timeout=3000)
        page.wait_for_timeout(1000)

        # Seleziona tipo notifica email (se disponibile un dropdown)
        try:
            page.get_by_role("combobox").filter(has_text="Email").first.click(timeout=2000)
        except Exception:
            pass

        # Inserisci email per il promemoria
        try:
            email_inp = page.locator("input[placeholder*='email'], input[type='email']").first
            if email_inp.count() > 0:
                email_inp.fill(config["pel"]["username"])
        except Exception:
            pass

        # Salva il dialog promemoria (scoped al dialog overlay, non al form evento)
        try:
            page.locator('#cdk-dialog-1, .cdk-overlay-pane').last.get_by_role("button", name="Salva").click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            try:
                page.get_by_role("button", name="Ok").first.click(timeout=2000)
            except Exception:
                pass

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09_promemoria_{datetime.now():%H-%M-%S}.png"))

        # Salva l'evento (usa .first per evitare strict mode se ci sono 2 Salva aperti)
        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1000)

        # Verifica che l'evento sia visibile
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_09___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_09 PASSED — evento: {titolo}")

    finally:
        elimina_evento_pel(page, titolo)
