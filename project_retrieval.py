"""Project-scoped retrieval for planning; never reads the connected source tree."""
from __future__ import annotations

import sqlite3
import re
from types import SimpleNamespace

from project_registry import DATA_ROOT, ProjectRegistry
from rag_service import SandboxRagService


def _snapshot_hits(registry: ProjectRegistry, project_id: str, query: str, limit: int) -> list[dict]:
    database = registry.state_dir(project_id) / "snapshot" / "project_snapshot.sqlite"
    if not database.is_file():
        return []
    normalized = query.casefold()
    tokens = re.findall(r"[a-z0-9]+", normalized)
    terms = [normalized]
    for token in tokens:
        if len(token) >= 4:
            terms.append(token)
            if token.endswith("s"):
                terms.append(token[:-1])
    for left, right in zip(tokens, tokens[1:]):
        combined = left + right.rstrip("s")
        if len(combined) >= 4:
            terms.append(combined)
    terms = list(dict.fromkeys(terms))
    connection = sqlite3.connect(database)
    try:
        rows = []
        seen = set()
        for term in terms:
            matched = connection.execute("""SELECT f.path, f.sha256, f.module, group_concat(DISTINCT s.name)
                FROM files f LEFT JOIN symbols s ON s.file_path = f.path
                WHERE lower(f.path) LIKE ? OR lower(COALESCE(s.name, '')) LIKE ?
                GROUP BY f.path, f.module ORDER BY f.path LIMIT ?""", (f"%{term}%", f"%{term}%", limit)).fetchall()
            for row in matched:
                if row[0] not in seen:
                    rows.append(row)
                    seen.add(row[0])
                if len(rows) >= limit:
                    break
            if len(rows) >= limit:
                break
    finally:
        connection.close()
    return [{"trust": "snapshot", "scope": "project-snapshot", "source": row[0], "sha256": row[1], "module": row[2],
             "text": f"Snapshot: {row[0]} | module: {row[2]} | symbols: {row[3] or ''}"} for row in rows]


def _chroma_hits(collection, query: str, scope: str, trust: str, limit: int) -> list[dict]:
    if collection.count() == 0:
        return []
    result = collection.query(
        query_texts=[query],
        n_results=min(limit, collection.count()),
        include=["documents", "metadatas", "distances"],
    )
    documents = result.get("documents", [[]])[0] or []
    metadata = result.get("metadatas", [[]])[0] or []
    distances = result.get("distances", [[]])[0] or []
    return [
        {
            "trust": trust,
            "scope": scope,
            "source": item.get("source") or item.get("card_id", "unknown"),
            "sha256": item.get("sha256", ""),
            "module": item.get("module") or item.get("modules", ""),
            "metadata": item,
            "text": text,
            "semantic_distance": distance,
        }
        for text, item, distance in zip(documents, metadata, distances)
    ]


def _literal_project_hits(collection, query: str, limit: int) -> list[dict]:
    """Find direct term matches in stored project chunks without reading source files."""
    if collection.count() == 0:
        return []
    terms = _query_terms(query)
    if not terms:
        return []
    result = collection.get(include=["documents", "metadatas"])
    best_by_source: dict[str, dict] = {}
    for text, metadata in zip(result.get("documents", []) or [], result.get("metadatas", []) or []):
        document_terms = {
            token.rstrip("s")
            for token in re.findall(r"[a-z0-9]+", text.casefold())
            if len(token) >= 4
        }
        lexical_matches = len(terms.intersection(document_terms))
        if not lexical_matches:
            continue
        source = metadata.get("source", "unknown")
        candidate = {
            "trust": "project code",
            "scope": "project-code",
            "source": source,
            "sha256": metadata.get("sha256", ""),
            "module": metadata.get("module", ""),
            "metadata": metadata,
            "text": text,
            "lexical_matches": lexical_matches,
        }
        previous = best_by_source.get(source)
        if previous is None or candidate["lexical_matches"] > previous["lexical_matches"]:
            best_by_source[source] = candidate
    return sorted(
        best_by_source.values(),
        key=lambda hit: (-hit["lexical_matches"], hit["source"]),
    )[:limit]


