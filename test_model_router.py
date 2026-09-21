import unittest
from unittest.mock import patch

from model_router import (
    DEFAULT_OLLAMA_COMPLETION_TIMEOUT_SECONDS,
    EmbeddingRequest,
    ModelProviderExhausted,
    ModelRequest,
    LiteLLMAdapter,
    ModelRouter,
    ollama_completion_timeout_seconds,
    PrivacyPolicy,
    QualityRequirement,
    TaskClass,
    safe_telemetry_metadata,
)


class FakeAdapter:
    def __init__(self, outcomes=None):
        self.outcomes = {model: list(values) for model, values in (outcomes or {}).items()}
        self.calls = []

    def complete(self, model, messages, **kwargs):
        self.calls.append((model, messages, kwargs))
        outcome = self.outcomes.get(model, [f"ok:{model}"])
        if len(outcome) > 1:
            value = outcome.pop(0)
        else:
            value = outcome[0]
        if isinstance(value, Exception):
            raise value
        return value

    def embed(self, model, inputs):
        self.calls.append((model, inputs, {}))
        return {"data": [{"embedding": [1.0, 2.0]}]}


class LiteLLMAdapterTests(unittest.TestCase):
    def test_ollama_completion_preserves_tool_schemas(self):
        class Client:
            def completion(self, **kwargs):
                self.kwargs = kwargs
                return object()

        client = Client()
        adapter = LiteLLMAdapter(client)
        tools = [{"type": "function", "function": {"name": "create_file"}}]
        adapter.complete("ollama/qwen2.5:14b", [{"role": "user", "content": "write a file"}], tools=tools)

        self.assertEqual(client.kwargs["tools"], tools)
        self.assertEqual(client.kwargs["api_base"], "http://localhost:11434")

    def test_ollama_completion_has_a_bounded_operator_configurable_wait(self):
        class Client:
            def completion(self, **kwargs):
                self.kwargs = kwargs
                return object()

        client = Client()
        with patch.dict("os.environ", {"MINI_AGENT_OLLAMA_TIMEOUT_SECONDS": "900"}):
            LiteLLMAdapter(client).complete(
                "ollama/qwen2.5:14b", [{"role": "user", "content": "diagnostic"}]
            )

        self.assertEqual(client.kwargs["timeout"], 900.0)

    def test_ollama_completion_timeout_defaults_to_warmup_safe_bound(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertEqual(
                ollama_completion_timeout_seconds(), DEFAULT_OLLAMA_COMPLETION_TIMEOUT_SECONDS
            )

class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


class ModelRouterTests(unittest.TestCase):
    def setUp(self):
        self.offline_env = patch.dict("os.environ", {"MINI_AGENT_OFFLINE": "0"})
        self.offline_env.start()
        self.addCleanup(self.offline_env.stop)
        self.messages = [{"role": "user", "content": "example"}]

    def test_private_requests_never_dispatch_to_cloud_and_keep_response(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter, sleeper=lambda _: None)
        result = router.complete(ModelRequest(model="gemini/gemini-2.5-flash", messages=self.messages))
        self.assertEqual(result.selected_model, "ollama/qwen2.5:14b")
        self.assertEqual(result.response, "ok:ollama/qwen2.5:14b")
        self.assertEqual([call[0] for call in adapter.calls], ["ollama/qwen2.5:14b"])

    def test_offline_mode_forces_cloud_eligible_requests_to_local_models(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter, offline_mode=True, sleeper=lambda _: None)
        result = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            estimated_cost_usd=0.01, budget_usd=1.0,
            fallback_models=("openai/gpt-4o-mini",),
        ))
        self.assertEqual(result.selected_model, "ollama/qwen2.5:14b")
        self.assertTrue(all(call[0].startswith("ollama/") for call in adapter.calls))

    def test_offline_local_failure_never_attempts_cloud_fallback(self):
        adapter = FakeAdapter({"ollama/qwen2.5:14b": [ConnectionError("network is unavailable")]})
        router = ModelRouter(adapter, offline_mode=True, sleeper=lambda _: None)
        request = ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0, fallback_models=("openai/gpt-4o-mini",),
        )
        with self.assertRaises(ModelProviderExhausted):
            router.complete(request)
        self.assertTrue(adapter.calls)
        self.assertTrue(all(call[0].startswith("ollama/") for call in adapter.calls))

    def test_offline_mode_can_be_enabled_from_runtime_environment(self):
        with patch.dict("os.environ", {"MINI_AGENT_OFFLINE": "true"}):
            router = ModelRouter(FakeAdapter())
        self.assertTrue(router.offline_mode)
        with patch.dict("os.environ", {"MINI_AGENT_OFFLINE": "sometimes"}):
            with self.assertRaisesRegex(ValueError, "must be a boolean"):
                ModelRouter(FakeAdapter())

    def test_cloud_requires_privacy_permission_explicit_eligibility_and_budget(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter, sleeper=lambda _: None)
        denied = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            estimated_cost_usd=0.02, budget_usd=0.01,
        ))
        self.assertEqual(denied.selected_model, "ollama/qwen2.5:14b")
        adapter.calls.clear()
        allowed = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            estimated_cost_usd=0.01, budget_usd=0.01,
        ))
        self.assertEqual(allowed.selected_model, "gemini/gemini-2.5-flash")
        self.assertEqual(adapter.calls[0][0], "gemini/gemini-2.5-flash")

    def test_provider_allowlist_filters_candidates_before_adapter_dispatch(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter, sleeper=lambda _: None)
        result = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0, allowed_providers=["ollama"],
        ))
        self.assertEqual(result.provider, "ollama")
        self.assertEqual([call[0] for call in adapter.calls], ["ollama/qwen2.5:14b"])

        adapter.calls.clear()
        with self.assertRaises(ModelProviderExhausted):
            router.complete(ModelRequest(
                model="ollama/qwen2.5:14b", messages=self.messages,
                allowed_providers=[],
            ))
        self.assertEqual(adapter.calls, [])

    def test_token_budgets_block_before_adapter_dispatch(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter)
        with self.assertRaises(ModelProviderExhausted):
            router.complete(ModelRequest(
                model="ollama/qwen2.5:14b", messages=self.messages,
                estimated_context_tokens=80, max_request_tokens=100,
                extra_kwargs={"max_tokens": 21},
            ))
        self.assertEqual(adapter.calls, [])

        with self.assertRaises(ModelProviderExhausted):
            router.complete(ModelRequest(
                model="ollama/qwen2.5:14b", messages=self.messages,
                estimated_context_tokens=10, max_task_tokens=100,
                task_tokens_used=91, extra_kwargs={"max_tokens": 10},
            ))
        self.assertEqual(adapter.calls, [])

        router.complete(ModelRequest(
            model="ollama/qwen2.5:14b", messages=self.messages,
            estimated_context_tokens=10, max_request_tokens=20,
            max_task_tokens=100, task_tokens_used=80, extra_kwargs={"max_tokens": 10},
        ))
        self.assertEqual([call[0] for call in adapter.calls], ["ollama/qwen2.5:14b"])

    def test_context_bound_fails_before_dispatch(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter)
        with self.assertRaises(ModelProviderExhausted):
            router.complete(ModelRequest(
                model="ollama/qwen2.5:14b", messages=self.messages,
                estimated_context_tokens=20, max_context_tokens=10,
            ))
        self.assertEqual(adapter.calls, [])

    def test_task_and_quality_preferences_are_deterministic_and_still_policy_gated(self):
        adapter = FakeAdapter()
        router = ModelRouter(
            adapter, sleeper=lambda _: None,
            task_preferences={TaskClass.REVIEW: ("ollama/review-model",)},
        )
        result = router.complete(ModelRequest(
            model="openai/unconfigured-primary", messages=self.messages,
            task_class=TaskClass.REVIEW, quality=QualityRequirement.STANDARD,
        ))
        self.assertEqual(result.selected_model, "ollama/review-model")
        self.assertEqual(adapter.calls[0][0], "ollama/review-model")

        adapter.outcomes["openai/unconfigured-primary"] = [RuntimeError("unavailable")]
        high_quality = ModelRequest(
            model="openai/unconfigured-primary", messages=self.messages,
            task_class=TaskClass.PLANNING, quality=QualityRequirement.HIGH,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0,
        )
        selected = router.complete(high_quality)
        self.assertEqual(selected.selected_model, "gemini/gemini-2.5-flash")

    def test_transient_failure_retries_are_bounded_then_falls_back(self):
        adapter = FakeAdapter({"gemini/gemini-2.5-flash": [TimeoutError("secret=hidden"), TimeoutError("hidden")]})
        router = ModelRouter(adapter, sleeper=lambda _: None)
        result = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            estimated_cost_usd=0.0, budget_usd=1.0, max_retries=1,
        ))
        self.assertEqual(result.selected_model, "openai/gpt-4o-mini")
        self.assertEqual(result.attempts, 3)
        self.assertNotIn("hidden", str(result))

    def test_quota_is_consumed_and_expiry_restores_provider(self):
        clock = FakeClock()
        adapter = FakeAdapter()
        router = ModelRouter(adapter, clock=clock, sleeper=lambda _: None)
        router.set_quota("gemini", 1, ttl_seconds=10)
        request = ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0,
        )
        first = router.complete(request)
        second = router.complete(request)
        self.assertEqual(first.selected_model, "gemini/gemini-2.5-flash")
        self.assertEqual(second.selected_model, "openai/gpt-4o-mini")
        clock.now = 11
        third = router.complete(request)
        self.assertEqual(third.selected_model, "gemini/gemini-2.5-flash")

    def test_unhealthy_provider_is_skipped_until_health_state_expires(self):
        clock = FakeClock()
        adapter = FakeAdapter({"gemini/gemini-2.5-flash": [ConnectionError("offline")]})
        router = ModelRouter(adapter, clock=clock, sleeper=lambda _: None, health_ttl_seconds=5)
        request = ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0,
        )
        first = router.complete(request)
        self.assertEqual(first.selected_model, "openai/gpt-4o-mini")
        adapter.calls.clear()
        router.complete(request)
        self.assertEqual([call[0] for call in adapter.calls], ["openai/gpt-4o-mini"])
        clock.now = 6
        adapter.outcomes["gemini/gemini-2.5-flash"] = ["cloud-ok"]
        third = router.complete(request)
        self.assertEqual(third.selected_model, "gemini/gemini-2.5-flash")

    def test_provider_error_details_are_redacted(self):
        adapter = FakeAdapter({"ollama/qwen2.5:14b": [RuntimeError("token=do-not-leak")]})
        router = ModelRouter(adapter, sleeper=lambda _: None)
        with self.assertRaises(ModelProviderExhausted) as raised:
            router.complete(ModelRequest(
                model="ollama/qwen2.5:14b", messages=self.messages,
                fallback_eligible=False,
            ))
        self.assertNotIn("do-not-leak", str(raised.exception))

    def test_provider_credentials_cannot_be_injected_as_request_arguments(self):
        with self.assertRaisesRegex(ValueError, "external runtime configuration"):
            ModelRequest(
                model="openai/gpt-4o-mini", messages=self.messages,
                privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
                budget_usd=1.0, extra_kwargs={"api_key": "secret"},
            )

    def test_quota_error_falls_back_to_the_permitted_secondary_provider(self):
        adapter = FakeAdapter({
            "gemini/gemini-2.5-flash": [type("RateLimitError", (Exception,), {"status_code": 429})("quota")],
        })
        router = ModelRouter(adapter, sleeper=lambda _: None)
        result = router.complete(ModelRequest(
            model="gemini/gemini-2.5-flash", messages=self.messages,
            privacy_policy=PrivacyPolicy.CLOUD_ALLOWED, cloud_eligible=True,
            budget_usd=1.0,
        ))
        self.assertEqual(result.selected_model, "openai/gpt-4o-mini")
        self.assertEqual(result.fallback_from, "gemini/gemini-2.5-flash")

    def test_embedding_contract_stays_local_and_preserves_litellm_data_shape(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter)
        response = router.embed(EmbeddingRequest(inputs=["text"]))
        self.assertEqual(response["data"][0]["embedding"], [1.0, 2.0])
        self.assertEqual(adapter.calls[0][0], "ollama/nomic-embed-text")
        with self.assertRaises(ValueError):
            EmbeddingRequest(inputs=["private"], model="openai/text-embedding-3-small")

    def test_completion_passes_existing_litellm_arguments_unchanged(self):
        adapter = FakeAdapter()
        router = ModelRouter(adapter)
        router.complete(ModelRequest(
            model="ollama/qwen2.5:14b", messages=self.messages,
            extra_kwargs={"max_tokens": 800, "temperature": 0.2},
        ))
        self.assertEqual(adapter.calls[0][2], {"max_tokens": 800, "temperature": 0.2})

    def test_telemetry_metadata_drops_payloads_and_secrets(self):
        safe = safe_telemetry_metadata({
            "provider": "ollama",
            "task_class": "coding",
            "prompt": "private source excerpt",
            "response": "model output",
            "api_key": "secret-token",
            "fallback_from": "gemini/model",
        })
        self.assertEqual(safe, {
            "provider": "ollama",
            "task_class": "coding",
            "fallback_from": "gemini/model",
        })


if __name__ == "__main__":
    unittest.main()
