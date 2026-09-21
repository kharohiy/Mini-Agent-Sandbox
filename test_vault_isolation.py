import tempfile
import unittest
from pathlib import Path

from data_guardrail import DataGuardrail
from vault_registry import get_user_vault


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
        self.assertTrue((self.base_dir / "alice" / ".vault").exists())
        self.assertFalse((self.base_dir / ".vault").exists())

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


if __name__ == "__main__":
    unittest.main()
