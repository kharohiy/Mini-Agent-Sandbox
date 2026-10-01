import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import project_manager
from project_registry import ProjectRegistry


class ProjectRegistryTests(unittest.TestCase):
    def test_legacy_registry_is_read_without_implicit_migration(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "connected-project"
            source.mkdir()
            database = root / "registry.sqlite"
            connection = sqlite3.connect(database)
            connection.execute(
                """CREATE TABLE projects (
                id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
                source_path TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL)"""
            )
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                ("demo--12345678", "Demo", str(source), "created", "updated"),
            )
            connection.commit()
            connection.close()

            registry = ProjectRegistry(database, root / "project-state")
            project = registry.get("demo--12345678")

            self.assertEqual(project["source_path"], str(source))
            self.assertEqual(project["source_kind"], "local")
            self.assertEqual(project["source_uri"], str(source))
            additional_source = root / "second-project"
            additional_source.mkdir()
            additional = registry.register(additional_source, "Second")
            self.assertEqual(additional["source_kind"], "local")
            self.assertEqual(additional["source_uri"], str(additional_source.resolve()))
            connection = sqlite3.connect(database)
            columns = {row[1] for row in connection.execute("PRAGMA table_info(projects)")}
            connection.close()
            self.assertNotIn("description", columns)

    def test_explicit_migration_preserves_project_identity_and_state_path(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "connected-project"
            source.mkdir()
            database = root / "registry.sqlite"
            connection = sqlite3.connect(database)
            connection.execute(
                """CREATE TABLE projects (
                id TEXT PRIMARY KEY, display_name TEXT NOT NULL,
                source_path TEXT NOT NULL UNIQUE, created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL)"""
            )
            connection.execute(
                "INSERT INTO projects VALUES (?, ?, ?, ?, ?)",
                ("demo--12345678", "Demo", str(source), "created", "updated"),
            )
            connection.commit()
            connection.close()

            registry = ProjectRegistry(database, root / "project-state")
            before = registry.get("demo--12345678")
            registry.migrate_metadata_schema()
            after = registry.get("demo--12345678")

            self.assertEqual(after["id"], before["id"])
            self.assertEqual(after["source_path"], before["source_path"])
            self.assertEqual(after["state_dir"], before["state_dir"])
            self.assertEqual(after["source_uri"], str(source))
            self.assertEqual(after["description"], "")
            updated = registry.update_metadata(
                before["id"],
                description="Synthetic fixture",
                source_kind="local",
                source_uri=str(source),
            )
            self.assertEqual(updated["description"], "Synthetic fixture")

    def test_new_catalog_stores_remote_metadata_without_fetching(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "checkout"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "state")
            project = registry.register(source, "Demo")

            updated = registry.update_metadata(
                project["id"],
                description="Synthetic project fixture",
                source_kind="git",
                source_uri="https://example.invalid/demo.git",
                configured_ref="main",
                resolved_revision="a" * 40,
            )

            self.assertEqual(updated["description"], "Synthetic project fixture")
            self.assertEqual(updated["source_kind"], "git")
            self.assertEqual(updated["source_uri"], "https://example.invalid/demo.git")
            self.assertEqual(updated["resolved_revision"], "a" * 40)

    def test_project_manager_accepts_catalog_metadata_without_remote_access(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "checkout"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "state")
            with patch("project_manager.ProjectRegistry", return_value=registry), patch(
                "project_manager.index_project",
                return_value=SimpleNamespace(indexed=1),
            ):
                result = project_manager.register_and_index(
                    str(source),
                    "Demo",
                    description="Synthetic fixture",
                    repository_url="https://example.invalid/demo.git",
                    configured_ref="main",
                    resolved_revision="a" * 40,
                )

            self.assertEqual(result["project"]["description"], "Synthetic fixture")
            self.assertEqual(result["project"]["source_kind"], "git")
            self.assertEqual(result["project"]["source_uri"], "https://example.invalid/demo.git")

    def test_git_metadata_rejects_non_https_or_embedded_credentials(self):
        for uri in ("ssh://git@example.com/repo.git", "https://user:secret@example.com/repo.git"):
            with self.subTest(uri=uri):
                with self.assertRaisesRegex(ValueError, "HTTPS URL without embedded credentials"):
                    ProjectRegistry._validate_metadata("", "git", uri)


if __name__ == "__main__":
    unittest.main()
