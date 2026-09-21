"""Ingest a registered snapshot into the canonical project-scoped Chroma RAG."""
from __future__ import annotations
import hashlib, sqlite3
from pathlib import Path
from types import SimpleNamespace
from langchain_text_splitters import RecursiveCharacterTextSplitter
from project_registry import DATA_ROOT, ProjectRegistry
from rag_service import SandboxRagService

def ingest_project(project_id: str, batch_size: int = 32, registry: ProjectRegistry | None = None) -> dict:
    registry = registry or ProjectRegistry(); project = registry.get(project_id); state = registry.state_dir(project_id)
    db = sqlite3.connect(state / "snapshot" / "project_snapshot.sqlite")
    try:
        files = db.execute("SELECT path, sha256, language, module FROM files ORDER BY path").fetchall()
    finally:
        db.close()
    service = SandboxRagService("local-operator", SimpleNamespace(base_dir=DATA_ROOT), project_id=project_id, registry=registry)
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=150)
    source_root = Path(project["source_path"])
    snapshot_sources = {row[0] for row in files}
    existing = service.collection.get(include=["metadatas"])
    indexed = skipped = removed = chunks = 0
    for metadata in existing.get("metadatas", []) or []:
        source = metadata.get("source")
        if source and source not in snapshot_sources:
            service.remove_document_chunks(source)
            removed += 1
    for relative, digest, language, module in files:
        source = source_root / relative
        if not source.is_file() or source.is_symlink():
            service.remove_document_chunks(relative)
            removed += 1
            continue
        existing_metadata = service.document_chunk_metadata(relative)
        if existing_metadata and all(item.get("sha256") == digest for item in existing_metadata):
            skipped += 1
            chunks += len(existing_metadata)
            continue
        parts = splitter.split_text(source.read_text(encoding="utf-8", errors="replace"))
        metadata = [{"source": relative, "sha256": digest, "language": language, "module": module, "scope": "project-code", "chunk_index": index} for index in range(len(parts))]
        ids = [hashlib.sha256(f"{project_id}:{relative}:{digest}:{index}".encode()).hexdigest() for index in range(len(parts))]
        service.replace_document_chunks(relative, parts, metadata, ids)
        indexed += 1
        chunks += len(parts)
    return {"project_id": project_id, "documents": len(files), "chunks": chunks,
            "indexed_documents": indexed, "skipped_documents": skipped,
            "removed_documents": removed}
