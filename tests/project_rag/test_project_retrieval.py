import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from project_registry import ProjectRegistry
from project_retrieval import (
    _chroma_hits,
    _fuse_project_hits,
    _literal_project_hits,
    _snapshot_hits,
    AmbiguousProjectFile,
    format_retrieval_context,
    retrieve_global_technical_references,
    retrieve_project_context,
)


class Collection:
    def __init__(self, document, metadata):
        self.document, self.metadata = document, metadata

    def count(self):
        return 1

    def query(self, **kwargs):
        where = kwargs.get("where")
        if where and any(self.metadata.get(key) != value for key, value in where.items()):
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        return {"documents": [[self.document]], "metadatas": [[self.metadata]], "distances": [[0.1]]}

    def get(self, **kwargs):
        return {"documents": [self.document], "metadatas": [self.metadata]}


class MultiChunkCollection:
    def __init__(self, records):
        self.records = records

    def count(self):
        return len(self.records)

    def get(self, **kwargs):
        where = kwargs.get("where", {})
        records = [
            record for record in self.records
            if all(record["metadata"].get(key) == value for key, value in where.items())
        ]
        return {
            "documents": [record["document"] for record in records],
            "metadatas": [record["metadata"] for record in records],
        }


class FakeRagService:
    def __init__(self, *args, **kwargs):
        self.collection = Collection("class MainActivity", {"source": "app/MainActivity.kt", "module": ":app"})
        self.knowledge_collection = Collection("Use repository boundary", {"card_id": "kc_project", "modules": '[":data"]'})
        self.document_collection = Collection("Owner supplied API notes", {"source": "notes.md", "ingestion_status": "active"})
        self.library_collection = Collection("Navigation is state-driven", {"source": "Compose.pdf", "context": "Navigation"})
        self.global_knowledge_collection = Collection("Validate in Docker", {"card_id": "kc_global", "modules": "[]"})


