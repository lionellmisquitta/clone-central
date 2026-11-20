"""Recording creates a standard local WAV without touching the microphone in CI."""
import tempfile
import unittest
import wave
from pathlib import Path
from recorder import save_wav, output_path, SAMPLE_RATE


class RecorderTests(unittest.TestCase):
    def test_wav_format_and_audio_samples(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "sample.wav"
            save_wav([b"\x00\x00" * 800], path)
            with wave.open(str(path), "rb") as stream:
                self.assertEqual(stream.getnchannels(), 1)
                self.assertEqual(stream.getsampwidth(), 2)
                self.assertEqual(stream.getframerate(), SAMPLE_RATE)
                self.assertEqual(stream.getnframes(), 800)

    def test_empty_recording_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaises(ValueError):
                save_wav([], Path(folder) / "empty.wav")

    def test_unique_local_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            a, b = output_path(folder), output_path(folder)
            self.assertNotEqual(a, b)
            self.assertEqual(a.suffix, ".wav")


if __name__ == "__main__":
    unittest.main()
