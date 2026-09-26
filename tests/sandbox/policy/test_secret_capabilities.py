import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

# LiteLLM normally refreshes bundled metadata during import. Keep these
# deterministic capability tests fully offline.
os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import secret_capabilities
import runner
from secret_capabilities import SecretCapability, resolve_capability_arguments
from vault_registry import get_user_vault


TOKEN = "__VAULT_SECRET_API_KEY_TEST__"


class SecretCapabilityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name) / "data"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_current_tool_arguments_stay_opaque_without_opening_vault(self):
        original_factory = secret_capabilities.get_user_vault
        calls = []
        secret_capabilities.get_user_vault = lambda user_id: calls.append(user_id)
        try:
            cases = (
                ("create_file", {"content": f"value={TOKEN}", "filepath": "note.md"}),
                ("read_file", {"filepath": TOKEN}),
                ("list_directory", {"dirpath": TOKEN}),
                ("propose_patch", {"diff": f"+{TOKEN}"}),
            )
            resolved_cases = [
                resolve_capability_arguments(tool_name, arguments, "alice")
                for tool_name, arguments in cases
            ]
        finally:
            secret_capabilities.get_user_vault = original_factory

        self.assertEqual(resolved_cases, [arguments for _, arguments in cases])
        self.assertEqual(calls, [])

    def test_disallowed_tool_is_refused_before_a_vault_lookup(self):
        original_factory = secret_capabilities.get_user_vault
        calls = []
        secret_capabilities.get_user_vault = lambda user_id: calls.append(user_id)
        try:
            with patch("runner.resolve_capability_arguments") as resolver:
                allowed, resolved = runner.authorize_tool_arguments(
                    "unknown_tool",
                    {"credential": TOKEN},
                    "alice",
                    "documentation",
                    "reviewer",
                )
        finally:
            secret_capabilities.get_user_vault = original_factory

        self.assertFalse(allowed)
        self.assertEqual(resolved, {"credential": TOKEN})
        self.assertEqual(calls, [])
        resolver.assert_not_called()

    def test_reviewer_file_write_is_refused_before_a_vault_lookup(self):
        with patch("runner.resolve_capability_arguments") as resolver:
            allowed, resolved = runner.authorize_tool_arguments(
                "create_file",
                {"filepath": "note.md", "content": TOKEN},
                "alice",
                "documentation",
                "reviewer",
            )

        self.assertFalse(allowed)
        self.assertEqual(resolved, {"filepath": "note.md", "content": TOKEN})
        resolver.assert_not_called()

    def test_exact_capability_resolves_only_for_its_tenant(self):
        get_user_vault("alice", self.base_dir).save_mapping({TOKEN: "alice-secret"})
        get_user_vault("bob", self.base_dir).save_mapping({TOKEN: "bob-secret"})
        capability = frozenset({SecretCapability("trusted_fixture", "credential")})
        def factory(user_id):
            return get_user_vault(user_id, self.base_dir)

        alice = resolve_capability_arguments(
            "trusted_fixture",
            {"credential": TOKEN},
            "alice",
            capabilities=capability,
            vault_factory=factory,
        )
        bob = resolve_capability_arguments(
            "trusted_fixture",
            {"credential": TOKEN},
            "bob",
            capabilities=capability,
            vault_factory=factory,
        )

        self.assertEqual(alice["credential"], "alice-secret")
        self.assertEqual(bob["credential"], "bob-secret")

    def test_nested_values_are_never_resolved(self):
        capability = frozenset({SecretCapability("trusted_fixture", "credential")})
        calls = []
        nested = {"credential": {"value": TOKEN}, "items": [TOKEN]}

        resolved = resolve_capability_arguments(
            "trusted_fixture",
            nested,
            "alice",
            capabilities=capability,
            vault_factory=lambda user_id: calls.append(user_id),
        )

        self.assertEqual(resolved, nested)
        self.assertEqual(calls, [])


if __name__ == "__main__":
    unittest.main()
