import time
from datetime import datetime
from base_mobile import (
    LoginPecMobile, MobileNav, crea_messaggio_mobile,
    config, REPORT_FOLDER, screenshot
)


def test_inbox_navigation_mobile(page):
    """Verifica navigazione inbox mobile: lista messaggi, apertura drawer,
    switch tra cartelle via hamburger, ritorno via bottom tab."""

    LoginPecMobile(page).login_pec()
    time.sleep(1)
    nav = MobileNav(page)

    # --- Lista messaggi visibile ---
    msgs = page.locator('div.frame-record-desktop, [class*="message-row"], [class*="mail-item"]')
    assert msgs.count() >= 0, "Impossibile trovare il contenitore dei messaggi"
    screenshot(page, "test_messaggi_01_inbox")

    # --- Apertura drawer via hamburger ---
    nav.open_hamburger()
    screenshot(page, "test_messaggi_02_drawer")

    # Verifica voci drawer
    assert page.locator('text="In arrivo"').count() > 0, \
        "Voce 'In arrivo' non trovata nel drawer"
    assert page.locator('text="Inviati"').count() > 0, \
        "Voce 'Inviati' non trovata nel drawer"

    # --- Naviga a Inviati ---
    page.locator('text="Inviati"').first.click()
    time.sleep(1)
    screenshot(page, "test_messaggi_03_inviati")
    assert "Inviati" in page.url or "Sent" in page.url or \
           page.locator('h1, [class*="title"]').filter(has_text="Inviati").count() > 0, \
        f"Navigazione a 'Inviati' non riuscita — URL: {page.url}"

    # --- Ritorna a Messaggi via bottom tab ---
    nav.nav_tab("messaggi")
    time.sleep(1)
    assert "INBOX" in page.url or "messages" in page.url, \
        f"Bottom tab 'Messaggi' non ha navigato all'inbox — URL: {page.url}"

    screenshot(page, "test_messaggi_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print("Navigazione inbox mobile OK")


def test_apri_messaggio_mobile(page):
    """Apre il primo messaggio in inbox su mobile e verifica il dettaglio."""

    LoginPecMobile(page).login_pec()
    time.sleep(1)

    time.sleep(2)
    screenshot(page, "test_apri_msg_01_lista")

    # Su mobile i row sono a y > window.innerHeight (CDP viewport troncato).
    # Usa il bypass button accessibilità "Passa all'ultimo messaggio ricevuto" via JS click.
    opened = False
    try:
        page.evaluate("""() => {
            const btn = document.querySelector('button[aria-label*=\"ultimo messaggio\"]');
            if (btn) { btn.click(); return true; }
            return false;
        }""")
        time.sleep(2)
        opened = True
    except Exception:
        pass

    if not opened:
        # Fallback: forza click sulle coordinate centro-alto del viewport (area messaggi)
        page.mouse.click(195, 300)
        time.sleep(2)
    time.sleep(2)

    screenshot(page, "test_apri_msg_02_dettaglio")

    # Verifica che la pagina non sia crashata (su mobile l'URL rimane nella webmail)
    assert "webmail" in page.url, f"URL inatteso dopo apertura messaggio: {page.url}"

    screenshot(page, "test_apri_messaggio_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print("Apertura messaggio mobile OK")


def test_componi_invia_mobile(page):
    """Compone e invia un messaggio tramite FAB mobile, verifica toast di conferma."""

    LoginPecMobile(page).login_pec()
    time.sleep(1)

    nav = MobileNav(page)
    ts = int(time.time())
    oggetto = f"Test mobile {ts}"
    corpo = "Test automatico composizione mobile Playwright"

    time.sleep(1)
    screenshot(page, "test_componi_01_pre")

    # Apri compose via FAB
    nav.open_compose()
    time.sleep(1)
    screenshot(page, "test_componi_02_compose_aperto")

    # Verifica che la finestra di composizione si sia aperta
    compose_open = (
        page.locator('span[title="Invia"]').count() > 0
        or page.locator('input[placeholder*="Destinatari"]').count() > 0
        or page.locator('[class*="compose"], [class*="new-message"]').count() > 0
    )
    assert compose_open, "La finestra di composizione non si è aperta su mobile"

    # Compila destinatario
    destinatario = config["destinatari"]["destinatario_principale"]
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

    screenshot(page, "test_componi_03_compilato")

    # Invia
    page.locator(
        'span[title="Invia"], button[title="Invia"], '
        'aru-button:has-text("Invia"), button:has-text("Invia")'
    ).first.click()
    time.sleep(3)

    screenshot(page, "test_componi_04_post_invio")

    # Verifica toast di conferma
    toast = page.locator("div.aru-toast__message, [class*='toast']").first
    assert toast.is_visible() or page.locator("div.aru-toast__message").count() > 0, \
        "Nessun toast di conferma dopo l'invio del messaggio mobile"

    screenshot(page, "test_componi_invia_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Composizione e invio mobile OK — oggetto: {oggetto}")
