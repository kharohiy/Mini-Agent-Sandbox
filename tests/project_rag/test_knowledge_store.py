import tempfile
import unittest
from pathlib import Path

from knowledge_store import KnowledgeStore
from project_registry import ProjectRegistry


class KnowledgeStoreTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.source = root / "source"
        self.source.mkdir()
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = self.registry.register(self.source, "Demo Project")
        self.store = KnowledgeStore(self.registry, root / "global")

    def tearDown(self):
        self.temporary.cleanup()

    def test_project_and_global_knowledge_are_isolated_and_evidence_gated(self):
        project_card = self.store.create(scope="project", project_id=self.project["id"], title="Core boundary", problem="Avoid cycles", decision="Use :core", rationale="Shared contracts", tags=["architecture"], affected_modules=[":core"])
        global_card = self.store.create(scope="global", title="Docker only", problem="Host safety", decision="Validate in Docker", rationale="Isolation", evidence=[{"type": "policy", "reference": "security-contract"}])
        self.assertEqual(self.store.list("project", self.project["id"])[0]["id"], project_card["id"])
        self.assertEqual(self.store.list("global")[0]["id"], global_card["id"])
        with self.assertRaises(ValueError):
            self.store.verify("project", project_card["id"], self.project["id"])
        verified = self.store.verify("global", global_card["id"])
        self.assertEqual(verified["status"], "verified")
        self.assertEqual(verified["confidence"], "verified")

    def test_registry_reuses_project_id_and_creates_only_state_outside_source(self):
        repeated = self.registry.register(self.source, "Different Name")
        self.assertEqual(repeated["id"], self.project["id"])
        self.assertFalse((self.source / ".mini-agent").exists())
        self.assertTrue((Path(self.project["state_dir"]) / "knowledge").is_dir())

    def test_evidence_is_append_only_and_history_is_available(self):
        card = self.store.create(scope="global", title="Network isolation", problem="Build safety", decision="Disable network", rationale="Contain execution")
        with self.assertRaises(ValueError):
            self.store.verify("global", card["id"])
        updated = self.store.add_evidence("global", card["id"], {"type": "policy", "reference": "security-contract", "description": "executor rule"})
        self.assertEqual(len(updated["evidence"]), 1)
        self.assertEqual(self.store.search("global", "network")[0]["id"], card["id"])
        self.store.verify("global", card["id"])
        self.store.set_status("global", card["id"], "archived")
        self.assertEqual([item["version"] for item in self.store.versions("global", card["id"])], [1, 2, 3, 4])
        self.assertEqual([item["action"] for item in self.store.audit("global", card["id"])], ["created", "evidence_added", "verified", "archived"])


if __name__ == "__main__":
    unittest.main()
