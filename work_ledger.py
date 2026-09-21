"""Persistent, project-isolated audit ledger for planned engineering work."""
from __future__ import annotations

import json
import sqlite3
import uuid
import hashlib
from contextlib import contextmanager
from datetime import datetime, timezone

from project_registry import ProjectRegistry
from project_policy import ProjectPolicyStore
from patch_policy import validate_unified_diff

STATUSES = {"proposed", "approved", "running", "blocked", "validated", "rejected", "superseded"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class WorkLedger:
    def __init__(self, project_id: str, registry: ProjectRegistry | None = None):
        self.project_id = project_id
        self.registry = registry or ProjectRegistry()
        self.registry.get(project_id)
        self.database = self.registry.state_dir(project_id) / "runs" / "work_ledger.sqlite"
        self.database.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""CREATE TABLE IF NOT EXISTS tasks (id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS plans (id TEXT PRIMARY KEY, task_id TEXT NOT NULL, objective TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, approved_at TEXT);
            CREATE TABLE IF NOT EXISTS plan_steps (id TEXT PRIMARY KEY, plan_id TEXT NOT NULL, position INTEGER NOT NULL, description TEXT NOT NULL, files TEXT NOT NULL, risks TEXT NOT NULL, validation TEXT NOT NULL, rollback TEXT NOT NULL, status TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS patches (id TEXT PRIMARY KEY, step_id TEXT NOT NULL, sha256 TEXT NOT NULL, diff TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS reviews (id TEXT PRIMARY KEY, patch_id TEXT NOT NULL, decision TEXT NOT NULL, notes TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS patch_approvals (id TEXT PRIMARY KEY, patch_id TEXT NOT NULL, patch_sha256 TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS validation_reports (id TEXT PRIMARY KEY, patch_id TEXT NOT NULL, status TEXT NOT NULL, report TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs (id TEXT PRIMARY KEY, task_id TEXT NOT NULL, status TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL);""")
            # Older records used "approved" for reviewer approval. Reclassify
            # unvalidated records so they require the new explicit user gate.
            db.execute("UPDATE patches SET status = 'review_approved' WHERE status = 'approved' AND id NOT IN (SELECT patch_id FROM validation_reports) AND id NOT IN (SELECT patch_id FROM patch_approvals)")

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self.database)
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    @staticmethod
    def _id(prefix): return f"{prefix}_{uuid.uuid4().hex}"

    def create_task(self, title: str, description: str) -> dict:
        if not title.strip() or not description.strip(): raise ValueError("title and description are required")
        task_id, now = self._id("task"), _now()
        with self._connect() as db: db.execute("INSERT INTO tasks VALUES (?, ?, ?, 'proposed', ?, ?)", (task_id, title.strip(), description.strip(), now, now))
        return self.task(task_id)

    def create_plan(self, task_id: str, objective: str) -> dict:
        self.task(task_id)
        if not objective.strip(): raise ValueError("plan objective is required")
        plan_id = self._id("plan")
        with self._connect() as db: db.execute("INSERT INTO plans VALUES (?, ?, ?, 'proposed', ?, NULL)", (plan_id, task_id, objective.strip(), _now()))
        return self.plan(plan_id)

    def add_step(self, plan_id: str, *, description: str, files: list[str], risks: str, validation: str, rollback: str) -> dict:
        plan = self.plan(plan_id)
        if plan["status"] != "proposed": raise ValueError("steps may only be added to a proposed plan")
        if not all(value.strip() for value in (description, risks, validation, rollback)) or not files: raise ValueError("description, files, risks, validation and rollback are required")
        step_id = self._id("step")
        with self._connect() as db:
            position = db.execute("SELECT COUNT(*) FROM plan_steps WHERE plan_id = ?", (plan_id,)).fetchone()[0] + 1
            db.execute("INSERT INTO plan_steps VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'proposed')", (step_id, plan_id, position, description.strip(), json.dumps(files), risks.strip(), validation.strip(), rollback.strip()))
        return self._step(step_id)

    def approve_plan(self, plan_id: str) -> dict:
        plan = self.plan(plan_id)
        if plan["status"] != "proposed" or not plan["steps"]: raise ValueError("a proposed plan needs at least one step before approval")
        now = _now()
        with self._connect() as db:
            db.execute("UPDATE plans SET status = 'approved', approved_at = ? WHERE id = ?", (now, plan_id))
            db.execute("UPDATE tasks SET status = 'approved', updated_at = ? WHERE id = ?", (now, plan["task_id"]))
        return self.plan(plan_id)

    def record_patch(self, step_id: str, diff: str) -> dict:
        step = self._step(step_id)
        plan = self.plan(step["plan_id"])
        if plan["status"] != "approved": raise ValueError("patches require an approved plan")
        changed_paths = validate_unified_diff(diff, step["files"])
        ProjectPolicyStore(self.registry).require_allowed_workspace_paths(self.project_id, changed_paths)
        patch_id, now = self._id("patch"), _now()
        digest = hashlib.sha256(diff.encode("utf-8")).hexdigest()
        with self._connect() as db:
            db.execute("INSERT INTO patches VALUES (?, ?, ?, ?, 'proposed', ?)", (patch_id, step_id, digest, diff, now))
            db.execute("UPDATE plan_steps SET status = 'running' WHERE id = ?", (step_id,))
            db.execute("UPDATE tasks SET status = 'running', updated_at = ? WHERE id = ?", (now, plan["task_id"]))
        return self.patch(patch_id)

    def record_review(self, patch_id: str, decision: str, notes: str) -> dict:
        if decision not in {"approved", "rejected"}: raise ValueError("review decision must be approved or rejected")
        patch = self.patch(patch_id)
        if patch["status"] != "proposed": raise ValueError("review can only be recorded once for a proposed patch")
        review_id, now = self._id("review"), _now()
        with self._connect() as db:
            db.execute("INSERT INTO reviews VALUES (?, ?, ?, ?, ?)", (review_id, patch_id, decision, notes, now))
            db.execute("UPDATE patches SET status = ? WHERE id = ?", ("review_approved" if decision == "approved" else "rejected", patch_id))
        return {"id": review_id, "patch_id": patch_id, "decision": decision, "notes": notes, "created_at": now}

    def approve_patch(self, patch_id: str, expected_sha256: str) -> dict:
        """Record the user's explicit, hash-bound approval after review."""
        patch = self.patch(patch_id)
        if patch["status"] != "review_approved":
            raise ValueError("user approval requires a positive reviewer decision")
        if expected_sha256 != patch["sha256"]:
            raise ValueError("user approval hash does not match the proposed diff")
        now = _now()
        with self._connect() as db:
            db.execute("INSERT INTO patch_approvals VALUES (?, ?, ?, ?)", (self._id("approval"), patch_id, patch["sha256"], now))
            db.execute("UPDATE patches SET status = 'approved' WHERE id = ?", (patch_id,))
        return self.patch(patch_id)

    def record_validation(self, patch_id: str, status: str, report: dict) -> dict:
        if status not in {"validated", "rejected", "blocked"}: raise ValueError("validation status is invalid")
        patch = self.patch(patch_id)
        if patch["status"] != "approved": raise ValueError("validation requires explicit user approval after patch review")
        report_id, now = self._id("validation"), _now()
        with self._connect() as db:
            db.execute("INSERT INTO validation_reports VALUES (?, ?, ?, ?, ?)", (report_id, patch_id, status, json.dumps(report), now))
            db.execute("UPDATE patches SET status = ? WHERE id = ?", (status, patch_id))
            if status == "validated":
                step = self._step(patch["step_id"]); plan = self.plan(step["plan_id"])
                db.execute("UPDATE plan_steps SET status = 'validated' WHERE id = ?", (step["id"],))
                db.execute("UPDATE tasks SET status = 'validated', updated_at = ? WHERE id = ?", (now, plan["task_id"]))
        return {"id": report_id, "patch_id": patch_id, "status": status, "report": report, "created_at": now}

    def record_run(self, task_id: str, status: str, detail: str) -> dict:
        if status not in STATUSES: raise ValueError("invalid run status")
        self.task(task_id)
        run_id, now = self._id("run"), _now()
        with self._connect() as db: db.execute("INSERT INTO runs VALUES (?, ?, ?, ?, ?)", (run_id, task_id, status, detail, now))
        return {"id": run_id, "task_id": task_id, "status": status, "detail": detail, "created_at": now}

    def task(self, task_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT id, title, description, status, created_at, updated_at FROM tasks WHERE id = ?", (task_id,)).fetchone()
            if not row: raise FileNotFoundError("task was not found")
            plans = [self._plan(db, item) for item in db.execute("SELECT id, task_id, objective, status, created_at, approved_at FROM plans WHERE task_id = ? ORDER BY created_at", (task_id,))]
            runs = [dict(zip(("id", "task_id", "status", "detail", "created_at"), item)) for item in db.execute("SELECT id, task_id, status, detail, created_at FROM runs WHERE task_id = ? ORDER BY created_at", (task_id,))]
        return dict(zip(("id", "title", "description", "status", "created_at", "updated_at"), row)) | {"project_id": self.project_id, "plans": plans, "runs": runs}

    def list_tasks(self, status: str | None = None) -> list[dict]:
        if status and status not in STATUSES: raise ValueError("invalid task status")
        with self._connect() as db:
            query = "SELECT id FROM tasks" + (" WHERE status = ?" if status else "") + " ORDER BY updated_at DESC"
            ids = [row[0] for row in db.execute(query, (status,) if status else ())]
        return [self.task(task_id) for task_id in ids]

    def plan(self, plan_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT id, task_id, objective, status, created_at, approved_at FROM plans WHERE id = ?", (plan_id,)).fetchone()
            if not row: raise FileNotFoundError("plan was not found")
            return self._plan(db, row)

    def patch(self, patch_id: str) -> dict:
        with self._connect() as db:
            row = db.execute("SELECT id, step_id, sha256, diff, status, created_at FROM patches WHERE id = ?", (patch_id,)).fetchone()
            if not row: raise FileNotFoundError("patch was not found")
            result = dict(zip(("id", "step_id", "sha256", "diff", "status", "created_at"), row))
            approval = db.execute("SELECT id, patch_sha256, created_at FROM patch_approvals WHERE patch_id = ? ORDER BY created_at DESC LIMIT 1", (patch_id,)).fetchone()
            result["user_approval"] = dict(zip(("id", "patch_sha256", "created_at"), approval)) if approval else None
            return result

    def validation_bundle(self, patch_id: str) -> dict:
        """Re-read the patch, approved step, review, and user approval together."""
        with self._connect() as db:
            db.execute("BEGIN")
            patch = db.execute(
                "SELECT id, step_id, sha256, diff, status, created_at FROM patches WHERE id = ?",
                (patch_id,),
            ).fetchone()
            if not patch:
                raise FileNotFoundError("patch was not found")
            step = db.execute(
                "SELECT id, plan_id, files FROM plan_steps WHERE id = ?", (patch[1],)
            ).fetchone()
            if not step:
                raise ValueError("patch plan step was not found")
            plan = db.execute("SELECT status FROM plans WHERE id = ?", (step[1],)).fetchone()
            reviews = db.execute(
                "SELECT id, decision, notes, created_at FROM reviews WHERE patch_id = ? ORDER BY created_at DESC LIMIT 1",
                (patch_id,),
            ).fetchone()
            approval = db.execute(
                "SELECT id, patch_sha256, created_at FROM patch_approvals WHERE patch_id = ? ORDER BY created_at DESC LIMIT 1",
                (patch_id,),
            ).fetchone()
        return {
            "patch": dict(zip(("id", "step_id", "sha256", "diff", "status", "created_at"), patch)),
            "step": {"id": step[0], "plan_id": step[1], "files": json.loads(step[2])},
            "plan_status": plan[0] if plan else None,
            "review": dict(zip(("id", "decision", "notes", "created_at"), reviews)) if reviews else None,
            "user_approval": dict(zip(("id", "patch_sha256", "created_at"), approval)) if approval else None,
        }

    def _plan(self, db, row):
        plan = dict(zip(("id", "task_id", "objective", "status", "created_at", "approved_at"), row))
        plan["steps"] = [self._step(row[0], db, item) for item in db.execute("SELECT id, plan_id, position, description, files, risks, validation, rollback, status FROM plan_steps WHERE plan_id = ? ORDER BY position", (row[0],))]
        for step in plan["steps"]:
            step["patches"] = []
            for patch_row in db.execute("SELECT id, step_id, sha256, diff, status, created_at FROM patches WHERE step_id = ? ORDER BY created_at", (step["id"],)):
                patch = dict(zip(("id", "step_id", "sha256", "diff", "status", "created_at"), patch_row))
                approval = db.execute("SELECT id, patch_sha256, created_at FROM patch_approvals WHERE patch_id = ? ORDER BY created_at DESC LIMIT 1", (patch["id"],)).fetchone()
                patch["user_approval"] = dict(zip(("id", "patch_sha256", "created_at"), approval)) if approval else None
                patch["reviews"] = [dict(zip(("id", "patch_id", "decision", "notes", "created_at"), review)) for review in db.execute("SELECT id, patch_id, decision, notes, created_at FROM reviews WHERE patch_id = ? ORDER BY created_at", (patch["id"],))]
                patch["validation_reports"] = [{"id": item[0], "patch_id": item[1], "status": item[2], "report": json.loads(item[3]), "created_at": item[4]} for item in db.execute("SELECT id, patch_id, status, report, created_at FROM validation_reports WHERE patch_id = ? ORDER BY created_at", (patch["id"],))]
                step["patches"].append(patch)
        return plan

    def _step(self, step_id, db=None, row=None):
        close = db is None; db = db or sqlite3.connect(self.database)
        try:
            row = row or db.execute("SELECT id, plan_id, position, description, files, risks, validation, rollback, status FROM plan_steps WHERE id = ?", (step_id,)).fetchone()
            if not row: raise FileNotFoundError("plan step was not found")
            result = dict(zip(("id", "plan_id", "position", "description", "files", "risks", "validation", "rollback", "status"), row)); result["files"] = json.loads(result["files"]); return result
        finally:
            if close: db.close()
