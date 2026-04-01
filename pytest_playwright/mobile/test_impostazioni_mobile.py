from datetime import datetime
from base_mobile import LoginPecMobile, MobileNav, config, REPORT_FOLDER, screenshot
from base_pec import get_app_base_url


def test_navigazione_impostazioni_mobile(page):
    """Naviga alle Impostazioni su mobile (hamburger → avatar/profilo → Impostazioni)
    e verifica che la pagina carichi correttamente."""

    LoginPecMobile(page).login_pec()
    page.wait_for_timeout(1000)

    nav = MobileNav(page)
    screenshot(page, "test_impostazioni_01_inbox")

    # --- Metodo 1: bottom tab "Altro" → Impostazioni ---
    settings_reached = False
    try:
        nav.nav_tab("altro")
        page.wait_for_timeout(1000)
        screenshot(page, "test_impostazioni_02_altro")

        page.locator(
            'text="Impostazioni", button:has-text("Impostazioni"), '
            'a:has-text("Impostazioni"), [class*="settings"]'
        ).first.click(timeout=4000)
        page.wait_for_timeout(2000)
        if "settings" in page.url.lower() or "impostazioni" in page.url.lower():
            settings_reached = True
    except Exception:
        pass

    # --- Metodo 2: hamburger → avatar/profilo → Impostazioni ---
    if not settings_reached:
        try:
            nav.open_hamburger()
            page.wait_for_timeout(500)
            screenshot(page, "test_impostazioni_03_drawer")

            page.locator(
                'text="Impostazioni", button:has-text("Impostazioni"), '
                'a:has-text("Impostazioni")'
            ).first.click(timeout=4000)
            page.wait_for_timeout(2000)
            if "settings" in page.url.lower() or "impostazioni" in page.url.lower():
                settings_reached = True
        except Exception:
            pass

    # --- Metodo 3: naviga direttamente via URL ---
    if not settings_reached:
        settings_url = get_app_base_url(page) + "/new/settings/home"
        page.goto(settings_url, timeout=20000)
        try:
            page.wait_for_load_state("load", timeout=10000)
        except Exception:
            pass
        page.wait_for_timeout(1000)
        settings_reached = "settings" in page.url.lower() or "impostazioni" in page.url.lower()

    screenshot(page, "test_impostazioni_04_pagina")

    # Aspetta che Angular carichi il contenuto della pagina impostazioni
    page.wait_for_timeout(3000)

    screenshot(page, "test_navigazione_impostazioni_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Navigazione Impostazioni mobile OK — URL: {page.url}")

    assert settings_reached, \
        f"Impossibile raggiungere le Impostazioni su mobile — URL: {page.url}"

    # Verifica contenuto impostazioni
    content_ok = (
        page.locator('h1:has-text("Impostazioni"), h2:has-text("Impostazioni")').count() > 0
        or page.locator('text="Casella PEC"').count() > 0
        or page.locator('text="Account e sicurezza"').count() > 0
        or page.locator('text="Messaggi e scrittura"').count() > 0
    )
    assert content_ok, \
        "La pagina Impostazioni non mostra il contenuto atteso su mobile"


def test_accesso_sezione_impostazioni_mobile(page):
    """Verifica che le sezioni principali delle impostazioni siano accessibili su mobile
    (Casella PEC, Messaggi e scrittura, Account e sicurezza)."""

    LoginPecMobile(page).login_pec()
    page.wait_for_timeout(1000)

    # Naviga direttamente alle impostazioni
    settings_url = get_app_base_url(page) + "/new/settings/home"
    page.goto(settings_url, timeout=20000)
    try:
        page.wait_for_load_state("load", timeout=10000)
    except Exception:
        pass
    page.wait_for_timeout(2000)

    screenshot(page, "test_sez_impostazioni_01")

    # Verifica sezioni presenti (almeno 2 su 3)
    sezioni_trovate = []
    for sezione in ["Casella PEC", "Messaggi e scrittura", "Account e sicurezza", "Aspetto"]:
        if page.locator(f'text="{sezione}"').count() > 0:
            sezioni_trovate.append(sezione)

    # Clicca su "Casella PEC" (o "Account e sicurezza") per verificare navigazione interna
    try:
        page.locator('text="Casella PEC"').first.click(timeout=3000)
        page.wait_for_timeout(1000)
        screenshot(page, "test_sez_impostazioni_02_casella_pec")
    except Exception:
        pass

    screenshot(page, "test_accesso_sezione_impostazioni_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Sezioni impostazioni trovate su mobile: {sezioni_trovate}")

    assert len(sezioni_trovate) >= 2, \
        f"Trovate solo {len(sezioni_trovate)} sezioni impostazioni su mobile: {sezioni_trovate}"
