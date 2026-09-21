"""Provider-neutral, deterministic routing contracts for completions and embeddings.

The router contains no provider SDK and never logs request content. Runtime
credentials remain the responsibility of the configured adapter (LiteLLM reads
provider keys from its normal environment configuration).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import os
import time
from typing import Any, Callable, Mapping, Protocol, Sequence


DEFAULT_OLLAMA_COMPLETION_TIMEOUT_SECONDS = 600.0
OLLAMA_COMPLETION_TIMEOUT_ENV = "MINI_AGENT_OLLAMA_TIMEOUT_SECONDS"


def ollama_completion_timeout_seconds() -> float:
    """Return the bounded local-provider wait configured by the operator.

    A synchronous completion without an HTTP timeout can leave a runner turn
    pending forever when Ollama accepts a request but inference never begins.
    The default deliberately permits normal local model warm-up; operators may
    raise it for slower hardware without changing code or routing policy.
    """
    raw_value = os.getenv(OLLAMA_COMPLETION_TIMEOUT_ENV, "").strip()
    if not raw_value:
        return DEFAULT_OLLAMA_COMPLETION_TIMEOUT_SECONDS
    try:
        timeout = float(raw_value)
    except ValueError as error:
        raise ValueError(
            f"{OLLAMA_COMPLETION_TIMEOUT_ENV} must be a number of seconds"
        ) from error
    if not 1.0 <= timeout <= 3600.0:
        raise ValueError(
            f"{OLLAMA_COMPLETION_TIMEOUT_ENV} must be between 1 and 3600 seconds"
        )
    return timeout


class TaskClass(str, Enum):
    PLANNING = "planning"
    CODING = "coding"
    REVIEW = "review"
    EMBEDDING = "embedding"


class PrivacyPolicy(str, Enum):
    LOCAL_ONLY = "local_only"
    CLOUD_ALLOWED = "cloud_allowed"


class QualityRequirement(str, Enum):
    STANDARD = "standard"
    HIGH = "high"


class ModelRoutingError(RuntimeError):
    """Safe-to-surface router failure; never includes a provider error string."""


class ModelProviderExhausted(ModelRoutingError):
    def __init__(self, failures: Sequence[tuple[str, str]]):
        self.failures = tuple(failures)
        summary = ", ".join(f"{model}:{error_type}" for model, error_type in failures)
        super().__init__(f"No eligible model provider succeeded ({summary or 'policy denied all routes'}).")


def safe_telemetry_metadata(metadata: Mapping[str, Any] | None) -> dict[str, str | int | float]:
    """Keep only bounded operational dimensions; payloads and secrets are dropped."""
    if not metadata:
        return {}
    safe: dict[str, str | int | float] = {}
    for key in ("provider", "task_class", "quality", "attempts", "fallback_from"):
        value = metadata.get(key)
        if isinstance(value, (str, int, float)) and len(str(value)) <= 128:
            safe[key] = value
    return safe


@dataclass(frozen=True)
class ModelRequest:
    model: str
    messages: Sequence[Mapping[str, Any]]
    task_class: TaskClass = TaskClass.CODING
    privacy_policy: PrivacyPolicy = PrivacyPolicy.LOCAL_ONLY
    cloud_eligible: bool = False
    quality: QualityRequirement = QualityRequirement.STANDARD
    estimated_context_tokens: int | None = None
    max_context_tokens: int = 131_072
    estimated_cost_usd: float = 0.0
    budget_usd: float = 0.0
    fallback_eligible: bool = True
    fallback_models: Sequence[str] = ()
    max_retries: int = 1
    allowed_providers: Sequence[str] | None = None
    max_request_tokens: int | None = None
    max_task_tokens: int | None = None
    task_tokens_used: int = 0
    extra_kwargs: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if isinstance(self.task_class, str):
            object.__setattr__(self, "task_class", TaskClass(self.task_class))
        if isinstance(self.privacy_policy, str):
            object.__setattr__(self, "privacy_policy", PrivacyPolicy(self.privacy_policy))
        if isinstance(self.quality, str):
            object.__setattr__(self, "quality", QualityRequirement(self.quality))
        if not isinstance(self.model, str) or not self.model.strip():
            raise ValueError("model is required")
        if not isinstance(self.messages, Sequence) or isinstance(self.messages, (str, bytes)):
            raise ValueError("messages must be a sequence")
        if self.max_retries < 0 or self.max_retries > 2:
            raise ValueError("max_retries must be between 0 and 2")
        if self.max_context_tokens <= 0:
            raise ValueError("max_context_tokens must be positive")
        if self.estimated_cost_usd < 0 or self.budget_usd < 0:
            raise ValueError("cost and budget must be non-negative")
        if self.allowed_providers is not None:
            if (not isinstance(self.allowed_providers, Sequence)
                    or isinstance(self.allowed_providers, (str, bytes)) or not all(
                isinstance(provider, str) and provider for provider in self.allowed_providers
            )):
                raise ValueError("allowed_providers must be a sequence of provider names")
            object.__setattr__(
                self, "allowed_providers", tuple(dict.fromkeys(
                    provider.lower() for provider in self.allowed_providers
                ))
            )
        for value, label in (
            (self.max_request_tokens, "max_request_tokens"),
            (self.max_task_tokens, "max_task_tokens"),
            (self.task_tokens_used, "task_tokens_used"),
        ):
            if value is not None and (type(value) is not int or value < 0):
                raise ValueError(f"{label} must be a non-negative integer")
        if "max_tokens" in self.extra_kwargs:
            max_tokens = self.extra_kwargs["max_tokens"]
            if type(max_tokens) is not int or max_tokens < 0:
                raise ValueError("max_tokens must be a non-negative integer")
        secret_kwargs = {"api_key", "apikey", "access_token", "auth_token", "authorization"}
        if secret_kwargs.intersection(str(key).lower() for key in self.extra_kwargs):
            raise ValueError("provider credentials must come from external runtime configuration")

    @property
    def context_tokens(self) -> int:
        if self.estimated_context_tokens is not None:
            return max(0, self.estimated_context_tokens)
        return sum(len(str(message.get("content", ""))) for message in self.messages) // 4

    @property
    def request_tokens(self) -> int:
        return self.context_tokens + self.extra_kwargs.get("max_tokens", 0)


@dataclass(frozen=True)
class EmbeddingRequest:
    inputs: Sequence[str]
    model: str = "ollama/nomic-embed-text"
    privacy_policy: PrivacyPolicy = PrivacyPolicy.LOCAL_ONLY
    max_items: int = 10_000

    def __post_init__(self):
        if self.privacy_policy is not PrivacyPolicy.LOCAL_ONLY:
            raise ValueError("embeddings are local-only in this phase")
        if self.model != "ollama/nomic-embed-text":
            raise ValueError("embedding model is fixed to local ollama/nomic-embed-text")
        if len(self.inputs) > self.max_items:
            raise ValueError("embedding input exceeds configured item limit")
        if any(not isinstance(item, str) for item in self.inputs):
            raise ValueError("embedding inputs must be text")


@dataclass(frozen=True)
class ModelResult:
    response: Any
    selected_model: str
    provider: str
    fallback_from: str | None
    attempts: int


class ModelAdapter(Protocol):
    def complete(self, model: str, messages: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any: ...
    def embed(self, model: str, inputs: Sequence[str]) -> Any: ...


class LiteLLMAdapter:
    """Existing LiteLLM dependency, wrapped behind the provider-neutral contract."""

    def __init__(self, client: Any = None):
        if client is None:
            import litellm
            client = litellm
        self.client = client

    def complete(self, model: str, messages: Sequence[Mapping[str, Any]], **kwargs: Any) -> Any:
        args = {"model": model, "messages": messages, **kwargs}
        if model.startswith("ollama/"):
            args.setdefault("api_base", "http://localhost:11434")
            args.setdefault("timeout", ollama_completion_timeout_seconds())
        elif "-lite" in model:
            args["tools"] = None
        return self.client.completion(**args)

    def embed(self, model: str, inputs: Sequence[str]) -> Any:
        return self.client.embedding(
            model=model,
            input=inputs,
            api_base="http://localhost:11434",
        )


class ModelRouter:
    """Select providers in stable order and enforce privacy, budget, quota and health."""

    def __init__(
        self,
        adapter: ModelAdapter,
        *,
        local_fallback: str = "ollama/qwen2.5:14b",
        cloud_fallbacks: Sequence[str] = ("gemini/gemini-2.5-flash", "openai/gpt-4o-mini"),
        task_preferences: Mapping[TaskClass, Sequence[str]] | None = None,
        health_ttl_seconds: float = 600,
        offline_mode: bool | None = None,
        sleeper: Callable[[float], None] = time.sleep,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.adapter = adapter
        self.local_fallback = local_fallback
        self.cloud_fallbacks = tuple(cloud_fallbacks)
        self.task_preferences = {
            task: tuple(models)
            for task, models in (task_preferences or {
                TaskClass.PLANNING: (local_fallback,),
                TaskClass.CODING: (local_fallback,),
                TaskClass.REVIEW: (local_fallback,),
                TaskClass.EMBEDDING: (),
            }).items()
        }
        self.health_ttl_seconds = max(0.0, health_ttl_seconds)
        if offline_mode is None:
            configured_offline = os.getenv("MINI_AGENT_OFFLINE", "").strip().lower()
            if configured_offline in {"", "0", "false", "no", "off"}:
                offline_mode = False
            elif configured_offline in {"1", "true", "yes", "on"}:
                offline_mode = True
            else:
                raise ValueError("MINI_AGENT_OFFLINE must be a boolean value")
        self.offline_mode = bool(offline_mode)
        self.sleeper = sleeper
        self.clock = clock
        self._unhealthy_until: dict[str, float] = {}
        self._quota: dict[str, tuple[int, float | None]] = {}

    @staticmethod
    def provider_for(model: str) -> str:
        return model.split("/", 1)[0].lower() if "/" in model else "unknown"

    def set_quota(self, provider: str, remaining_requests: int, *, ttl_seconds: float | None = None) -> None:
        if remaining_requests < 0:
            raise ValueError("remaining_requests must be non-negative")
        expires = None if ttl_seconds is None else self.clock() + max(0.0, ttl_seconds)
        self._quota[provider.lower()] = (remaining_requests, expires)

    def _quota_remaining(self, provider: str) -> int | None:
        entry = self._quota.get(provider)
        if entry is None:
            return None
        remaining, expires = entry
        if expires is not None and self.clock() >= expires:
            del self._quota[provider]
            return None
        return remaining

    def _eligible(self, model: str, request: ModelRequest) -> bool:
        provider = self.provider_for(model)
        is_local = provider == "ollama"
        if request.allowed_providers is not None and provider not in request.allowed_providers:
            return False
        if self.offline_mode and not is_local:
            return False
        if not is_local and not (request.privacy_policy is PrivacyPolicy.CLOUD_ALLOWED and request.cloud_eligible):
            return False
        if request.context_tokens > request.max_context_tokens:
            return False
        if (request.max_request_tokens is not None
                and request.request_tokens > request.max_request_tokens):
            return False
        if (request.max_task_tokens is not None
                and request.task_tokens_used + request.request_tokens > request.max_task_tokens):
            return False
        if not is_local and (request.budget_usd <= 0 or request.estimated_cost_usd > request.budget_usd):
            return False
        if self.clock() < self._unhealthy_until.get(provider, 0.0):
            return False
        remaining = self._quota_remaining(provider)
        return remaining is None or remaining > 0

    def _models(self, request: ModelRequest) -> list[str]:
        ordered: list[str] = [request.model]
        if request.fallback_eligible:
            ordered.extend(request.fallback_models)
            if request.quality is QualityRequirement.HIGH:
                ordered.extend(self.cloud_fallbacks)
            elif request.privacy_policy is PrivacyPolicy.CLOUD_ALLOWED and request.cloud_eligible:
                ordered.extend(self.cloud_fallbacks)
            ordered.extend(self.task_preferences.get(request.task_class, ()))
            ordered.append(self.local_fallback)
        return list(dict.fromkeys(model for model in ordered if self._eligible(model, request)))

    @staticmethod
    def _is_transient(error: Exception) -> bool:
        name = type(error).__name__.lower()
        status = getattr(error, "status_code", None)
        return status == 429 or any(marker in name for marker in ("timeout", "connection", "ratelimit", "temporar"))

    def complete(self, request: ModelRequest) -> ModelResult:
        models = self._models(request)
        failures: list[tuple[str, str]] = []
        attempted = 0
        for model in models:
            provider = self.provider_for(model)
            retries = request.max_retries
            while True:
                attempted += 1
                try:
                    response = self.adapter.complete(model, request.messages, **dict(request.extra_kwargs))
                    remaining = self._quota_remaining(provider)
                    if remaining is not None:
                        _, expires = self._quota[provider]
                        self._quota[provider] = (max(0, remaining - 1), expires)
                    return ModelResult(
                        response=response,
                        selected_model=model,
                        provider=provider,
                        fallback_from=request.model if model != request.model else None,
                        attempts=attempted,
                    )
                except Exception as error:
                    error_type = type(error).__name__
                    failures.append((model, error_type))
                    if self._is_transient(error):
                        self._unhealthy_until[provider] = self.clock() + self.health_ttl_seconds
                        if getattr(error, "status_code", None) == 429 or "ratelimit" in error_type.lower():
                            self.set_quota(provider, 0, ttl_seconds=self.health_ttl_seconds)
                    if not self._is_transient(error) or retries <= 0:
                        break
                    self.sleeper(min(0.25 * (2 ** (request.max_retries - retries)), 1.0))
                    retries -= 1
        raise ModelProviderExhausted(failures)

    def embed(self, request: EmbeddingRequest) -> Any:
        if not request.model.startswith("ollama/"):
            raise ModelRoutingError("Embedding model must use the configured local Ollama provider.")
        try:
            return self.adapter.embed(request.model, request.inputs)
        except Exception as error:
            raise ModelProviderExhausted(((request.model, type(error).__name__),)) from None


_default_router: ModelRouter | None = None


def get_default_model_router() -> ModelRouter:
    """Return the shared production router; tests should inject their own adapter."""
    global _default_router
    if _default_router is None:
        _default_router = ModelRouter(LiteLLMAdapter())
    return _default_router
