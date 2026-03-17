import os
import time
import re
import json
from playwright.sync_api import Page, expect

# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato dinamico ---
file_allegato = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))


class LoginPel:
    def __init__(self, page: Page):
        self.page = page

    def login_pel(self, config):
        self.page.goto(config["pel"]["url"], timeout=30_000)

        username = config["pel"]["username"]
        password = config["pel"]["password"]

        self.page.locator("input[name='username'], input#username, input[type='email']").first.fill(username)
        self.page.locator("input[name='password'], input#password, input[type='password']").first.fill(password)
        self.page.locator("button[type='submit'], button:has-text('Login'), aru-button[skin='primary']").first.click()

        self.page.wait_for_load_state("networkidle", timeout=20_000)

        url_pattern = config["pel"].get("inbox_url_pattern", "INBOX")
        expect(self.page).to_have_url(re.compile(f".*({url_pattern}).*"), timeout=20_000)

        # Cookie (se presente)
        try:
            self.page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
        except Exception:
            pass

        # Chiudi modale iniziale (se presente)
        try:
            self.page.locator('button[aria-label="Chiudi"], button:has-text("Non ora"), button:has-text("Ricordarmelo")').first.click(timeout=3000)
        except Exception:
            pass


class HelperPel:

    def crea_messaggio(
        page: Page,
        config: dict,
        oggetto: str,
        corpo: str,
        path_allegato: str = None,
        destinatario_key: str = "destinatario_principale"
    ):
        destinatario: str = config["destinatari"].get(destinatario_key)
        if not destinatario:
            raise ValueError(f"Destinatario non trovato in config per la chiave {destinatario_key}")

        # Dismiss overlay se presente
        if page.locator('.cdk-overlay-backdrop').first.is_visible():
            for _ in range(3):
                if not page.locator('.cdk-overlay-backdrop').is_visible():
                    break
                try:
                    btn = page.locator('button:has-text("Ricordarmelo"), button:has-text("Chiudi"), button:has-text("Non ora")').first
                    if btn.is_visible():
                        btn.click(force=True)
                        time.sleep(0.5)
                        continue
                    page.locator('.cdk-overlay-pane').last.locator('button').last.click(force=True)
                    time.sleep(0.5)
                except Exception:
                    break

        # Nuovo messaggio
        page.locator("button:has-text('Nuovo messaggio'), aru-button:has-text('Scrivi')").first.click(force=True)
        try:
            page.locator("input[placeholder='Destinatari']").fill(destinatario, timeout=2000)
        except Exception:
            page.locator('input[aria-label="input field"]').click()
            page.locator("input[placeholder='Destinatari']").fill(destinatario)

        page.locator('input[aria-label="input field"]').fill(oggetto)
        page.locator("div[contenteditable='true']").fill(corpo)

        if path_allegato:
            page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
            with page.expect_file_chooser() as fc_info:
                page.locator("aru-menu-item", has_text="Carica da dispositivo").first.click()
            file_chooser = fc_info.value
            file_chooser.set_files([path_allegato])
            page.wait_for_timeout(5000)
            time.sleep(3)
