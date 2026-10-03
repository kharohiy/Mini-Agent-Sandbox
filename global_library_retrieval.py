"""Read the existing shared book collection without opening a project or user RAG."""

import hashlib
import re
from pathlib import Path

from model_router import EmbeddingRequest, get_default_model_router


LIBRARY_PATH = Path(__file__).resolve().parent / "data/knowledge/global/chroma_db"
LIBRARY_COLLECTION = "android_architecture_library"


def _section_key(metadata):
    headings = tuple(str(metadata.get(key, "")) for key in (
        "Header 1", "Header 2", "Header 3",
    ))
    return headings if any(headings) else (str(metadata.get("context", "")),)


def _with_same_section_continuation(collection, item, cache):
    """Attach one bounded successor when a book paragraph continues next chunk."""
    chunk_id, text, metadata = item
    source = metadata.get("source")
    if (not isinstance(source, str) or not source.lower().endswith(".pdf")
            or "/" in source or "\\" in source or metadata.get("project_id")
            or not metadata.get("context")):
        return chunk_id, text, metadata, []
    if source not in cache:
        result = collection.get(
            where={"source": source}, include=["documents", "metadatas"],
        )
        rows = list(zip(
            result.get("ids", []), result.get("documents", []),
            result.get("metadatas", []), strict=True,
        ))
        if rows and all(isinstance(row[2].get("chunk_index"), int) for row in rows):
            rows.sort(key=lambda row: row[2]["chunk_index"])
        cache[source] = rows
    rows = cache[source]
    position = next((index for index, row in enumerate(rows) if row[0] == chunk_id), None)
    if position is None or position + 1 >= len(rows):
        return chunk_id, text, metadata, []
    next_id, next_text, next_metadata = rows[position + 1]
    if (_section_key(next_metadata) != _section_key(metadata)
            or not isinstance(next_text, str) or not next_text.strip()):
        return chunk_id, text, metadata, []
    combined = text.rstrip() + "\n\n[CONTINUATION]\n" + next_text.lstrip()
    return chunk_id, combined, metadata, [next_id]


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
    source_cache = {}
    for item in list(selected.values())[:top_k]:
        chunk_id, text, metadata, continuation_ids = _with_same_section_continuation(
            collection, item, source_cache,
        )
        if not isinstance(text, str) or not text.strip() or not isinstance(metadata, dict):
            raise ValueError("Invalid book chunk")
        source = metadata.get("source")
        if (not isinstance(source, str) or not source.lower().endswith(".pdf")
                or "/" in source or "\\" in source or metadata.get("project_id")):
            raise ValueError("Invalid book source")
        excerpt = text[:4000]
        references.append({
            "scope": "global-library", "source": source, "chunk_id": chunk_id,
            "chunk_ids": [chunk_id, *continuation_ids],
            "text": excerpt, "sha256": hashlib.sha256(excerpt.encode("utf-8")).hexdigest(),
        })
    return references
