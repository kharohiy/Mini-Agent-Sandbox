"""Deterministic draft proposals from grounded project-Q&A evidence."""
from __future__ import annotations

import sqlite3

from knowledge_store import KnowledgeStore
from project_registry import ProjectRegistry


def _snapshot_hashes(registry: ProjectRegistry, project_id: str) -> dict[str, str]:
    database = registry.state_dir(project_id) / "snapshot" / "project_snapshot.sqlite"
    if not database.is_file():
        raise ValueError("project snapshot is unavailable")
    connection = sqlite3.connect(database)
    try:
        return {path: sha256 for path, sha256 in connection.execute("SELECT path, sha256 FROM files")}
    finally:
        connection.close()


def _validated_evidence(project_id: str, evidence: list[dict], registry: ProjectRegistry) -> list[dict]:
    if not evidence:
        raise ValueError("grounded proposal requires project-code evidence")
    hashes = _snapshot_hashes(registry, project_id)
    validated: list[dict] = []
    seen: set[str] = set()
    for item in evidence:
        if item.get("project_id") != project_id:
            raise ValueError("evidence project does not match proposal project")
        if item.get("scope") != "project-code":
            raise ValueError("only project-code evidence may support a project knowledge proposal")
        source = item.get("source")
        sha256 = item.get("sha256")
        if not isinstance(source, str) or not isinstance(sha256, str):
            raise ValueError("evidence source and sha256 are required")
        if hashes.get(source) != sha256:
            raise ValueError("evidence source is missing or stale for the current project snapshot")
        if source not in seen:
            validated.append({"type": "project-code", "reference": source, "description": f"sha256={sha256}"})
            seen.add(source)
    return validated


def create_grounded_project_knowledge_draft(
    *,
    project_id: str,
    question: str,
    candidate_fact: str,
    evidence: list[dict],
    title: str,
    registry: ProjectRegistry | None = None,
    store: KnowledgeStore | None = None,
) -> dict:
    """Create a draft card only; verification and RAG synchronization stay external."""
    if not all(isinstance(value, str) and value.strip() for value in (question, candidate_fact, title)):
        raise ValueError("question, candidate_fact and title are required")
    registry = registry or ProjectRegistry()
    registry.get(project_id)
    validated = _validated_evidence(project_id, evidence, registry)
    store = store or KnowledgeStore(registry)
    card = store.create(
        scope="project",
        project_id=project_id,
        title=title,
        problem=f"Grounded Q&A question: {question.strip()}",
        decision=candidate_fact.strip(),
        rationale="Draft generated from validated current project-code evidence; explicit human verification is required before indexing.",
        evidence=validated,
    )
    return {"card": card, "proposal_status": "draft", "evidence": validated}
