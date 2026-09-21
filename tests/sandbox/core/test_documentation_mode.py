import unittest

from runner import AGENT_TOOLS, agent_tools_for_task_mode, documentation_path_allowed, model_fact_update_denied


class Message:
    def __init__(self, content):
        self.content = content
        self.tool_calls = None


class Response:
    def __init__(self, content):
        self.choices = [type("Choice", (), {"message": Message(content)})()]


class DocumentationTaskModeTests(unittest.TestCase):
    def test_documentation_mode_exposes_only_workspace_markdown_tools(self):
        names = {tool["function"]["name"] for tool in agent_tools_for_task_mode("documentation")}
        self.assertEqual(names, {"create_file", "read_file", "list_directory"})
        self.assertNotIn("update_project_fact", {tool["function"]["name"] for tool in AGENT_TOOLS})

    def test_documentation_mode_rejects_non_markdown_paths(self):
        self.assertTrue(documentation_path_allowed("documentation", "create_file", "architecture_summary.md"))
        self.assertFalse(documentation_path_allowed("documentation", "create_file", "CheatCodesScreen.kt"))
        self.assertFalse(documentation_path_allowed("documentation", "read_file", "project_facts.json"))

    def test_model_generated_fact_promotion_is_denied(self):
        self.assertIn("cannot be promoted automatically", model_fact_update_denied())

    def test_documentation_reviewer_completion_does_not_ingest_facts(self):
        from tests.sandbox.core.test_documentation_policy import DocumentationCompletionGateTests
        state, _ = DocumentationCompletionGateTests().run_review()
        self.assertEqual(state["status"], "completed")
        self.assertFalse(any("approval" in key.lower() or "validation" in key.lower() for key in state))

    def test_unknown_task_mode_is_rejected(self):
        with self.assertRaises(ValueError):
            agent_tools_for_task_mode("unknown")


if __name__ == "__main__":
    unittest.main()
