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
        "importa_messaggi": "dati_test/messaggio importato automation playwright.eml",
        "rubrica_import": "dati_test/rubrica.csv",
        "calendario_import": "dati_test/calendario-test.ics",
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
# Account "primo accesso assoluto" (tipico di PEL Domini, mai usati prima —
# gli account PEL Staff già usati ripetutamente di norma non li mostrano più)
# mostrano, alla prima visita di OGNI sezione (non solo al login), un modal
# di benvenuto a carosello e un toast "Attiva la verifica in 2 passaggi"
# (Popover API nativa, con comparsa asincrona). Entrambi bloccano i click
# successivi tramite il loro backdrop/overlay.
#
# NB: setInterval, requestAnimationFrame e MutationObserver registrati da
# uno script iniettato con page.add_init_script() NON scattano mai più di
# una volta in questo ambiente headless (verificato con un contatore
# indipendente: resta fermo a 1 anche con la pagina attiva per 6+ secondi).
# Il polling va quindi guidato da Python — page.evaluate() chiamato a
# intervalli da wait_for_timeout(), non da timer lato JS — e ripetuto dopo
# ogni navigazione, perché il modal può comparire alla prima visita di
# qualsiasi sezione, non solo subito dopo il login.
# ---------------------------------------------------------------------------
from base_pel import dismiss_onboarding  # noqa: E402


@pytest.fixture(autouse=True)
def _dismiss_onboarding(page):
    """Chiude gli elementi di onboarding dopo ogni page.goto() del test."""
    original_goto = page.goto

    def patched_goto(url, **kwargs):
        result = original_goto(url, **kwargs)
        dismiss_onboarding(page, rounds=3, interval_ms=400)
        return result

    page.goto = patched_goto
    yield


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
