# ARUBA Webmail — End-to-End Test Automation Suite

Comprehensive end-to-end test automation framework for **Aruba Webmail PEC** (Certified Email) and **PEL Staff** (Staff Calendar Portal), built with [Playwright](https://playwright.dev/python/) and [pytest](https://pytest.org/).

---

## Overview

| Suite | Tests | Tech | Environment |
|-------|-------|------|-------------|
| PEC Desktop | 65 | Playwright + pytest | Chromium |
| PEC Mobile | 10 | Playwright (iPhone 14) | WebKit |
| PEL Staff | 15 | Playwright + pytest | Chromium |
| **Total** | **90** | | |

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
| Calendario | 10 | Create/edit/delete events, recurring events, reminders, all-day events, import/export, navigation, search |
| Conservazione | 2 | Conservation settings, folder navigation |
| Contatti | 8 | Add/edit/delete contacts, search, favourites, group import/export |
| Fatture | 3 | Invoice reception, visualisation, download |
| Impostazioni | 7 | Signature, out-of-office, filters, display settings |
| Messaggi | 27 | Send/receive, attachments, reply/reply-all, forward, drafts, labels, move, delete/restore, read/unread, high-priority, search, PEC receipts (RA/RD) |

### PEC Mobile (`pytest_playwright/mobile/`)

10 tests on iPhone 14 viewport:
- Login, messages, calendar, contacts, settings

### PEL Staff (`pytest_pel/`)

15 tests for the Aruba Staff Calendar Portal:
- Login
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
The BNL environment has 300+ messages in inbox; tests that naively use `.first` open the wrong message. All inbox interactions use `filter(has_text=oggetto)` + polling:
```python
msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
for _ in range(20):
    page.wait_for_timeout(4000)
    page.locator('aru-symbol[title="Aggiorna"]').click()
    if msg.count() > 0:
        break
```

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
├── pytest_pel/                 # PEL Staff suite (15 tests)
│   ├── conftest.py
│   ├── base_pel.py
│   ├── config.example.json
│   └── test_*.py
├── dati_test/                  # Test data files (PDF, EML, CSV, ICS)
├── .github/workflows/          # CI/CD pipelines
│   ├── python-tests.yml        # PEC Desktop (auto on push + manual)
│   ├── python-tests-mobile.yml # PEC Mobile (manual only)
│   └── python-tests-pel.yml    # PEL Staff (auto on push + manual)
├── pytest.ini
└── requirements.txt
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

All credentials are stored as **GitHub Secrets** — the `conftest.py` in each suite reads them from environment variables and writes `config.json` at runtime.

### Required Secrets

| Secret | Used by |
|--------|---------|
| `TEST_PEC_URL` | PEC Desktop + Mobile |
| `TEST_PEC_USERNAME` | PEC Desktop + Mobile |
| `TEST_PEC_PASSWORD` | PEC Desktop + Mobile |
| `TEST_PEC_DESTINATARIO_SECONDARIO` | PEC Desktop |
| `TEST_PEL_URL` | PEL Staff |
| `TEST_PEL_USERNAME` | PEL Staff |
| `TEST_PEL_PASSWORD` | PEL Staff |

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
