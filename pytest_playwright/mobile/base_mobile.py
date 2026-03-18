import os
import re
import sys
import json
import time
from datetime import datetime
from playwright.sync_api import Page, expect

# Percorso config.json nella cartella padre (pytest_playwright/)
_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _BASE_DIR)

CONFIG_FILE = os.path.join(_BASE_DIR, "config.json")
with open(CONFIG_FILE, encoding="utf-8") as _f:
    config = json.load(_f)

REPORT_FOLDER = os.path.join(_BASE_DIR, "test-results", "mobile")
os.makedirs(REPORT_FOLDER, exist_ok=True)


# ---------------------------------------------------------------------------
# Selectors mobile
# ---------------------------------------------------------------------------

# Hamburger ≡ (top-left header)
_HAMBURGER = (
    'button[aria-label="Menu"], '
    'button[aria-label="menu"], '
    'button[aria-label="Apri menu"], '
    'button[aria-label="Toggle navigation"], '
    'header button:first-child, '
    '[class*="hamburger"] button, '
    'button:has(svg[title="Menu"]), '
    'button:has(aru-symbol[title="Menu"])'
)

# Label dei bottom tab (testo esatto) — usati con get_by_text() che pierces shadow DOM
_BOTTOM_TAB_LABELS = {
    "messaggi":   "Messaggi",
    "contatti":   "Contatti",
    "calendario": "Calendario",
    "altro":      "Altro",
}

# FAB compose (matita blu in basso a destra) — bypass button accesso diretto
_FAB_COMPOSE = (
    'button[aria-label="Passa alla creazione del messaggio"], '
    'button[aria-label="Nuovo messaggio"], '
    'button[aria-label*="Nuovo"], '
    'button[aria-label*="componi"], '
    'button[aria-label*="Componi"], '
    'button[aria-label*="scrivi"], '
    '[class*="fab"] button, '
    'button[class*="fab"]'
)

# Hamburger — l'ARU-BUTTON ghost dentro lo slot symbol-sx di aru-navbar
_HAMBURGER = (
    '[slot="symbol-sx"] aru-button, '
    'aru-navbar aru-button[kind="ghost"], '
    'button[aria-label="Menu"], '
    'button[aria-label="Apri menu"], '
    'button.bypass-button[aria-label*="cartella"]'
)


# ---------------------------------------------------------------------------
# LoginPecMobile
# ---------------------------------------------------------------------------

class LoginPecMobile:
    """Login PEC — identico al desktop, l'interfaccia di login non cambia su mobile."""

    def __init__(self, page: Page):
        self.page = page

    def login_pec(self, cfg: dict = None):
        if cfg is None:
            cfg = config

        for attempt in range(3):
            try:
                self.page.goto(cfg["pec"]["url"], timeout=60_000)
                break
            except Exception:
                if attempt == 2:
                    raise
                self.page.wait_for_timeout(5000)

        self.page.locator(
            "input[name='username'], input#username, input[type='email']"
        ).first.fill(cfg["pec"]["username"])

        self.page.locator(
            "input[name='password'], input#password, input[type='password']"
        ).first.fill(cfg["pec"]["password"])

        # Chiudi cookie banner prima di cliccare submit (su mobile può coprire il bottone)
        for cookie_sel in [
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            ".CybotCookiebotDialogBodyButton:last-child",
            'button[id*="CybotCookiebotDialog"]',
        ]:
            try:
                self.page.locator(cookie_sel).first.click(timeout=2000)
                time.sleep(0.3)
                break
            except Exception:
                pass

        # Chiudi eventuali modal (es. modalStore promo/news)
        try:
            self.page.locator('#modalStore button, [id*="modal"] button.btn-primary').last.click(timeout=2000)
            time.sleep(0.3)
        except Exception:
            pass

        self.page.locator(
            "button[type='submit'], button:has-text('Login'), button:has-text('Accedi')"
        ).first.click()

        self.page.wait_for_load_state("networkidle", timeout=20_000)

        url_pattern = cfg["pec"].get("inbox_url_pattern", "INBOX")
        expect(self.page).to_have_url(re.compile(f".*({url_pattern}).*"), timeout=20_000)

        # Chiudi cookie banner webmail (appare dopo il login, diverso da quello del login page)
        for selector in [
            'button:has-text("Accetta tutti")',
            "#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll",
            '.CybotCookiebotDialogBodyButton',
            'button[aria-label="Chiudi"]',
            'button:has-text("Non ora")',
            'button:has-text("Ricordarmelo")',
        ]:
            try:
                self.page.locator(selector).first.click(timeout=1500)
                time.sleep(0.3)
            except Exception:
                pass
        # Attesa extra per garantire che il banner sia scomparso
        time.sleep(0.5)


