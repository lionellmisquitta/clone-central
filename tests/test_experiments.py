"""Fast standard-library checks; these do NOT claim model inference succeeded."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from experiments.voice_clone import VOICE_MODELS, model_for
from experiments.separate_music import MUSIC_MODELS, command_for


class ExperimentChecks(unittest.TestCase):
    def test_all_presets_exist(self):
        self.assertEqual(set(VOICE_MODELS), {"fast", "balanced", "studio"})
        self.assertEqual(set(MUSIC_MODELS), set(VOICE_MODELS))

    def test_voice_uses_base_checkpoints(self):
        for mode in VOICE_MODELS:
            self.assertTrue(model_for(mode).endswith("-Base"))

    def test_music_arguments_keep_spaces_in_paths(self):
        source = Path("folder with spaces/my track.wav")
        cmd = command_for(source, "balanced", Path("output dir"))
        self.assertEqual(cmd[-1], str(source))
        self.assertIn("htdemucs", cmd)
        self.assertEqual(cmd[cmd.index("-d") + 1], "cpu")

    def test_music_fast_uses_quantized(self):
        self.assertIn("mdx_q", command_for(Path("a.wav"), "fast", Path("out")))


if __name__ == "__main__":
    unittest.main()
