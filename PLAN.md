# Audio-first experiments — current scope

**Two equal pillars:** Voice and Music. No UI, database, plugin system, downloader, or project manager until real audio is generated.

- V1: use official Qwen3-TTS Python API and an authorized local reference clip to generate a cloned-voice WAV. Measure wall time, output duration and perceived quality.
- M1: use Demucs to separate an authorized song into vocals and accompaniment; measure wall time, inspect both WAVs.
- M2: after M1, test conversion with an existing authorized singing-voice model. **Not implemented**.
- Later: combine demonstrated capabilities into a basic UI, then expand with mixing, pitch processing, and mastering.

Modes are **candidate processing choices**, not a verified quality ranking:
- Fast: Qwen 0.6B Base; Demucs mdx_q
- Balanced: Qwen 0.6B Base; Demucs htdemucs
- Studio: Qwen 1.7B Base; Demucs htdemucs_ft

Balanced and Fast use the same voice checkpoint initially: no claim of a voice-quality difference yet. Final presets require listening tests and hardware benchmarks. Studio may be impractically slow on CPU.

**No real-world performance verified yet.** Github CI exercises Python argument logic; real model inference must be run separately. Voice/music files are local and excluded from Git.