# ---------------------------------------------------------------------------
# MobileNav — navigazione hamburger + bottom tabs + FAB
# ---------------------------------------------------------------------------

class MobileNav:
    """Helper per navigazione mobile."""

    def __init__(self, page: Page):
        self.page = page

    def open_hamburger(self):
        """Apre il drawer cliccando il bottone hamburger (≡).
        get_by_role pierces shadow DOM — l'aru-menu ha aria-label='Menu'."""
        try:
            self.page.get_by_role("button", name="Menu").first.click(timeout=4000)
        except Exception:
            # Fallback CSS su slot visibile
            self.page.locator('[slot="symbol-sx"] aru-button').first.click(force=True)
        time.sleep(0.8)

    def close_drawer(self):
        """Chiude il drawer laterale (X o Escape)."""
        try:
            self.page.locator(
                'button[aria-label="Chiudi"], '
                '[class*="drawer"] button[aria-label="Chiudi"]'
            ).first.click(timeout=2000)
        except Exception:
            try:
                self.page.keyboard.press("Escape")
            except Exception:
                pass
        time.sleep(0.5)

    def nav_tab(self, tab: str):
        """Naviga tramite bottom tab bar: messaggi | contatti | calendario | altro.
        Usa get_by_text() che pierces shadow DOM automaticamente."""
        label = _BOTTOM_TAB_LABELS.get(tab.lower())
        if not label:
            raise ValueError(f"Tab sconosciuto: {tab}")
        # get_by_text pierces shadow DOM — prende l'ultimo elemento con quel testo
        # (il più in basso nella pagina = bottom nav tab)
        els = self.page.get_by_text(label, exact=True)
        count = els.count()
        assert count > 0, f"Tab '{label}' non trovato (shadow DOM incluso)"
        els.last.click()
        time.sleep(1)

    def nav_folder(self, folder_name: str):
        """Apre hamburger e naviga a una cartella (es. 'In arrivo', 'Inviati')."""
        self.open_hamburger()
        self.page.get_by_text(folder_name, exact=True).first.click()
        time.sleep(1)

    def open_compose(self):
        """Clicca il FAB di composizione (matita blu) via shadow DOM traversal."""
        self.click_fab("Nuovo messaggio")
        time.sleep(1)

    def click_fab(self, aria_label: str = None):
        """Clicca il FAB (60×60 aru-button) tramite page.mouse.click() alle sue coordinate.
        Il FAB non ha aria-label: trovato per dimensione (≥55×55).
        I bottom-tab nav sono solo 50px di altezza: non vengono confusi col FAB."""
        for btn in self.page.locator('aru-button').all():
            try:
                bb = btn.bounding_box()
                if bb and bb['width'] >= 55 and bb['height'] >= 55:
                    cx = bb['x'] + bb['width'] / 2
                    cy = bb['y'] + bb['height'] / 2
                    self.page.mouse.click(cx, cy)
                    return
            except Exception:
                pass

    def is_bottom_nav_visible(self) -> bool:
        """Verifica che la bottom navigation mobile sia presente.
        Usa get_by_text() che pierces shadow DOM."""
        return self.page.get_by_text("Messaggi", exact=True).count() > 0


# ---------------------------------------------------------------------------
# Helper compose messaggio mobile
# ---------------------------------------------------------------------------

def crea_messaggio_mobile(page: Page, cfg: dict, oggetto: str, corpo: str):
    """
    Compone un messaggio via FAB mobile e lo invia.
    Non allega file (le UI mobile variano troppo per l'upload).
    """
    nav = MobileNav(page)
    nav.open_compose()

    destinatario = cfg["destinatari"]["destinatario_principale"]

    # Campo destinatario
    page.locator(
        "input[placeholder*='Destinatari'], input[placeholder*='destinatari'], "
        "input[aria-label*='Destinatari']"
    ).first.fill(destinatario)
    page.keyboard.press("Enter")
    time.sleep(0.5)

    # Oggetto
    page.locator(
        "input[aria-label='input field'], input[placeholder*='Oggetto'], "
        "input[placeholder*='oggetto']"
    ).first.fill(oggetto)

    # Corpo
    page.locator("div[contenteditable='true']").first.fill(corpo)

    # Invia
    page.locator(
        'span[title="Invia"], button[title="Invia"], '
        'aru-button:has-text("Invia"), button:has-text("Invia")'
    ).first.click()
    time.sleep(3)


# ---------------------------------------------------------------------------
# Screenshot helper
# ---------------------------------------------------------------------------

def screenshot(page: Page, name: str):
    path = os.path.join(REPORT_FOLDER, f"{name}_{datetime.now():%H-%M-%S}.png")
    page.screenshot(path=path, full_page=True)
    return path
