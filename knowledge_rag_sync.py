"""Evidence-gated synchronization from knowledge cards to canonical Chroma RAG."""
from __future__ import annotations

import json
from types import SimpleNamespace

from knowledge_store import KnowledgeStore
from project_registry import DATA_ROOT, ProjectRegistry
from rag_service import SandboxRagService


def _document(card: dict) -> str:
    evidence = "\n".join(f"- {item['type']}: {item['reference']} — {item['description']}" for item in card["evidence"])
    return f"# {card['title']}\n\nProblem: {card['problem']}\n\nDecision: {card['decision']}\n\nRationale: {card['rationale']}\n\nEvidence:\n{evidence}"


def sync_card(card_id: str, *, scope: str, project_id: str | None = None,
              store: KnowledgeStore | None = None, registry: ProjectRegistry | None = None) -> dict:
    """Synchronize one card; only verified cards can be written to Chroma."""
    registry = registry or ProjectRegistry()
    store = store or KnowledgeStore(registry)
    cards = store.list(scope, project_id)
    card = next((item for item in cards if item["id"] == card_id), None)
    if not card:
        raise FileNotFoundError("knowledge card was not found")
    service = SandboxRagService("local-operator", SimpleNamespace(base_dir=DATA_ROOT),
                                project_id=project_id, registry=registry)
    if card["status"] in {"deprecated", "archived"}:
        service.remove_knowledge_card(card_id, scope)
        return {"card_id": card_id, "action": "deindexed", "status": card["status"]}
    if card["status"] != "verified":
        raise ValueError("only verified cards can be synchronized to RAG")
    metadata = {
        "card_id": card_id, "scope": scope, "status": "verified",
        "project_id": project_id or "", "modules": json.dumps(card["affected_modules"]),
        "evidence": json.dumps(card["evidence"], ensure_ascii=False),
    }
    service.replace_verified_knowledge_card(card_id, _document(card), metadata)
    return {"card_id": card_id, "action": "indexed", "status": "verified"}
