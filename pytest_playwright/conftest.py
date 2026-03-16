import os
import json
import pytest

# ---------------------------------------------------------------------------
# Crea config.json dalle variabili d'ambiente se PEC_URL è definita.
# Questo codice gira a livello di modulo (prima della collection dei test),
# quindi base_pec.py troverà il file quando verrà importato.
# ---------------------------------------------------------------------------
_pec_url = os.environ.get("PEC_URL")
if _pec_url:
    _inbox_pattern = os.environ.get("PEC_INBOX_URL_PATTERN", "INBOX")
    _config = {
        "pec": {
            "url": _pec_url,
            "username": os.environ.get("PEC_USERNAME", ""),
            "password": os.environ.get("PEC_PASSWORD", ""),
            "inbox_url_pattern": _inbox_pattern,
        },
        "destinatari": {
            "destinatario_principale": os.environ.get("PEC_USERNAME", ""),
            "destinatario_secondario": os.environ.get("PEC_DESTINATARIO_SECONDARIO", ""),
        },
        "test_folder": "pytest_playwright",
        "report_folder": "pytest_playwright/test-results",
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
