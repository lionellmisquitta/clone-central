"""Local model library with a small Tkinter UI. No server, database or plugin system.

The folder is user-selected and remembered under LOCALAPPDATA. Downloaded model
files are never stored in this Git repository. Run through MODEL-LIBRARY.cmd.
"""
import json
import os
import subprocess
import sys
import threading
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

CATALOG = {
    "Qwen3-TTS 0.6B Base": ("voice", "Qwen/Qwen3-TTS-12Hz-0.6B-Base", "qwen-0.6b-base"),
    "Qwen3-TTS 1.7B Base": ("voice", "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "qwen-1.7b-base"),
    "Demucs MDX Quantized": ("music", "mdx_q", "mdx_q"),
    "Demucs HTDemucs": ("music", "htdemucs", "htdemucs"),
    "Demucs HTDemucs Fine Tuned": ("music", "htdemucs_ft", "htdemucs_ft"),
}
CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CloneCentral" / "settings.json"
DEFAULT_ROOT = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CloneCentral" / "models"


def read_root():
    try:
        data = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        return Path(data["models_folder"]).expanduser()
    except (OSError, ValueError, KeyError, TypeError):
        return DEFAULT_ROOT


def save_root(root):
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps({"models_folder": str(root)}, indent=2), encoding="utf-8")


def model_folder(root, name):
    kind, _, slug = CATALOG[name]
    return Path(root) / kind / slug


def installed(root):
    found = []
    for name in CATALOG:
        folder = model_folder(root, name)
        marker = folder / ".clone-central-ready"
        if marker.is_file():
            found.append(name)
    return found


def download_model(root, name):
    """Download trusted, catalog-listed model; mark installed only on success."""
    kind, repo_or_name, _ = CATALOG[name]
    folder = model_folder(root, name)
    folder.mkdir(parents=True, exist_ok=True)
    marker = folder / ".clone-central-ready"
    marker.unlink(missing_ok=True)
    if kind == "voice":
        from huggingface_hub import snapshot_download

        snapshot_download(
            repo_id=repo_or_name,
            local_dir=str(folder),
            # Files come from the official Qwen organisation.
        )
    else:
        # Use the separate music environment so Torch package versions do not
        # conflict with the voice environment. The cache lives in chosen folder.
        music_env = Path(__file__).resolve().parent / ".venv-music"
        music_python = music_env / "Scripts" / "python.exe" if os.name == "nt" else music_env / "bin" / "python"
        if not music_python.exists():
            subprocess.run(["py", "-3.12", "-m", "venv", str(music_env)], check=True)
        probe = subprocess.run([str(music_python), "-c", "import demucs"], capture_output=True)
        if probe.returncode != 0:
            subprocess.run([str(music_python), "-m", "pip", "install", "demucs"], check=True)
        env = os.environ.copy()
        env["TORCH_HOME"] = str(folder)
        subprocess.run([
            str(music_python), "-c",
            "from demucs.pretrained import get_model; import sys; get_model(sys.argv[1])",
            repo_or_name,
        ], check=True, env=env)
        # Demucs may download multiple pieces; only mark after all load successfully.
    marker.write_text(repo_or_name + "\n", encoding="utf-8")
    return folder


class Library(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Clone Central - Model Library")
        self.geometry("640x375")
        self.minsize(600, 330)
        self.root_dir = tk.StringVar(value=str(read_root()))
        self.available = tk.StringVar(value=next(iter(CATALOG)))
        self.selected = tk.StringVar()
        self.status = tk.StringVar(value="Choose a download or select an installed model.")
        self.busy = False

        area = ttk.Frame(self, padding=18)
        area.pack(fill="both", expand=True)
        ttk.Label(area, text="Model storage folder").pack(anchor="w")
        folder_row = ttk.Frame(area)
        folder_row.pack(fill="x", pady=(3, 12))
        ttk.Entry(folder_row, textvariable=self.root_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse...", command=self.browse).pack(side="left", padx=(8, 0))
        ttk.Label(area, text="Available for download").pack(anchor="w")
        row = ttk.Frame(area)
        row.pack(fill="x", pady=(3, 12))
        ttk.Combobox(row, textvariable=self.available, values=list(CATALOG), state="readonly").pack(side="left", fill="x", expand=True)
        self.download_button = ttk.Button(row, text="Download", command=self.download)
        self.download_button.pack(side="left", padx=(8, 0))

        ttk.Label(area, text="Installed models (choose the one to use)").pack(anchor="w")
        row2 = ttk.Frame(area)
        row2.pack(fill="x", pady=(3, 12))
        self.installed_combo = ttk.Combobox(row2, textvariable=self.selected, state="readonly")
        self.installed_combo.pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Refresh", command=self.refresh).pack(side="left", padx=(8, 0))
        ttk.Button(area, text="Use selected model", command=self.use_selected).pack(anchor="w")
        ttk.Label(area, textvariable=self.status, wraplength=570).pack(anchor="w", pady=(14, 0))
        ttk.Label(area, text="Downloads stay local. No voice samples or weights are uploaded to GitHub.", foreground="#555").pack(anchor="w", pady=(12, 0))
        self.refresh()

    def current_root(self):
        root = Path(self.root_dir.get()).expanduser()
        if not str(root).strip():
            raise ValueError("Choose a model folder.")
        root.mkdir(parents=True, exist_ok=True)
        save_root(root)
        return root

    def browse(self):
        choice = filedialog.askdirectory(title="Choose a folder for AI models", initialdir=self.root_dir.get())
        if choice:
            self.root_dir.set(choice)
            self.current_root()
            self.refresh()

    def refresh(self):
        try:
            names = installed(self.current_root())
            self.installed_combo["values"] = names
            if self.selected.get() not in names:
                self.selected.set(names[0] if names else "")
        except (OSError, ValueError) as exc:
            self.status.set(str(exc))

    def download(self):
        if self.busy:
            return
        name = self.available.get()
        try:
            root = self.current_root()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Folder error", str(exc))
            return
        if model_folder(root, name).joinpath(".clone-central-ready").exists():
            self.status.set(name + " is already installed.")
            return
        self.busy = True
        self.download_button.configure(state="disabled")
        self.status.set(f"Downloading {name} to {root}. This may take a while...")
        def worker():
            try:
                folder = download_model(root, name)
                self.after(0, lambda: self.finish(name + " downloaded to " + str(folder)))
            except Exception as exc:
                reason = str(exc)
                self.after(0, lambda: self.finish("Download failed: " + reason))
        threading.Thread(target=worker, daemon=True).start()

    def finish(self, status):
        self.busy = False
        self.download_button.configure(state="normal")
        self.status.set(status)
        self.refresh()

    def use_selected(self):
        name = self.selected.get()
        if name not in CATALOG:
            messagebox.showinfo("Nothing installed", "Download a model first.")
            return
        root = self.current_root()
        kind, model_id, _ = CATALOG[name]
        env = os.environ.copy()
        env["CLONE_CENTRAL_MODEL_NAME"] = model_id
        env["CLONE_CENTRAL_MODEL_PATH"] = str(model_folder(root, name))
        launcher = "VOICE-EXPERIMENT.cmd" if kind == "voice" else "MUSIC-EXPERIMENT.cmd"
        script = Path(__file__).resolve().parent / launcher
        if not script.is_file():
            messagebox.showerror("Missing launcher", str(script))
            return
        self.status.set("Opening " + launcher + " with " + name)
        subprocess.Popen(["cmd", "/c", "start", "", "cmd", "/k", str(script)], cwd=str(script.parent), env=env)


if __name__ == "__main__":
    Library().mainloop()
