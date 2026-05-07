import os
import json
import time
from datetime import datetime

from base_pec import LoginPec, Helper
from playwright.sync_api import expect


# --- Leggi config.json ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
with open(CONFIG_FILE) as f:
    config = json.load(f)

# --- Cartella test e report ---
TEST_FOLDER = config.get("test_folder", os.path.dirname(os.path.abspath(__file__)))
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

# --- Percorso allegato ---
_GIT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_raw = os.environ.get("FILE_ALLEGATO", config.get("file_allegato"))
file_allegato = os.path.normpath(os.path.join(_GIT_ROOT, _raw)) if _raw and not os.path.isabs(_raw) else _raw


def test_scarica_allegato_ricevuto(page):
    # Login PEC
    LoginPec(page).login_pec(config)

    ts = int(time.time())
    oggetto = f"Test scarica allegato playwright {ts}"

    # Invia messaggio con allegato a se stessi
    Helper.crea_messaggio(
        page,
        config,
        oggetto=oggetto,
        corpo="Messaggio con allegato da scaricare",
        path_allegato=file_allegato,
    )
    page.locator('span[title="Invia"], span[title="Envoyer"]').click()

    # Polling: cerca il messaggio specifico per oggetto (non il primo in assoluto)
    # 40 iterazioni * ~4s = ~160s per ambienti lenti (SMB con inbox piena)
    msg = page.locator('div.frame-record-desktop').filter(has_text=oggetto)
    for _ in range(40):
        page.wait_for_timeout(3000)
        page.locator('aru-symbol[title="Aggiorna"], aru-symbol[title="Actualiser"]').click()
        page.wait_for_timeout(1000)
        if msg.count() > 0:
            break
    msg.first.click(timeout=15000)
    page.locator('div.message-content-body').wait_for(state="visible", timeout=10000)

    # Apri in nuova finestra
    link_external_button = page.locator('aru-symbol[title="Apri in una nuova finestra"], aru-symbol[title="Ouvrir dans une nouvelle fenêtre"]').first
    link_external_button.wait_for(state="visible", timeout=10000)

    with page.expect_popup() as popup_info:
        link_external_button.click()

    new_page = popup_info.value
    new_page.set_viewport_size({"width": 1280, "height": 900})
    new_page.wait_for_load_state("domcontentloaded")
    new_page.wait_for_load_state("load")
    assert "external-message" in new_page.url

    # Clicca il chip allegato — selettori multipli + fallback get_by_text + JS coords
    nome_file = os.path.basename(file_allegato)

    def _click_attachment_chip(target_page, name):
        # Screenshot pre-ricerca per diagnosticare CI
        target_page.wait_for_timeout(1500)
        target_page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"debug_chip_pre_{datetime.now():%H-%M-%S}.png"
        ))

        # Ordine originale: NON modificare, altrimenti .first cambia elemento
        loc = target_page.locator(
            f'[title="{name}"], '
            f'button:has-text("{name}"), '
            f'[aria-label="{name}"], '
            f'span:has-text("{name}")'
        ).first
        try:
            loc.wait_for(state="visible", timeout=5000)
            loc.click(force=True)
            return
        except Exception:
            pass

        # Fallback sequenziali per nome file
        for sel in [
            f'a:has-text("{name}")',
            f'aru-chips-item:has-text("{name}")',
            f'[class*="chips"]:has-text("{name}")',
            f'[class*="attachment"]:has-text("{name}")',
        ]:
            try:
                item = target_page.locator(sel).first
                if item.count() > 0 and item.is_visible():
                    item.click(force=True)
                    return
            except Exception:
                pass

        # Fallback generico: qualsiasi chip/allegato visibile (1 solo allegato nel msg)
        for sel in ['aru-chips-item', '[class*="chip"]', 'aru-attachment', '[class*="attachment"]']:
            try:
                item = target_page.locator(sel).first
                if item.count() > 0 and item.is_visible():
                    item.click(force=True)
                    return
            except Exception:
                pass

        # get_by_role fallback
        for role in ["button", "link", "listitem"]:
            try:
                el = target_page.get_by_role(role, name=name)
                if el.count() > 0:
                    el.first.click(force=True)
                    return
            except Exception:
                pass

        # get_by_text (parziale e esatto)
        stem = os.path.splitext(name)[0]
        for exact in [False, True]:
            for txt in ([name, stem] if not exact else [name]):
                try:
                    target_page.get_by_text(txt, exact=exact).first.click(force=True)
                    return
                except Exception:
                    pass

        # Scansione JS: tutti gli elementi del DOM per testo/title/aria-label
        import json as _json
        coords = target_page.evaluate(f"""() => {{
            const name = {_json.dumps(name)};
            const stem = name.replace(/\\.[^.]+$/, '');
            function matches(el) {{
                const text = (el.textContent || '').trim();
                const title = el.getAttribute('title') || '';
                const aria = el.getAttribute('aria-label') || '';
                return text === name || text.includes(stem) ||
                       title === name || aria === name;
            }}
            const candidates = [];
            for (const el of document.querySelectorAll('*')) {{
                if (matches(el)) {{
                    const rect = el.getBoundingClientRect();
                    if (rect.width > 5 && rect.height > 5 && rect.y >= 0 && rect.y < window.innerHeight) {{
                        candidates.push({{x: rect.x + rect.width / 2, y: rect.y + rect.height / 2, area: rect.width * rect.height}});
                    }}
                }}
            }}
            candidates.sort((a, b) => a.area - b.area);
            return candidates.length > 0 ? candidates[0] : null;
        }}""")
        if coords:
            print(f"Allegato trovato via JS scan: {coords}")
            target_page.mouse.click(coords['x'], coords['y'])
            return

        target_page.screenshot(path=os.path.join(
            REPORT_FOLDER, f"debug_chip_fail_{datetime.now():%H-%M-%S}.png"
        ))
        raise Exception(f"Allegato '{name}' non trovato nella pagina")

    _click_attachment_chip(new_page, nome_file)
    new_page.wait_for_timeout(1000)

    # Scarica l'allegato — IT: "Scarica" / FR: "Télécharger"
    # The download button is in a CDK overlay dropdown. The inner shadow DOM button has wrong
    # bounding box coords, so we locate the CDK pane (regular DOM) and click via mouse.click().
    # Route interception forces Content-Disposition: attachment so Chrome downloads the PDF.
    download_path = os.path.join(REPORT_FOLDER, f"allegato_scaricato_{datetime.now():%Y-%m-%d_%H-%M-%S}_{nome_file}")

    def _force_attachment(route):
        url = route.request.url.lower()
        if any(k in url for k in ['.pdf', 'download', 'attach', 'allegat', '/file']):
            resp = route.fetch()
            headers = dict(resp.headers)
            headers['content-disposition'] = f'attachment; filename="{nome_file}"'
            route.fulfill(response=resp, headers=headers)
        else:
            route.continue_()

    # Find the download dropdown — cerca prima il pane che contiene il testo download
    coords = new_page.evaluate("""() => {
        const downloadKeywords = ['Scarica', 'Télécharger', 'Download', 'Téléch'];
        // 1) Cerca CDK pane che contiene il testo download
        for (const sel of ['.cdk-overlay-pane', '[role="menu"]', '[role="listbox"]']) {
            for (const el of document.querySelectorAll(sel)) {
                const text = el.textContent || '';
                const hasDownload = downloadKeywords.some(k => text.includes(k));
                const rect = el.getBoundingClientRect();
                if (hasDownload && rect.width > 30 && rect.height > 20 && rect.y >= 0 && rect.y < window.innerHeight) {
                    return {x: rect.x + rect.width / 2, y: rect.y + rect.height * 0.3};
                }
            }
        }
        // 2) Qualsiasi CDK overlay pane sufficientemente grande
        for (const el of document.querySelectorAll('.cdk-overlay-pane')) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 80 && rect.height > 40 && rect.y >= 0 && rect.y < window.innerHeight) {
                return {x: rect.x + rect.width / 2, y: rect.y + rect.height * 0.3};
            }
        }
        // 3) Fallback: primo aru-button visibile
        for (const el of document.querySelectorAll('aru-button')) {
            const rect = el.getBoundingClientRect();
            if (rect.width > 10 && rect.height > 10 && rect.y > 0 && rect.y < window.innerHeight) {
                return {x: rect.x + rect.width / 2, y: rect.y + rect.height / 2};
            }
        }
        return null;
    }""")
    print(f"Download button coords via overlay: {coords}")

    new_page.route('**', _force_attachment)
    try:
        with new_page.expect_download(timeout=30000) as download_info:
            if coords:
                new_page.mouse.click(coords['x'], coords['y'])
            else:
                new_page.locator('button[title="Scarica"], button[title="Télécharger"]').first.click(force=True)
        download = download_info.value
        download.save_as(download_path)
    finally:
        new_page.unroute('**', _force_attachment)

    # Screenshot
    screenshot_path = os.path.join(
        REPORT_FOLDER,
        f"test_messaggi_20___{datetime.now():%Y-%m-%d_%H-%M-%S}.png"
    )
    new_page.screenshot(path=screenshot_path, full_page=True)
    print(f"File scaricato in: {download_path}")
    print(f"Screenshot salvato in: {screenshot_path}")
    # Verifica che il file sia stato scaricato
    assert os.path.exists(download_path), f"Il file non è stato scaricato: {download_path}"
    assert os.path.getsize(download_path) > 0, "Il file scaricato è vuoto"
