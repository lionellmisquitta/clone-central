"""Verify the Windows one-window voice flow has no console-launch regression."""
import ast
import unittest
from pathlib import Path


class VoiceWindowTests(unittest.TestCase):
    def test_voice_generation_is_embedded_in_picker(self):
        source = (Path(__file__).resolve().parents[1] / "model_library.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        library = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Library")
        methods = {n.name: n for n in library.body if isinstance(n, ast.FunctionDef)}
        self.assertIn("run_voice", methods)
        self.assertIn("finish_generation", methods)
        self.assertIn("open_output", methods)
        selected = ast.get_source_segment(source, methods["use_selected"])
        self.assertNotIn("CREATE_NEW_CONSOLE", selected)
        self.assertNotIn("VOICE-EXPERIMENT.cmd", selected)
        self.assertIn("self.run_voice", selected)

    def test_voice_stream_is_hidden_on_windows(self):
        source = (Path(__file__).resolve().parents[1] / "model_library.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        library = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "Library")
        method = next(n for n in library.body if isinstance(n, ast.FunctionDef) and n.name == "run_voice")
        snippet = ast.get_source_segment(source, method)
        self.assertIn("CREATE_NO_WINDOW", snippet)
        self.assertIn("stderr=subprocess.STDOUT", snippet)


if __name__ == "__main__":
    unittest.main()
