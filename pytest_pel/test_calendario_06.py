import os
import json
from datetime import datetime
from base_pel import LoginPel


CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE, encoding="utf-8") as f:
    config = json.load(f)

REPORT_FOLDER = config.get("report_folder", os.path.join(os.path.dirname(os.path.abspath(__file__)), "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)


def test_cambio_vista_calendario(page):
    """Verifica il cambio di vista: Settimana → Giorno → Mese → Eventi → Settimana."""
    LoginPel(page).login_pel(config)
    page.get_by_role("button", name="Calendario").click()
    page.wait_for_timeout(1500)

    # Intestazione attuale (contiene data/periodo corrente)
    header = page.locator('[title="Settimana"], button[aria-label*="week"], h1, h2').first

    for vista, selector in [
        ("Giorno",    '[title="Giorno"]'),
        ("Mese",      '[title="Mese"]'),
        ("Eventi",    '[title="Eventi"]'),
        ("Settimana", '[title="Settimana"]'),
    ]:
        page.locator(selector).first.click()
        page.wait_for_timeout(1000)
        page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_06_{vista.lower()}_{datetime.now():%H-%M-%S}.png"))
        print(f"  Vista {vista}: URL={page.url}")

    page.screenshot(path=os.path.join(REPORT_FOLDER, f"test_calendario_06___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"), full_page=True)
    print("test_calendario_06 PASSED")
