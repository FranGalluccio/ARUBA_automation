import os
import json
from datetime import datetime
from base_pel import LoginPel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_navigazione_periodi_calendario(page):
    """
    Verifica la navigazione del calendario PEL:
    - click su una data futura nella mini-calendar aggiorna la main view
    - click su 'Oggi' torna alla settimana corrente
    """
    LoginPel(page).login_pel(config)
    page.get_by_role("button", name="Calendario").click()
    page.wait_for_timeout(1500)

    def get_main_first_day():
        """Restituisce il testo della prima cella header della settimana nella main view."""
        cells = page.locator(".fc-col-header-cell").all()
        if cells:
            return cells[0].inner_text().strip()
        return ""

    # Leggi il periodo corrente
    day_iniziale = get_main_first_day()
    print(f"  Main view primo giorno iniziale: {day_iniziale!r}")

    # Avanza di un mese nella mini-calendar cliccando Next
    page.locator('[title="Next"]').click()
    page.wait_for_timeout(800)

    # Clicca il primo giorno disponibile del mese successivo nella mini-calendar
    future_day = page.locator(
        ".vanilla-calendar-day__btn:not(.vanilla-calendar-day__btn_prev)"
        ":not(.vanilla-calendar-day__btn_next)"
        ":not(.vanilla-calendar-day__btn_today)"
    ).first
    if future_day.count() > 0:
        txt = future_day.inner_text().strip()
        print(f"  Click giorno futuro mini-cal: {txt!r}")
        future_day.click()
        page.wait_for_timeout(1000)

    day_dopo_nav = get_main_first_day()
    print(f"  Main view primo giorno dopo nav: {day_dopo_nav!r}")
    assert day_dopo_nav != day_iniziale, \
        "La navigazione tramite mini-calendar non ha aggiornato la main view"

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_07_nav_{datetime.now():%H-%M-%S}.png"))

    # Torna ad oggi con il pulsante "Oggi"
    page.locator('[title="Oggi"]').first.click()
    page.wait_for_timeout(800)
    day_oggi = get_main_first_day()
    print(f"  Main view primo giorno dopo Oggi: {day_oggi!r}")

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_07___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
    assert day_oggi == day_iniziale, \
        f"Il pulsante Oggi non ha riportato alla settimana corrente (atteso {day_iniziale!r}, trovato {day_oggi!r})"
    print("test_calendario_07 PASSED")
