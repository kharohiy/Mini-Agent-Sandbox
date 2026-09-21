"""Registry and isolated state paths for connected projects."""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path


DATA_ROOT = Path(__file__).resolve().parent / "data"
PROJECTS_ROOT = DATA_ROOT / "projects"
REGISTRY_DB = DATA_ROOT / "registry" / "projects.sqlite"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _slug(value: str) -> str:
    result = re.sub(r"[^a-z0-9]+", "-", value.casefold()).strip("-")
    return result or "project"


class ProjectRegistry:
    def __init__(self, database: Path = REGISTRY_DB, projects_root: Path = PROJECTS_ROOT):
        self.database = Path(database)
        self.projects_root = Path(projects_root)
        self.database.parent.mkdir(parents=True, exist_ok=True)
        self.projects_root.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.database)
        try:
            connection.execute(
                """CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, display_name TEXT NOT NULL, source_path TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL
                )"""
            )
            connection.commit()
        finally:
            connection.close()

    def register(self, source_path: str | Path, display_name: str | None = None) -> dict:
        source = Path(source_path).resolve()
        if not source.is_dir() or source.is_symlink():
            raise ValueError("project must be an existing non-symlink directory")
        existing = self.by_source(source)
        if existing:
            return existing
        name = display_name or source.name
        project_id = f"{_slug(name)}--{hashlib.sha256(str(source).encode('utf-8')).hexdigest()[:8]}"
        now = _now()
        connection = sqlite3.connect(self.database)
        try:
            connection.execute("INSERT INTO projects VALUES (?, ?, ?, ?, ?)", (project_id, name, str(source), now, now))
            connection.commit()
        finally:
            connection.close()
        state = self.state_dir(project_id)
        for name in ("snapshot", "rag", "knowledge", "runs", "exports"):
            (state / name).mkdir(parents=True, exist_ok=True)
        return self.get(project_id)

    def get(self, project_id: str) -> dict:
        connection = sqlite3.connect(self.database)
        try:
            row = connection.execute("SELECT id, display_name, source_path, created_at, updated_at FROM projects WHERE id = ?", (project_id,)).fetchone()
        finally:
            connection.close()
        if not row:
            raise FileNotFoundError("registered project was not found")
        return {"id": row[0], "display_name": row[1], "source_path": row[2], "created_at": row[3], "updated_at": row[4], "state_dir": str(self.state_dir(row[0]))}

    def by_source(self, source_path: Path) -> dict | None:
        connection = sqlite3.connect(self.database)
        try:
            row = connection.execute("SELECT id FROM projects WHERE source_path = ?", (str(source_path),)).fetchone()
        finally:
            connection.close()
        return self.get(row[0]) if row else None

    def list(self) -> list[dict]:
        connection = sqlite3.connect(self.database)
        try:
            ids = [row[0] for row in connection.execute("SELECT id FROM projects ORDER BY display_name")]
        finally:
            connection.close()
        return [self.get(project_id) for project_id in ids]

    def state_dir(self, project_id: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*--[0-9a-f]{8}", project_id):
            raise ValueError("invalid project id")
        return self.projects_root / project_id
