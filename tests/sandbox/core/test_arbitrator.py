import sys
import os
from copy import deepcopy
from contextlib import redirect_stdout
from io import StringIO
import unittest
from unittest.mock import patch

# LiteLLM normally refreshes its bundled model metadata during import. Keep
# fake-only unit tests fully offline while retaining the packaged fallback map.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import runner
from model_router import ModelResult, PrivacyPolicy

class MockResponse:
    class Message:
        def __init__(self, content):
            self.content = content
            self.tool_calls = None
        def model_dump(self):
            return {"role": "assistant", "content": self.content}
            
    class Choice:
        def __init__(self, content):
            self.message = MockResponse.Message(content)
            
    class Usage:
        total_tokens = 10
        
    def __init__(self, content):
        self.choices = [MockResponse.Choice(content)]
        self.usage = MockResponse.Usage()

def mock_llm_completion(model, messages, **kwargs):
    if not model.startswith("ollama/"):
        return MockResponse("mocked")

    mock_llm_completion.agent_calls += 1
    agent_call = mock_llm_completion.agent_calls
    if agent_call == 7:
        return MockResponse("ARBITRATOR DECISION: I have reviewed the logs. We will use the Repository pattern.")
    if agent_call in {1, 3, 5, 8}:
        return MockResponse("```kotlin\nfun add(a: Int, b: Int) = a + b\n```")
    if agent_call == 9:
        mock_llm_completion.reviewed_after_arbitration = True
        return MockResponse('{"decision":"APPROVE"}')
    if agent_call in {2, 4, 6}:
        # Reject until the Arbitrator has made an architectural decision.
        return MockResponse('{"decision":"REJECTED","reason":"Needs rework"}')
    
    return MockResponse("mocked")

def test_deadlock_arbitration():
    print("Starting Arbitration test...")
    mock_llm_completion.agent_calls = 0
    mock_llm_completion.reviewed_after_arbitration = False
    # Mock safe_llm_completion
    with patch('runner.safe_llm_completion', side_effect=mock_llm_completion), \
         patch('runner.SandboxRagService') as rag_service_cls:
        rag_service_cls.return_value.query_relevant_docs.return_value = []
        # We also need to mock validate_generated_code so it doesn't fail Ruff/Semgrep and loop infinitely
        with patch('runner.validate_generated_code', return_value=(True, "")):
            # Force the language gateway to just return english
            with patch('runner.language_gateway', return_value=("Write code", "en")):
                
                # Capture print statements to verify the output flow
                import io
                capturedOutput = io.StringIO()
                sys.stdout = capturedOutput
                
                # Fake input for the loop
                sys.stdin = io.StringIO("Write code\n\n")
                
                runner.run_agent_loop("test_user_arbitrator")
                
                sys.stdout = sys.__stdout__
                output = capturedOutput.getvalue()
                
                # Check for key phrases in output
                assert "Deadlock detected. Invoking Architectural Arbitrator" in output, "Arbitrator was not invoked!"
                assert "ARBITRATOR DECISION:" in output, "Arbitrator did not provide a decision!"
                assert "🎯 TASK COMPLETED" in output, "Task did not complete gracefully!"
                assert "Graceful Abandonment" not in output, "Hit hard step limit instead of resolving via Arbitrator!"
                assert mock_llm_completion.reviewed_after_arbitration, "Reviewer was bypassed after Arbitrator!"
                
                print("Arbitrated Debate logic passed successfully!")


class ModelCompatibilityTests(unittest.TestCase):
    def test_compatibility_facade_returns_original_response_shape_and_defaults_local(self):
        response = MockResponse("compatible")

        class FakeRouter:
            def complete(self, request):
                self.request = request
                return ModelResult(response, request.model, "ollama", None, 1)

        fake_router = FakeRouter()

        class FakeVault:
            def save_mapping(self, _mapping):
                pass

        with patch.object(runner, "MODEL_ROUTER", fake_router), \
             patch.object(runner.guardrail, "run", side_effect=lambda text, _user: text), \
             patch.object(runner.guardrail, "extract_vault_mapping", return_value={}), \
             patch.object(runner, "get_user_vault", return_value=FakeVault()):
            actual = runner.safe_llm_completion(
                "ollama/qwen2.5:14b", [{"role": "user", "content": "hello"}]
            )

        self.assertIs(actual, response)
        self.assertEqual(actual.choices[0].message.content, "compatible")
        self.assertEqual(fake_router.request.privacy_policy, PrivacyPolicy.LOCAL_ONLY)
        self.assertFalse(fake_router.request.cloud_eligible)
        self.assertEqual(fake_router.request.extra_kwargs["max_tokens"], 1500)


