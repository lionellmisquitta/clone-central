"""Local model library with a small Tkinter UI. No server, database or plugin system.

The folder is user-selected and remembered under LOCALAPPDATA. Downloaded model
files are never stored in this Git repository. Run through MODEL-LIBRARY.cmd.
"""
import argparse
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, messagebox, ttk
from recorder import MAX_SECONDS, MicrophoneRecorder, output_path

CATALOG = {
    "Qwen3-TTS 0.6B Base": ("voice", "Qwen/Qwen3-TTS-12Hz-0.6B-Base", "qwen-0.6b-base"),
    "Qwen3-TTS 1.7B Base": ("voice", "Qwen/Qwen3-TTS-12Hz-1.7B-Base", "qwen-1.7b-base"),
    "Demucs MDX Quantized": ("music", "mdx_q", "mdx_q"),
    "Demucs HTDemucs": ("music", "htdemucs", "htdemucs"),
    "Demucs HTDemucs Fine Tuned": ("music", "htdemucs_ft", "htdemucs_ft"),
}
CONFIG_PATH = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CloneCentral" / "settings.json"
DEFAULT_ROOT = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "CloneCentral" / "models"

# User-friendly stable aliases. GUI and CLI share the same catalog and download code.
ALIASES = {
    "qwen-0.6b": "Qwen3-TTS 0.6B Base",
    "qwen-1.7b": "Qwen3-TTS 1.7B Base",
    "demucs-mdx": "Demucs MDX Quantized",
    "demucs-htdemucs": "Demucs HTDemucs",
    "demucs-htdemucs-ft": "Demucs HTDemucs Fine Tuned",
}



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


