import tempfile
import unittest
from pathlib import Path

from project_policy import ProjectPolicyStore, default_policy
from project_registry import ProjectRegistry


class ProjectPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        source = root / "source"
        source.mkdir()
        registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = registry.register(source, "Demo")
        self.store = ProjectPolicyStore(registry)

    def tearDown(self):
        self.temporary.cleanup()

    def test_default_policy_is_default_deny_and_auto_apply_is_disabled(self):
        policy = self.store.get(self.project["id"])
        self.assertEqual(policy, default_policy())
        self.assertEqual(policy["auto_apply_level"], "never")

    def test_policy_is_validated_versioned_and_audited_without_secret_values(self):
        policy = default_policy() | {
            "allowed_workspace_paths": ["app", "docs"],
            "validation_profiles": ["gradle:testDebugUnitTest"],
            "model_providers": ["ollama"],
            "budgets": {"max_task_tokens": 1200, "max_request_tokens": 400},
        }
        stored = self.store.update(self.project["id"], policy)
        self.assertEqual(stored["allowed_workspace_paths"], ["app", "docs"])
        self.assertEqual(self.store.get(self.project["id"]), stored)
        event = self.store.audit(self.project["id"])[0]
        self.assertEqual(set(event), {"action", "schema_version", "sha256", "created_at"})
        self.assertEqual(event["action"], "policy_updated")

    def test_policy_rejects_traversal_unknown_provider_and_auto_apply(self):
        for change in (
            {"allowed_workspace_paths": ["../outside"]},
            {"model_providers": ["unknown"]},
            {"auto_apply_level": "patches"},
        ):
            with self.subTest(change=change), self.assertRaises(ValueError):
                self.store.update(self.project["id"], default_policy() | change)

    def test_workspace_paths_are_default_deny_and_boundary_aware(self):
        with self.assertRaisesRegex(ValueError, "does not allow"):
            self.store.require_allowed_workspace_paths(self.project["id"], ["app/Main.kt"])
        self.store.update(self.project["id"], default_policy() | {
            "allowed_workspace_paths": ["app", "README.md"],
        })
        self.store.require_allowed_workspace_paths(self.project["id"], ["app/Main.kt", "README.md"])
        with self.assertRaisesRegex(ValueError, "not allowed"):
            self.store.require_allowed_workspace_paths(self.project["id"], ["application/Main.kt"])


if __name__ == "__main__":
    unittest.main()
