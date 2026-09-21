import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from runner import validate_generated_code


class LanguageValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    @patch("runner.subprocess.run")
    def test_python_workspace_uses_python_validators(self, run):
        (self.workspace / "main.py").write_text("print('ok')", encoding="utf-8")
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        is_clean, _ = validate_generated_code(self.workspace)

        self.assertTrue(is_clean)
        self.assertEqual(run.call_count, 2)
        self.assertIn("ruff", run.call_args_list[0].args[0])
        self.assertIn("semgrep", run.call_args_list[1].args[0])

    def test_kotlin_workspace_without_gradle_wrapper_fails_closed(self):
        (self.workspace / "Main.kt").write_text("fun main() = Unit", encoding="utf-8")

        is_clean, message = validate_generated_code(self.workspace)

        self.assertFalse(is_clean)
        self.assertIn("Gradle wrapper", message)

    @patch("runner.subprocess.run")
    def test_kotlin_workspace_uses_gradle_lint_and_tests(self, run):
        (self.workspace / "Main.kt").write_text("fun main() = Unit", encoding="utf-8")
        wrapper = self.workspace / ("gradlew.bat" if os.name == "nt" else "gradlew")
        wrapper.write_text("", encoding="utf-8")
        run.return_value = MagicMock(returncode=0, stdout="", stderr="")

        is_clean, _ = validate_generated_code(self.workspace)

        self.assertTrue(is_clean)
        self.assertEqual(run.call_count, 1)
        self.assertEqual(run.call_args.args[0][1:], ["--offline", "lint", "test"])

    def test_mixed_workspace_fails_closed(self):
        (self.workspace / "main.py").write_text("print('ok')", encoding="utf-8")
        (self.workspace / "Main.kt").write_text("fun main() = Unit", encoding="utf-8")

        is_clean, message = validate_generated_code(self.workspace)

        self.assertFalse(is_clean)
        self.assertIn("Mixed Python/Kotlin", message)


    def test_markdown_only_workspace_passes_without_code_execution(self):
        (self.workspace / "architecture_summary.md").write_text("# Architecture\\n", encoding="utf-8")

        is_clean, message = validate_generated_code(self.workspace)

        self.assertTrue(is_clean)
        self.assertIn("Documentation-only", message)
if __name__ == "__main__":
    unittest.main()