def alias_for(name):
    return next(alias for alias, title in ALIASES.items() if title == name)


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
        self.geometry("860x820")
        self.minsize(740, 700)
        self.root_dir = tk.StringVar(value=str(read_root()))
        self.available = tk.StringVar(value=next(iter(CATALOG)))
        self.selected = tk.StringVar()
        self.status = tk.StringVar(value="Choose a download or select an installed model.")
        self.busy = False
        self.recorder = MicrophoneRecorder()
        self.recording_at = None
        self.reference_path = tk.StringVar(value="No recording yet")
        self.record_time = tk.StringVar(value="Ready to record (up to 30 seconds)")
        self.reference_text = tk.StringVar()
        self.target_text = tk.StringVar(value="Welcome to Clone Central. This is my first AI-generated recording.")
        self.mode = tk.StringVar(value="fast")
        self.output_file = None

        area = ttk.Frame(self, padding=18)
        area.pack(fill="both", expand=True)
        ttk.Label(area, text="Model storage folder").pack(anchor="w")
        folder_row = ttk.Frame(area)
        folder_row.pack(fill="x", pady=(3, 12))
        ttk.Entry(folder_row, textvariable=self.root_dir).pack(side="left", fill="x", expand=True)
        ttk.Button(folder_row, text="Browse...", command=self.browse).pack(side="left", padx=(8, 0))
        ttk.Label(area, text="Available for download (same as clone-central pull)").pack(anchor="w")
        row = ttk.Frame(area)
        row.pack(fill="x", pady=(3, 12))
        ttk.Combobox(row, textvariable=self.available, values=list(CATALOG), state="readonly").pack(side="left", fill="x", expand=True)
        self.download_button = ttk.Button(row, text="Download", command=self.download)
        self.download_button.pack(side="left", padx=(8, 0))
        ttk.Button(area, text="Copy pull command", command=self.copy_pull).pack(anchor="w", pady=(0, 8))

        ttk.Label(area, text="Installed models (choose the one to use)").pack(anchor="w")
        row2 = ttk.Frame(area)
        row2.pack(fill="x", pady=(3, 12))
        self.installed_combo = ttk.Combobox(row2, textvariable=self.selected, state="readonly")
        self.installed_combo.pack(side="left", fill="x", expand=True)
        ttk.Button(row2, text="Refresh", command=self.refresh).pack(side="left", padx=(8, 0))
        ttk.Label(area, text="Reference voice — record directly in Clone Central").pack(anchor="w", pady=(4, 3))
        buttons = ttk.Frame(area)
        buttons.pack(fill="x")
        self.record_button = ttk.Button(buttons, text="Record WAV", command=self.start_recording)
        self.record_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Stop and save", command=self.stop_recording, state="disabled")
        self.stop_button.pack(side="left", padx=8)
        ttk.Label(buttons, textvariable=self.record_time).pack(side="left", padx=8)
        ttk.Label(area, textvariable=self.reference_path, wraplength=620).pack(anchor="w", pady=(4, 8))
        ttk.Label(area, text="Exact words spoken in your reference recording").pack(anchor="w")
        ttk.Entry(area, textvariable=self.reference_text).pack(fill="x", pady=(2, 7))
        ttk.Label(area, text="New words for Clone Central to speak").pack(anchor="w")
        ttk.Entry(area, textvariable=self.target_text).pack(fill="x", pady=(2, 7))
        controls = ttk.Frame(area)
        controls.pack(fill="x", pady=(4, 5))
        ttk.Label(controls, text="Quality:").pack(side="left")
        ttk.Combobox(controls, textvariable=self.mode, values=["fast", "balanced", "studio"], state="readonly", width=12).pack(side="left", padx=8)
        self.generate_button = ttk.Button(controls, text="Generate voice", command=self.use_selected)
        self.generate_button.pack(side="left", padx=8)
        self.progress = ttk.Progressbar(area, mode="indeterminate")
        self.progress.pack(fill="x", pady=(4, 7))
        ttk.Label(area, text="Generation activity (no separate console)").pack(anchor="w")
        self.log_area = tk.Text(area, height=7, wrap="word", state="disabled")
        self.log_area.pack(fill="both", expand=True, pady=(3, 5))
        ttk.Button(area, text="Open generated WAV", command=self.open_output).pack(anchor="w")
        ttk.Label(area, textvariable=self.status, wraplength=570).pack(anchor="w", pady=(14, 0))
        ttk.Label(area, text="Downloads stay local. No voice samples or weights are uploaded to GitHub.", foreground="#555").pack(anchor="w", pady=(12, 0))
        self.refresh()

    def current_root(self):
        raw = self.root_dir.get().strip()
        if not raw:
            raise ValueError("Choose a model folder.")
        root = Path(raw).expanduser()
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

    def copy_pull(self):
        command = "clone-central pull " + alias_for(self.available.get())
        self.clipboard_clear()
        self.clipboard_append(command)
        self.status.set("Copied: " + command)

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

    def start_recording(self):
        try:
            self.recorder.start()
        except Exception as exc:
            messagebox.showerror("Microphone error", "Could not start recording: " + str(exc))
            return
        self.recording_at = time.monotonic()
        self.record_button.configure(state="disabled")
        self.stop_button.configure(state="normal")
        self.status.set("Recording from your default microphone. Speak naturally, then click Stop and save.")
        self.update_record_timer()

    def update_record_timer(self):
        if self.recording_at is None:
            return
        seconds = time.monotonic() - self.recording_at
        self.record_time.set(f"Recording: {seconds:.1f}s / {MAX_SECONDS}s")
        if seconds >= MAX_SECONDS:
            self.stop_recording()
        else:
            self.after(200, self.update_record_timer)

    def stop_recording(self):
        if self.recording_at is None:
            return
        self.recording_at = None
        destination = output_path(CONFIG_PATH.parent / "recordings")
        try:
            path = self.recorder.stop(destination)
        except Exception as exc:
            self.status.set("Recording failed: " + str(exc))
            messagebox.showerror("Recording error", str(exc))
        else:
            self.reference_path.set(str(path))
            self.status.set("WAV saved locally. Select your voice model and click Use selected model.")
        self.record_button.configure(state="normal")
        self.stop_button.configure(state="disabled")
        self.record_time.set("Ready to record (up to 30 seconds)")

    def log(self, line):
        self.log_area.configure(state="normal")
        self.log_area.insert("end", line.rstrip() + "\n")
        self.log_area.see("end")
        self.log_area.configure(state="disabled")
        self.status.set(line.strip()[-140:])

    def open_output(self):
        if self.output_file and self.output_file.is_file():
            os.startfile(str(self.output_file))
        else:
            messagebox.showinfo("No audio yet", "Generate a voice WAV first.")

    def use_selected(self):
        if self.busy:
            return
        name = self.selected.get()
        if name not in CATALOG:
            messagebox.showinfo("Nothing installed", "Download a model first.")
            return
        kind, model_id, _ = CATALOG[name]
        if kind != "voice":
            messagebox.showinfo("Music", "Music separation still uses the separate experiment; this window now handles voice.")
            return
        ref = Path(self.reference_path.get())
        if not ref.is_file():
            messagebox.showerror("Reference required", "Record your voice using Record WAV first.")
            return
        exact = self.reference_text.get().strip()
        target = self.target_text.get().strip()
        if not exact or not target:
            messagebox.showerror("Text required", "Enter the exact spoken words and the new words to generate.")
            return
        try:
            root = self.current_root()
        except (OSError, ValueError) as exc:
            messagebox.showerror("Model folder", str(exc))
            return
        folder = model_folder(root, name)
        if not (folder / ".clone-central-ready").is_file():
            messagebox.showerror("Model not ready", "Selected model is not downloaded.")
            return
        app_dir = Path(__file__).resolve().parent
        python = Path(sys.executable)
        output = CONFIG_PATH.parent / "outputs" / "voice.wav"
        self.output_file = None
        self.busy = True
        self.generate_button.configure(state="disabled")
        self.progress.start(12)
        self.log("Preparing voice generator for " + name + "...")
        self.log("First run installs voice dependencies. CPU inference may be slow.")
        args = [str(python), str(app_dir / "experiments" / "voice_clone.py"), "--reference", str(ref),
                "--reference-text", exact, "--text", target, "--mode", self.mode.get(),
                "--model-path", str(folder), "--output", str(output)]
        threading.Thread(target=self.run_voice, args=(python, app_dir, args, output), daemon=True).start()

    def run_voice(self, python, app_dir, args, output):
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        def run_step(command):
            process = subprocess.Popen(command, cwd=str(app_dir), stdout=subprocess.PIPE,
                                       stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                       errors="replace", bufsize=1, creationflags=creationflags)
            for line in process.stdout:
                value = line.strip()
                if value:
                    self.after(0, lambda item=value: self.log(item))
            return process.wait()

        try:
            check = subprocess.run([str(python), "-c", "import qwen_tts, soundfile"],
                                   capture_output=True, creationflags=creationflags)
            if check.returncode:
                self.after(0, lambda: self.log("Installing Qwen3-TTS dependencies locally..."))
                if run_step([str(python), "-m", "pip", "install", "qwen-tts", "soundfile"]):
                    raise RuntimeError("Dependency installation failed. See activity log.")
            if run_step(args):
                raise RuntimeError("Voice generation failed. See activity log.")
            if not output.is_file() or output.stat().st_size == 0:
                raise RuntimeError("No voice WAV was produced.")
            self.after(0, lambda: self.finish_generation(output, None))
        except Exception as exc:
            reason = str(exc)
            self.after(0, lambda: self.finish_generation(None, reason))

    def finish_generation(self, output, error):
        self.busy = False
        self.generate_button.configure(state="normal")
        self.progress.stop()
        if error:
            self.log("ERROR: " + error)
        else:
            self.output_file = output
            self.log("SUCCESS: Saved WAV at " + str(output))


