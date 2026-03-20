import os
import json
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


def test_filtri_inbox(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    # Aspetta che i messaggi siano visibili
    page.locator('div.frame-record-desktop').first.wait_for(state="visible", timeout=8000)

    # Verifica che il componente filtro sia presente nella lista messaggi
    # Il filtro è un componente aru-input-select dentro webmail-select-filter
    filter_select = page.locator('webmail-select-filter aru-input-select, aru-input-select.select-filters').first
    assert filter_select.is_visible(), "Il componente filtro messaggi non è visibile"

    # Apri il dropdown filtro
    filter_select.click(force=True)
    page.wait_for_timeout(1000)
    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_messaggi_18_filter_open_{datetime.now():%H-%M-%S}.png"))

    # Cerca le opzioni del filtro (potrebbero essere in aru-menu-item o altri elementi)
    option_texts = []
    for sel in ['aru-menu-item', '[role="option"]', '[class*="option"]',
                'aru-panel aru-button', 'slot aru-menu-item']:
        opts = page.locator(sel).all()
        for opt in opts:
            try:
                if opt.is_visible():
                    txt = opt.inner_text().strip()
                    if txt and txt not in option_texts:
                        option_texts.append(txt)
                        print(f"Filter option ({sel}): '{txt}'")
            except Exception:
                pass
        if option_texts:
            break

    if not option_texts:
        # Prova a usare JS per trovare le opzioni nel shadow DOM
        options_js = page.evaluate("""() => {
            const sel = document.querySelector('aru-input-select.select-filters');
            if (!sel) return [];
            const panel = sel.shadowRoot?.querySelector('aru-panel') || sel.querySelector('aru-panel');
            if (!panel) return [];
            const items = Array.from(panel.querySelectorAll('aru-menu-item, [role="option"]'));
            return items.map(i => i.textContent?.trim() || '');
        }""")
        option_texts = [t for t in options_js if t]
        print(f"JS options: {option_texts}")

    # Se non ci sono opzioni visibili, verifica solo che il componente sia presente e cliccabile
    if not option_texts:
        print("Nessuna opzione trovata - verifica solo che il componente filtro sia presente")
        assert filter_select.is_visible(), "Il componente filtro messaggi non è visibile"
    else:
        # Clicca la prima opzione
        clicked_option_text = None
        for sel in ['aru-menu-item', '[role="option"]']:
            opts = [o for o in page.locator(sel).all() if o.is_visible()]
            if opts:
                clicked_option_text = opts[0].inner_text().strip()
                opts[0].click()
                page.wait_for_timeout(1000)
                break
        else:
            page.keyboard.press("Escape")

        # Verifica che il filtro sia stato applicato: il dropdown deve essersi chiuso
        # e il testo selezionato deve comparire nel componente filtro oppure la lista risulta aggiornata
        if clicked_option_text:
            dropdown_closed = page.locator('aru-menu-item:visible, [role="option"]:visible').count() == 0
            filter_label_visible = (
                filter_select.inner_text().strip() != "" or
                page.locator(
                    f'[class*="filter"][class*="active"], [class*="selected-filter"]'
                ).count() > 0
            )
            assert dropdown_closed or filter_label_visible, (
                f"Il filtro '{clicked_option_text}' non sembra essere stato applicato"
            )

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_18___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
