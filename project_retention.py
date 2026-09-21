"""Read-only, project-scoped retention previews for operational metadata."""
from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from project_policy import ProjectPolicyStore
from project_registry import ProjectRegistry


class RetentionPreviewBlocked(ValueError):
    """Raised when an event store cannot be safely classified for retention."""


class ProjectRetentionPreview:
    """Calculate retention metadata without changing any project files."""

    _CATEGORIES = (
        ("telemetry", "telemetry_days", ("telemetry", "events.jsonl")),
        ("audit", "audit_days", ("policy", "audit.jsonl")),
    )

    def __init__(self, registry: ProjectRegistry | None = None, policy_store: ProjectPolicyStore | None = None):
        self.registry = registry or ProjectRegistry()
        self.policy_store = policy_store or ProjectPolicyStore(self.registry)

    def preview(self, project_id: str, *, now: datetime | None = None) -> dict[str, Any]:
        """Return counts only; malformed metadata blocks rather than deletes."""
        self.registry.get(project_id)
        reference_time = self._utc_now(now)
        retention = self.policy_store.get(project_id)["retention"]
        state_dir = self.registry.state_dir(project_id)
        categories = []
        for category, retention_field, relative_path in self._CATEGORIES:
            retention_days = retention[retention_field]
            cutoff = reference_time - timedelta(days=retention_days)
            timestamps = self._timestamps(state_dir.joinpath(*relative_path), category)
            categories.append(
                {
                    "category": category,
                    "retention_days": retention_days,
                    "total_events": len(timestamps),
                    "expired_events": sum(timestamp < cutoff for timestamp in timestamps),
                }
            )
        return {"project_id": project_id, "categories": categories}

    @staticmethod
    def _utc_now(value: datetime | None) -> datetime:
        value = value or datetime.now(timezone.utc)
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("retention preview time must be timezone-aware")
        return value.astimezone(timezone.utc)

    @staticmethod
    def _timestamps(path: Path, category: str) -> list[datetime]:
        if not path.exists():
            return []
        timestamps = []
        for line in path.read_text(encoding="utf-8").splitlines():
            try:
                event = json.loads(line)
                created_at = event["created_at"] if isinstance(event, dict) else None
                if not isinstance(created_at, str):
                    raise ValueError("created_at is missing")
                timestamp = datetime.fromisoformat(created_at)
                if timestamp.tzinfo is None or timestamp.utcoffset() is None:
                    raise ValueError("created_at is not timezone-aware")
            except (TypeError, ValueError, json.JSONDecodeError) as exc:
                raise RetentionPreviewBlocked(
                    f"retention preview blocked by malformed {category} event"
                ) from exc
            timestamps.append(timestamp.astimezone(timezone.utc))
        return timestamps
