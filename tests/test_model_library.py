"""CLI and catalog tests without any network access or model download."""
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

try:
    import model_library as library
except ImportError:
    library = None


@unittest.skipIf(library is None, "Tkinter is unavailable on this test host")
class LocalModelLibraryTests(unittest.TestCase):
    def test_catalog_aliases_unique(self):
        self.assertEqual(len(set(library.ALIASES.values())), len(library.CATALOG))
        self.assertEqual(set(library.ALIASES.values()), set(library.CATALOG))

    def test_list_only_returns_ready_models(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            voice_name = library.ALIASES["qwen-0.6b"]
            folder = library.model_folder(root, voice_name)
            folder.mkdir(parents=True)
            self.assertNotIn(voice_name, library.installed(root))
            (folder / ".clone-central-ready").write_text("test\n")
            self.assertIn(voice_name, library.installed(root))

    def test_cli_pull_passes_same_name_and_root_as_gui(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with patch.object(library, "download_model") as download:
                result = library.cli(["pull", "qwen-0.6b", "--folder", str(root)])
                self.assertEqual(result, 0)
                download.assert_called_once_with(root, library.ALIASES["qwen-0.6b"])

    def test_cli_list_shows_installed_alias(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            title = library.ALIASES["demucs-htdemucs"]
            folder = library.model_folder(root, title)
            folder.mkdir(parents=True)
            (folder / ".clone-central-ready").write_text("test\n")
            buf = io.StringIO()
            with redirect_stdout(buf):
                result = library.cli(["list", "--folder", str(root)])
            self.assertEqual(result, 0)
            self.assertIn("demucs-htdemucs", buf.getvalue())

    def test_failed_pull_does_not_claim_success(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(library, "download_model", side_effect=RuntimeError("network unavailable")):
                self.assertEqual(
                    library.cli(["pull", "qwen-0.6b", "--folder", temp]), 1
                )


if __name__ == "__main__":
    unittest.main()
