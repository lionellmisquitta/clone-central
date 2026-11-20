"""Minimal microphone WAV recorder. Keeps recordings local; no cloud or GUI dependencies."""
from datetime import datetime
from pathlib import Path
import wave

SAMPLE_RATE = 16000
CHANNELS = 1
MAX_SECONDS = 30


def save_wav(frames, destination, sample_rate=SAMPLE_RATE):
    """Write signed 16-bit mono PCM WAV; fail for empty captures."""
    if not frames or not any(frames):
        raise ValueError("No microphone audio captured.")
    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(CHANNELS)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)
        wav.writeframes(b"".join(frames))
    return destination


def output_path(folder):
    """Distinct file per recording; never overwrite an earlier reference."""
    return Path(folder) / ("reference-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f") + ".wav")


class MicrophoneRecorder:
    """Single sounddevice stream; GUI owns start, stop and status."""
    def __init__(self):
        self.stream = None
        self.frames = []

    def start(self):
        if self.stream is not None:
            raise RuntimeError("Recording is already in progress")
        import sounddevice as sd
        self.frames = []

        def collect(indata, frames, time_info, status):
            # PortAudio callback: never call Tk from this thread.
            self.frames.append(indata.copy().tobytes())

        stream = sd.InputStream(
            samplerate=SAMPLE_RATE, channels=CHANNELS, dtype="int16",
            blocksize=1024, callback=collect,
        )
        stream.start()
        self.stream = stream

    def stop(self, destination):
        if self.stream is None:
            raise RuntimeError("Recording has not started")
        stream = self.stream
        self.stream = None
        try:
            stream.stop()
        finally:
            stream.close()
        frames = self.frames
        self.frames = []
        return save_wav(frames, destination)
