import os
import sys
import json
import time
import socket
import threading
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Import our sorter engine
import sorter_engine

PORT = 52140
DAEMON_ACTIVE = False
DAEMON_FOLDER = ""
DAEMON_THREAD = None

def get_base_dir():
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))

def get_web_dir():
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        bundle_web = os.path.join(sys._MEIPASS, "web")
        if os.path.exists(bundle_web):
            return bundle_web
    return os.path.join(get_base_dir(), "web")

BASE_DIR = get_base_dir()
WEB_DIR = get_web_dir()

def get_default_directories():
    user_home = Path.home()
    downloads = user_home / "Downloads"
    desktop = user_home / "Desktop"
    documents = user_home / "Documents"
    return {
        "home": str(user_home),
        "downloads": str(downloads) if downloads.exists() else str(user_home),
        "desktop": str(desktop) if desktop.exists() else str(user_home),
        "documents": str(documents) if documents.exists() else str(user_home),
        "current": BASE_DIR
    }

def pick_folder_native(initial_dir=""):
    try:
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        root.wm_attributes("-topmost", 1)
        selected = filedialog.askdirectory(initialdir=initial_dir or str(Path.home()), title="Pilih Folder untuk Dirapikan")
        root.destroy()
        return selected if selected else ""
    except Exception as e:
        print(f"Tkinter dialog error: {e}")
        # PowerShell fallback
        try:
            ps_cmd = (
                "Add-Type -AssemblyName System.Windows.Forms; "
                "$fb = New-Object System.Windows.Forms.FolderBrowserDialog; "
                "$fb.Description = 'Pilih Folder untuk Dirapikan'; "
                "$res = $fb.ShowDialog(); "
                "if ($res -eq [System.Windows.Forms.DialogResult]::OK) { Write-Output $fb.SelectedPath }"
            )
            out = subprocess.check_output(["powershell", "-NoProfile", "-Command", ps_cmd], text=True).strip()
            return out
        except Exception as ps_err:
            print(f"PowerShell dialog error: {ps_err}")
            return ""

def daemon_worker():
    global DAEMON_ACTIVE, DAEMON_FOLDER
    print(f"[Daemon] Started monitoring {DAEMON_FOLDER}")
    while DAEMON_ACTIVE:
        try:
            if DAEMON_FOLDER and os.path.exists(DAEMON_FOLDER):
                rules = sorter_engine.load_rules()
                res = sorter_engine.scan_directory(DAEMON_FOLDER, target_mode="in_place", rules=rules)
                if res["items"]:
                    print(f"[Daemon] Found {len(res['items'])} new files to organize...")
                    sorter_engine.execute_organize(res["items"])
        except Exception as e:
            print(f"[Daemon] Error in background sort: {e}")
        time.sleep(5)
    print("[Daemon] Stopped.")

class AppRequestHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

    def send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False).encode("utf-8"))

    def do_GET(self):
        if self.path == "/api/status":
            last_undo = sorter_engine.get_last_undoable_batch()
            self.send_json({
                "status": "online",
                "default_dirs": get_default_directories(),
                "daemon_active": DAEMON_ACTIVE,
                "daemon_folder": DAEMON_FOLDER,
                "last_undo": last_undo
            })
        elif self.path == "/api/rules":
            rules = sorter_engine.load_rules()
            self.send_json(rules)
        else:
            super().do_GET()

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length).decode("utf-8") if content_length > 0 else "{}"
        try:
            payload = json.loads(body) if body else {}
        except Exception:
            payload = {}

        if self.path == "/api/scan":
            folder = payload.get("folder", "")
            target_mode = payload.get("target_mode", "in_place")
            custom_target = payload.get("custom_target", "")
            if not folder or not os.path.isdir(folder):
                self.send_json({"error": "Folder yang dipilih tidak valid."}, status=400)
                return
            try:
                result = sorter_engine.scan_directory(folder, target_mode=target_mode, custom_target=custom_target)
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)

        elif self.path == "/api/organize":
            items = payload.get("items", [])
            if not items:
                self.send_json({"error": "Tidak ada file yang dipilih untuk dirapikan."}, status=400)
                return
            try:
                result = sorter_engine.execute_organize(items)
                self.send_json(result)
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)

        elif self.path == "/api/undo":
            batch_id = payload.get("batch_id")
            result = sorter_engine.undo_last_batch(batch_id)
            self.send_json(result)

        elif self.path == "/api/rules":
            try:
                sorter_engine.save_rules(payload)
                self.send_json({"success": True})
            except Exception as e:
                self.send_json({"error": str(e)}, status=500)

        elif self.path == "/api/browse":
            initial_dir = payload.get("initial_dir", "")
            chosen = pick_folder_native(initial_dir)
            self.send_json({"folder": chosen})

        elif self.path == "/api/daemon/toggle":
            global DAEMON_ACTIVE, DAEMON_FOLDER, DAEMON_THREAD
            target_folder = payload.get("folder", "")
            if not DAEMON_ACTIVE:
                if not target_folder or not os.path.isdir(target_folder):
                    self.send_json({"error": "Folder monitoring tidak valid."}, status=400)
                    return
                DAEMON_ACTIVE = True
                DAEMON_FOLDER = target_folder
                DAEMON_THREAD = threading.Thread(target=daemon_worker, daemon=True)
                DAEMON_THREAD.start()
            else:
                DAEMON_ACTIVE = False
            self.send_json({"daemon_active": DAEMON_ACTIVE, "daemon_folder": DAEMON_FOLDER})

        else:
            self.send_json({"error": "Not Found"}, status=404)

def find_available_port(start_port=52140):
    port = start_port
    while port < start_port + 50:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def launch_gui_window(url):
    # Try Chrome App mode first
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe",
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]
    
    for path in chrome_paths:
        if os.path.exists(path):
            try:
                subprocess.Popen([
                    path,
                    f"--app={url}",
                    "--window-size=1240,820",
                    "--window-position=100,60"
                ])
                print(f"Launched native App Window via: {path}")
                return
            except Exception as e:
                print(f"Error launching {path}: {e}")

    # Fallback to default browser
    webbrowser.open(url)

def run_server():
    port = find_available_port(PORT)
    server_address = ('127.0.0.1', port)
    httpd = ThreadingHTTPServer(server_address, AppRequestHandler)
    app_url = f"http://127.0.0.1:{port}"
    print(f"\n=======================================================")
    print(f" SortSensei is running at: {app_url}")
    print(f" Web UI path: {WEB_DIR}")
    print(f"=======================================================\n")

    threading.Timer(0.8, lambda: launch_gui_window(app_url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping SortSensei...")
        httpd.server_close()

if __name__ == "__main__":
    run_server()
