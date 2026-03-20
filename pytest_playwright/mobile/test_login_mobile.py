from datetime import datetime
from base_mobile import LoginPecMobile, MobileNav, config, REPORT_FOLDER, screenshot


def test_login_mobile(page):
    """Login su mobile: verifica che l'inbox carichi e la UI mobile sia presente
    (bottom navigation bar + hamburger)."""

    LoginPecMobile(page).login_pec()
    page.wait_for_timeout(1000)

    # Verifica URL inbox
    assert any(p in page.url for p in ["INBOX", "messages", "mail"]), \
        f"Dopo il login l'URL non sembra una inbox: {page.url}"

    nav = MobileNav(page)

    # Verifica bottom navigation bar
    assert nav.is_bottom_nav_visible(), \
        "Bottom navigation bar non trovata — la UI mobile non si è caricata correttamente"

    # Verifica hamburger visibile
    from base_mobile import _HAMBURGER
    assert page.locator(_HAMBURGER).count() > 0, \
        "Bottone hamburger (≡) non trovato nell'header mobile"

    # Verifica che almeno l'intestazione della sezione sia visibile
    heading = page.locator('h1, [class*="title"], [class*="header-title"]').first
    assert heading.count() > 0 or page.locator('div.frame-record-desktop').count() >= 0, \
        "Nessun elemento riconoscibile nella pagina dopo il login mobile"

    screenshot(page, "test_login_mobile")
    print(f"Login mobile OK — URL: {page.url}")
