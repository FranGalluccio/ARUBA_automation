import tkinter as tk
from tkinter import messagebox, filedialog
from threading import Thread
import subprocess
import os
import json
import webbrowser
from datetime import datetime
import sys
import glob

# --- Carica configurazione ---
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
if not os.path.exists(CONFIG_FILE):
    messagebox.showerror("Errore", f"File di configurazione {CONFIG_FILE} non trovato!")
    raise FileNotFoundError(f"{CONFIG_FILE} non trovato")

with open(CONFIG_FILE) as f:
    config = json.load(f)

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))  # Root del progetto Git_automation
REPORT_FOLDER = config.get("report_folder", os.path.join(PROJECT_ROOT, "test-results"))
os.makedirs(REPORT_FOLDER, exist_ok=True)

FIREFOX_PATH = config.get("firefox_path", "")

# --- Lista test che richiedono allegato ---
TEST_CON_ALLEGATO = ["test_new_message.py"]

# Processo pytest attivo
current_process = None


# ------------------------------------------------------
#        FUNZIONI SUPPORTO
# ------------------------------------------------------

def generate_report_path():
    """Crea un percorso report unico con timestamp."""
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    return os.path.join(REPORT_FOLDER, f"report_{timestamp}.html")


def set_ui_running(running: bool):
    """Abilita/disabilita la UI mentre i test sono in corso."""
    if running:
        status_label.config(text="🟡 Test in esecuzione...", fg="orange")
        btn_run_selected.config(state="disabled")
        btn_run_all.config(state="disabled")
        btn_open_report.config(state="disabled")
        btn_stop.config(state="normal")
    else:
        status_label.config(text="🟢 Pronto", fg="green")
        btn_run_selected.config(state="normal")
        btn_run_all.config(state="normal")
        btn_open_report.config(state="normal")
        btn_stop.config(state="disabled")


def stop_tests():
    """Interrompe il processo pytest in esecuzione."""
    global current_process
    if current_process and current_process.poll() is None:
        current_process.terminate()
        status_label.config(text="🔴 Test interrotti", fg="red")
        current_process = None
        set_ui_running(False)


def run_pytest(test_file=None):
    """Esegue pytest tramite Popen (interrompibile)."""
    global current_process

    report_path = generate_report_path()
    cmd = [sys.executable, "-m", "pytest", "--html", report_path, "--self-contained-html"]

    if test_file:
        cmd.append(os.path.join(PROJECT_ROOT, test_file))
    else:
        # Prende tutti i test nell'intero progetto
        test_files = glob.glob(os.path.join(PROJECT_ROOT, "**", "test_*.py"), recursive=True)
        if not test_files:
            messagebox.showwarning("Attenzione", f"Nessun test trovato in {PROJECT_ROOT}")
            set_ui_running(False)
            return
        cmd.extend(test_files)

    try:
        current_process = subprocess.Popen(cmd)
        current_process.wait()

        if current_process.returncode == 0:
            messagebox.showinfo("✅ Test Completati", f"Tutti i test sono passati!\nReport: {report_path}")
        else:
            messagebox.showerror("❌ Test Falliti", f"Alcuni test non sono passati.\nReport: {report_path}")

    except Exception as e:
        messagebox.showerror("Errore", str(e))

    finally:
        set_ui_running(False)
        current_process = None


def start_test_thread(test_file=None):
    set_ui_running(True)
    Thread(target=run_pytest, args=(test_file,), daemon=True).start()


def start_test_thread_with_optional_file(test_file=None):
    """Gestisce file picker per test che richiedono allegato."""
    if test_file in TEST_CON_ALLEGATO:
        file_path = filedialog.askopenfilename(title="Seleziona file da allegare")
        if not file_path:
            messagebox.showwarning("Attenzione", "File non selezionato. Test annullato.")
            return
        os.environ["FILE_ALLEGATO"] = file_path
    else:
        os.environ.pop("FILE_ALLEGATO", None)

    start_test_thread(test_file)


def open_report():
    """Apre l'ultimo report HTML."""
    reports = [
        os.path.join(REPORT_FOLDER, f)
        for f in os.listdir(REPORT_FOLDER)
        if f.endswith(".html")
    ]

    if not reports:
        messagebox.showwarning("Attenzione", "Nessun report disponibile.")
        return

    latest_report = max(reports, key=os.path.getctime)

    if FIREFOX_PATH:
        try:
            subprocess.Popen([FIREFOX_PATH, latest_report], shell=True)
        except FileNotFoundError:
            messagebox.showerror("Errore", f"Firefox non trovato. Controlla {CONFIG_FILE}")
    else:
        webbrowser.open(latest_report)


# ------------------------------------------------------
#                     GUI
# ------------------------------------------------------

root = tk.Tk()
root.title("Playwright Test Launcher")
root.geometry("500x420")

tk.Label(root, text="Seleziona test da eseguire:").pack(pady=10)

# Lista test disponibili nel progetto
test_files = glob.glob(os.path.join(PROJECT_ROOT, "**", "test_*.py"), recursive=True)
test_files_relative = [os.path.relpath(f, PROJECT_ROOT) for f in test_files]

var_test = tk.StringVar(root)
if test_files_relative:
    var_test.set(test_files_relative[0])
else:
    messagebox.showwarning("Attenzione", f"Nessun test trovato in {PROJECT_ROOT}")
    test_files_relative = []

tk.OptionMenu(root, var_test, *test_files_relative).pack(pady=5)

status_label = tk.Label(root, text="🟢 Pronto", fg="green")
status_label.pack(pady=10)

btn_run_selected = tk.Button(
    root,
    text="Esegui Test Selezionato",
    command=lambda: start_test_thread_with_optional_file(var_test.get())
)
btn_run_selected.pack(pady=10)

btn_run_all = tk.Button(
    root,
    text="Esegui Tutta la Suite",
    command=lambda: start_test_thread()
)
btn_run_all.pack(pady=10)

btn_open_report = tk.Button(
    root,
    text="Apri Ultimo Report HTML",
    command=open_report
)
btn_open_report.pack(pady=10)

btn_stop = tk.Button(
    root,
    text="⛔ Stop Test",
    command=stop_tests,
    state="disabled"
)
btn_stop.pack(pady=10)

root.mainloop()