def _query_terms(query: str) -> set[str]:
    return {
        token.rstrip("s")
        for token in re.findall(r"[a-z0-9]+", query.casefold())
        if len(token) >= 4
    }


def _fuse_project_hits(query: str, exact: list[dict], semantic: list[dict], limit: int) -> list[dict]:
    """Fuse lexical source evidence with semantic chunks without requiring an exact question."""
    terms = _query_terms(query)
    candidates: dict[tuple[str, str], dict] = {}
    for position, hit in enumerate(semantic):
        key = (hit["scope"], hit["source"])
        entry = candidates.setdefault(key, hit | {"retrieval_score": 0.0})
        distance = hit.get("semantic_distance")
        entry["retrieval_score"] += 3.0 - min(float(distance or 0.0), 2.0)
        entry["semantic_rank"] = position
    for hit in exact:
        key = (hit["scope"], hit["source"])
        text_terms = set(re.findall(r"[a-z0-9]+", hit["text"].casefold()))
        lexical_matches = len(terms.intersection(text_terms))
        entry = candidates.setdefault(key, hit | {"retrieval_score": 0.0})
        entry["retrieval_score"] += 1.0 + lexical_matches
        entry["lexical_matches"] = lexical_matches
    return sorted(
        candidates.values(),
        key=lambda hit: (-hit["retrieval_score"], hit["source"]),
    )[:limit]


def _source_hits(collection, snapshots: list[dict], limit: int) -> list[dict]:
    """Resolve exact snapshot matches from existing chunks, never the source tree."""
    hits = []
    for snapshot in snapshots[:limit]:
        result = collection.get(where={"source": snapshot["source"]},
                                include=["documents", "metadatas"], limit=32)
        chunks = sorted(zip(result.get("documents", []) or [], result.get("metadatas", []) or []),
                        key=lambda pair: pair[1].get("chunk_index", 0))
        text = "\n".join(text for text, _ in chunks)[:6000]
        if text.strip():
            hits.append({"trust": "project code", "scope": "project-code",
                         "source": snapshot["source"], "sha256": snapshot["sha256"],
                         "module": snapshot["module"], "text": text})
    return hits


def retrieve_project_context(project_id: str, query: str, *, top_k: int = 4,
                             prefer_exact_sources: bool = False,
                             registry: ProjectRegistry | None = None) -> list[dict]:
    """Retrieve ordered, isolated planning context for one registered project."""
    if not query.strip():
        raise ValueError("retrieval query is required")
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    service = SandboxRagService("local-operator", SimpleNamespace(base_dir=DATA_ROOT),
                                project_id=project_id, registry=registry)
    snapshots = _snapshot_hits(registry, project_id, query, top_k)
    exact = _source_hits(service.collection, snapshots, top_k) if prefer_exact_sources else []
    literal = _literal_project_hits(service.collection, query, top_k)
    semantic = _chroma_hits(service.collection, query, "project-code", "project code", top_k)
    project_code = _fuse_project_hits(query, exact + literal, semantic, top_k)
    return (
        snapshots
        + project_code
        + _chroma_hits(service.knowledge_collection, query, "project-knowledge", "verified project knowledge", top_k)
    )


def retrieve_global_technical_references(project_id: str, query: str, *, top_k: int = 2,
                                         registry: ProjectRegistry | None = None) -> list[dict]:
    """Return optional shared technical references after project evidence is selected.

    Global library material is deliberately separate from project retrieval: it
    may explain an evidenced concept, but cannot establish a project fact.
    """
    if not query.strip():
        raise ValueError("retrieval query is required")
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    service = SandboxRagService("local-operator", SimpleNamespace(base_dir=DATA_ROOT),
                                project_id=project_id, registry=registry)
    return _chroma_hits(
        service.library_collection,
        query,
        "global-library",
        "technical reference",
        top_k,
    )


def format_retrieval_context(hits: list[dict]) -> str:
    if not hits:
        return "No relevant project-scoped context."
    blocks = []
    for index, hit in enumerate(hits, 1):
        label = hit["trust"].upper()
        blocks.append(f"[{index}] TRUST: {label} | SCOPE: {hit['scope']} | SOURCE: {hit['source']} | MODULE: {hit['module']}\n{hit['text']}")
    return "\n\n".join(blocks)
