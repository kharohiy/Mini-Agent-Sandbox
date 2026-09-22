import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from data_guardrail import DataGuardrail
from vault_registry import VaultRegistry, get_user_vault


class VaultIsolationTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.base_dir = Path(self.temp_dir.name) / "data"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_vault_mappings_are_not_shared_between_users(self):
        alice_vault = get_user_vault("alice", self.base_dir)
        bob_vault = get_user_vault("bob", self.base_dir)
        token = "__VAULT_SECRET_API_KEY_TEST__"

        alice_vault.save_mapping({token: "alice-secret"})

        self.assertEqual(alice_vault.get_secret(token), "alice-secret")
        self.assertIsNone(bob_vault.get_secret(token))
        self.assertTrue((self.base_dir / "alice" / "vault.enc").exists())
        self.assertTrue((self.base_dir / "alice" / "vault.key").exists())
        self.assertFalse((self.base_dir / "vault.enc").exists())

    def test_mapping_survives_a_fresh_factory_instance_for_the_same_tenant(self):
        token = "__VAULT_SECRET_API_KEY_TEST__"
        get_user_vault("alice", self.base_dir).save_mapping({token: "alice-secret"})

        fresh_vault = get_user_vault("alice", self.base_dir)

        self.assertEqual(fresh_vault.get_secret(token), "alice-secret")

    def test_complete_legacy_pair_is_copied_without_deleting_legacy_files(self):
        user_dir = self.base_dir / "alice"
        user_dir.mkdir(parents=True)
        token = "__VAULT_SECRET_API_KEY_TEST__"
        legacy = VaultRegistry(user_dir / ".vault", user_dir / ".vault_key")
        legacy.save_mapping({token: "legacy-secret"})

        canonical = get_user_vault("alice", self.base_dir)

        self.assertEqual(canonical.get_secret(token), "legacy-secret")
        self.assertTrue((user_dir / ".vault").exists())
        self.assertTrue((user_dir / ".vault_key").exists())
        self.assertTrue((user_dir / "vault.enc").exists())
        self.assertTrue((user_dir / "vault.key").exists())

        canonical.save_mapping({"__VAULT_SECRET_SECOND__": "new-secret"})
        self.assertEqual(
            get_user_vault("alice", self.base_dir).get_secret("__VAULT_SECRET_SECOND__"),
            "new-secret",
        )

    def test_incomplete_or_conflicting_pairs_fail_closed(self):
        alice_dir = self.base_dir / "alice"
        alice_dir.mkdir(parents=True)
        (alice_dir / ".vault").write_bytes(b"encrypted-without-key")
        with self.assertRaisesRegex(ValueError, "incomplete"):
            get_user_vault("alice", self.base_dir)

        bob_dir = self.base_dir / "bob"
        bob_dir.mkdir()
        VaultRegistry(bob_dir / ".vault", bob_dir / ".vault_key").save_mapping({"token": "legacy"})
        VaultRegistry(bob_dir / "vault.enc", bob_dir / "vault.key").save_mapping({"token": "canonical"})
        with self.assertRaisesRegex(ValueError, "conflict"):
            get_user_vault("bob", self.base_dir)

    def test_existing_vault_without_key_is_never_rekeyed(self):
        user_dir = self.base_dir / "alice"
        user_dir.mkdir(parents=True)
        (user_dir / "vault.enc").write_bytes(b"unreadable")

        with self.assertRaisesRegex(ValueError, "incomplete"):
            get_user_vault("alice", self.base_dir)

        self.assertFalse((user_dir / "vault.key").exists())

    def test_directory_instead_of_a_vault_file_fails_closed(self):
        user_dir = self.base_dir / "alice"
        user_dir.mkdir(parents=True)
        (user_dir / "vault.enc").mkdir()
        (user_dir / "vault.key").write_bytes(b"not-a-key")

        with self.assertRaisesRegex(ValueError, "regular files"):
            get_user_vault("alice", self.base_dir)

    def test_guardrail_registry_is_scoped_to_the_user(self):
        guardrail = DataGuardrail()
        alice_text = guardrail._generate_vault_token("EMAIL", "alice@example.com", "alice")
        bob_text = guardrail._generate_vault_token("EMAIL", "bob@example.com", "bob")

        self.assertIn("__VAULT_SECRET_EMAIL_", alice_text)
        self.assertIn("__VAULT_SECRET_EMAIL_", bob_text)
        self.assertEqual(len(guardrail.extract_vault_mapping("alice")), 1)
        self.assertEqual(len(guardrail.extract_vault_mapping("bob")), 1)
        self.assertNotEqual(guardrail.extract_vault_mapping("alice"), guardrail.extract_vault_mapping("bob"))

    def test_rejects_unsafe_user_id(self):
        with self.assertRaises(ValueError):
            get_user_vault("../other", self.base_dir)

    def test_rejects_a_symlinked_tenant_directory(self):
        target = self.base_dir / "outside"
        target.mkdir(parents=True)
        try:
            os.symlink(target, self.base_dir / "alice", target_is_directory=True)
        except OSError as error:
            self.skipTest(f"symlink creation unavailable: {type(error).__name__}")

        with self.assertRaisesRegex(ValueError, "symlink"):
            get_user_vault("alice", self.base_dir)

    def test_symlink_refusal_is_deterministic_without_windows_privileges(self):
        with patch(
            "vault_registry.Path.is_symlink",
            autospec=True,
            side_effect=lambda path: path.name == "alice",
        ):
            with self.assertRaisesRegex(ValueError, "symlink"):
                get_user_vault("alice", self.base_dir)


if __name__ == "__main__":
    unittest.main()
