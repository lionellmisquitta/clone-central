"""Separate an authorized recording into vocals and accompaniment with Demucs."""
import argparse
import subprocess
import sys
import time
from pathlib import Path

MUSIC_MODELS = {
    "fast": "mdx_q",
    "balanced": "htdemucs",
    "studio": "htdemucs_ft",
}


def command_for(input_file, mode, output_dir):
    return [
        sys.executable, "-m", "demucs",
        "--two-stems=vocals", "-n", MUSIC_MODELS[mode],
        "-d", "cpu", "-o", str(output_dir), str(input_file),
    ]


def main():
    parser = argparse.ArgumentParser(description="Separate vocals and accompaniment locally")
    parser.add_argument("input", type=Path, help="Authorized audio recording")
    parser.add_argument("--mode", choices=MUSIC_MODELS, default="balanced")
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/stems"))
    args = parser.parse_args()
    if not args.input.is_file():
        parser.error(f"Audio input not found: {args.input}")
    args.output_dir.mkdir(parents=True, exist_ok=True)
    cmd = command_for(args.input, args.mode, args.output_dir)
    print(f"Using Demucs {MUSIC_MODELS[args.mode]} on CPU...", flush=True)
    start = time.perf_counter()
    subprocess.run(cmd, check=True)
    print(f"ELAPSED_SECONDS={time.perf_counter()-start:.2f}")
    print(f"Find vocals.wav and no_vocals.wav under: {args.output_dir.resolve()}")


if __name__ == "__main__":
    main()
