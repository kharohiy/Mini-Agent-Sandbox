import tempfile
import unittest
from pathlib import Path

from runner import SandboxStorage


class SandboxStorageSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.storage = SandboxStorage(Path(self.temp_dir.name) / "data")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_user_id_cannot_escape_data_root(self):
        for user_id in ("../outside", "nested/user", "C:\\outside", ""):
            with self.subTest(user_id=user_id):
                with self.assertRaises(ValueError):
                    self.storage._get_user_dir(user_id)

    def test_workspace_path_rejects_prefix_collision_and_traversal(self):
        workspace = self.storage._get_user_dir("alice")
        sibling = workspace.parent / "alice_evil" / "secret.txt"

        with self.assertRaises(ValueError):
            self.storage.resolve_workspace_path("alice", "../alice_evil/secret.txt")

        self.assertFalse(sibling.exists())

    def test_workspace_path_stays_under_tenant_directory(self):
        workspace = self.storage._get_user_dir("alice")
        target = self.storage.resolve_workspace_path("alice", "src/main.py")

        self.assertEqual(target, workspace / "src" / "main.py")

    def test_workspace_path_rejects_symlinked_directory(self):
        workspace = self.storage._get_user_dir("alice")
        outside = Path(self.temp_dir.name) / "outside"
        outside.mkdir()
        link = workspace / "linked"
        try:
            link.symlink_to(outside, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f"Symlinks are unavailable in this environment: {exc}")

        with self.assertRaises(ValueError):
            self.storage.resolve_workspace_path("alice", "linked/secret.txt")


if __name__ == "__main__":
    unittest.main()
