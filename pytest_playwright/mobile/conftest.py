import os
import sys
import pytest
from datetime import datetime

# Aggiunge pytest_playwright/ al path per importare base_mobile e config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture(scope="session")
def browser_type_launch_args(browser_type_launch_args):
    return {**browser_type_launch_args, "headless": True}


@pytest.fixture(scope="session")
def browser_context_args(playwright):
    """Contesto iPhone 14 — sovrascrive il viewport desktop del conftest padre."""
    device = playwright.devices["iPhone 14"]
    return {
        **device,
        "ignore_https_errors": True,
    }


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    setattr(item, f"rep_{rep.when}", rep)


@pytest.fixture(autouse=True)
def screenshot_on_failure(request, page):
    """Screenshot automatico su fallimento, salvato in test-results/failures/mobile/."""
    yield

    if request.node.rep_call.failed if hasattr(request.node, "rep_call") else False:
        try:
            report_folder = os.path.join(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                "test-results", "failures", "mobile"
            )
            os.makedirs(report_folder, exist_ok=True)
            ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            test_name = request.node.name
            page.screenshot(
                path=os.path.join(report_folder, f"FAIL_{test_name}_{ts}.png"),
                full_page=True
            )
            print(f"\n[FAILURE-MOBILE] Screenshot salvato: FAIL_{test_name}_{ts}.png")
            print(f"[FAILURE-MOBILE] URL: {page.url}")
        except Exception as e:
            print(f"\n[FAILURE-MOBILE] Impossibile salvare diagnostica: {e}")
