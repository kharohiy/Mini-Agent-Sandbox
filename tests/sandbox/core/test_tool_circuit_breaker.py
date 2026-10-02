import json
import os
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import runner
from tests.sandbox.core.test_documentation_policy import CONTRACT, HITS


def make_call(index):
    return SimpleNamespace(
        id=f"call-{index}",
        function=SimpleNamespace(name="unknown_tool", arguments=json.dumps({"index": index})),
    )


def make_response(calls=None, content="query terms"):
    message = SimpleNamespace(content=content, tool_calls=calls)
    message.model_dump = lambda: {"role": "assistant", "content": content}
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


class ToolCircuitBreakerTests(unittest.TestCase):
    def test_limit_blocks_next_call_and_persists_non_resumable_incident_in_both_modes(self):
        for task_mode, limit, mode_calls in (("code", 2, 3), ("documentation", 3, 4)):
            with self.subTest(task_mode=task_mode), tempfile.TemporaryDirectory() as temp:
                storage = runner.SandboxStorage(temp)
                state = {
                    "status": "in_progress",
                    "task_mode": task_mode,
                    "task": "Create architecture_summary.md" if task_mode == "documentation" else "Inspect source",
                    "current_turn": "coder",
                    "memory": [],
                    "tool_executions": [],
                    "metrics": {"total_cost": 0.0},
                    "agent_steps": 0,
                    "user_lang": "en",
                }
                if task_mode == "documentation":
                    state.update({
                        "documentation_contract": CONTRACT,
                        "project_id": "demo",
                    })
                storage.save_state("breaker-user", state)
                tool_response = make_response([make_call(index) for index in range(mode_calls)])
                model_calls = []

                def complete(model, *_args, **_kwargs):
                    model_calls.append(model)
                    if model.startswith("ollama/"):
                        return tool_response
                    return make_response(content="source terms")

                roles = {"agents": {"coder": {"name": "Coder", "model": "ollama/test"}}}
                with patch("runner.SandboxStorage", return_value=storage), \
                     patch("runner.load_json", return_value=roles), \
                     patch("runner.safe_llm_completion", side_effect=complete), \
                     patch("runner.SandboxRagService") as rag_cls, \
                     patch("runner.retrieve_project_context_with_telemetry", return_value=HITS), \
                     patch("runner.format_retrieval_context", return_value="project evidence"), \
                     patch("runner.count_context_tokens", return_value=SimpleNamespace(tokens=8, mode="test")), \
                     patch("runner.MAX_TOOL_CALLS_PER_TURN", limit), \
                     patch("runner.agent_tools_for_task_mode", return_value=[{"type": "function"}]), \
                     patch("runner.authorize_tool_arguments", side_effect=lambda _name, args, *_rest: (True, args)), \
                     patch("runner.trigger_regulator") as regulator, \
                     patch("builtins.print") as output:
                    rag_cls.return_value.query_relevant_docs.return_value = []
                    runner.run_agent_loop("breaker-user", resume=True)

                saved = storage.get_current_state("breaker-user")
                incident = saved["breaker_incident"]
                self.assertEqual(saved["status"], "breaker_blocked")
                self.assertEqual(saved["current_turn"], "coder")
                self.assertEqual(len(saved["tool_executions"]), limit)
                self.assertEqual(incident["limit"], limit)
                self.assertEqual(incident["attempted_call_number"], limit + 1)
                self.assertEqual(incident["processed_calls_before_block"], limit)
                self.assertEqual(incident["task_mode"], task_mode)
                self.assertEqual(sum(model.startswith("ollama/") for model in model_calls), 1)
                self.assertIn("Incident recorded", str(output.call_args_list))
                self.assertIn("not rolled back", str(output.call_args_list))
                regulator.assert_not_called()
                with self.assertRaisesRegex(ValueError, "cannot be resumed"):
                    runner._load_resumable_state(storage, "breaker-user", {"coder": {}})

    def test_session_reset_clears_breaker_state_without_touching_user_facts(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            user_dir = storage._get_user_dir("breaker-user")
            storage.save_state("breaker-user", {
                "status": "breaker_blocked",
                "breaker_incident": {"type": "tool_call_limit_exceeded"},
            })
            facts_path = user_dir / "project_facts.json"
            facts_path.write_text("[]", encoding="utf-8")

            self.assertTrue(storage.reset_session_state("breaker-user"))
            self.assertEqual(storage.get_current_state("breaker-user")["status"], "pending")
            self.assertTrue(facts_path.exists())


if __name__ == "__main__":
    unittest.main()
