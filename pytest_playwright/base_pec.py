import os
import time
import re
import json
from urllib.parse import urlparse
from playwright.sync_api import Page, expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Root del repo (parent di pytest_playwright/) ---
GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def dismiss_overlay(page: Page):
    """Chiude qualsiasi CDK overlay backdrop attivo (welcome wizard, dialog).
    Da chiamare prima di click force=True su elementi potenzialmente bloccati."""
    for _ in range(5):
        try:
            page.wait_for_function(
                "!document.querySelector('.cdk-overlay-backdrop-showing')",
                timeout=500,
            )
            break
        except Exception:
            pass
        try:
            page.evaluate("""() => {
                const dismissTexts = ['Chiudi', 'Non ora', 'Ricordarmelo', 'Capito', 'Ho capito', 'Ok'];
                const pane = document.querySelector('.cdk-overlay-pane');
                if (!pane) { return; }
                const closeBtn = pane.querySelector(
                    'button[aria-label="Chiudi"], button[title="Chiudi"]'
                );
                if (closeBtn) { closeBtn.click(); return; }
                for (const btn of pane.querySelectorAll('button')) {
                    if (dismissTexts.includes(btn.textContent.trim())) { btn.click(); return; }
                }
            }""")
        except Exception:
            pass
        try:
            page.keyboard.press("Escape")
        except Exception:
            pass
        page.wait_for_timeout(500)


def get_app_base_url(page: Page) -> str:
    """Restituisce schema+host dell'app webmail dalla pagina corrente.
    Funziona sia in ambienti test (es. webmail.test.pec.aruba.it)
    sia in prod-aruba dove l'URL di login è su login.aruba.it."""
    parsed = urlparse(page.url)
    return f"{parsed.scheme}://{parsed.netloc}"


def _resolve_path(raw):
    """Risolve un path relativo rispetto alla root del repo Git_automation/."""
    if raw and not os.path.isabs(raw):
        return os.path.normpath(os.path.join(GIT_ROOT, raw))
    return raw


# --- Percorso allegato dinamico ---
file_allegato = _resolve_path(os.environ.get("FILE_ALLEGATO", config.get("file_allegato")))

class LoginPec:
    def __init__(self, page: Page):
        self.page = page

    def login_pec(self, config):
        username = config["pec"]["username"]
        password = config["pec"]["password"]

    # Vai alla pagina di login (retry su errori di rete transitori)
        for _attempt in range(3):
            try:
                self.page.goto(config["pec"]["url"], timeout=60_000)
                break
            except Exception:
                if _attempt == 2:
                    raise
                self.page.wait_for_timeout(5000)

    # Compila username
        _user_loc = self.page.locator("input[name='username'], input#username, input[type='email']").first
        try:
            _user_loc.fill(username)
        except Exception:
            _user_loc.scroll_into_view_if_needed()
            _user_loc.fill(username, force=True)

    # Compila password
        _pass_loc = self.page.locator("input[name='password'], input#password, input[type='password']").first
        try:
            _pass_loc.fill(password)
        except Exception:
            _pass_loc.scroll_into_view_if_needed()
            _pass_loc.fill(password, force=True)

    # Clicca login
        self.page.locator("button[type='submit'], button:has-text('Login')").first.click()

    # Attendi caricamento pagina
        self.page.wait_for_load_state("load", timeout=30_000)
        self.page.wait_for_timeout(5000)

    # Gestisci errore 500 dell'ambiente: riprova il login da capo
        try:
            _title = self.page.title()
        except Exception:
            _title = ""
        if "500" in _title or "Internal Server Error" in _title or "ajaxmail" in self.page.url:
            self.page.wait_for_timeout(3000)
            self.page.goto(config["pec"]["url"], timeout=60_000)
            self.page.wait_for_load_state("load", timeout=30_000)
            self.page.locator("input[name='username'], input#username, input[type='email']").first.fill(username)
            self.page.locator("input[name='password'], input#password, input[type='password']").first.fill(password)
            self.page.locator("button[type='submit'], button:has-text('Login')").first.click()
            self.page.wait_for_load_state("load", timeout=30_000)
            self.page.wait_for_timeout(5000)

    # Gestisci redirect smart-login (sessione residua che intercetta il login)
        if "smart-login" in self.page.url:
            inbox_url = get_app_base_url(self.page) + "/new/messages/INBOX"
            self.page.goto(inbox_url, timeout=60_000, wait_until="domcontentloaded")
            self.page.wait_for_timeout(3000)

    # Gestisci redirect Keycloak authenticate (execution token scaduto post-submit)
        elif "login-actions/authenticate" in self.page.url:
            # Token scaduto lato server: riprova fino a 3 volte con URL base fresco
            for _retry in range(3):
                self.page.goto(config["pec"]["url"], timeout=60_000)
                self.page.wait_for_load_state("load", timeout=30_000)
                if "login-actions/authenticate" not in self.page.url:
                    break
                self.page.wait_for_timeout(2000)
            # Ora compila e invia
            try:
                self.page.locator("input[name='username'], input#username, input[type='email']").first.fill(username, timeout=10000)
                self.page.locator("input[name='password'], input#password, input[type='password']").first.fill(password)
                self.page.locator("button[type='submit'], button:has-text('Login')").first.click()
                self.page.wait_for_load_state("load", timeout=30_000)
                self.page.wait_for_timeout(5000)
            except Exception:
                pass
            if "smart-login" in self.page.url:
                inbox_url = get_app_base_url(self.page) + "/new/messages/INBOX"
                self.page.goto(inbox_url, timeout=60_000, wait_until="domcontentloaded")
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
            self.page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=2000)
        except Exception:
            pass

    # Chiudi modale iniziale (se presente)
        try:
            self.page.locator('button[aria-label="Chiudi"]').first.click(timeout=3000)
        except Exception:
            pass

    # Chiudi qualsiasi CDK overlay backdrop (welcome wizard, ecc.) rimasto dopo il login
        dismiss_overlay(self.page)

            
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
        page.locator("button:has-text('Nuovo messaggio'), button:has-text('Nouveau message')").click(force=True)
        try:
            page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").fill(destinatario, timeout=2000)
        except:
            page.locator('input[aria-label="input field"]').click()
            page.locator("input[placeholder='Destinatari'], input[placeholder='Destinataires']").fill(destinatario)
    # Oggetto e corpo
        page.locator('input[aria-label="input field"]').fill(oggetto)
        page.locator("div[contenteditable='true']").fill(corpo)

    # Allegato opzionale
        if path_allegato:
                page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()
                with page.expect_file_chooser() as fc_info:
                    page.locator("aru-menu-item:has-text('Carica da dispositivo'), aru-menu-item:has-text('appareil'), aru-menu-item:has-text('dispositivo')").first.click()
                file_chooser = fc_info.value
                file_chooser.set_files([path_allegato])
                page.wait_for_timeout(5000)
                time.sleep(3)

    # Dismiss cookie banner se appare durante la composizione del messaggio
        try:
            page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click(timeout=2000)
        except Exception:
            pass


