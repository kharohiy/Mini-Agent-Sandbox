import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import runner


def response(content=None, calls=None):
    message = SimpleNamespace(content=content, tool_calls=calls)
    message.model_dump = lambda: {"role": "assistant", "content": content}
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def create_file_call():
    return SimpleNamespace(
        id="create-file-call",
        function=SimpleNamespace(
            name="create_file",
            arguments=json.dumps({
                "filepath": "runner_probe.md",
                "content": "# Runner probe\n",
            }),
        ),
    )


class RunnerToolPersistenceTests(unittest.TestCase):
    def test_tool_result_and_redacted_error_persist_if_next_completion_fails(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            storage.save_state("probe", {
                "status": "in_progress",
                "task_mode": "code",
                "task": "Create one local probe file",
                "current_turn": "coder",
                "memory": [{"role": "user", "content": "Create one local probe file"}],
                "tool_executions": [],
                "metrics": {"total_cost": 0.0},
                "agent_steps": 0,
                "user_lang": "en",
            })
            agent_calls = 0

            def complete(model, *_args, **_kwargs):
                nonlocal agent_calls
                if model.startswith("gemini/"):
                    return response("probe terms")
                agent_calls += 1
                if agent_calls == 1:
                    return response(calls=[create_file_call()])
                raise RuntimeError("sensitive raw exception detail")

            roles = {"agents": {"coder": {"name": "Coder", "model": "ollama/test"}}}
            with patch("runner.SandboxStorage", return_value=storage), \
                 patch("runner.load_json", return_value=roles), \
                 patch("runner.safe_llm_completion", side_effect=complete), \
                 patch("runner.SandboxRagService") as rag_service, \
                 patch("runner.count_context_tokens", return_value=SimpleNamespace(tokens=8, mode="test")), \
                 patch("runner.trigger_regulator"), \
                 patch("builtins.print"):
                rag_service.return_value.query_relevant_docs.return_value = []
                runner.run_agent_loop("probe", resume=True)

            saved = storage.get_current_state("probe")
            artifact = Path(temp) / "probe" / "runner_probe.md"
            self.assertTrue(artifact.is_file())
            self.assertEqual(len(saved["tool_executions"]), 1)
            self.assertEqual(saved["tool_executions"][0]["tool_name"], "create_file")
            self.assertEqual(saved["last_runner_error"]["category"], "model_completion")
            self.assertEqual(saved["last_runner_error"]["exception_type"], "RuntimeError")
            self.assertEqual(saved["last_runner_error"]["stage"], "model_completion")
            self.assertNotIn("sensitive raw exception detail", json.dumps(saved))
            self.assertEqual(saved["status"], "in_progress")


if __name__ == "__main__":
    unittest.main()
