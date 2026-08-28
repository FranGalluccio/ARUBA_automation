import os
import json
import pytest
from datetime import datetime

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
            "url": _pec_url.strip(),
            "username": os.environ.get("PEC_USERNAME", "").strip(),
            "password": os.environ.get("PEC_PASSWORD", "").strip(),
            "inbox_url_pattern": _inbox_pattern.strip(),
        },
        "destinatari": {
            "destinatario_principale": os.environ.get("PEC_USERNAME", "").strip(),
            "destinatario_secondario": os.environ.get("PEC_DESTINATARIO_SECONDARIO", "").strip(),
        },
        "pec_secondario": {
            "url": _pec_url.strip(),
            "username": os.environ.get("PEC_DESTINATARIO_SECONDARIO", "").strip(),
            "password": os.environ.get("PEC_DESTINATARIO_SECONDARIO_PASSWORD", "").strip(),
            "inbox_url_pattern": _inbox_pattern.strip(),
        },
        "test_folder": "pytest_playwright",
        "report_folder": "pytest_playwright/test-results",
        "file_allegato": "dati_test/allegato-test.pdf",
        "file_fattura": "dati_test/fattura-reale-02.eml",
        "importa_messaggi": "dati_test/messaggio importato automation playwright.eml",
        "rubrica_import": "dati_test/rubrica.csv",
        "calendario_import": "dati_test/calendario-test.ics",
    }
    _config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    with open(_config_path, "w", encoding="utf-8") as _f:
        json.dump(_config, _f, indent=2)


def pytest_collection_modifyitems(items):
    """Esegue prima tutti i test della suite 'messaggi', poi il resto
    (l'ordine relativo all'interno dei due gruppi resta invariato)."""
    messaggi = [item for item in items if "test_messaggi" in item.nodeid]
    altri = [item for item in items if "test_messaggi" not in item.nodeid]
    items[:] = messaggi + altri


@pytest.fixture(autouse=True)
def dismiss_cookiebot(page):
    """Auto-dismisses CybotCookiebotDialog whenever it intercepts pointer events.

    Usa evaluate() invece di .click() per evitare attese di visibilità:
    il banner può essere in DOM ma non ancora visibile (animazione) oppure
    già in dismissal — il click JS bypassa tutti i check di actionability.
    """
    def _dismiss():
        page.evaluate("""() => {
            const btn = document.getElementById(
                'CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll'
            );
            if (btn) btn.click();
        }""")

    try:
        page.add_locator_handler(
            page.locator("#CybotCookiebotDialog"),
            _dismiss,
            no_wait_after=True,
        )
    except AttributeError:
        pass  # Playwright < 1.44, nessun locator_handler disponibile
    yield


@pytest.fixture(autouse=True)
def dismiss_cdk_overlay(page):
    """Auto-dismisses CDK overlay backdrops (welcome wizard, dialog) che bloccano i click.

    Registra un locator_handler su .cdk-overlay-backdrop-showing: Playwright lo
    chiama automaticamente prima di qualsiasi azione non-force quando il backdrop
    è visibile, evitando timeout da intercettazione pointer-events.
    """
    def _dismiss():
        try:
            page.evaluate("""() => {
                const dismissTexts = ['Chiudi', 'Non ora', 'Ricordarmelo', 'Capito', 'Ho capito', 'Ok', 'Close', 'Fermer', 'Ignorer'];
                // Controlla TUTTI i pane CDK, salta quelli con input (form di inserimento dati)
                // oppure con >= 2 aru-button (dialog di conferma tipo Si/No — gestiti dal test)
                for (const pane of document.querySelectorAll('.cdk-overlay-pane')) {
                    if (pane.querySelector('input[placeholder], textarea')) continue;
                    if (pane.querySelectorAll('aru-button').length >= 2) continue;
                    const closeBtn = pane.querySelector(
                        'button[aria-label="Chiudi"], button[title="Chiudi"]'
                    );
                    if (closeBtn) { closeBtn.click(); return; }
                    for (const btn of pane.querySelectorAll('button')) {
                        if (dismissTexts.includes(btn.textContent.trim())) { btn.click(); return; }
                    }
                }
            }""")
        except Exception:
            pass

    try:
        page.add_locator_handler(
            page.locator('.cdk-overlay-backdrop-showing'),
            _dismiss,
            no_wait_after=True,
        )
    except (AttributeError, Exception):
        pass
    yield


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    return {
        **browser_context_args,
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
    }


# ---------------------------------------------------------------------------
# Screenshot automatico + contesto diagnostico su ogni test fallito.
# Viene eseguito per ogni test che usa il fixture "page" (autouse=False
# ma collegato tramite il parametro page).
# ---------------------------------------------------------------------------
@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Cattura screenshot, URL e titolo pagina se il test fallisce."""
    yield

    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        _save_failure_info(request, page)


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """Rende il risultato del test accessibile al fixture screenshot_on_failure."""
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


def _save_failure_info(request, page):
    """Salva screenshot e log diagnostico in test-results/failures/."""
    try:
        # Determina la cartella di output
        report_folder = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "test-results", "failures"
        )
        os.makedirs(report_folder, exist_ok=True)

        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        test_name = request.node.name

        # Screenshot della pagina al momento del fallimento
        screenshot_path = os.path.join(report_folder, f"FAIL_{test_name}_{ts}.png")
        page.screenshot(path=screenshot_path, full_page=True)

        # Log diagnostico: URL + titolo
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

        # Stampa nel log di pytest per visibilità immediata in CI
        print(f"\n[FAILURE] Screenshot: {screenshot_path}")
        print(f"[FAILURE] URL al momento del fallimento: {current_url}")
        print(f"[FAILURE] Titolo pagina: {page_title}")

    except Exception as e:
        print(f"\n[FAILURE] Impossibile salvare info diagnostica: {e}")
