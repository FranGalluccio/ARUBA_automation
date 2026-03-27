import os
import json
from datetime import datetime
import time
from base_pec import LoginPec, Helper

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

def test_ripristino_messaggi(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Invia 2 messaggi a se stesso con oggetti univoci
    oggetti = []
    for i in range(2):
        ts = int(time.time())
        oggetto_i = f"Test ripristino {ts}_{i}"
        oggetti.append(oggetto_i)
        Helper.crea_messaggio(
            page, config,
            oggetto=oggetto_i,
            corpo="Test automatico ripristino messaggi",
        )
        page.locator('span[title="Invia"]').click()
        page.wait_for_timeout(3000)

    # Polling: attendi che entrambi i messaggi arrivino in inbox
    for oggetto_i in oggetti:
        msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto_i)
        for _ in range(20):
            page.wait_for_timeout(3000)
            page.locator('aru-symbol[title="Aggiorna"]').click()
            page.wait_for_timeout(1000)
            if msg.count() > 0:
                break

    # Seleziona i messaggi tramite hover + JS click su checkbox (bypassa shadow DOM)
    for oggetto_i in oggetti:
        row = page.locator('div.frame-record-desktop').filter(has_text=oggetto_i).first
        row.scroll_into_view_if_needed()
        row.hover()
        page.wait_for_timeout(600)
        row.locator('div.aru-input-checkbox').first.evaluate('el => el.click()')
        page.wait_for_timeout(600)

    # Clicca Elimina (attendi toolbar visibile)
    elimina_btn = page.locator('aru-button:has(aru-symbol[title="Elimina"])')
    elimina_btn.first.wait_for(state="visible", timeout=10000)
    elimina_btn.first.click()
    page.wait_for_timeout(1000)
    try:
        page.get_by_role("button", name="Sì").click(timeout=2000)
        page.wait_for_timeout(1000)
    except Exception:
        pass

    # Apri cestino
    page.locator('button[title="Cestino"]').click()
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    count = page.locator('div.frame-record-desktop').count()
    assert count >= 2, f"Cestino ha solo {count} messaggi — impossibile testare il ripristino"

    # Seleziona i 2 messaggi nel cestino tramite hover + JS click su checkbox
    for idx, oggetto_i in enumerate(oggetti):
        rows_match = page.locator('div.frame-record-desktop').filter(has_text=oggetto_i)
        row = rows_match.first if rows_match.count() > 0 else page.locator('div.frame-record-desktop').nth(idx)
        row.scroll_into_view_if_needed()
        row.hover()
        page.wait_for_timeout(600)
        row.locator('div.aru-input-checkbox').first.evaluate('el => el.click()')
        page.wait_for_timeout(600)

    # Clicca su sposta (attendi toolbar visibile)
    sposta_btn = page.locator('aru-button:has(aru-symbol[title="Sposta"])')
    sposta_btn.first.wait_for(state="visible", timeout=10000)
    sposta_btn.first.click()

    # Sposta in arrivo
    page.locator("aru-webmail-menu-item[webmailmenuopener]").locator("span:has-text('In arrivo')").click()

    # Verifica toast di conferma ripristino
    toast = page.locator("div.aru-toast__message").filter(has_text="I messaggi selezionati sono stati spostati in In arrivo").first
    toast.wait_for(state="visible", timeout=8000)

    # Percorso screenshot dinamico
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
    assert "I messaggi selezionati sono stati spostati in In arrivo" in toast.text_content()
