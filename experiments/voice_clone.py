"""Generate a local reference-voice WAV using a selected installed Qwen Base model."""
import argparse
import os
import time
from pathlib import Path

VOICE_MODELS = {
    "fast": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "balanced": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "studio": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}


def model_for(mode, selected=None):
    return selected or VOICE_MODELS[mode]


def main():
    parser = argparse.ArgumentParser(description="Clone an authorized reference voice locally")
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--reference-text", required=True)
    parser.add_argument("--text", required=True)
    parser.add_argument("--mode", choices=VOICE_MODELS, default="balanced")
    parser.add_argument("--model-path", type=Path, default=None,
                        help="Installed local Qwen Base model directory from the library")
    parser.add_argument("--output", type=Path, default=Path("outputs/voice.wav"))
    args = parser.parse_args()
    if not args.reference.is_file():
        parser.error(f"Reference WAV not found: {args.reference}")
    if args.reference.suffix.lower() != ".wav":
        parser.error("Use a WAV reference for this initial experiment.")
    if not args.reference_text.strip() or not args.text.strip():
        parser.error("Reference transcript and target text cannot be blank.")
    chosen = args.model_path or os.environ.get("CLONE_CENTRAL_MODEL_PATH")
    if chosen:
        chosen = Path(chosen)
        if not (chosen / ".clone-central-ready").is_file():
            parser.error(f"Chosen model is not installed: {chosen}")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    model_id = str(chosen) if chosen else model_for(args.mode)
    print(f"Loading {model_id} on CPU.", flush=True)
    start = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(
        model_id, device_map="cpu", dtype=torch.float32
    )
    waves, sample_rate = model.generate_voice_clone(
        text=args.text,
        language="English",
        ref_audio=str(args.reference),
        ref_text=args.reference_text,
    )
    sf.write(str(args.output), waves[0], sample_rate)
    elapsed = time.perf_counter() - start
    duration = len(waves[0]) / sample_rate
    print(f"OUTPUT={args.output.resolve()}")
    print(f"AUDIO_SECONDS={duration:.2f} ELAPSED_SECONDS={elapsed:.2f}")
    print(f"REALTIME_FACTOR={elapsed / duration:.2f}" if duration else "Output was empty")


if __name__ == "__main__":
    main()
