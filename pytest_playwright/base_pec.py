import time
import re
from playwright.sync_api import Page
from playwright.sync_api import expect
import pytest

class LoginPec:
    def __init__(self, page: Page):
        self.page = page

    def login_pec(self):
        # Vai alla pagina di login
        self.page.goto("https://webmail.test.pec.aruba.it/", timeout=30_000)
        
        username = "francescoconservazione@pec.it"
        password = "123456Abc!"

        # Compila username
        self.page.locator("input[name='username'], input#username, input[type='email']").first.fill(username)

        # Compila password
        self.page.locator("input[name='password'], input#password, input[type='password']").first.fill(password)

        # Clicca login
        self.page.locator("button[type='submit'], button:has-text('Login')").first.click()

        # Attendi caricamento pagina
        self.page.wait_for_load_state("networkidle", timeout=20_000)
        
        # Verifica che l'elemento di logout sia visibile per confermare il login
        expect(self.page).to_have_url(re.compile(".*(INBOX).*"), timeout=20_000)
        
        # Cookie (se presente)
        try:
            self.page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
        except:
            pass
        
        # Chiudi modale iniziale (se presente)
        try:
            self.page.locator('button[aria-label="Chiudi"]').first.click(timeout=3000)
        except:
            pass
            
            
class Helper:

    def setup_method(self, method, page: Page):
        """Setup comune: login e accettazione cookie"""
        self.page = page
        LoginPec(self.page).login_pec(
            "francescoconservazione@pec.it",
            "1234567Ab!",
            "https://webmail.test.pec.aruba.it/"
        )
        # Accetta cookie
        self.page.locator("#CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
        

    def crea_messaggio(
    page: Page,
    destinatario: str,
    oggetto: str,
    corpo: str,
    path_allegato: str = None  # allegato facoltativo
):
    # Nuovo messaggio
        page.locator("button:has-text('Nuovo messaggio')").click()
        try:
            page.locator("input[placeholder='Destinatari']").fill(destinatario, timeout=2000)
        except:
            page.locator('input[aria-label="input field"]').click()
            page.locator("input[placeholder='Destinatari']").fill(destinatario)
        page.locator('input[aria-label="input field"]').fill(oggetto)
        page.locator("div[contenteditable='true']").fill(corpo)

    # Se c'è un allegato da caricare
        if path_allegato:
        # Apri menu allegati
            page.locator("aru-button-menu:has(use[href*='attachments-outline'])").click()

        # Intercetta il file chooser e seleziona il file
            with page.expect_file_chooser() as fc_info:
                page.locator("aru-menu-item", has_text="Carica da dispositivo").first.click()
            file_chooser = fc_info.value
            file_chooser.set_files([path_allegato])

        # Attendi caricamento allegato
            page.wait_for_timeout(5000)
            
        # Piccola attesa per sicurezza
        time.sleep(3)



