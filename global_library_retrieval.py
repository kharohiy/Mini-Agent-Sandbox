"""Read the existing shared book collection without opening a project or user RAG."""

import hashlib
import re
from pathlib import Path

from model_router import EmbeddingRequest, get_default_model_router


LIBRARY_PATH = Path(__file__).resolve().parent / "data/knowledge/global/chroma_db"
LIBRARY_COLLECTION = "android_architecture_library"


def _identifier_hits(collection, question):
    """Find bounded literal evidence for camel-case identifiers missed by vectors."""
    identifiers = list(dict.fromkeys(
        word for word in re.findall(r"\b[A-Za-z][A-Za-z0-9]*\b", question)
        if re.search(r"[a-z][A-Z]", word)
    ))[:3]
    if not identifiers:
        return []
    variants = list(dict.fromkeys(
        variant for word in identifiers
        for variant in (word, re.sub(r"([a-z])([A-Z])", r"\1 \2", word).lower())
    ))
    clauses = [{"$contains": variant} for variant in variants]
    result = collection.get(
        where_document={"$or": clauses}, include=["documents", "metadatas"], limit=32,
    )
    hits = []
    for chunk_id, text, metadata in zip(
        result["ids"], result["documents"], result["metadatas"], strict=True,
    ):
        if not isinstance(text, str) or not isinstance(metadata, dict):
            raise ValueError("Invalid book chunk")
        headings = " ".join(str(value) for key, value in metadata.items()
                            if key.startswith("Header") or key == "context").lower()
        # A contents listing is not an explanatory passage, even on an exact hit.
        if re.search(r"\b(contents|table of contents)\b", headings):
            continue
        heading_match = any(variant.lower() in headings for variant in variants)
        hits.append((heading_match, chunk_id, text, metadata))
    hits.sort(key=lambda item: (not item[0], item[1]))
    return [(chunk_id, text, metadata) for _, chunk_id, text, metadata in hits[:2]]


def retrieve_book_references(question, *, top_k=3):
    """Query existing book chunks only; never ingest or create a collection."""
    if not isinstance(question, str) or not question.strip():
        raise ValueError("A non-empty question is required")
    if not isinstance(top_k, int) or not 1 <= top_k <= 3:
        raise ValueError("Book retrieval is limited to 1..3 chunks")
    if not (LIBRARY_PATH / "chroma.sqlite3").is_file():
        raise FileNotFoundError("Shared library is not indexed")

    import chromadb
    from chromadb.config import Settings

    client = chromadb.PersistentClient(
        path=str(LIBRARY_PATH), settings=Settings(anonymized_telemetry=False),
    )
    collection = client.get_collection(LIBRARY_COLLECTION, embedding_function=None)
    count = collection.count()
    if not count:
        return []
    embedded = get_default_model_router().embed(EmbeddingRequest(
        model="ollama/nomic-embed-text", inputs=[question],
    ))
    result = collection.query(
        query_embeddings=[embedded.data[0]["embedding"]], n_results=min(count, top_k),
        include=["documents", "metadatas"],
    )
    semantic = list(zip(
        result["ids"][0], result["documents"][0], result["metadatas"][0], strict=True,
    ))
    literal = _identifier_hits(collection, question)
    selected = {}
    for item in literal + semantic:
        selected.setdefault(item[0], item)
    references = []
    for chunk_id, text, metadata in list(selected.values())[:top_k]:
        if not isinstance(text, str) or not text.strip() or not isinstance(metadata, dict):
            raise ValueError("Invalid book chunk")
        source = metadata.get("source")
        if (not isinstance(source, str) or not source.lower().endswith(".pdf")
                or "/" in source or "\\" in source or metadata.get("project_id")):
            raise ValueError("Invalid book source")
        excerpt = text[:4000]
        references.append({
            "scope": "global-library", "source": source, "chunk_id": chunk_id,
            "text": excerpt, "sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        })
    return references
