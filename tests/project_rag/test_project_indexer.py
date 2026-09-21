import json
import tempfile
import unittest
from pathlib import Path

from project_indexer import index_project
from project_search import search_snapshot, snapshot_summary


class ProjectIndexerTests(unittest.TestCase):
    def make_project(self, root: Path):
        (root / "app/src/main/java/example").mkdir(parents=True)
        (root / "app/src/test/java/example").mkdir(parents=True)
        (root / "app/build").mkdir(parents=True)
        (root / "settings.gradle.kts").write_text('include(":app")\n', encoding="utf-8")
        (root / "app/build.gradle.kts").write_text('plugins { kotlin("android") }\nandroid { compileSdk = 35; defaultConfig { minSdk = 23 } }\n', encoding="utf-8")
        (root / "app/src/main/java/example/Greeting.kt").write_text(
            "package example\nimport kotlin.text.uppercase\nclass Greeting { fun message() = \"hi\" }\n", encoding="utf-8")
        (root / "app/src/test/java/example/GreetingTest.kt").write_text(
            "package example\nclass GreetingTest\n", encoding="utf-8")
        (root / "app/build/generated.kt").write_text("ignored", encoding="utf-8")

    def test_snapshot_is_incremental_and_does_not_write_to_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            output = Path(temporary) / "snapshot"
            root.mkdir()
            self.make_project(root)
            first = index_project(root, output)
            self.assertEqual(first.indexed, 4)
            self.assertEqual(first.modules, 2)
            self.assertGreaterEqual(first.symbols, 2)
            self.assertFalse((root / ".mini-agent").exists())
            second = index_project(root, output)
            self.assertEqual(second.indexed, 0)
            self.assertEqual(second.unchanged, 4)
            greeting = root / "app/src/main/java/example/Greeting.kt"
            greeting.write_text(greeting.read_text(encoding="utf-8") + "\nfun extra() = 1\n", encoding="utf-8")
            third = index_project(root, output)
            self.assertEqual(third.indexed, 1)
            summary = json.loads(Path(third.snapshot).read_text(encoding="utf-8"))
            self.assertEqual(summary["files"], 4)
            self.assertEqual(summary["gradle"]["modules"][":app"]["sdk"]["compileSdk"], 35)

    def test_search_returns_symbols_without_reading_project_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "project"
            snapshots = Path(temporary) / "snapshots"
            root.mkdir()
            self.make_project(root)
            index_project(root, snapshots / "demo")
            summary = snapshot_summary("demo", snapshots)
            results = search_snapshot("demo", "Greeting", root=snapshots)
            self.assertEqual(summary["modules"], [":", ":app"])
            self.assertEqual(len(results), 2)
            self.assertTrue(any(item["is_test"] for item in results))


if __name__ == "__main__":
    unittest.main()