def cli(argv=None):
    """Minimal Ollama-style CLI sharing the same download and installed-model logic."""
    parser = argparse.ArgumentParser(prog="clone-central", description="Local model downloader")
    actions = parser.add_subparsers(dest="action")
    pull = actions.add_parser("pull", help="Download model by its alias")
    pull.add_argument("model", choices=ALIASES)
    pull.add_argument("--folder", type=Path, help="Model storage root (saved for subsequent runs)")
    listing = actions.add_parser("list", help="List downloaded models")
    listing.add_argument("--folder", type=Path)
    actions.add_parser("models", help="Open graphical model picker")
    args = parser.parse_args(argv)
    if args.action in (None, "models"):
        Library().mainloop()
        return 0
    root = args.folder.expanduser() if args.folder else read_root()
    if args.folder:
        save_root(root)
    if args.action == "list":
        names = installed(root)
        print("Model folder:", root)
        if not names:
            print("No installed models. Run: clone-central pull qwen-0.6b")
        for name in names:
            print(alias_for(name), "-", name, "-", model_folder(root, name))
        return 0
    name = ALIASES[args.model]
    folder = model_folder(root, name)
    if (folder / ".clone-central-ready").is_file():
        print("Already installed:", name, "at", folder)
        return 0
    print("Downloading:", name, "to", folder, flush=True)
    try:
        download_model(root, name)
    except Exception as exc:
        print("Download failed:", exc, file=sys.stderr)
        return 1
    print("Installed:", name, "at", folder)
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