class ProjectRetrievalTests(unittest.TestCase):
    def test_explicit_filename_survives_generic_words_and_semantic_noise(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "snapshot").mkdir()
            db = sqlite3.connect(root / "snapshot/project_snapshot.sqlite")
            db.executescript("CREATE TABLE files (path TEXT, sha256 TEXT, module TEXT); CREATE TABLE symbols (file_path TEXT, name TEXT);")
            target = "core/domain/model/CheatCodes.kt"
            distractors = [f"app/gamescheats/Other{index}.kt" for index in range(6)]
            db.executemany("INSERT INTO files VALUES (?, ?, ':core')",
                           [(path, "a" * 64) for path in distractors + [target]])
            db.commit()
            db.close()
            registry = SimpleNamespace(state_dir=lambda _: root, get=lambda _: {})
            query = "does project gta cheats app have file CheatCodes.kt? If yes answer, what in this file CheatCodes.kt ?"
            records = [{"document": "data class CheatCodes(val groups: List<CheatCodeGroup>)",
                        "metadata": {"source": target, "sha256": "a" * 64}}]
            service = SimpleNamespace(collection=MultiChunkCollection(records))
            with patch("project_retrieval.SandboxRagService", return_value=service), \
                 patch("project_retrieval._chroma_hits") as semantic:
                hits = retrieve_project_context("demo", query, registry=registry, prefer_exact_sources=True)
            semantic.assert_not_called()
            code = [hit for hit in hits if hit["scope"] == "project-code"]
            self.assertEqual([hit["source"] for hit in code], [target])
            self.assertIn("CheatCodeGroup", code[0]["text"])
            self.assertEqual(code[0]["chunk_hashes"], ["a" * 64])

    def test_ambiguous_basename_requires_path_and_missing_file_has_no_substitute(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "snapshot").mkdir()
            db = sqlite3.connect(root / "snapshot/project_snapshot.sqlite")
            db.executescript("CREATE TABLE files (path TEXT, sha256 TEXT, module TEXT); CREATE TABLE symbols (file_path TEXT, name TEXT);")
            db.executemany("INSERT INTO files VALUES (?, ?, ':core')", [
                ("one/Model.kt", "a" * 64), ("two/Model.kt", "b" * 64),
                ("one/ModelRepository.kt", "c" * 64),
            ])
            db.commit()
            db.close()
            registry = SimpleNamespace(state_dir=lambda _: root, get=lambda _: {})
            with self.assertRaisesRegex(AmbiguousProjectFile, "Specify the project-relative path"):
                _snapshot_hits(registry, "demo", "Explain Model.kt", 4)
            exact = _snapshot_hits(registry, "demo", "Explain one/Model.kt", 4)
            self.assertEqual([hit["source"] for hit in exact], ["one/Model.kt"])
            with patch("project_retrieval.SandboxRagService"), \
                 patch("project_retrieval._chroma_hits") as semantic:
                self.assertEqual(retrieve_project_context("demo", "Explain Missing.kt", registry=registry), [])
            semantic.assert_not_called()

    def test_context_is_ordered_and_carries_trust_source_and_module(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            db_path = registry.state_dir(project["id"]) / "snapshot" / "project_snapshot.sqlite"
            db = sqlite3.connect(db_path)
            try:
                db.executescript("CREATE TABLE files (path TEXT, sha256 TEXT, module TEXT); CREATE TABLE symbols (file_path TEXT, name TEXT);")
                db.execute("INSERT INTO files VALUES ('app/MainActivity.kt', ?, ':app')", ("a" * 64,))
                db.execute("INSERT INTO symbols VALUES ('app/MainActivity.kt', 'MainActivity')")
                db.commit()
            finally:
                db.close()
            with patch("project_retrieval.SandboxRagService", FakeRagService):
                hits = retrieve_project_context(project["id"], "MainActivity", registry=registry)
            self.assertEqual(
                [hit["trust"] for hit in hits],
                ["snapshot", "project code", "verified project knowledge", "user supplied project document"],
            )
            context = format_retrieval_context(hits)
            self.assertIn("SOURCE: app/MainActivity.kt", context)
            self.assertIn("MODULE: :app", context)
            self.assertNotIn("VERIFY GLOBAL KNOWLEDGE", context)

    def test_global_library_is_a_separate_optional_stage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            with patch("project_retrieval.SandboxRagService", FakeRagService):
                hits = retrieve_global_technical_references(project["id"], "navigation", registry=registry)
            self.assertEqual([(hit["scope"], hit["trust"], hit["source"]) for hit in hits], [
                ("global-library", "technical reference", "Compose.pdf"),
            ])

    def test_literal_project_match_is_ranked_before_incidental_semantic_hit(self):
        collection = Collection(
            '<application tools:targetApi="31">',
            {"source": "app/src/main/AndroidManifest.xml", "module": ":app"},
        )
        hits = _literal_project_hits(
            collection,
            "What tools targetApi is declared in the Android manifest?",
            4,
        )
        self.assertEqual([hit["source"] for hit in hits], ["app/src/main/AndroidManifest.xml"])
        self.assertGreaterEqual(hits[0]["lexical_matches"], 2)

    def test_literal_project_match_assembles_adjacent_chunks_from_selected_source(self):
        collection = MultiChunkCollection([
            {
                "document": (
                    '<activity android:name=".MainActivity">\n'
                    '<intent-filter><action android:name="android.intent.action.MAIN" />'
                ),
                "metadata": {
                    "source": "app/src/main/AndroidManifest.xml",
                    "sha256": "a" * 64,
                    "module": ":app",
                    "chunk_index": 0,
                },
            },
            {
                "document": (
                    '<category android:name="android.intent.category.LAUNCHER" />'
                    "</intent-filter></activity>"
                ),
                "metadata": {
                    "source": "app/src/main/AndroidManifest.xml",
                    "sha256": "a" * 64,
                    "module": ":app",
                    "chunk_index": 1,
                },
            },
            {
                "document": "class OtherActivity",
                "metadata": {"source": "app/OtherActivity.kt", "module": ":app", "chunk_index": 0},
            },
        ])
        hits = _literal_project_hits(
            collection,
            "Which activity is declared with MAIN and LAUNCHER in the Android manifest?",
            1,
        )
        self.assertEqual(hits[0]["source"], "app/src/main/AndroidManifest.xml")
        self.assertIn('android:name=".MainActivity"', hits[0]["text"])
        self.assertIn("android.intent.action.MAIN", hits[0]["text"])
        self.assertIn("android.intent.category.LAUNCHER", hits[0]["text"])
        self.assertNotIn("OtherActivity", hits[0]["text"])
        self.assertEqual(hits[0]["chunk_hashes"], ["a" * 64, "a" * 64])

    def test_fusion_keeps_selected_source_assembly_over_semantic_tail_chunk(self):
        semantic = [{
            "scope": "project-code", "source": "app/src/main/AndroidManifest.xml",
            "text": "android.intent.category.LAUNCHER", "semantic_distance": 0.1,
        }]
        exact = [{
            "scope": "project-code", "source": "app/src/main/AndroidManifest.xml",
            "text": "android:name=\".MainActivity\" android.intent.action.MAIN android.intent.category.LAUNCHER",
            "lexical_matches": 3,
        }]
        hits = _fuse_project_hits("MainActivity MAIN LAUNCHER", exact, semantic, 1)
        self.assertIn(".MainActivity", hits[0]["text"])
        self.assertIn("android.intent.action.MAIN", hits[0]["text"])

    def test_pending_project_document_is_not_retrieved(self):
        pending = Collection("uncommitted document", {"source": "notes.md", "ingestion_status": "pending"})
        hits = _chroma_hits(
            pending,
            "document",
            "project-document",
            "user supplied project document",
            4,
            where={"ingestion_status": "active"},
        )
        self.assertEqual(hits, [])


if __name__ == "__main__":
    unittest.main()
