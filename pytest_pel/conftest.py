import os
import json
import pytest
from datetime import datetime

# ---------------------------------------------------------------------------
# Crea config.json dalle variabili d'ambiente se PEL_URL è definita.
# ---------------------------------------------------------------------------
_pel_url = os.environ.get("PEL_URL")
if _pel_url:
    _config = {
        "pel": {
            "url": _pel_url.strip(),
            "username": os.environ.get("PEL_USERNAME", "").strip(),
            "password": os.environ.get("PEL_PASSWORD", "").strip(),
            "inbox_url_pattern": os.environ.get("PEL_INBOX_URL_PATTERN", "INBOX").strip(),
        },
        "destinatari": {
            "destinatario_principale": os.environ.get("PEL_USERNAME", "").strip(),
            "destinatario_secondario": os.environ.get("PEL_DESTINATARIO_SECONDARIO", "").strip(),
        },
        "test_folder": "pytest_pel",
        "report_folder": "pytest_pel/test-results",
        "file_allegato": "dati_test/allegato-test.pdf",
    }
    _config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(_config_path, "w", encoding="utf-8") as _f:
        json.dump(_config, _f, indent=2)


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


# ---------------------------------------------------------------------------
# Screenshot automatico + contesto diagnostico su ogni test fallito.
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Cattura screenshot, URL e titolo pagina se il test fallisce."""
    yield

    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        _save_failure_info(request, page)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _save_failure_info(request, page):
    try:
        report_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test-results", "failures"
        )
        os.makedirs(report_folder, exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        test_name = request.node.name

        screenshot_path = os.path.join(report_folder, f"FAIL_{test_name}_{ts}.png")
        page.screenshot(path=screenshot_path, full_page=True)

        current_url = page.url
        try:
            page_title = page.title()
        except Exception:
            page_title = "(non disponibile)"

        log_path = os.path.join(report_folder, f"FAIL_{test_name}_{ts}.txt")
        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"Test fallito: {test_name}\n")
            f.write(f"Timestamp:    {ts}\n")
            f.write(f"URL:          {current_url}\n")
            f.write(f"Titolo pagina:{page_title}\n")

        print(f"\n[FAILURE] Screenshot: {screenshot_path}")
        print(f"[FAILURE] URL al momento del fallimento: {current_url}")
        print(f"[FAILURE] Titolo pagina: {page_title}")

    except Exception as e:
        print(f"\n[FAILURE] Impossibile salvare info diagnostica: {e}")
