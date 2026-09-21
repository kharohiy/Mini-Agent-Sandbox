"""Versioned, evidence-gated knowledge cards with strict project/global scope."""
from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

from project_registry import DATA_ROOT, ProjectRegistry


VALID_STATUS = {"draft", "proposed", "verified", "deprecated", "archived"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class KnowledgeStore:
    def __init__(self, registry: ProjectRegistry | None = None, global_root: Path | None = None):
        self.registry = registry or ProjectRegistry()
        self.global_root = global_root or DATA_ROOT / "knowledge" / "global"

    def _database(self, scope: str, project_id: str | None = None) -> Path:
        if scope == "global" and project_id is None:
            return self.global_root / "global_knowledge.sqlite"
        if scope == "project" and project_id:
            return self.registry.state_dir(project_id) / "knowledge" / "project_knowledge.sqlite"
        raise ValueError("global knowledge cannot have a project id; project knowledge requires one")

    def _connect(self, scope: str, project_id: str | None = None) -> sqlite3.Connection:
        database = self._database(scope, project_id)
        database.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.executescript(
            """CREATE TABLE IF NOT EXISTS cards (
            id TEXT PRIMARY KEY, scope TEXT NOT NULL, project_id TEXT, status TEXT NOT NULL,
            title TEXT NOT NULL, problem TEXT NOT NULL, decision TEXT NOT NULL, rationale TEXT NOT NULL,
            tags TEXT NOT NULL, affected_modules TEXT NOT NULL, confidence TEXT NOT NULL,
            supersedes TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS evidence (
            card_id TEXT NOT NULL, evidence_type TEXT NOT NULL, reference TEXT NOT NULL, description TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS versions (
            card_id TEXT NOT NULL, version INTEGER NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY(card_id, version)
            );
            CREATE TABLE IF NOT EXISTS audit (
            card_id TEXT NOT NULL, action TEXT NOT NULL, detail TEXT NOT NULL, created_at TEXT NOT NULL
            );"""
        )
        return connection

    def create(self, *, scope: str, title: str, problem: str, decision: str, rationale: str,
               project_id: str | None = None, tags: list[str] | None = None,
               affected_modules: list[str] | None = None, evidence: list[dict] | None = None) -> dict:
        if not all(value.strip() for value in (title, problem, decision, rationale)):
            raise ValueError("title, problem, decision and rationale are required")
        card_id = f"kc_{uuid.uuid4().hex}"
        now = _now()
        card = {"id": card_id, "scope": scope, "project_id": project_id, "status": "draft", "title": title,
                "problem": problem, "decision": decision, "rationale": rationale, "tags": tags or [],
                "affected_modules": affected_modules or [], "confidence": "unverified", "supersedes": None,
                "created_at": now, "updated_at": now, "evidence": evidence or []}
        connection = self._connect(scope, project_id)
        try:
            with connection:
                connection.execute("INSERT INTO cards VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                    (card_id, scope, project_id, "draft", title, problem, decision, rationale, json.dumps(card["tags"]),
                     json.dumps(card["affected_modules"]), "unverified", None, now, now))
                connection.executemany("INSERT INTO evidence VALUES (?, ?, ?, ?)",
                    [(card_id, item["type"], item["reference"], item.get("description", "")) for item in card["evidence"]])
                self._version(connection, card, 1)
                self._audit(connection, card_id, "created", "draft knowledge card")
        finally:
            connection.close()
        return card

    def list(self, scope: str, project_id: str | None = None, status: str | None = None) -> list[dict]:
        connection = self._connect(scope, project_id)
        try:
            query = "SELECT id, scope, project_id, status, title, problem, decision, rationale, tags, affected_modules, confidence, supersedes, created_at, updated_at FROM cards"
            values: tuple = ()
            if status:
                if status not in VALID_STATUS:
                    raise ValueError("invalid status")
                query += " WHERE status = ?"
                values = (status,)
            rows = connection.execute(query + " ORDER BY updated_at DESC", values).fetchall()
            return [self._card(connection, row) for row in rows]
        finally:
            connection.close()

    def get(self, scope: str, card_id: str, project_id: str | None = None) -> dict:
        connection = self._connect(scope, project_id)
        try:
            row = connection.execute("SELECT id, scope, project_id, status, title, problem, decision, rationale, tags, affected_modules, confidence, supersedes, created_at, updated_at FROM cards WHERE id = ?", (card_id,)).fetchone()
            if not row:
                raise FileNotFoundError("knowledge card was not found")
            return self._card(connection, row)
        finally:
            connection.close()

    def search(self, scope: str, query: str, project_id: str | None = None) -> list[dict]:
        if not query.strip():
            raise ValueError("search query is required")
        connection = self._connect(scope, project_id)
        try:
            term = f"%{query.strip()}%"
            rows = connection.execute("SELECT id, scope, project_id, status, title, problem, decision, rationale, tags, affected_modules, confidence, supersedes, created_at, updated_at FROM cards WHERE title LIKE ? OR problem LIKE ? OR decision LIKE ? OR rationale LIKE ? ORDER BY updated_at DESC", (term, term, term, term)).fetchall()
            return [self._card(connection, row) for row in rows]
        finally:
            connection.close()

    def add_evidence(self, scope: str, card_id: str, evidence: dict, project_id: str | None = None) -> dict:
        if not all(isinstance(evidence.get(key), str) and evidence[key].strip() for key in ("type", "reference")):
            raise ValueError("evidence type and reference are required")
        description = evidence.get("description", "")
        if not isinstance(description, str):
            raise ValueError("evidence description must be text")
        connection = self._connect(scope, project_id)
        try:
            with connection:
                card = self.get(scope, card_id, project_id)
                connection.execute("INSERT INTO evidence VALUES (?, ?, ?, ?)", (card_id, evidence["type"].strip(), evidence["reference"].strip(), description))
                now = _now()
                connection.execute("UPDATE cards SET updated_at = ? WHERE id = ?", (now, card_id))
                card["evidence"].append({"type": evidence["type"].strip(), "reference": evidence["reference"].strip(), "description": description})
                card["updated_at"] = now
                self._version(connection, card, self._next_version(connection, card_id))
                self._audit(connection, card_id, "evidence_added", evidence["reference"].strip())
                return card
        finally:
            connection.close()

    def versions(self, scope: str, card_id: str, project_id: str | None = None) -> list[dict]:
        connection = self._connect(scope, project_id)
        try:
            return [{"version": row[0], "card": json.loads(row[1]), "created_at": row[2]} for row in connection.execute("SELECT version, payload, created_at FROM versions WHERE card_id = ? ORDER BY version", (card_id,))]
        finally:
            connection.close()

    def audit(self, scope: str, card_id: str, project_id: str | None = None) -> list[dict]:
        connection = self._connect(scope, project_id)
        try:
            return [{"action": row[0], "detail": row[1], "created_at": row[2]} for row in connection.execute("SELECT action, detail, created_at FROM audit WHERE card_id = ? ORDER BY rowid", (card_id,))]
        finally:
            connection.close()

    def verify(self, scope: str, card_id: str, project_id: str | None = None) -> dict:
        connection = self._connect(scope, project_id)
        try:
            with connection:
                row = connection.execute("SELECT id, scope, project_id, status, title, problem, decision, rationale, tags, affected_modules, confidence, supersedes, created_at, updated_at FROM cards WHERE id = ?", (card_id,)).fetchone()
                if not row:
                    raise FileNotFoundError("knowledge card was not found")
                evidence_count = connection.execute("SELECT COUNT(*) FROM evidence WHERE card_id = ?", (card_id,)).fetchone()[0]
                if not evidence_count:
                    raise ValueError("verified cards require evidence")
                now = _now()
                connection.execute("UPDATE cards SET status = 'verified', confidence = 'verified', updated_at = ? WHERE id = ?", (now, card_id))
                updated = list(row); updated[3] = "verified"; updated[10] = "verified"; updated[13] = now
                card = self._card(connection, tuple(updated))
                self._version(connection, card, self._next_version(connection, card_id))
                self._audit(connection, card_id, "verified", "evidence reviewed")
                return card
        finally:
            connection.close()

    def set_status(self, scope: str, card_id: str, status: str, project_id: str | None = None) -> dict:
        if status not in {"deprecated", "archived"}:
            raise ValueError("only deprecated or archived statuses may be set directly")
        connection = self._connect(scope, project_id)
        try:
            with connection:
                row = connection.execute("SELECT id, scope, project_id, status, title, problem, decision, rationale, tags, affected_modules, confidence, supersedes, created_at, updated_at FROM cards WHERE id = ?", (card_id,)).fetchone()
                if not row:
                    raise FileNotFoundError("knowledge card was not found")
                now = _now()
                connection.execute("UPDATE cards SET status = ?, updated_at = ? WHERE id = ?", (status, now, card_id))
                updated = list(row); updated[3] = status; updated[13] = now
                card = self._card(connection, tuple(updated))
                self._version(connection, card, self._next_version(connection, card_id))
                self._audit(connection, card_id, status, f"card marked {status}")
                return card
        finally:
            connection.close()

    @staticmethod
    def _next_version(connection: sqlite3.Connection, card_id: str) -> int:
        return connection.execute("SELECT COALESCE(MAX(version), 0) + 1 FROM versions WHERE card_id = ?", (card_id,)).fetchone()[0]

    @staticmethod
    def _audit(connection: sqlite3.Connection, card_id: str, action: str, detail: str) -> None:
        connection.execute("INSERT INTO audit VALUES (?, ?, ?, ?)", (card_id, action, detail, _now()))

    @staticmethod
    def _version(connection: sqlite3.Connection, card: dict, version: int) -> None:
        connection.execute("INSERT INTO versions VALUES (?, ?, ?, ?)", (card["id"], version, json.dumps(card, ensure_ascii=False), _now()))

    @staticmethod
    def _card(connection: sqlite3.Connection, row: tuple) -> dict:
        card = dict(zip(("id", "scope", "project_id", "status", "title", "problem", "decision", "rationale", "tags", "affected_modules", "confidence", "supersedes", "created_at", "updated_at"), row))
        card["tags"] = json.loads(card["tags"]); card["affected_modules"] = json.loads(card["affected_modules"])
        card["evidence"] = [{"type": item[0], "reference": item[1], "description": item[2]} for item in connection.execute("SELECT evidence_type, reference, description FROM evidence WHERE card_id = ?", (card["id"],))]
        return card
