# ARUBA Webmail — End-to-End Test Automation Suite

Comprehensive end-to-end test automation framework for **Aruba Webmail PEC** (Certified Email) and **PEL Staff** (Staff Calendar Portal), built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/).

---

## Overview

| Suite | Tests | Tech | Environment |
|-------|-------|------|-------------|
| PEC Desktop | 65 | Playwright + pytest | Chromium |
| PEC Mobile | 10 | Playwright (iPhone 14) | WebKit |
| PEL Staff | 17 | Playwright + pytest | Chromium |
| **Total** | **92** | | |

The suite runs on **self-hosted GitHub Actions runners** and supports multiple target environments (test, staging, production) selectable at workflow dispatch time.

---

## Tech Stack

- **Python 3.13** · **pytest 9** · **pytest-playwright 0.7**
- **Playwright** (sync API) — Chromium + WebKit
- **GitHub Actions** — CI/CD with self-hosted runners
- **pytest-html** — HTML test reports with screenshots on failure

---

## Test Suites

### PEC Desktop (`pytest_playwright/`)

65 tests covering the full Aruba Webmail PEC feature set:

| Module | Tests | What is tested |
|--------|-------|----------------|
| Login | 2 | Successful login, invalid credentials |
| Accessi | 3 | Access management, Supervisor360 card, navigation |
| Archivio | 2 | Archive configuration, message archiving |
| Calendario | 10 | Create/edit/delete events, recurring events, reminders, all-day events, import/export, navigation, search, invite delivery to a secondary recipient account |
| Conservazione | 2 | Conservation settings, folder navigation |
| Contatti | 10 | Add/edit/delete contacts, search, favourites, group import/export |
| Fatture | 2 | Invoice reception, visualisation, download |
| Impostazioni | 7 | Signature, out-of-office, filters, display settings |
| Messaggi | 27 | Send/receive, attachments, reply/reply-all, forward, drafts, labels, move, delete/restore, read/unread, high-priority, search, PEC receipts (RA/RD) |

### PEC Mobile (`pytest_playwright/mobile/`)

10 tests on iPhone 14 viewport:
- Login, messages, calendar, contacts, settings

### PEL Staff (`pytest_pel/`)

17 tests for the Aruba Staff Calendar Portal:
- 2 login tests
- 13 calendar tests: create/edit/delete events, recurring events, reminders, invitees, drag-and-drop, view switching, conflict detection, all-day events, import/export
- 2 settings tests

---

## Key Technical Challenges

### Shadow DOM traversal
Aruba Webmail uses Angular web components (`aru-button`, `aru-symbol`) whose text lives inside shadow roots. Standard CSS selectors fail; Playwright's `.filter(has_text=...)` pierces shadow DOM correctly:
```python
# CSS has-text() in locator string → FAILS on shadow DOM
# Playwright filter → WORKS
page.locator('aru-button').filter(has_text="Modifica").first.click()
```

### Dynamic cookie banner handling
`CybotCookiebotDialog` reappears unpredictably during tests. A global `add_locator_handler` in `conftest.py` auto-dismisses it via JS (bypasses visibility checks for mid-animation state):
```python
page.add_locator_handler(
    page.locator("#CybotCookiebotDialog"),
    lambda: page.evaluate("document.getElementById('CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll')?.click()"),
    no_wait_after=True,
)
```

### Multi-environment robustness
If the environment has a lot of messages in inbox; tests that naively use `.first` open the wrong message. All inbox interactions use `filter(has_text=oggetto)` + polling:
```python
msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
for _ in range(20):
    page.wait_for_timeout(4000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    if msg.count() > 0:
        break
```

