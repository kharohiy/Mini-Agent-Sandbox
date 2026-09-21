import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path

from project_policy import ProjectPolicyStore, default_policy
from project_registry import ProjectRegistry
from project_retention import ProjectRetentionPreview, RetentionPreviewBlocked


class ProjectRetentionPreviewTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        source = root / "source"
        source.mkdir()
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = self.registry.register(source, "Demo")
        self.policy = ProjectPolicyStore(self.registry)
        self.preview = ProjectRetentionPreview(self.registry, self.policy)

    def tearDown(self):
        self.temporary.cleanup()

    def _write_events(self, category, events):
        directory, filename = (("telemetry", "events.jsonl") if category == "telemetry" else ("policy", "audit.jsonl"))
        path = self.registry.state_dir(self.project["id"]) / directory / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("".join(json.dumps(event) + "\n" for event in events), encoding="utf-8")
        return path

    def test_preview_is_project_isolated_and_uses_utc_retention_boundary(self):
        other_source = Path(self.temporary.name) / "other-source"
        other_source.mkdir()
        other = self.registry.register(other_source, "Other")
        self.policy.update(self.project["id"], default_policy() | {"retention": {"audit_days": 1, "telemetry_days": 1}})
        self._write_events("telemetry", [
            {"created_at": "2025-12-31T23:59:59+00:00", "secret": "must not appear"},
            {"created_at": "2026-01-01T00:00:00+00:00"},
        ])
        other_path = self.registry.state_dir(other["id"]) / "telemetry" / "events.jsonl"
        other_path.parent.mkdir(parents=True, exist_ok=True)
        other_path.write_text('{"created_at":"2000-01-01T00:00:00+00:00"}\n', encoding="utf-8")

        result = self.preview.preview(self.project["id"], now=datetime(2026, 1, 2, tzinfo=timezone.utc))

        self.assertEqual(result["categories"], [
            {"category": "telemetry", "retention_days": 1, "total_events": 2, "expired_events": 1},
            {"category": "audit", "retention_days": 1, "total_events": 1, "expired_events": 0},
        ])
        self.assertNotIn("must not appear", json.dumps(result))

    def test_missing_stores_are_empty_and_preview_does_not_modify_any_scope(self):
        state = self.registry.state_dir(self.project["id"])
        knowledge = state / "knowledge" / "card.json"
        ledger = state / "runs" / "work_ledger.sqlite"
        vault = state / ".vault_key"
        for path in (knowledge, ledger, vault):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"preserve")
        before = {path: path.read_bytes() for path in (knowledge, ledger, vault)}

        result = self.preview.preview(self.project["id"], now=datetime(2026, 1, 2, tzinfo=timezone.utc))

        self.assertEqual(result["categories"], [
            {"category": "telemetry", "retention_days": 30, "total_events": 0, "expired_events": 0},
            {"category": "audit", "retention_days": 30, "total_events": 0, "expired_events": 0},
        ])
        self.assertEqual({path: path.read_bytes() for path in before}, before)

    def test_malformed_event_blocks_preview_without_changing_the_file(self):
        path = self._write_events("telemetry", [{"created_at": "2026-01-01T00:00:00+00:00"}])
        with path.open("a", encoding="utf-8") as event_file:
            event_file.write("not-json\n")
        before = path.read_bytes()

        with self.assertRaisesRegex(RetentionPreviewBlocked, "malformed telemetry event"):
            self.preview.preview(self.project["id"], now=datetime(2026, 1, 2, tzinfo=timezone.utc))

        self.assertEqual(path.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
