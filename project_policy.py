"""Versioned, default-deny project policy storage for Phase 8 governance."""
from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from project_registry import ProjectRegistry


SCHEMA_VERSION = 1
ALLOWED_PROVIDERS = {"ollama", "openai", "gemini"}
AUTO_APPLY_LEVELS = {"never"}
PROFILE_RE = re.compile(r"[A-Za-z0-9_.:-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def default_policy() -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "allowed_workspace_paths": [],
        "validation_profiles": [],
        "model_providers": [],
        "budgets": {"max_task_tokens": 0, "max_request_tokens": 0},
        "retention": {"audit_days": 30, "telemetry_days": 30},
        "auto_apply_level": "never",
    }


class ProjectPolicyStore:
    def __init__(self, registry: ProjectRegistry | None = None):
        self.registry = registry or ProjectRegistry()

    def get(self, project_id: str) -> dict[str, Any]:
        self.registry.get(project_id)
        path = self._policy_path(project_id)
        if not path.exists():
            return default_policy()
        return self._validate(json.loads(path.read_text(encoding="utf-8")))

    def update(self, project_id: str, policy: dict[str, Any]) -> dict[str, Any]:
        self.registry.get(project_id)
        validated = self._validate(policy)
        path = self._policy_path(project_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(validated, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        digest = hashlib.sha256(json.dumps(validated, sort_keys=True).encode("utf-8")).hexdigest()
        with self._audit_path(project_id).open("a", encoding="utf-8") as audit_file:
            audit_file.write(
                json.dumps({"action": "policy_updated", "schema_version": SCHEMA_VERSION, "sha256": digest, "created_at": _now()}) + "\n"
            )
        return validated

    def audit(self, project_id: str) -> list[dict[str, Any]]:
        self.registry.get(project_id)
        path = self._audit_path(project_id)
        if not path.exists():
            return []
        return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line]

    def require_allowed_workspace_paths(self, project_id: str, paths: list[str]) -> None:
        """Fail closed unless every patch path is inside the project allowlist."""
        allowed_paths = self.get(project_id)["allowed_workspace_paths"]
        if not allowed_paths:
            raise ValueError("project policy does not allow any workspace paths")
        disallowed = [
            path for path in paths
            if not any(path == allowed or path.startswith(allowed + "/") for allowed in allowed_paths)
        ]
        if disallowed:
            raise ValueError("patch path is not allowed by the project workspace policy")

    def _policy_path(self, project_id: str) -> Path:
        return self.registry.state_dir(project_id) / "policy" / "project_policy.json"

    def _audit_path(self, project_id: str) -> Path:
        return self.registry.state_dir(project_id) / "policy" / "audit.jsonl"

    @staticmethod
    def _validate(policy: dict[str, Any]) -> dict[str, Any]:
        expected = set(default_policy())
        if not isinstance(policy, dict) or set(policy) != expected:
            raise ValueError("policy must contain exactly the supported fields")
        if policy["schema_version"] != SCHEMA_VERSION:
            raise ValueError("unsupported policy schema version")
        paths = policy["allowed_workspace_paths"]
        if not isinstance(paths, list) or any(not isinstance(path, str) or not path or Path(path).is_absolute() or ".." in Path(path).parts for path in paths):
            raise ValueError("allowed_workspace_paths must be relative, non-traversing paths")
        profiles = policy["validation_profiles"]
        if not isinstance(profiles, list) or any(not isinstance(profile, str) or not PROFILE_RE.fullmatch(profile) for profile in profiles):
            raise ValueError("validation_profiles contain an invalid profile name")
        providers = policy["model_providers"]
        if not isinstance(providers, list) or not set(providers).issubset(ALLOWED_PROVIDERS):
            raise ValueError("model_providers contain an unsupported provider")
        ProjectPolicyStore._validate_limits(policy["budgets"], {"max_task_tokens", "max_request_tokens"}, "budgets", 0, 10_000_000)
        ProjectPolicyStore._validate_limits(policy["retention"], {"audit_days", "telemetry_days"}, "retention", 1, 3650)
        if policy["auto_apply_level"] not in AUTO_APPLY_LEVELS:
            raise ValueError("auto_apply_level is not supported")
        return {
            "schema_version": SCHEMA_VERSION,
            "allowed_workspace_paths": sorted(set(paths)),
            "validation_profiles": sorted(set(profiles)),
            "model_providers": sorted(set(providers)),
            "budgets": dict(policy["budgets"]),
            "retention": dict(policy["retention"]),
            "auto_apply_level": policy["auto_apply_level"],
        }

    @staticmethod
    def _validate_limits(value: Any, expected: set[str], label: str, minimum: int, maximum: int) -> None:
        if not isinstance(value, dict) or set(value) != expected or any(type(item) is not int or not minimum <= item <= maximum for item in value.values()):
            raise ValueError(f"{label} must contain bounded integer limits")