class ResumeIntegrationTests(unittest.TestCase):
    def test_resume_restores_saved_task_and_retrieves_its_project_context(self):
        saved = {
            "status": "in_progress",
            "task": "Continue the saved navigation fix",
            "user_lang": "en",
            "current_turn": "reviewer",
            "memory": [
                {"role": "user", "content": "NEW TASK FROM USER: Continue the saved navigation fix"},
                {"role": "coder", "content": "Updated the route mapping."},
            ],
            "tool_executions": [],
            "project_id": "demo-project",
            "agent_steps": 4,
            "metrics": {"total_cost": 0.0},
        }

        class ResumeStorage:
            def __init__(self, base_dir):
                self.state = deepcopy(saved)
                self.saved_state = None

            def get_current_state(self, _user_id):
                return deepcopy(self.state)

            def assemble_context_window(self, _user_id, _task, system_prompt, _state):
                return system_prompt

            def save_state(self, _user_id, state):
                self.saved_state = deepcopy(state)

            def update_state_metrics(self, _user_id, state, *_metrics):
                self.saved_state = deepcopy(state)

            def ingest_and_extract_facts(self, _user_id, _memory):
                return None

        storage_instances = []

        def make_storage(base_dir):
            instance = ResumeStorage(base_dir)
            storage_instances.append(instance)
            return instance

        retrieval_calls = []

        def retrieve(project_id, query, *, top_k):
            retrieval_calls.append((project_id, query, top_k))
            return [{"text": "saved project evidence"}]

        def completion(model, messages, **_kwargs):
            if "STRUCTURED VERDICT REQUIRED" in messages[0]["content"]:
                return MockResponse('{"decision":"APPROVE"}')
            if model.endswith("flash-lite"):
                return MockResponse("route, navigation")
            return MockResponse("Task resumed successfully.")

        roles = {"agents": {"reviewer": {
            "name": "Reviewer", "model": "ollama/qwen2.5:14b", "system_prompt": "Review saved work."
        }}}
        with patch("runner.load_json", return_value=roles), \
             patch("runner.SandboxStorage", side_effect=make_storage), \
             patch("runner.safe_llm_completion", side_effect=completion), \
             patch("runner.retrieve_project_context", side_effect=retrieve), \
             patch("runner.format_retrieval_context", return_value="saved project evidence"), \
             patch("runner.trigger_regulator"), \
             patch("runner.reverse_language_gateway", side_effect=lambda text, _lang: text), \
             patch("builtins.input", side_effect=AssertionError("resume must not prompt for a new task")):
            with redirect_stdout(StringIO()):
                runner.run_agent_loop("resume-user", resume=True)

        self.assertEqual(retrieval_calls, [("demo-project", f"{saved['task']}, route, navigation", 4)])
        self.assertEqual(storage_instances[0].saved_state["status"], "completed")
        self.assertEqual(storage_instances[0].saved_state["agent_steps"], 5)


class ResumeStateValidationTests(unittest.TestCase):
    def test_only_interrupted_structurally_valid_tasks_can_resume(self):
        class Storage:
            def __init__(self, state):
                self.state = state

            def get_current_state(self, _user_id):
                return self.state

        valid = {
            "status": "in_progress", "task": "saved task", "memory": [],
            "tool_executions": [], "current_turn": "coder", "metrics": {},
        }
        restored = runner._load_resumable_state(Storage(valid), "user", {"coder": {}})
        self.assertIs(restored, valid)
        for invalid in (
            {**valid, "status": "completed"},
            {**valid, "task": ""},
            {**valid, "memory": None},
            {**valid, "memory": ["bad entry"]},
            {**valid, "current_turn": "unknown"},
            {**valid, "metrics": []},
            {**valid, "metrics": {"total_cost": "free"}},
            {**valid, "agent_steps": -1},
        ):
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    runner._load_resumable_state(Storage(invalid), "user", {"coder": {}})

if __name__ == "__main__":
    test_deadlock_arbitration()
