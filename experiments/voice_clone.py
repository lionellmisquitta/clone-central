"""Generate one cloned-voice WAV. No UI, adapter classes or model manager."""
import argparse
import time
from pathlib import Path

VOICE_MODELS = {
    "fast": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "balanced": "Qwen/Qwen3-TTS-12Hz-0.6B-Base",
    "studio": "Qwen/Qwen3-TTS-12Hz-1.7B-Base",
}


def model_for(mode):
    return VOICE_MODELS[mode]


def main():
    parser = argparse.ArgumentParser(description="Clone an authorized reference voice locally")
    parser.add_argument("--reference", type=Path, required=True, help="Reference voice WAV, not uploaded to GitHub")
    parser.add_argument("--reference-text", required=True, help="Verbatim transcript of the reference voice clip")
    parser.add_argument("--text", required=True, help="New words to synthesize")
    parser.add_argument("--mode", choices=VOICE_MODELS, default="balanced")
    parser.add_argument("--output", type=Path, default=Path("outputs/voice.wav"))
    args = parser.parse_args()
    if not args.reference.is_file():
        parser.error(f"Reference WAV not found: {args.reference}")
    if args.reference.suffix.lower() != ".wav":
        parser.error("Use a WAV reference for this initial experiment.")
    if not args.reference_text.strip() or not args.text.strip():
        parser.error("Reference transcript and target text cannot be blank.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Lazy imports: simple unit tests run without heavy AI packages.
    import torch
    import soundfile as sf
    from qwen_tts import Qwen3TTSModel

    print(f"Loading {model_for(args.mode)} on CPU (first run downloads model outside Git).", flush=True)
    start = time.perf_counter()
    model = Qwen3TTSModel.from_pretrained(
        model_for(args.mode), device_map="cpu", dtype=torch.float32
    )
    print("Generating voice...", flush=True)
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
