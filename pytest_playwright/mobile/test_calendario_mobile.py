import time
from datetime import datetime
from base_mobile import LoginPecMobile, MobileNav, config, REPORT_FOLDER, screenshot


def test_navigazione_calendario_mobile(page):
    """Naviga al Calendario via bottom tab e verifica il caricamento."""

    LoginPecMobile(page).login_pec()
    page.wait_for_timeout(1000)

    nav = MobileNav(page)
    nav.nav_tab("calendario")
    page.wait_for_timeout(2000)

    screenshot(page, "test_calendario_01_sezione")

    screenshot(page, "test_navigazione_calendario_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Navigazione Calendario mobile OK — URL: {page.url}")

    assert "calendar" in page.url.lower() or "calendario" in page.url.lower() or \
           page.locator('h1, [class*="title"]').filter(has_text="Calendario").count() > 0, \
        f"Navigazione a Calendario non riuscita — URL: {page.url}"

    # Verifica che la griglia del calendario o almeno i controlli siano visibili
    cal_visible = (
        page.locator('[class*="calendar"], [class*="cal-"], aru-calendar').count() > 0
        or page.locator('button:has-text("Nuovo evento")').count() > 0
        or page.locator('button[title="Nuovo evento"]').count() > 0
    )
    assert cal_visible, "Nessun elemento calendario riconoscibile su mobile"


def test_crea_elimina_evento_mobile(page):
    """Crea un nuovo evento dal calendario mobile e lo elimina (cleanup)."""

    LoginPecMobile(page).login_pec()
    page.wait_for_timeout(1000)

    nav = MobileNav(page)
    nav.nav_tab("calendario")
    page.wait_for_timeout(2000)

    ts = int(time.time())
    titolo = f"Evento mobile {ts}"

    screenshot(page, "test_evento_01_pre")

    # --- Clicca "Nuovo evento" (FAB blu "+") via JS click (bypassa viewport CDP) ---
    nav = MobileNav(page)
    nav.click_fab("Nuovo evento")
    page.wait_for_timeout(1000)

    screenshot(page, "test_evento_02_form")

    # Compila titolo
    page.get_by_placeholder("Inserisci un titolo").fill(titolo)
    page.wait_for_timeout(500)

    # Salva
    page.get_by_role("button", name="Salva").click()
    page.wait_for_timeout(2000)

    screenshot(page, "test_evento_03_salvato")

    # Verifica che non sia apparso un errore (presenza toast di errore = fail)
    error_toast = page.locator(
        '[class*="toast"][class*="error"], [class*="toast"][class*="danger"]'
    ).count()

    screenshot(page, "test_crea_elimina_evento_mobile___" + datetime.now().strftime("%Y-%m-%d_%H-%M-%S"))
    print(f"Crea/elimina evento mobile OK — titolo: {titolo}")

    assert error_toast == 0, "Toast di errore dopo il salvataggio dell'evento mobile"

    # --- Cleanup: elimina l'evento ---
    try:
        nav.nav_tab("calendario")
        page.wait_for_timeout(1000)
        page.get_by_role("button", name="Eventi").click(timeout=3000)
        page.wait_for_timeout(2000)
        while True:
            ev = page.locator('a, [class*="event"]').filter(has_text=titolo).first
            if ev.count() == 0:
                break
            ev.click()
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Annulla evento").first.click()
            page.wait_for_timeout(1000)
            page.get_by_role("button", name="Elimina").first.click()
            page.wait_for_timeout(2000)
            try:
                toast = page.locator("div.aru-toast__message").first
                if toast.is_visible():
                    print(f"Toast eliminazione: {toast.text_content()}")
            except Exception:
                pass
    except Exception:
        pass
