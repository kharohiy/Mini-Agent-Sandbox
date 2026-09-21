import tempfile
import unittest
from pathlib import Path

from project_document_ingestion import (
    ingest_project_document,
    list_project_documents,
    remove_project_document,
)
from project_registry import ProjectRegistry


class FakeCollection:
    def __init__(self):
        self.records = {}
        self.fail_after_pending = False
        self.calls = 0

    def upsert(self, *, documents, metadatas, ids):
        self.calls += 1
        for document, metadata, chunk_id in zip(documents, metadatas, ids):
            self.records[chunk_id] = {"document": document, "metadata": metadata}
        if self.fail_after_pending and self.calls == 2:
            raise RuntimeError("embedding unavailable")

    def delete(self, *, ids):
        for chunk_id in ids:
            self.records.pop(chunk_id, None)


class FakeService:
    def __init__(self):
        self.document_collection = FakeCollection()


class ProjectDocumentIngestionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.source_a = root / "source-a"
        self.source_a.mkdir()
        self.source_b = root / "source-b"
        self.source_b.mkdir()
        self.project_a = self.registry.register(self.source_a, "Project A")
        self.project_b = self.registry.register(self.source_b, "Project B")
        self.service = FakeService()

    def tearDown(self):
        self.temporary.cleanup()

    def ingest(self, project_id, content="Owner API notes explain the request boundary."):
        return ingest_project_document(
            project_id,
            source="owner-notes.md",
            content=content,
            content_type="text/markdown",
            confirmed=True,
            registry=self.registry,
            service=self.service,
        )

    def test_explicit_ingestion_is_idempotent_and_manifest_is_metadata_only(self):
        first = self.ingest(self.project_a["id"])
        second = self.ingest(self.project_a["id"])
        self.assertEqual(first["action"], "indexed")
        self.assertEqual(second["action"], "unchanged")
        documents = list_project_documents(self.project_a["id"], registry=self.registry)
        self.assertEqual(len(documents), 1)
        self.assertEqual(documents[0]["project_id"], self.project_a["id"])
        self.assertNotIn("content", documents[0])
        self.assertEqual(len(self.service.document_collection.records), documents[0]["chunk_count"])

    def test_changed_content_replaces_only_its_own_deterministic_chunks(self):
        self.ingest(self.project_a["id"])
        old_ids = set(self.service.document_collection.records)
        result = self.ingest(self.project_a["id"], "Revised owner API notes explain the request boundary and retries.")
        self.assertEqual(result["action"], "replaced")
        self.assertFalse(old_ids.intersection(self.service.document_collection.records))
        self.assertEqual(
            {item["metadata"]["project_id"] for item in self.service.document_collection.records.values()},
            {self.project_a["id"]},
        )

    def test_project_and_legacy_boundaries_fail_closed(self):
        self.ingest(self.project_a["id"])
        self.assertEqual(list_project_documents(self.project_b["id"], registry=self.registry), [])
        with self.assertRaises(FileNotFoundError):
            remove_project_document(
                self.project_b["id"], "owner-notes.md", confirmed=True,
                registry=self.registry, service=self.service,
            )
        with self.assertRaises(FileNotFoundError):
            ingest_project_document(
                "not-a-project", source="owner-notes.md", content="x", confirmed=True,
                registry=self.registry, service=self.service,
            )
        with self.assertRaises(ValueError):
            ingest_project_document(
                self.project_a["id"], source="..\\outside.md", content="x", confirmed=True,
                registry=self.registry, service=self.service,
            )

    def test_embedding_failure_cleans_pending_chunks_and_never_records_success(self):
        self.service.document_collection.fail_after_pending = True
        with self.assertRaisesRegex(RuntimeError, "embedding unavailable"):
            self.ingest(self.project_a["id"])
        self.assertEqual(self.service.document_collection.records, {})
        self.assertEqual(list_project_documents(self.project_a["id"], registry=self.registry), [])

    def test_confirmation_is_required_for_ingestion_and_removal(self):
        with self.assertRaises(ValueError):
            ingest_project_document(
                self.project_a["id"], source="owner-notes.md", content="x",
                registry=self.registry, service=self.service,
            )
        self.ingest(self.project_a["id"])
        with self.assertRaises(ValueError):
            remove_project_document(
                self.project_a["id"], "owner-notes.md", registry=self.registry, service=self.service,
            )


if __name__ == "__main__":
    unittest.main()
