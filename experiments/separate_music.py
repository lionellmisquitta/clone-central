"""Separate an authorized song into vocals and accompaniment with Demucs."""
import argparse
import os
import subprocess
import sys
import time
from pathlib import Path

MUSIC_MODELS = {"fast": "mdx_q", "balanced": "htdemucs", "studio": "htdemucs_ft"}


def command_for(input_file, mode, output_dir, model=None):
    return [
        sys.executable, "-m", "demucs",
        "--two-stems=vocals", "-n", model or MUSIC_MODELS[mode],
        "-d", "cpu", "-o", str(output_dir), str(input_file),
    ]


def main():
    parser = argparse.ArgumentParser(description="Separate vocals and accompaniment locally")
    parser.add_argument("input", type=Path)
    parser.add_argument("--mode", choices=MUSIC_MODELS, default="balanced")
    parser.add_argument("--model", choices=list(MUSIC_MODELS.values()),
                        help="Installed model selected from the model library")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/stems"))
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Audio input not found: {args.input}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    selected = args.model or os.environ.get("CLONE_CENTRAL_MODEL_NAME")
    if selected:
        if selected not in MUSIC_MODELS.values():
            parser.error("Invalid installed music model selection")
        selected_path = os.environ.get("CLONE_CENTRAL_MODEL_PATH")
        if selected_path and not (Path(selected_path) / ".clone-central-ready").is_file():
            parser.error("Selected model is not fully installed")
    cmd = command_for(args.input, args.mode, args.output_dir, selected)
    env = os.environ.copy()
    if selected and env.get("CLONE_CENTRAL_MODEL_PATH"):
        env["TORCH_HOME"] = env["CLONE_CENTRAL_MODEL_PATH"]
    print(f"Using Demucs {selected or MUSIC_MODELS[args.mode]} on CPU.", flush=True)
    start = time.perf_counter()
    subprocess.run(cmd, check=True, env=env)
    print(f"ELAPSED_SECONDS={time.perf_counter()-start:.2f}")
    print(f"Find vocals.wav and no_vocals.wav under: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
