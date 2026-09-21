from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import runner
from model_router import ModelProviderExhausted, ModelResult
from project_policy import default_policy


class RunnerProjectTelemetryTests(unittest.TestCase):
    def test_retrieval_records_only_outcome_and_not_query_or_hits(self):
        hits = [{"source": "private/app.py", "text": "secret source excerpt"}]
        with patch("runner.retrieve_project_context", return_value=hits), patch(
            "runner.record_project_telemetry"
        ) as record:
            self.assertEqual(
                runner.retrieve_project_context_with_telemetry("demo--123", "private query", top_k=4),
                hits,
            )
        record.assert_called_once_with("demo--123", event="retrieval", outcome="success")
        self.assertNotIn("private", repr(record.call_args))

    def test_failed_retrieval_records_failure_without_the_query(self):
        with patch("runner.retrieve_project_context", side_effect=RuntimeError("unavailable")), patch(
            "runner.record_project_telemetry"
        ) as record:
            with self.assertRaisesRegex(RuntimeError, "unavailable"):
                runner.retrieve_project_context_with_telemetry("demo--123", "private query")
        record.assert_called_once_with("demo--123", event="retrieval", outcome="failure")
        self.assertNotIn("private", repr(record.call_args))

    def test_model_completion_records_bounded_project_metadata_only(self):
        response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content=None))],
            usage=SimpleNamespace(prompt_tokens=7, completion_tokens=5),
        )
        result = ModelResult(response, "ollama/qwen2.5:14b", "ollama", None, 1)
        vault = Mock()
        with patch("runner.ProjectPolicyStore") as policy_store, patch.object(
            runner.MODEL_ROUTER, "complete", return_value=result
        ) as complete, patch(
            "runner.get_user_vault", return_value=vault
        ), patch.object(runner.guardrail, "run", side_effect=lambda text, _: text), patch.object(
            runner.guardrail, "extract_vault_mapping", return_value={}
        ), patch("runner.log_prediction_telemetry"), patch(
            "runner.record_project_telemetry"
        ) as record:
            policy_store.return_value.get.return_value = default_policy() | {
                "model_providers": ["ollama"],
                "budgets": {"max_task_tokens": 10_000, "max_request_tokens": 10_000},
            }
            self.assertIs(
                runner.safe_llm_completion(
                    "ollama/qwen2.5:14b",
                    [{"role": "user", "content": "private prompt"}],
                    user_id="telemetry-test",
                    project_id="demo--123",
                ),
                response,
            )
        record.assert_called_once_with(
            "demo--123", event="model", outcome="success", provider="ollama", tokens=12
        )
        request = complete.call_args.args[0]
        self.assertEqual(request.allowed_providers, ("ollama",))
        self.assertEqual(request.max_request_tokens, 10_000)
        self.assertEqual(request.max_task_tokens, 10_000)
        self.assertNotIn("private", repr(record.call_args))

    def test_model_failure_records_only_provider_and_outcome(self):
        vault = Mock()
        exhausted = ModelProviderExhausted([("ollama/qwen2.5:14b", "ConnectionError")])
        with patch("runner.ProjectPolicyStore") as policy_store, patch.object(
            runner.MODEL_ROUTER, "complete", side_effect=exhausted
        ), patch(
            "runner.get_user_vault", return_value=vault
        ), patch.object(runner.guardrail, "run", side_effect=lambda text, _: text), patch.object(
            runner.guardrail, "extract_vault_mapping", return_value={}
        ), patch("runner.log_prediction_telemetry"), patch(
            "runner.record_project_telemetry"
        ) as record:
            policy_store.return_value.get.return_value = default_policy() | {
                "model_providers": ["ollama"],
                "budgets": {"max_task_tokens": 10_000, "max_request_tokens": 10_000},
            }
            with self.assertRaises(ModelProviderExhausted):
                runner.safe_llm_completion(
                    "ollama/qwen2.5:14b",
                    [{"role": "user", "content": "private prompt"}],
                    user_id="telemetry-test",
                    project_id="demo--123",
                )
        record.assert_called_once_with(
            "demo--123", event="model", outcome="failure", provider="ollama"
        )
        self.assertNotIn("private", repr(record.call_args))

if __name__ == "__main__":
    unittest.main()
