"""Explicit, project-bound ingestion for user-supplied supplemental documents."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from types import SimpleNamespace
from typing import Any

from project_registry import DATA_ROOT, ProjectRegistry
from rag_service import SandboxRagService


MAX_DOCUMENT_CHARS = 100_000
CHUNK_SIZE = 1_000
CHUNK_OVERLAP = 150
ALLOWED_CONTENT_TYPES = {"text/plain", "text/markdown"}
_SOURCE_RE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._ -]{0,127}\Z")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _manifest_path(registry: ProjectRegistry, project_id: str) -> Path:
    return registry.state_dir(project_id) / "rag" / "project_documents.json"


def _load_manifest(registry: ProjectRegistry, project_id: str) -> dict[str, Any]:
    path = _manifest_path(registry, project_id)
    if not path.exists():
        return {"schema_version": 1, "documents": {}}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("project document manifest is unreadable") from exc
    if payload.get("schema_version") != 1 or not isinstance(payload.get("documents"), dict):
        raise ValueError("project document manifest has an invalid schema")
    return payload


def _write_manifest(registry: ProjectRegistry, project_id: str, manifest: dict[str, Any]) -> None:
    path = _manifest_path(registry, project_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix="project_documents.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            json.dump(manifest, handle, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
            handle.flush()
            os.fsync(handle.fileno())
        Path(temporary).replace(path)
    except Exception:
        Path(temporary).unlink(missing_ok=True)
        raise


def _validate_input(source: str, content: str, content_type: str) -> None:
    if not isinstance(source, str) or not _SOURCE_RE.fullmatch(source):
        raise ValueError("source must be a short logical document name, not a path")
    if not isinstance(content, str) or not content.strip():
        raise ValueError("document content is required")
    if len(content) > MAX_DOCUMENT_CHARS:
        raise ValueError(f"document exceeds {MAX_DOCUMENT_CHARS} character limit")
    if content_type not in ALLOWED_CONTENT_TYPES:
        raise ValueError("unsupported document content type")


def _chunks(content: str) -> list[str]:
    chunks = []
    start = 0
    while start < len(content):
        end = min(len(content), start + CHUNK_SIZE)
        chunks.append(content[start:end])
        if end == len(content):
            break
        start = end - CHUNK_OVERLAP
    return chunks


def _document_ids(project_id: str, source: str, checksum: str, count: int) -> list[str]:
    prefix = hashlib.sha256(f"{project_id}\0{source}\0{checksum}".encode("utf-8")).hexdigest()
    return [f"project-document:{prefix}:{index:05d}" for index in range(count)]


def list_project_documents(project_id: str, *, registry: ProjectRegistry | None = None) -> list[dict[str, Any]]:
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    manifest = _load_manifest(registry, project_id)
    return [manifest["documents"][source] for source in sorted(manifest["documents"])]


def ingest_project_document(
    project_id: str,
    *,
    source: str,
    content: str,
    content_type: str = "text/plain",
    confirmed: bool = False,
    registry: ProjectRegistry | None = None,
    service: SandboxRagService | None = None,
) -> dict[str, Any]:
    """Replace one explicitly confirmed supplemental document atomically enough for retrieval.

    The content arrives as request data, never as an arbitrary local file path.
    The manifest has metadata only; it intentionally does not duplicate document text.
    """
    if confirmed is not True:
        raise ValueError("explicit document ingestion confirmation is required")
    _validate_input(source, content, content_type)
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    manifest = _load_manifest(registry, project_id)
    checksum = hashlib.sha256(content.encode("utf-8")).hexdigest()
    existing = manifest["documents"].get(source)
    if existing and existing.get("sha256") == checksum and existing.get("content_type") == content_type:
        return {"action": "unchanged", "document": existing}

    service = service or SandboxRagService(
        "local-operator", SimpleNamespace(base_dir=DATA_ROOT), project_id=project_id, registry=registry
    )
    collection = service.document_collection
    if collection is None:
        raise ValueError("project document collection requires a project id")
    text_chunks = _chunks(content)
    ids = _document_ids(project_id, source, checksum, len(text_chunks))
    metadata = [
        {
            "scope": "project-document",
            "trust": "user supplied project document",
            "project_id": project_id,
            "source": source,
            "sha256": checksum,
            "content_type": content_type,
            "chunk_index": index,
            "ingestion_status": "pending",
        }
        for index in range(len(text_chunks))
    ]
    try:
        collection.upsert(documents=text_chunks, metadatas=metadata, ids=ids)
        active_metadata = [item | {"ingestion_status": "active"} for item in metadata]
        collection.upsert(documents=text_chunks, metadatas=active_metadata, ids=ids)
        if existing and existing.get("chunk_ids"):
            collection.delete(ids=existing["chunk_ids"])
    except Exception:
        try:
            collection.delete(ids=ids)
        except Exception:
            pass
        raise

    record = {
        "source": source,
        "project_id": project_id,
        "content_type": content_type,
        "sha256": checksum,
        "chunk_count": len(ids),
        "chunk_ids": ids,
        "ingested_at": _now(),
        "status": "active",
    }
    manifest["documents"][source] = record
    _write_manifest(registry, project_id, manifest)
    return {"action": "replaced" if existing else "indexed", "document": record}


def remove_project_document(
    project_id: str, source: str, *, confirmed: bool = False,
    registry: ProjectRegistry | None = None, service: SandboxRagService | None = None,
) -> dict[str, Any]:
    """Remove one explicitly named supplemental document, never code or knowledge."""
    if confirmed is not True:
        raise ValueError("explicit document removal confirmation is required")
    _validate_input(source, "x", "text/plain")
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    manifest = _load_manifest(registry, project_id)
    record = manifest["documents"].get(source)
    if not record:
        raise FileNotFoundError("project document was not found")
    service = service or SandboxRagService(
        "local-operator", SimpleNamespace(base_dir=DATA_ROOT), project_id=project_id, registry=registry
    )
    if service.document_collection is None:
        raise ValueError("project document collection requires a project id")
    service.document_collection.delete(ids=record["chunk_ids"])
    del manifest["documents"][source]
    _write_manifest(registry, project_id, manifest)
    return {"action": "removed", "document": record}