### Multi-account recipient verification
Some flows (e.g. sending a calendar invite) can't be verified from the sender's session alone. `test_calendario_03.py` opens a second, independent `BrowserContext` logged in as a separate recipient account and polls that account's own inbox until the invite email actually arrives — proving end-to-end delivery, not just that the sender's UI reported success. Both `page` (organizer) and `page2` (recipient) are kept open at the same time for the whole cross-check, rather than closing one before opening the other:
```python
context2 = browser.new_context(viewport={"width": 1920, "height": 1080}, ignore_https_errors=True)
page2 = context2.new_page()
LoginPec(page2).login_pec(config_secondario)
for _ in range(6):
    page2.locator('aru-symbol[title="Aggiorna"]').click()
    page2.wait_for_timeout(5000)
    if page2.get_by_text(titolo_evento, exact=False).count() > 0:
        break
```
The test then goes further than delivery: it opens the invite email on `page2` and clicks the RSVP "Sì" button (`aru-button[aru-id="msg-dtl-body-event-current-btn-0"]` — a stable, language-independent selector since the visible label changes between IT/FR), checks the event shows up correctly in the recipient's own Calendario (organizer listed among the attendees, not just a same-titled stray event), and — still without closing `context2` — switches back to `page` to poll the organizer's inbox for the "Accettato: ..." notification before any cleanup happens.

### FullCalendar drag-and-drop
Reliable drag requires slow incremental mouse movement (25 steps × 30 ms):
```python
page.mouse.move(src_x, src_y)
page.mouse.down()
for step in range(25):
    page.mouse.move(src_x + (delta_x * step / 25), ..., steps=1)
    page.wait_for_timeout(30)
page.mouse.up()
```

---

## Project Structure

```
.
├── pytest_playwright/          # PEC Desktop suite (65 tests)
│   ├── conftest.py             # Fixtures: cookie handler, failure screenshots
│   ├── base_pec.py             # LoginPec + Helper (reusable actions)
│   ├── config.example.json     # Config template
│   ├── test_*.py               # Test files (one per feature module)
│   └── mobile/                 # PEC Mobile suite (10 tests)
│       ├── conftest.py
│       ├── base_mobile.py
│       └── test_*.py
├── pytest_pel/                 # PEL Staff suite (17 tests)
│   ├── conftest.py
│   ├── base_pel.py
│   ├── config.example.json
│   └── test_*.py
├── dati_test/                  # Test data files (PDF, EML, CSV, ICS)
├── .github/workflows/          # CI/CD pipelines
│   ├── python-tests.yml        # PEC Desktop (auto on push + manual)
│   ├── python-tests-mobile.yml # PEC Mobile (manual only)
│   └── python-tests-pel.yml    # PEL Staff (auto on push + manual)
├── genera_excel_suite.py       # Generates suite_test_pec.xlsx (testbook)
├── genera_excel_suite_mobile.py# Generates suite_test_pec_mobile.xlsx
├── genera_excel_suite_pel.py   # Generates suite_test_pel.xlsx
├── suite_test_pec.xlsx         # Testbook: PEC Desktop
├── suite_test_pec_mobile.xlsx  # Testbook: PEC Mobile
├── suite_test_pel.xlsx         # Testbook: PEL Staff
├── pytest.ini
└── requirements.txt
```

---

## Testbook

Each suite has a companion **Excel testbook** — one row per test case (module, file, function, description, numbered steps, expected result), meant for manual QA review and non-technical stakeholders rather than for running tests. It's generated from a Python data structure, not hand-edited in Excel, so it can't drift into a spreadsheet-only description of behaviour the code no longer has:

| Generator | Output | Suite |
|-----------|--------|-------|
| `genera_excel_suite.py` | `suite_test_pec.xlsx` | PEC Desktop (65 rows) |
| `genera_excel_suite_mobile.py` | `suite_test_pec_mobile.xlsx` | PEC Mobile (10 rows) |
| `genera_excel_suite_pel.py` | `suite_test_pel.xlsx` | PEL Staff (17 rows) |

Whenever a test's behaviour changes (new assertion, new step, different expected result), update the corresponding tuple in the generator script and regenerate:

