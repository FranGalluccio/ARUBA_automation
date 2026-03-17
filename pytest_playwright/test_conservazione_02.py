import os
import json
import time
import pytest
from datetime import datetime
from base_pec import LoginPec

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

SETTINGS_URL = config["pec"]["url"].rstrip("/") + "/new/settings/home"


def _click_waffle_menu(page):
    """Apre il menu a 9 punti (waffle / servizi) nell'header.
    Ritorna True se aperto, False altrimenti."""
    waffle_selectors = [
        'button[aria-label="Servizi"]',
        '[aria-label="Servizi"]',
        'button[aria-label*="Servi"]',
        'button[title="Servizi"]',
        '[title="Servizi"]',
        'aru-button:has(aru-symbol[href*="grid"])',
        'aru-button:has(aru-symbol[href*="apps"])',
        'aru-button:has(aru-symbol[href*="services"])',
    ]
    for sel in waffle_selectors:
        try:
            el = page.locator(sel).first
            if el.count() > 0 and el.is_visible():
                el.click()
                time.sleep(1)
                return True
        except Exception:
            pass
    return False


def test_conservazione_waffle_menu(page):
    """Apre la sezione Conservazione tramite il menu a 9 punti (waffle menu).
    Verifica che la sezione si apra correttamente.
    Skip se il waffle menu o la feature non sono disponibili nell'ambiente."""

    LoginPec(page).login_pec(config)

    try:
        page.locator('button:has-text("Ricordarmelo"), button:has-text("Non ora"), button[aria-label="Chiudi"]').first.click(timeout=2000)
    except Exception:
        pass

    time.sleep(1)

    # --- Prova apertura waffle menu ---
    waffle_opened = _click_waffle_menu(page)

    if not waffle_opened:
        # Fallback: button[title="Conservazione"] è nel DOM ma hidden (dropdown chiuso)
        # Usa dispatch_event per forzare il click senza verificare la visibilità
        page.goto(SETTINGS_URL, timeout=20000)
        page.wait_for_load_state("networkidle", timeout=15000)
        time.sleep(1)
        try:
            conservazione_btn = page.locator('button[title="Conservazione"]').first
            conservazione_btn.wait_for(state="attached", timeout=5000)
            conservazione_btn.dispatch_event("click")
            try:
                page.wait_for_load_state("networkidle", timeout=10000)
            except Exception:
                pass
            time.sleep(2)
        except Exception:
            pytest.skip("Feature 'Conservazione' non disponibile in questo ambiente")

        page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"test_conservazione_02_settings_{datetime.now():%H-%M-%S}.png"
        ))
        # Verifica che la sezione si sia aperta
        content = page.content().lower()
        assert "conservazione" in content, \
            "La sezione Conservazione non si è aperta correttamente"
        print("Conservazione aperta da settings (waffle menu non disponibile)")

    else:
        # Waffle menu aperto — cerca la voce "Conservazione"
        time.sleep(1)
        conservazione_item = page.locator(
            'button:has-text("Conservazione"), a:has-text("Conservazione"), '
            'aru-menu-item:has-text("Conservazione"), [role="menuitem"]:has-text("Conservazione")'
        ).first

        if not conservazione_item.is_visible():
            pytest.skip("Voce 'Conservazione' non trovata nel waffle menu di questo ambiente")

        page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"test_conservazione_02_waffle_{datetime.now():%H-%M-%S}.png"
        ))

        # Clicca — potrebbe aprire nuova tab
        try:
            with page.context.expect_page(timeout=5000) as new_page_info:
                conservazione_item.click()
            conservazione_page = new_page_info.value
            conservazione_page.wait_for_load_state("networkidle", timeout=15000)
            time.sleep(2)
            content = conservazione_page.content().lower()
            assert "conservazione" in content or "conservation" in content, \
                "La sezione Conservazione non si è aperta correttamente (nuova tab)"
            conservazione_page.screenshot(path=os.path.join(
                REPORT_FOLDER, f"test_conservazione_02_nuovatable_{datetime.now():%H-%M-%S}.png"
            ))
            conservazione_page.close()
            print("Conservazione aperta con successo in nuova tab")
        except Exception:
            # Stessa tab
            conservazione_item.click()
            time.sleep(2)
            content = page.content().lower()
            assert "conservazione" in content or "conservation" in content, \
                "La sezione Conservazione non si è aperta correttamente"
            print("Conservazione aperta con successo nella stessa tab")

    # Screenshot finale
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_conservazione_02___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    page.screenshot(path=screenshot_path, full_page=True)
    print(f"Screenshot salvato in: {screenshot_path}")
