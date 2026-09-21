import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from knowledge_rag_sync import sync_card
from knowledge_store import KnowledgeStore
from project_registry import ProjectRegistry


class FakeRagService:
    indexed = []
    removed = []

    def __init__(self, *args, **kwargs):
        self.project_id = kwargs.get("project_id")

    def replace_verified_knowledge_card(self, card_id, document, metadata):
        self.indexed.append((card_id, document, metadata, self.project_id))

    def remove_knowledge_card(self, card_id, scope):
        self.removed.append((card_id, scope, self.project_id))


class KnowledgeRagSyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        root = Path(self.temp.name)
        source = root / "source"
        source.mkdir()
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = self.registry.register(source, "Demo")
        self.store = KnowledgeStore(self.registry, root / "global")
        FakeRagService.indexed, FakeRagService.removed = [], []

    def tearDown(self):
        self.temp.cleanup()

    def test_only_verified_card_is_indexed_with_evidence_and_scope(self):
        card = self.store.create(scope="project", project_id=self.project["id"], title="Boundary", problem="Cycles", decision="Use core", rationale="Contracts", affected_modules=[":core"], evidence=[{"type": "source", "reference": "core/build.gradle.kts", "description": "module boundary"}])
        with patch("knowledge_rag_sync.SandboxRagService", FakeRagService):
            with self.assertRaises(ValueError):
                sync_card(card["id"], scope="project", project_id=self.project["id"], store=self.store, registry=self.registry)
            self.store.verify("project", card["id"], self.project["id"])
            result = sync_card(card["id"], scope="project", project_id=self.project["id"], store=self.store, registry=self.registry)
        self.assertEqual(result["action"], "indexed")
        _, document, metadata, project_id = FakeRagService.indexed[0]
        self.assertIn("core/build.gradle.kts", document)
        self.assertEqual(project_id, self.project["id"])
        self.assertEqual(metadata["scope"], "project")
        self.assertEqual(metadata["modules"], '[":core"]')

    def test_deprecated_card_is_deindexed(self):
        card = self.store.create(scope="global", title="Docker", problem="Safety", decision="Use Docker", rationale="Isolation", evidence=[{"type": "policy", "reference": "contract"}])
        self.store.verify("global", card["id"])
        self.store.set_status("global", card["id"], "deprecated")
        with patch("knowledge_rag_sync.SandboxRagService", FakeRagService):
            result = sync_card(card["id"], scope="global", store=self.store, registry=self.registry)
        self.assertEqual(result["action"], "deindexed")
        self.assertEqual(FakeRagService.removed, [(card["id"], "global", None)])


if __name__ == "__main__":
    unittest.main()
