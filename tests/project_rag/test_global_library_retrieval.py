import os
import unittest

import chromadb
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

from global_library_retrieval import (
    LIBRARY_COLLECTION, LIBRARY_PATH, _identifier_hits, retrieve_book_references,
)


class GlobalLibraryRetrievalTests(unittest.TestCase):
    def test_identifier_lookup_finds_spaced_name_and_excludes_contents(self):
        collection = MagicMock()
        collection.get.return_value = {
            "ids": ["toc", "incidental", "explanation"],
            "documents": ["Slot table .... 52", "Use a slot table", "A slot table stores groups"],
            "metadatas": [
                {"source": "Book.pdf", "Header 1": "**Contents**"},
                {"source": "Book.pdf", "Header 1": "Other topic"},
                {"source": "Book.pdf", "Header 1": "The slot table in depth"},
            ],
        }
        hits = _identifier_hits(collection, "Explain SlotTable")
        self.assertEqual([hit[0] for hit in hits], ["explanation", "incidental"])
        collection.get.assert_called_once_with(
            where_document={"$or": [{"$contains": "SlotTable"}, {"$contains": "slot table"}]},
            include=["documents", "metadatas"], limit=32,
        )

    def test_identifier_evidence_precedes_unrelated_semantic_results(self):
        collection = MagicMock()
        collection.count.return_value = 3
        collection.query.return_value = {
            "ids": [["intro", "lexical"]],
            "documents": [["Introduction", "slot table groups"]],
            "metadatas": [[{"source": "Book.pdf"}, {"source": "Book.pdf"}]],
        }
        collection.get.return_value = {
            "ids": ["lexical"], "documents": ["slot table groups"],
            "metadatas": [{"source": "Book.pdf", "Header 1": "Slot table"}],
        }
        with patch("pathlib.Path.is_file", return_value=True), \
             patch.object(chromadb, "PersistentClient") as constructor, \
             patch("global_library_retrieval.get_default_model_router") as router:
            constructor.return_value.get_collection.return_value = collection
            router.return_value.embed.return_value = SimpleNamespace(data=[{"embedding": [0.1]}])
            hits = retrieve_book_references("Explain SlotTable")
        self.assertEqual([hit["chunk_id"] for hit in hits], ["lexical", "intro"])

    def test_only_existing_global_collection_is_opened_and_embedding_is_local(self):
        client = MagicMock()
        collection = client.get_collection.return_value
        collection.count.return_value = 1
        collection.query.return_value = {
            "ids": [["book-1"]], "documents": [["coroutine text"]],
            "metadatas": [[{"source": "Kotlin In Action.pdf"}]],
        }
        with patch("pathlib.Path.is_file", return_value=True), \
             patch.object(chromadb, "PersistentClient", return_value=client) as constructor, \
             patch("global_library_retrieval.get_default_model_router") as router:
            router.return_value.embed.return_value = SimpleNamespace(data=[{"embedding": [0.1]}])
            hits = retrieve_book_references("coroutines")
        self.assertEqual(constructor.call_args.kwargs["path"], str(LIBRARY_PATH))
        client.get_collection.assert_called_once_with(LIBRARY_COLLECTION, embedding_function=None)
        self.assertEqual([call[0] for call in client.method_calls], ["get_collection"])
        request = router.return_value.embed.call_args.args[0]
        self.assertEqual(request.model, "ollama/nomic-embed-text")
        self.assertEqual(request.privacy_policy.value, "local_only")
        self.assertEqual(hits[0]["scope"], "global-library")
        self.assertEqual(hits[0]["chunk_id"], "book-1")
        self.assertEqual(len(hits[0]["sha256"]), 64)
        collection.query.assert_called_once_with(
            query_embeddings=[[0.1]], n_results=1, include=["documents", "metadatas"],
        )

    def test_missing_library_does_not_create_database_or_call_model(self):
        with patch("pathlib.Path.is_file", return_value=False), \
             patch.object(chromadb, "PersistentClient") as constructor, \
             patch("global_library_retrieval.get_default_model_router") as router:
            with self.assertRaises(FileNotFoundError):
                retrieve_book_references("question")
        constructor.assert_not_called()
        router.assert_not_called()

    def test_project_metadata_in_book_results_is_rejected(self):
        collection = MagicMock()
        collection.count.return_value = 1
        collection.query.return_value = {
            "ids": [["invalid"]], "documents": [["project text"]],
            "metadatas": [[{"source": "Book.pdf", "project_id": "some-project"}]],
        }
        with patch("pathlib.Path.is_file", return_value=True), \
             patch.object(chromadb, "PersistentClient") as constructor, \
             patch("global_library_retrieval.get_default_model_router") as router:
            constructor.return_value.get_collection.return_value = collection
            router.return_value.embed.return_value = SimpleNamespace(data=[{"embedding": [0.1]}])
            with self.assertRaisesRegex(ValueError, "book source"):
                retrieve_book_references("question")
