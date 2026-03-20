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

class LoginPec:
    def __init__(self, page: Page):
        self.page = page

    def login_pec(self, config):
    # Vai alla pagina di login (retry su errori di rete transitori)
        for _attempt in range(3):
            try:
                self.page.goto(config["pec"]["url"], timeout=60_000)
                break
            except Exception:
                if _attempt == 2:
                    raise
                self.page.wait_for_timeout(5000)

        username = config["pec"]["username"]
        password = config["pec"]["password"]

    # Compila username
        self.page.locator("input[name='username'], input#username, input[type='email']").first.fill(username)

    # Compila password
        self.page.locator("input[name='password'], input#password, input[type='password']").first.fill(password)

    # Clicca login
        self.page.locator("button[type='submit'], button:has-text('Login')").first.click()

    # Attendi caricamento pagina
        self.page.wait_for_load_state("load", timeout=30_000)
        self.page.wait_for_timeout(5000)

    # Gestisci redirect smart-login (sessione residua che intercetta il login)
        if "smart-login" in self.page.url:
            inbox_url = config["pec"]["url"].rstrip("/") + "/new/messages/INBOX"
            self.page.goto(inbox_url, timeout=30_000)
            self.page.wait_for_load_state("load", timeout=20_000)
            self.page.wait_for_timeout(3000)

    # Verifica login riuscito (pattern URL configurabile per ambienti diversi)
        url_pattern = config["pec"].get("inbox_url_pattern", "INBOX")
        expect(self.page).to_have_url(re.compile(f".*({url_pattern}).*"), timeout=30_000)

    # BNL: dopo il login reindirizza a /security/managedetails (pannello gestione account).
    # Il link "Read emails" è nel dropdown del profilo utente (elemento <a> con testo email).
        if "/security/" in self.page.url or "managedetails" in self.page.url:
            try:
                # Apri il dropdown cliccando il link con l'email in alto a destra (<a> non <button>)
                self.page.locator('a:has-text("@")').last.click(timeout=5000)
                self.page.wait_for_timeout(1000)
                # Naviga direttamente alla webmail usando l'href del link "Read emails"
                webmail_url = self.page.get_by_role("link", name="Read emails").first.get_attribute("href", timeout=3000)
                if webmail_url:
                    self.page.goto(webmail_url, timeout=30_000)
                    self.page.wait_for_load_state("load", timeout=20_000)
            except Exception:
                pass

    # Cookie (se presente)
        try:
            self.page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
        except Exception:
            pass

    # Chiudi modale iniziale (se presente)
        try:
            self.page.locator('button[aria-label="Chiudi"]').first.click(timeout=3000)
        except Exception:
            pass

            
class Helper:

    def crea_messaggio(
        page: Page,
        config: dict,
        oggetto: str,
        corpo: str,
        path_allegato: str = None,
        destinatario_key: str = "destinatario_principale"
    ):
    # --- Prendi destinatario dal config ---
        destinatario: str = config["destinatari"].get(destinatario_key)
        if not destinatario:
            raise ValueError(f"Destinatario non trovato in config per la chiave {destinatario_key}")

    # --- Dismiss any CDK backdrop (e.g., "Adegua la tua PEC" notice) ---
        if page.locator('.cdk-overlay-backdrop').first.is_visible():
            import time as _time
            for _ in range(3):
                if not page.locator('.cdk-overlay-backdrop').is_visible():
                    break
                try:
                    # Prova "Ricordarmelo" o "Chiudi" nell'overlay attivo
                    btn = page.locator('button:has-text("Ricordarmelo"), button:has-text("Chiudi"), button:has-text("Non ora")').first
                    if btn.is_visible():
                        btn.click(force=True)
                        _time.sleep(0.5)
                        continue
                    # Fallback: click l'ultimo button nell'ultimo pane
                    page.locator('.cdk-overlay-pane').last.locator('button').last.click(force=True)
                    _time.sleep(0.5)
                except Exception:
                    break

    # --- Nuovo messaggio ---
        page.locator("button:has-text('Nuovo messaggio')").click(force=True)
        try:
            page.locator("input[placeholder='Destinatari']").fill(destinatario, timeout=2000)
        except:
            page.locator('input[aria-label="input field"]').click()
            page.locator("input[placeholder='Destinatari']").fill(destinatario)
    # Oggetto e corpo
        page.locator('input[aria-label="input field"]').fill(oggetto)
        page.locator("div[contenteditable='true']").fill(corpo)

    # Allegato opzionale
        if path_allegato:
                page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
                with page.expect_file_chooser() as fc_info:
                    page.locator("aru-menu-item", has_text="Carica da dispositivo").first.click()
                file_chooser = fc_info.value
                file_chooser.set_files([path_allegato])
                page.wait_for_timeout(5000)
                time.sleep(3)

