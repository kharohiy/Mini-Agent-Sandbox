"""Read-only, redacted Phase 8 metrics derived from persisted project state."""
from __future__ import annotations

from collections import Counter
from typing import Any


def build_project_metrics(tasks: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    task_statuses = Counter(task["status"] for task in tasks)
    report_statuses: Counter[str] = Counter()
    stage_statuses: Counter[str] = Counter()
    for task in tasks:
        for plan in task["plans"]:
            for step in plan["steps"]:
                for patch in step["patches"]:
                    for report in patch["validation_reports"]:
                        report_statuses[report["status"]] += 1
                        for stage in report["report"].get("stages", []):
                            if isinstance(stage, dict) and isinstance(stage.get("status"), str):
                                stage_statuses[stage["status"]] += 1
    card_statuses = Counter(card["status"] for card in cards)
    return {
        "task_outcomes": {"total": len(tasks), "by_status": dict(sorted(task_statuses.items()))},
        "validation": {
            "reports_by_status": dict(sorted(report_statuses.items())),
            "stages_by_status": dict(sorted(stage_statuses.items())),
        },
        "knowledge": {"total": len(cards), "by_status": dict(sorted(card_statuses.items()))},
        "retrieval_quality": {"availability": "not_recorded"},
        "model_usage": {"availability": "not_recorded"},
    }
