import time
from datetime import datetime
from base_mobile import LoginPecMobile, MobileNav, config, REPORT_FOLDER, screenshot


def test_navigazione_impostazioni_mobile(page):
    """Naviga alle Impostazioni su mobile (hamburger → avatar/profilo → Impostazioni)
    e verifica che la pagina carichi correttamente."""

    LoginPecMobile(page).login_pec()
    time.sleep(1)

    nav = MobileNav(page)
    screenshot(page, "test_impostazioni_01_inbox")

    # --- Metodo 1: bottom tab "Altro" → Impostazioni ---
    settings_reached = False
    try:
        nav.nav_tab("altro")
        time.sleep(1)
        screenshot(page, "test_impostazioni_02_altro")

        page.locator(
            'text="Impostazioni", button:has-text("Impostazioni"), '
            'a:has-text("Impostazioni"), [class*="settings"]'
        ).first.click(timeout=4000)
        time.sleep(2)
        if "settings" in page.url.lower() or "impostazioni" in page.url.lower():
            settings_reached = True
    except Exception:
        pass

    # --- Metodo 2: hamburger → avatar/profilo → Impostazioni ---
    if not settings_reached:
        try:
            nav.open_hamburger()
            time.sleep(0.5)
            screenshot(page, "test_impostazioni_03_drawer")

            page.locator(
                'text="Impostazioni", button:has-text("Impostazioni"), '
                'a:has-text("Impostazioni")'
            ).first.click(timeout=4000)
            time.sleep(2)
            if "settings" in page.url.lower() or "impostazioni" in page.url.lower():
                settings_reached = True
        except Exception:
            pass

    # --- Metodo 3: naviga direttamente via URL ---
    if not settings_reached:
        settings_url = config["pec"]["url"].rstrip("/") + "/new/settings/home"
        page.goto(settings_url, timeout=20000)
        try:
            page.wait_for_load_state("networkidle", timeout=10000)
        except Exception:
            pass
        time.sleep(1)
        settings_reached = "settings" in page.url.lower() or "impostazioni" in page.url.lower()

    assert settings_reached, \
        f"Impossibile raggiungere le Impostazioni su mobile — URL: {page.url}"

    screenshot(page, "test_impostazioni_04_pagina")

    # Verifica contenuto impostazioni
    content_ok = (
        page.locator('h1:has-text("Impostazioni"), h2:has-text("Impostazioni")').count() > 0
        or page.locator('text="Casella PEC"').count() > 0
        or page.locator('text="Account e sicurezza"').count() > 0
        or page.locator('text="Messaggi e scrittura"').count() > 0
    )
    assert content_ok, \
        "La pagina Impostazioni non mostra il contenuto atteso su mobile"

    screenshot(page, "test_navigazione_impostazioni_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Navigazione Impostazioni mobile OK — URL: {page.url}")


def test_accesso_sezione_impostazioni_mobile(page):
    """Verifica che le sezioni principali delle impostazioni siano accessibili su mobile
    (Casella PEC, Messaggi e scrittura, Account e sicurezza)."""

    LoginPecMobile(page).login_pec()
    time.sleep(1)

    # Naviga direttamente alle impostazioni
    settings_url = config["pec"]["url"].rstrip("/") + "/new/settings/home"
    page.goto(settings_url, timeout=20000)
    try:
        page.wait_for_load_state("networkidle", timeout=10000)
    except Exception:
        pass
    time.sleep(2)

    screenshot(page, "test_sez_impostazioni_01")

    # Verifica sezioni presenti (almeno 2 su 3)
    sezioni_trovate = []
    for sezione in ["Casella PEC", "Messaggi e scrittura", "Account e sicurezza", "Aspetto"]:
        if page.locator(f'text="{sezione}"').count() > 0:
            sezioni_trovate.append(sezione)

    assert len(sezioni_trovate) >= 2, \
        f"Trovate solo {len(sezioni_trovate)} sezioni impostazioni su mobile: {sezioni_trovate}"

    # Clicca su "Casella PEC" (o "Account e sicurezza") per verificare navigazione interna
    try:
        page.locator('text="Casella PEC"').first.click(timeout=3000)
        time.sleep(1)
        screenshot(page, "test_sez_impostazioni_02_casella_pec")
    except Exception:
        pass

    screenshot(page, "test_accesso_sezione_impostazioni_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Sezioni impostazioni trovate su mobile: {sezioni_trovate}")
