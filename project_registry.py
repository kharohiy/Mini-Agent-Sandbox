"""Registry and isolated state paths for connected projects."""
from __future__ import annotations

import hashlib
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit


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
                created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
                description TEXT NOT NULL DEFAULT '', source_kind TEXT NOT NULL DEFAULT 'local',
                source_uri TEXT NOT NULL DEFAULT '', configured_ref TEXT NOT NULL DEFAULT '',
                resolved_revision TEXT NOT NULL DEFAULT ''
                )"""
            )
            connection.commit()
        finally:
            connection.close()

    def register(
        self,
        source_path: str | Path,
        display_name: str | None = None,
        *,
        description: str = "",
        source_kind: str = "local",
        source_uri: str | None = None,
        configured_ref: str = "",
        resolved_revision: str = "",
    ) -> dict:
        source = Path(source_path).resolve()
        if not source.is_dir() or source.is_symlink():
            raise ValueError("project must be an existing non-symlink directory")
        source_uri = source_uri or str(source)
        self._validate_metadata(description, source_kind, source_uri, configured_ref, resolved_revision)
        existing = self.by_source(source)
        if existing:
            metadata = {
                "description": description,
                "source_kind": source_kind,
                "source_uri": source_uri,
                "configured_ref": configured_ref,
                "resolved_revision": resolved_revision,
            }
            if any(metadata[key] for key in ("description", "configured_ref", "resolved_revision")) or source_kind != "local" or source_uri != str(source):
                return self.update_metadata(existing["id"], **metadata)
            return existing
        name = display_name or source.name
        project_id = f"{_slug(name)}--{hashlib.sha256(str(source).encode('utf-8')).hexdigest()[:8]}"
        now = _now()
        connection = sqlite3.connect(self.database)
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)")}
            values = {
                "id": project_id,
                "display_name": name,
                "source_path": str(source),
                "created_at": now,
                "updated_at": now,
                "description": description,
                "source_kind": source_kind,
                "source_uri": source_uri,
                "configured_ref": configured_ref,
                "resolved_revision": resolved_revision,
            }
            optional = set(values) - {"id", "display_name", "source_path", "created_at", "updated_at"}
            metadata_requested = (
                bool(description or configured_ref or resolved_revision)
                or source_kind != "local"
                or source_uri != str(source)
            )
            if optional - columns and metadata_requested:
                raise RuntimeError("project catalog metadata migration is required before saving metadata")
            selected = [column for column in values if column in columns]
            placeholders = ", ".join("?" for _ in selected)
            connection.execute(
                f"INSERT INTO projects ({', '.join(selected)}) VALUES ({placeholders})",
                tuple(values[column] for column in selected),
            )
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
            connection.row_factory = sqlite3.Row
            row = connection.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        finally:
            connection.close()
        if not row:
            raise FileNotFoundError("registered project was not found")
        project = dict(row)
        project.setdefault("description", "")
        project.setdefault("source_kind", "local")
        project.setdefault("source_uri", project["source_path"])
        project.setdefault("configured_ref", "")
        project.setdefault("resolved_revision", "")
        project["state_dir"] = str(self.state_dir(project["id"]))
        return project

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

    def migrate_metadata_schema(self) -> None:
        """Explicitly add catalog metadata columns; callers own backup and approval."""
        connection = sqlite3.connect(self.database)
        try:
            with connection:
                columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)")}
                additions = {
                    "description": "TEXT NOT NULL DEFAULT ''",
                    "source_kind": "TEXT NOT NULL DEFAULT 'local'",
                    "source_uri": "TEXT NOT NULL DEFAULT ''",
                    "configured_ref": "TEXT NOT NULL DEFAULT ''",
                    "resolved_revision": "TEXT NOT NULL DEFAULT ''",
                }
                for name, declaration in additions.items():
                    if name not in columns:
                        connection.execute(f"ALTER TABLE projects ADD COLUMN {name} {declaration}")
                connection.execute("UPDATE projects SET source_uri = source_path WHERE source_uri = ''")
        finally:
            connection.close()

    def update_metadata(
        self,
        project_id: str,
        *,
        description: str,
        source_kind: str,
        source_uri: str,
        configured_ref: str = "",
        resolved_revision: str = "",
    ) -> dict:
        self._validate_metadata(description, source_kind, source_uri, configured_ref, resolved_revision)
        connection = sqlite3.connect(self.database)
        try:
            columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)")}
            required = {"description", "source_kind", "source_uri", "configured_ref", "resolved_revision"}
            if not required.issubset(columns):
                raise RuntimeError("project catalog metadata migration is required before saving metadata")
            with connection:
                cursor = connection.execute(
                    """UPDATE projects SET description = ?, source_kind = ?, source_uri = ?,
                    configured_ref = ?, resolved_revision = ?, updated_at = ? WHERE id = ?""",
                    (description, source_kind, source_uri, configured_ref, resolved_revision, _now(), project_id),
                )
                if cursor.rowcount != 1:
                    raise FileNotFoundError("registered project was not found")
        finally:
            connection.close()
        return self.get(project_id)

    @staticmethod
    def _validate_metadata(
        description: str,
        source_kind: str,
        source_uri: str,
        configured_ref: str = "",
        resolved_revision: str = "",
    ) -> None:
        if not isinstance(description, str) or len(description) > 500:
            raise ValueError("project description must be text up to 500 characters")
        if not isinstance(source_kind, str) or source_kind not in {"local", "git"}:
            raise ValueError("source_kind must be 'local' or 'git'")
        if not isinstance(source_uri, str) or not source_uri.strip():
            raise ValueError("source_uri is required")
        if not isinstance(configured_ref, str) or not isinstance(resolved_revision, str):
            raise ValueError("repository ref and revision must be text")
        if source_kind == "git":
            parsed = urlsplit(source_uri)
            if (
                parsed.scheme != "https"
                or not parsed.hostname
                or parsed.username
                or parsed.password
                or parsed.query
                or parsed.fragment
            ):
                raise ValueError("git source_uri must be an HTTPS URL without embedded credentials")
            if resolved_revision and not re.fullmatch(r"(?:[0-9a-f]{40}|[0-9a-f]{64})", resolved_revision):
                raise ValueError("resolved git revision must be a full commit hash")

    def state_dir(self, project_id: str) -> Path:
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]*--[0-9a-f]{8}", project_id):
            raise ValueError("invalid project id")
        return self.projects_root / project_id
