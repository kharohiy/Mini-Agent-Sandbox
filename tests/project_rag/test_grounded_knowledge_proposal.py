import sqlite3
import tempfile
import unittest
from pathlib import Path

from grounded_knowledge_proposal import create_grounded_project_knowledge_draft
from knowledge_store import KnowledgeStore
from project_registry import ProjectRegistry


class GroundedKnowledgeProposalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        source = root / "source"
        source.mkdir()
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = self.registry.register(source, "Demo")
        self.store = KnowledgeStore(self.registry, root / "global")
        database = self.registry.state_dir(self.project["id"]) / "snapshot" / "project_snapshot.sqlite"
        connection = sqlite3.connect(database)
        try:
            connection.execute("CREATE TABLE files (path TEXT, sha256 TEXT)")
            connection.execute("INSERT INTO files VALUES (?, ?)", ("app/Main.kt", "a" * 64))
            connection.commit()
        finally:
            connection.close()

    def tearDown(self):
        self.temporary.cleanup()

    def proposal(self, evidence):
        return create_grounded_project_knowledge_draft(
            project_id=self.project["id"],
            question="Where is the entry point?",
            candidate_fact="Main.kt contains the entry point.",
            title="Application entry point",
            evidence=evidence,
            registry=self.registry,
            store=self.store,
        )

    def valid_evidence(self):
        return [{
            "project_id": self.project["id"],
            "scope": "project-code",
            "source": "app/Main.kt",
            "sha256": "a" * 64,
        }]

    def test_valid_current_project_evidence_creates_draft_only(self):
        result = self.proposal(self.valid_evidence())
        card = result["card"]
        self.assertEqual(result["proposal_status"], "draft")
        self.assertEqual(card["status"], "draft")
        self.assertEqual(card["evidence"], [{"type": "project-code", "reference": "app/Main.kt", "description": f"sha256={'a' * 64}"}])
        actions = self.store.audit("project", card["id"], self.project["id"])
        self.assertEqual([item["action"] for item in actions], ["created"])

    def test_global_missing_stale_and_cross_project_evidence_are_rejected(self):
        valid = self.valid_evidence()[0]
        invalid_cases = [
            [],
            [{**valid, "scope": "global-library"}],
            [{**valid, "source": "app/Missing.kt"}],
            [{**valid, "sha256": "b" * 64}],
            [{**valid, "project_id": "other--12345678"}],
        ]
        for evidence in invalid_cases:
            with self.subTest(evidence=evidence):
                with self.assertRaises(ValueError):
                    self.proposal(evidence)


if __name__ == "__main__":
    unittest.main()
