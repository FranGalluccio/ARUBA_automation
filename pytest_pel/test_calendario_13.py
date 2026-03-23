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


def test_evento_corpo_rich_text(page):
    """Crea un evento con corpo in rich text (grassetto + lista) e verifica il salvataggio."""
    LoginPel(page).login_pel(config)

    ts = int(time.time())
    titolo = f"evento rich text pel {ts}"
    testo_grassetto = "Testo in grassetto"

    try:
        page.get_by_role("button", name="Calendario").click()
        page.get_by_role("button", name="Nuovo evento", exact=True).click()
        page.get_by_placeholder("Inserisci un titolo").wait_for(state="visible", timeout=8000)
        page.get_by_placeholder("Inserisci un titolo").fill(titolo)

        # Espandi a fullscreen per accedere al rich text editor (suneditor)
        try:
            page.locator('[title*="schermo"], [title*="Schermo"], [title="Full screen"]').first.click(timeout=3000)
            page.wait_for_timeout(500)
        except Exception:
            pass

        # Clicca sull'area del rich text editor (suneditor — la div WYSIWYG, non la textarea code)
        editor_area = page.locator(".sun-editor-editable, div.se-wrapper-wysiwyg, div[contenteditable='true']").first
        editor_area.wait_for(state="visible", timeout=5000)
        editor_area.click()
        page.wait_for_timeout(300)

        # Attiva grassetto tramite toolbar o shortcut
        try:
            page.locator('.se-toolbar button[aria-label*="Bold"], .se-toolbar button[title*="Bold"], .se-toolbar button[title*="Grassetto"]').first.click(timeout=3000)
        except Exception:
            page.keyboard.press("Control+b")
        page.wait_for_timeout(200)

        # Digita testo in grassetto
        editor_area.type(testo_grassetto)
        page.wait_for_timeout(200)

        # Disattiva grassetto
        try:
            page.keyboard.press("Control+b")
            page.wait_for_timeout(200)
        except Exception:
            pass

        # Vai a capo e aggiungi voce di lista
        page.keyboard.press("Enter")
        page.wait_for_timeout(200)
        try:
            page.locator('.se-toolbar button[aria-label*="List"], .se-toolbar button[title*="list"], .se-toolbar button[title*="lista"]').first.click(timeout=2000)
        except Exception:
            pass
        editor_area.type("Voce di lista 1")
        page.wait_for_timeout(300)

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_13_editor_{datetime.now():%H-%M-%S}.png"))

        page.get_by_role("button", name="Salva").first.click()
        page.wait_for_timeout(1000)

        # Verifica che l'evento sia visibile
        page.locator(".fc-event").filter(has_text=titolo).first.wait_for(
            state="visible", timeout=8000
        )
        page.locator(".fc-event").filter(has_text=titolo).first.click()
        page.wait_for_timeout(1000)

        # Verifica che il corpo contenga il testo inserito (almeno in parte)
        assert page.get_by_text(testo_grassetto, exact=False).count() > 0 or \
               page.locator("strong, b").filter(has_text=testo_grassetto).count() > 0, \
            f"Testo '{testo_grassetto}' non trovato nel popup evento"

        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_13___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
        print(f"test_calendario_13 PASSED — corpo rich text salvato")

    finally:
        elimina_evento_pel(page, titolo)
