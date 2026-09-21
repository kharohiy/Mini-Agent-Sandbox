"""Bounded, redacted read-only summaries for Phase 8 operations views."""
from __future__ import annotations

from typing import Any


MAX_TASKS = 25
MAX_CARDS = 25


def build_operations_view(project: dict[str, Any], tasks: list[dict[str, Any]], cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Return operational metadata without task text, diffs, reports, or card content."""
    return {
        "project": {
            key: project[key]
            for key in ("id", "display_name", "created_at", "updated_at")
        },
        "tasks": [_task_summary(task) for task in tasks[:MAX_TASKS]],
        "knowledge_candidates": [_card_summary(card) for card in cards[:MAX_CARDS]],
    }


def _task_summary(task: dict[str, Any]) -> dict[str, Any]:
    return {
        key: task[key]
        for key in ("id", "status", "created_at", "updated_at")
    } | {
        "plans": [_plan_summary(plan) for plan in task["plans"]],
        "runs": [
            {key: run[key] for key in ("id", "status", "created_at")}
            for run in task["runs"]
        ],
    }


def _plan_summary(plan: dict[str, Any]) -> dict[str, Any]:
    return {
        key: plan[key]
        for key in ("id", "status", "created_at", "approved_at")
    } | {"steps": [_step_summary(step) for step in plan["steps"]]}


def _step_summary(step: dict[str, Any]) -> dict[str, Any]:
    return {
        key: step[key]
        for key in ("id", "position", "files", "status")
    } | {"patches": [_patch_summary(patch) for patch in step["patches"]]}


def _patch_summary(patch: dict[str, Any]) -> dict[str, Any]:
    return {
        key: patch[key]
        for key in ("id", "sha256", "status", "created_at")
    } | {
        "reviewed": bool(patch["reviews"]),
        "user_approved": patch["user_approval"] is not None,
        "validation_reports": [
            {key: report[key] for key in ("id", "status", "created_at")}
            for report in patch["validation_reports"]
        ],
    }


def _card_summary(card: dict[str, Any]) -> dict[str, Any]:
    return {
        key: card[key]
        for key in ("id", "status", "confidence", "affected_modules", "updated_at")
    }
