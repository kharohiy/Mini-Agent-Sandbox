import unittest
from types import SimpleNamespace
from unittest.mock import patch

from project_qa import ask_project


class ProjectQaTests(unittest.TestCase):
    def test_technical_reference_is_separate_from_project_evidence(self):
        completions = []

        def complete(*args, **kwargs):
            completions.append(args[1])
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Grounded answer."))])

        with patch("project_qa.retrieve_project_context", return_value=[{
            "scope": "project-code", "source": "app/MainActivity.kt", "sha256": "a" * 64, "text": "fun main() {}",
        }]), patch("project_qa.retrieve_global_technical_references", return_value=[{
            "scope": "global-library", "source": "Compose.pdf", "text": "Navigation explanation",
        }]), patch("project_qa.safe_llm_completion", side_effect=complete):
            answer = ask_project("demo--123", "Where is navigation created?", include_technical_reference=True)

        self.assertEqual(answer["sources"], ["app/MainActivity.kt"])
        self.assertEqual(answer["project_evidence"], [{
            "project_id": "demo--123", "scope": "project-code",
            "source": "app/MainActivity.kt", "sha256": "a" * 64,
        }])
        self.assertEqual(answer["technical_references"], ["Compose.pdf"])
        self.assertIn("PROJECT EVIDENCE:\nSOURCE: app/MainActivity.kt", completions[0][1]["content"])
        self.assertIn("TECHNICAL REFERENCE (explanation only; never evidence of a project fact):", completions[0][1]["content"])
        self.assertIn("Project facts require project evidence", completions[0][0]["content"])


if __name__ == "__main__":
    unittest.main()
