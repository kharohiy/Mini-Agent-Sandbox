"""Read-only search over project snapshots; source files are never opened here."""
from __future__ import annotations

import argparse
import json
import re
import sqlite3
from pathlib import Path


SNAPSHOT_ROOT = Path(__file__).resolve().parent / "data" / "project_snapshots"
PROJECT_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def snapshot_database(project_id: str, root: Path = SNAPSHOT_ROOT) -> Path:
    if not PROJECT_ID.fullmatch(project_id):
        raise ValueError("project id may contain only letters, digits, '_' and '-'")
    database = (root / project_id / "project_snapshot.sqlite").resolve()
    if database.parent.parent != root.resolve() or not database.is_file():
        raise FileNotFoundError("project snapshot was not found")
    return database


def list_projects(root: Path = SNAPSHOT_ROOT) -> list[str]:
    if not root.is_dir():
        return []
    return sorted(item.name for item in root.iterdir() if item.is_dir() and PROJECT_ID.fullmatch(item.name) and (item / "project_snapshot.sqlite").is_file())


def snapshot_summary(project_id: str, root: Path = SNAPSHOT_ROOT) -> dict:
    database = snapshot_database(project_id, root)
    connection = sqlite3.connect(database)
    try:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        files = connection.execute("SELECT COUNT(*) FROM files").fetchone()[0]
        symbols = connection.execute("SELECT COUNT(*) FROM symbols").fetchone()[0]
    finally:
        connection.close()
    return {"id": project_id, "project": metadata.get("project"), "indexed_at": metadata.get("indexed_at"),
        "modules": json.loads(metadata.get("modules", "[]")), "gradle": json.loads(metadata.get("gradle", "{}")),
        "files": files, "symbols": symbols}


def search_snapshot(project_id: str, query: str, limit: int = 20, root: Path = SNAPSHOT_ROOT) -> list[dict]:
    if not query.strip():
        raise ValueError("query cannot be empty")
    limit = max(1, min(limit, 100))
    pattern = f"%{query.casefold()}%"
    database = snapshot_database(project_id, root)
    connection = sqlite3.connect(database)
    try:
        rows = connection.execute(
            """
            SELECT f.path, f.module, f.is_test, group_concat(DISTINCT s.name)
            FROM files f LEFT JOIN symbols s ON s.file_path = f.path
            LEFT JOIN relations r ON r.source_path = f.path
            WHERE lower(f.path) LIKE ? OR lower(COALESCE(s.name, '')) LIKE ?
               OR lower(COALESCE(s.package_name, '')) LIKE ? OR lower(COALESCE(r.target, '')) LIKE ?
            GROUP BY f.path, f.module, f.is_test
            ORDER BY f.is_test, f.path LIMIT ?
            """, (pattern, pattern, pattern, pattern, limit),
        ).fetchall()
    finally:
        connection.close()
    return [{"path": row[0], "module": row[1], "is_test": bool(row[2]),
             "symbols": sorted(filter(None, (row[3] or "").split(",")))} for row in rows]


def main() -> None:
    parser = argparse.ArgumentParser(description="Search a read-only project snapshot")
    parser.add_argument("project_id")
    parser.add_argument("query", nargs="?")
    parser.add_argument("--limit", type=int, default=20)
    arguments = parser.parse_args()
    result = snapshot_summary(arguments.project_id) if arguments.query is None else search_snapshot(arguments.project_id, arguments.query, arguments.limit)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
