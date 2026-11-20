# Clone Central — Local Model Library

This is a **minimal local chooser**, not a model marketplace. No application server or database.

1. Extract the Windows experiment ZIP.
2. On an approved Windows machine with Python **3.12** installed, double-click **MODEL-LIBRARY.cmd**.
3. Under **Model storage folder**, choose any local folder with ample free disk space (e.g. `D:\AI Models\CloneCentral`). The app remembers the folder under `%LOCALAPPDATA%\CloneCentral\settings.json`.
4. Choose an official Qwen3-TTS Base model or a Demucs separation model in **Available for download**.
5. Click **Download**. Only the selected model is downloaded. This may require many gigabytes and could take substantial time.
6. Once complete, the model automatically appears in the **Installed models** dropdown. Choose one and click **Use selected model** to launch the appropriate voice or music experiment. It uses your installed local model.
7. To switch models, return to the library, choose another installed item and open the experiment again.

**Voice models:** 0.6B Base / 1.7B Base from the official Qwen Hugging Face organization.

**Music models:** mdx_q / htdemucs / htdemucs_ft from Demucs' pretrained model catalogue.

Only catalog-listed model names are available; this version does **not** allow arbitrary third-party URLs. An installation is marked ready after the download/load operation returns successfully; an interrupted download is not shown as installed. A ready marker does not prove the model's integrity cryptographically or that it will run on your CPU. Run and verify WAV output on the Surface before declaring success.

The local model folder, voice samples and music files must never be added to GitHub. The Python environments are per-folder, ignored by Git. Music and voice dependencies are separate for compatibility.

**Known limitations:** no download progress bar (status text only), no uninstall button, no integrity pinning, no model benchmarks, no training, no RVC inference, no full audio editor. GitHub Actions can package the scripts, but cannot validate your actual Surface's audio-quality or processing speed.

## Ollama-style commands (now supported)

From the extracted experiment folder, open Command Prompt and use:

```bat
clone-central pull qwen-0.6b
clone-central pull demucs-htdemucs
clone-central list
clone-central models
```

`pull` downloads the selected model to the SAME folder used by the graphical picker.
`list` shows only completed local downloads; `models` opens the picker.
Use `--folder "D:\\AI Models\\CloneCentral"` after a `pull` or `list` command to choose a storage directory; a chosen folder is remembered.

The graphical picker also has a **Copy pull command** button. Both interfaces share one small model catalog. First launch installs only the Python download helper; actual models remain external downloads. This is an experimental source-based ZIP, not a self-contained .exe.

## Record a reference WAV without installing another recorder

Open Model Library and click **Record WAV**; speak for 10–20 seconds (30-second limit), then **Stop and save**. A mono 16-kHz signed 16-bit WAV is saved outside OneDrive by default under `%LOCALAPPDATA%\CloneCentral\recordings`. The path appears in the same window. Clicking **Use selected model** automatically passes this WAV to the voice experiment, where you must enter **exactly what you said** as the reference transcript and then your new target text. The default microphone is used; Windows microphone permission must be enabled. This is local recording, not cloud upload.

**Current limitation:** generation still uses a command window. The in-window generation and progress view remain future work; do not claim they exist.
