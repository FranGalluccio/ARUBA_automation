import tkinter as tk
from tkinter import messagebox, filedialog
from threading import Thread
import subprocess
import os
import json
import webbrowser
from datetime import datetime
import sys

# --- Carica configurazione ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
if not os.path.exists(CONFIG_FILE):
    messagebox.showerror("Errore", f"File di configurazione {CONFIG_FILE} non trovato!")
    raise FileNotFoundError(f"{CONFIG_FILE} non trovato")

with open(CONFIG_FILE) as f:
    config = json.load(f)

TEST_FOLDER = config.get("test_folder", "pytest_playwright")
REPORT_FOLDER = config.get("report_folder", os.path.join(TEST_FOLDER, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

FIREFOX_PATH = config.get("firefox_path", "")  # se vuoto, usa browser di default

# --- Lista test che richiedono allegato ---
TEST_CON_ALLEGATO = ["test_new_message.py"]

# --- Funzioni ---
def generate_report_path():
    """Crea un percorso report unico con data/ora"""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(REPORT_FOLDER, f"report_{timestamp}.html")

def run_pytest(test_file=None):
    """Esegue pytest con report HTML unico usando Python della venv"""
    report_path = generate_report_path()
    cmd = [sys.executable, "-m", "pytest", f"--html={report_path}", "--self-contained-html"]

    if test_file:
        cmd.append(os.path.join(TEST_FOLDER, test_file))
    else:
        # lancia tutti i test_*.py nella cartella
        test_files = [os.path.join(TEST_FOLDER, f) for f in os.listdir(TEST_FOLDER)
                      if f.startswith("test_") and f.endswith(".py")]
        if not test_files:
            messagebox.showwarning("Attenzione", f"Nessun test trovato in {TEST_FOLDER}")
            return
        cmd.extend(test_files)

    try:
        subprocess.run(cmd, check=True)
        messagebox.showinfo("✅ Test Completati", f"Tutti i test sono passati!\nReport: {report_path}")
    except subprocess.CalledProcessError as e:
        messagebox.showerror("❌ Test Falliti", f"Alcuni test non sono passati.\nErrore: {e}")

def start_test_thread(test_file=None):
    """Esegue pytest in un thread separato"""
    Thread(target=run_pytest, args=(test_file,), daemon=True).start()

def start_test_thread_with_optional_file(test_file=None):
    """Gestisce file picker solo per test che richiedono un allegato"""
    if test_file in TEST_CON_ALLEGATO:
        file_path = filedialog.askopenfilename(title="Seleziona file da allegare")
        if not file_path:
            messagebox.showwarning("Attenzione", "Non hai selezionato alcun file. Il test non verrà eseguito.")
            return
        os.environ["FILE_ALLEGATO"] = file_path  # passa il file al test
    else:
        os.environ.pop("FILE_ALLEGATO", None)

    start_test_thread(test_file)

def open_report():
    """Apri l'ultimo report HTML con Firefox o browser di default"""
    reports = [os.path.join(REPORT_FOLDER, f) for f in os.listdir(REPORT_FOLDER) if f.endswith(".html")]
    if not reports:
        messagebox.showwarning("Attenzione", "Nessun report disponibile. Esegui prima un test.")
        return

    latest_report = max(reports, key=os.path.getctime)

    if FIREFOX_PATH:
        try:
            subprocess.Popen([FIREFOX_PATH, latest_report], shell=True)
        except FileNotFoundError:
            messagebox.showerror(
                "Errore",
                f"Firefox non trovato. Controlla il percorso in {CONFIG_FILE}"
            )
    else:
        webbrowser.open(latest_report)

# --- GUI ---
root = tk.Tk()
root.title("Playwright Test Launcher")
root.geometry("500x350")

tk.Label(root, text="Seleziona test da lanciare:").pack(pady=10)

# Trova tutti i file di test nella cartella
test_files = [f for f in os.listdir(TEST_FOLDER) if f.startswith("test_") and f.endswith(".py")]
if not test_files:
    messagebox.showwarning("Attenzione", f"Nessun test trovato in {TEST_FOLDER}")
    test_files = []

var_test = tk.StringVar(root)
if test_files:
    var_test.set(test_files[0])

tk.OptionMenu(root, var_test, *test_files).pack(pady=5)

tk.Button(root, text="Esegui Test Selezionato",
          command=lambda: start_test_thread_with_optional_file(var_test.get())).pack(pady=10)

tk.Button(root, text="Esegui Tutta la Suite",
          command=lambda: start_test_thread()).pack(pady=10)

tk.Button(root, text="Apri Ultimo Report HTML",
          command=open_report).pack(pady=10)

root.mainloop()
