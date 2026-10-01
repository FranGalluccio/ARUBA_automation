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


def trova_cartella_sidebar(page: Page, nome_cartella: str, max_scroll: int = 25):
    """Cerca una cartella per titolo nella sidebar 'Le mie cartelle', scrollando
    con eventi reali del mouse. La lista è a virtual-scroll (Angular CDK): con
    molte cartelle nell'account, solo una finestra attorno alla posizione di
    scroll corrente è presente nel DOM. Impostare scrollTop via JS non basta a
    far ricalcolare la viewport — serve un vero evento di scroll (mouse.wheel).
    Restituisce il locator della cartella trovata (count() > 0), o l'ultimo
    locator provato se non trovata entro max_scroll tentativi."""
    selettore = f'button[title="{nome_cartella}"], [title="{nome_cartella}"]'
    loc = page.locator(selettore)
    if loc.count() > 0:
        return loc

    nav = page.locator("nav.folders-container").first
    box = nav.bounding_box()
    if not box:
        return loc
    page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)

    # Scrolla dall'alto: azzera lo scroll, poi scende gradualmente
    page.evaluate("() => { const n = document.querySelector('nav.folders-container'); if (n) n.scrollTop = 0; }")
    page.wait_for_timeout(200)
    for _ in range(max_scroll):
        loc = page.locator(selettore)
        if loc.count() > 0:
            return loc
        page.mouse.wheel(0, 300)
        page.wait_for_timeout(150)
    return page.locator(selettore)


class LoginPel:
    def __init__(self, page: Page):
        self.page = page

    def login_pel(self, config):
        username = config["pel"]["username"]
        password = config["pel"]["password"]
        url_pattern = config["pel"].get("inbox_url_pattern", "INBOX|management|messages")

        # Il login a due step (dominio "Aruba Mail" generico) a volte non va a buon
        # fine al primo tentativo (torna alla pagina di login senza errore visibile):
        # ritenta l'intero flusso da capo invece di solo l'ultimo click.
        for _attempt in range(3):
            self.page.goto(config["pel"]["url"], timeout=30_000)

            # Aspetta che il campo username sia visibile (caricamento asincrono)
            # Il form PEL usa name='text' per l'username (non 'username' o 'email')
            username_input = self.page.locator("input[name='text'], input[name='username'], input#username, input[type='email']").first
            username_input.wait_for(state="visible", timeout=15_000)
            username_input.fill(username)
            self.page.wait_for_timeout(500)

            # Login a due step: email + "Prosegui", il campo password appare solo
            # dopo. Se già presente, è un form a step unico.
            password_input = self.page.locator("input[name='password'], input#password, input[type='password']")
            if password_input.count() == 0:
                prosegui_btn = self.page.locator('button:has-text("Prosegui"), button:has-text("Continua")').first
                prosegui_btn.click()
                password_input.first.wait_for(state="visible", timeout=15_000)

            password_input.first.fill(password)
            self.page.wait_for_timeout(300)

            # Selettore specifico sul title: button[type='submit']/has-text generici
            # possono fare match su un bottone diverso prima di quello giusto nel DOM.
            accedi_btn = self.page.locator("button[title='Accedi']").first
            if accedi_btn.count() == 0:
                accedi_btn = self.page.locator("button[type='submit'], button:has-text('Login'), button:has-text('Accedi'), aru-button[skin='primary']").first
            accedi_btn.click()

            self.page.wait_for_load_state("load", timeout=20_000)

            try:
                expect(self.page).to_have_url(re.compile(f".*({url_pattern}).*"), timeout=10_000)
                break
            except Exception:
                if _attempt == 2:
                    raise
                self.page.wait_for_timeout(2000)

        # Se atterrati su management/home, naviga esplicitamente all'inbox PEL
        if "management" in self.page.url:
            login_url = config["pel"]["url"].rstrip("/")
            base_url = login_url.split("/auth/")[0] if "/auth/" in login_url else login_url
            self.page.goto(f"{base_url}/messages/INBOX", timeout=20_000)
            self.page.wait_for_load_state("load", timeout=20_000)
            self.page.wait_for_timeout(1500)

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


def elimina_evento_pel(page, testo: str, max_iter: int = 20):
    """Elimina tutti gli eventi PEL che contengono 'testo' nella vista Eventi.
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
        # exact=True evita strict mode violation con "Gestione calendario" visibile
        page.get_by_role("button", name="Calendario", exact=True).click()
        page.get_by_role("button", name="Eventi").wait_for(state="visible", timeout=5000)
        page.get_by_role("button", name="Eventi").click(force=True)
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
                page.locator('button[title="Annulla evento"]').first.click(timeout=3000)
                page.wait_for_timeout(500)
            except Exception:
                pass
            try:
                page.get_by_role("radio", name="Tutti gli eventi").check(timeout=2000)
                page.wait_for_timeout(300)
                page.get_by_role("button", name="Ok").first.click(timeout=2000)
                page.wait_for_timeout(500)
            except Exception:
                pass
            try:
                page.get_by_role("button", name="Elimina").first.click(timeout=3000)
                page.wait_for_timeout(1500)
            except Exception:
                pass
            try:
                page.keyboard.press("Escape")
                page.wait_for_timeout(300)
            except Exception:
                pass
            page.get_by_role("button", name="Eventi").click(force=True)
            page.wait_for_timeout(1500)
    except Exception:
        pass
