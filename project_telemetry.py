"""Project-scoped telemetry with a strict, payload-free event schema."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from project_registry import ProjectRegistry

EVENT_TYPES = {"validation", "retrieval", "model"}
OUTCOMES = {"validated", "rejected", "blocked", "success", "failure"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class ProjectTelemetryStore:
    def __init__(self, registry: ProjectRegistry | None = None):
        self.registry = registry or ProjectRegistry()

    def record(self, project_id: str, *, event: str, outcome: str,
               provider: str | None = None, tokens: int = 0, cost_usd: float = 0.0) -> dict[str, Any]:
        self.registry.get(project_id)
        if event not in EVENT_TYPES or outcome not in OUTCOMES:
            raise ValueError("telemetry event or outcome is unsupported")
        if provider is not None and provider not in {"ollama", "openai", "gemini"}:
            raise ValueError("telemetry provider is unsupported")
        if type(tokens) is not int or not 0 <= tokens <= 10_000_000:
            raise ValueError("telemetry tokens must be bounded integers")
        if isinstance(cost_usd, bool) or not isinstance(cost_usd, (int, float)) or not 0 <= cost_usd <= 1_000_000:
            raise ValueError("telemetry cost must be bounded")
        entry = {"event": event, "outcome": outcome, "provider": provider, "tokens": tokens,
                 "cost_usd": float(cost_usd), "created_at": _now()}
        path = self._path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as telemetry_file:
            telemetry_file.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry

    def summary(self, project_id: str) -> dict[str, Any]:
        self.registry.get(project_id)
        entries = self._entries(project_id)
        return {"events": len(entries),
                "by_event": dict(sorted(Counter(entry["event"] for entry in entries).items())),
                "by_outcome": dict(sorted(Counter(entry["outcome"] for entry in entries).items())),
                "by_provider": dict(sorted(Counter(entry["provider"] for entry in entries if entry["provider"]).items())),
                "tokens": sum(entry["tokens"] for entry in entries),
                "cost_usd": round(sum(entry["cost_usd"] for entry in entries), 6)}

    def _path(self, project_id: str) -> Path:
        return self.registry.state_dir(project_id) / "telemetry" / "events.jsonl"

    def _entries(self, project_id: str) -> list[dict[str, Any]]:
        path = self._path(project_id)
        return [] if not path.exists() else [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]