def elimina_evento_pec(page, testo: str, max_iter: int = 20):
    """Elimina tutti gli eventi PEC che contengono 'testo' nella vista Eventi.
    Chiamare dal blocco finally del test per garantire il cleanup."""
    try:
        # Chiudi eventuali dialog/overlay aperti prima di navigare
        for _ in range(4):
            try:
                if page.locator('.cdk-overlay-backdrop').count() > 0:
                    page.keyboard.press("Escape")
                    page.wait_for_timeout(400)
                else:
                    break
            except Exception:
                break
        for cal_name in ["Calendario", "Calendrier"]:
            try:
                page.get_by_role("button", name=cal_name, exact=True).click(timeout=3000)
                break
            except Exception:
                pass
        for ev_name in ["Eventi", "Événements", "Agenda", "Events"]:
            try:
                btn = page.get_by_role("button", name=ev_name)
                btn.wait_for(state="visible", timeout=3000)
                btn.click(force=True)
                break
            except Exception:
                pass
        page.wait_for_timeout(1500)
        for _ in range(max_iter):
            ev = page.get_by_text(testo, exact=False).first
            if ev.count() == 0:
                break
            ev.click()
            page.wait_for_timeout(1500)
            try:
                page.locator('button:has(aru-symbol[symbol="dots-separator"])').first.click(timeout=3000)
                page.wait_for_timeout(500)
            except Exception:
                pass
            try:
                page.locator(
                    'button[title="Annulla evento"], button[title="Annuler l\'événement"], '
                    'button[title="Supprimer l\'événement"]'
                ).first.click(timeout=3000)
                page.wait_for_timeout(500)
            except Exception:
                pass
            # Gestione eventi ricorrenti: seleziona "Tutti gli eventi" → Ok
            try:
                for radio_name in ["Tutti gli eventi", "Tous les événements", "All events"]:
                    try:
                        page.get_by_role("radio", name=radio_name).check(timeout=1000)
                        break
                    except Exception:
                        pass
                page.wait_for_timeout(300)
                page.get_by_role("button", name="Ok").first.click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass
            try:
                for del_name in ["Elimina", "Supprimer", "Delete"]:
                    try:
                        page.get_by_role("button", name=del_name).first.click(timeout=2000)
                        break
                    except Exception:
                        pass
                page.wait_for_timeout(1500)
            except Exception:
                pass
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception:
                pass
            for ev_name in ["Eventi", "Événements", "Agenda", "Events"]:
                try:
                    btn = page.get_by_role("button", name=ev_name)
                    if btn.count() > 0 and btn.first.is_visible():
                        btn.first.click(force=True)
                        break
                except Exception:
                    pass
            page.wait_for_timeout(1500)
    except Exception:
        pass
