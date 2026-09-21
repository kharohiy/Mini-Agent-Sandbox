import tempfile
import unittest
from pathlib import Path

from project_registry import ProjectRegistry
from project_telemetry import ProjectTelemetryStore


class ProjectTelemetryTests(unittest.TestCase):
    def test_events_are_project_scoped_aggregated_and_payload_free(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            store = ProjectTelemetryStore(registry)
            store.record(project["id"], event="validation", outcome="validated")
            store.record(project["id"], event="model", outcome="success", provider="ollama", tokens=120, cost_usd=0.0012)
            self.assertEqual(store.summary(project["id"])["tokens"], 120)
            self.assertEqual(store.summary(project["id"])["by_provider"], {"ollama": 1})

    def test_invalid_or_unscoped_events_are_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            store = ProjectTelemetryStore(registry)
            with self.assertRaises(ValueError):
                store.record(project["id"], event="prompt", outcome="success")
            with self.assertRaises(FileNotFoundError):
                store.record("unknown--00000000", event="model", outcome="success")


if __name__ == "__main__":
    unittest.main()
