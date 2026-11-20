# Run the first real audio experiments

**Goal:** produce one cloned-voice WAV and one separated song on your own authorized machine. No web UI yet. Install only on a device and network where policy permits personal voice cloning and model downloads.

## Requirements
- Python **3.12** in a clean environment. Existing Python 3.14 may not be supported by the audio packages.
- Windows PowerShell or Command Prompt, network access to approved model hosts, sufficient disk space.
- Your own consenting reference voice in WAV format and its **exact transcript**.
- Your own or licensed music input. Nothing personal should be pushed to the public GitHub repo.
- No GPU assumed. First CPU run may be slow and downloads can be large.

## Voice experiment V1
In PowerShell after cloning the repo:
```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install qwen-tts soundfile
.\.venv\Scripts\python.exe experiments\voice_clone.py --reference "C:\Audio\my voice.wav" --reference-text "The exact words in my reference recording." --text "Clone Central is ready for its first voice experiment." --mode fast --output "outputs\voice.wav"
```
The official Python package downloads its model into Hugging Face's **local cache**, not GitHub. On first use, allow a substantial download. `fast` and `balanced` currently select the same 0.6B Base checkpoint; `studio` selects 1.7B Base and may be much slower. Neither speed nor voice fidelity is verified on your Surface yet. Do not commit recorded references.

## Music experiment M1
Use a **separate** virtual environment to avoid entangling older Demucs dependencies with Qwen.
```powershell
py -3.12 -m venv .venv-music
.\.venv-music\Scripts\python.exe -m pip install --upgrade pip
.\.venv-music\Scripts\python.exe -m pip install demucs
.\.venv-music\Scripts\python.exe experiments\separate_music.py "C:\Audio\my authorized song.wav" --mode fast
```
Demucs downloads a separation checkpoint when needed. Look under `outputs\stems\<model>\<song>\` for `vocals.wav` and `no_vocals.wav`. Use WAV initially; other formats may need FFmpeg. Music presets: fast=`mdx_q`, balanced=`htdemucs`, studio=`htdemucs_ft`. These are candidate modes, **not demonstrated quality rankings**.

## What to record
For each run: Windows build, CPU/RAM, preset, source duration, elapsed time, peak RAM, whether the output is playable, and your quality judgment. Do not include private voice/music in public issues or Actions artifacts.

## Quick code checks (no AI models)
```powershell
py -3.12 -m unittest discover -s tests -v
```

## Known limitations
- No installed app, model manager, singing conversion or full-track mixing yet.
- The official Qwen Python runtime may be slow or incompatible with a CPU-only Windows configuration; a faster C/quantized implementation remains an experiment.
- Demucs upstream is archived and Python / Torch / torchaudio compatibility may require adjustment.
- Stems are not perfect; vocal/instrumental leakage is expected.
- Workstation IT policy may prohibit running or installing the software; packaging does not bypass that policy.

Upstream references:
- https://github.com/QwenLM/Qwen3-TTS
- https://github.com/facebookresearch/demucs