```bash
python genera_excel_suite.py
python genera_excel_suite_mobile.py
python genera_excel_suite_pel.py
```

---

## Local Setup

### Prerequisites
- Python 3.11+
- Playwright browsers installed

```bash
# Clone and install dependencies
git clone https://github.com/FranGalluccio/ARUBA_automation.git
cd ARUBA_automation
pip install -r requirements.txt
playwright install chromium
```

### Configure credentials

**PEC suite:**
```bash
cp pytest_playwright/config.example.json pytest_playwright/config.json
# Edit config.json with your PEC credentials
```

**PEL suite:**
```bash
cp pytest_pel/config.example.json pytest_pel/config.json
# Edit config.json with your PEL credentials
```

> `config.json` is in `.gitignore` — credentials never enter version control.

### Run tests locally

```bash
# PEC Desktop — all tests
pytest pytest_playwright/ --browser chromium -v

# PEC Desktop — single test file
pytest pytest_playwright/test_messaggi_01.py -v

# PEC Mobile
pytest pytest_playwright/mobile/ --browser webkit -v

# PEL Staff
pytest pytest_pel/ --browser chromium -v
```

---

## CI/CD (GitHub Actions)

All credentials are stored as **GitHub Secrets** — the `conftest.py` in each suite reads them from environment variables and writes `config.json` at runtime. The target URL itself is *not* a secret: it's selected inline in the workflow from the `ambiente` input.

### Required Secrets

Each workflow picks a secret set based on the `ambiente` selected at dispatch time (falls back to `TEST_*` on plain `push`). Every secret below needs one variant per prefix actually in use.

**PEC Desktop + Mobile** (`python-tests.yml`, `python-tests-mobile.yml`) — prefixes `TEST_` (default), `BNL_`, `FR_`, `POCFR_` (Desktop only), `PROD_`:

| Secret (per prefix) | Purpose |
|--------|---------|
| `<PREFIX>_PEC_USERNAME` | Login account under test |
| `<PREFIX>_PEC_PASSWORD` | Login account under test |
| `<PREFIX>_PEC_DESTINATARIO_SECONDARIO` | Email address invited/CC'd as a secondary recipient |
| `<PREFIX>_PEC_DESTINATARIO_SECONDARIO_PASSWORD` | Password to log into that secondary account, to verify calendar invite delivery end-to-end (`test_calendario_03.py`) |

**PEL Staff** (`python-tests-pel.yml`) — prefixes `TEST_` (default), `PROD_STAFF_`:

| Secret (per prefix) | Purpose |
|--------|---------|
| `<PREFIX>_PEL_USERNAME` | Login account under test |
| `<PREFIX>_PEL_PASSWORD` | Login account under test |
| `<PREFIX>_PEL_DESTINATARIO_SECONDARIO` | Secondary recipient email address |

> If a `*_DESTINATARIO_SECONDARIO_PASSWORD` secret isn't configured for an environment, the affected test skips only the recipient-side verification step instead of failing.

### Trigger

- **PEC Desktop / PEL**: automatic on `push` to `main` + manual (`workflow_dispatch`) with environment selector
- **PEC Mobile**: manual only

### Artifacts
Each run produces:
- `report.html` — full HTML report with test status
- `report.xml` — JUnit XML for CI dashboards
- `test-results/failures/` — screenshot + URL + page title for every failed test

---

## Reports

Failure diagnostics are captured automatically by `conftest.py`:

```
test-results/failures/
├── FAIL_test_risposta_messaggio[chromium]_2026-03-30_11-03-30.png
└── FAIL_test_risposta_messaggio[chromium]_2026-03-30_11-03-30.txt
     → Test: test_risposta_messaggio[chromium]
     → URL: https://webmail.../INBOX
     → Title: (307) Messaggi | Webmail PEC
```

---

## License

This project is provided for portfolio and demonstration purposes.
