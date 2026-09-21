import hashlib
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from project_rag_ingestion import ingest_project


class FakeCollection:
    def __init__(self):
        self.records = {}

    def get(self, where=None, include=None):
        entries = list(self.records.items())
        if where:
            entries = [(key, value) for key, value in entries if all(value["metadata"].get(k) == v for k, v in where.items())]
        return {"ids": [key for key, _ in entries], "metadatas": [value["metadata"] for _, value in entries]}


class FakeService:
    collection = FakeCollection()
    replacements = []

    def __init__(self, *args, **kwargs):
        pass

    def document_chunk_metadata(self, source):
        return self.collection.get(where={"source": source})["metadatas"]

    def replace_document_chunks(self, source, chunks, metadata, ids):
        self.replacements.append(source)
        self.remove_document_chunks(source)
        for chunk, item, chunk_id in zip(chunks, metadata, ids):
            self.collection.records[chunk_id] = {"document": chunk, "metadata": item}

    def remove_document_chunks(self, source):
        for chunk_id, value in list(self.collection.records.items()):
            if value["metadata"].get("source") == source:
                del self.collection.records[chunk_id]


class FakeRegistry:
    def __init__(self, source, state):
        self.source, self.state = source, state

    def get(self, project_id):
        return {"source_path": str(self.source)}

    def state_dir(self, project_id):
        return self.state


class ProjectRagIngestionTests(unittest.TestCase):
    def setUp(self):
        FakeService.collection, FakeService.replacements = FakeCollection(), []
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        self.source, self.state = root / "source", root / "state"
        self.source.mkdir(); (self.state / "snapshot").mkdir(parents=True)
        self.registry = FakeRegistry(self.source, self.state)
        self.write_snapshot({"src/A.kt": "class A", "src/B.kt": "class B"})

    def tearDown(self):
        self.temp.cleanup()

    def write_snapshot(self, sources):
        db = sqlite3.connect(self.state / "snapshot" / "project_snapshot.sqlite")
        try:
            db.execute("DROP TABLE IF EXISTS files")
            db.execute("CREATE TABLE files (path TEXT, sha256 TEXT, language TEXT, module TEXT)")
            for relative, text in sources.items():
                target = self.source / relative; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(text, encoding="utf-8")
                db.execute("INSERT INTO files VALUES (?, ?, 'kotlin', ':app')", (relative, hashlib.sha256(text.encode()).hexdigest()))
            db.commit()
        finally:
            db.close()

    def ingest(self):
        with patch("project_rag_ingestion.SandboxRagService", FakeService):
            return ingest_project("demo", registry=self.registry)

    def test_rerun_skips_unchanged_chunks_with_deterministic_ids(self):
        first = self.ingest()
        ids = set(FakeService.collection.records)
        second = self.ingest()
        self.assertEqual(first["indexed_documents"], 2)
        self.assertEqual(second["indexed_documents"], 0)
        self.assertEqual(second["skipped_documents"], 2)
        self.assertEqual(set(FakeService.collection.records), ids)

    def test_changed_source_replaces_only_its_chunks_and_removed_source_is_deindexed(self):
        self.ingest()
        self.write_snapshot({"src/A.kt": "class A { fun changed() = 1 }"})
        result = self.ingest()
        self.assertEqual(result["indexed_documents"], 1)
        self.assertEqual(result["removed_documents"], 1)
        self.assertEqual({item["metadata"]["source"] for item in FakeService.collection.records.values()}, {"src/A.kt"})


if __name__ == "__main__":
    unittest.main()
