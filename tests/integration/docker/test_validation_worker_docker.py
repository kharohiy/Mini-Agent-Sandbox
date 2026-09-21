"""Phase 5 integration tests run only against copied Kotlin/Android fixtures."""
import os
import shutil
import subprocess
import tempfile
import unittest
import difflib
from pathlib import Path

from capability_policy import CapabilityPolicy
from project_registry import ProjectRegistry
from project_policy import ProjectPolicyStore, default_policy
from sandbox_executor import DockerSandboxExecutor
from validation_worker import ValidationRejected, ValidationWorker
from work_ledger import WorkLedger

FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "kotlin-android"
DOCKER = os.environ.get("DOCKER_BIN") or shutil.which("docker")


def docker_available():
    return bool(DOCKER) and subprocess.run([DOCKER, "info"], capture_output=True).returncode == 0


def file_diff(path, old, new):
    unified = list(difflib.unified_diff(old.splitlines(), new.splitlines(),
                                        fromfile=f"a/{path}", tofile=f"b/{path}", n=3, lineterm=""))
    return (f"diff --git a/{path} b/{path}\n" + "\n".join(unified) + "\n")


def source_bytes(root):
    return {path.relative_to(root).as_posix(): path.read_bytes()
            for path in root.rglob("*") if path.is_file()}


@unittest.skipUnless(docker_available(), "Docker CLI or daemon is unavailable")
class ValidationWorkerDockerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "registered-fixture"
        shutil.copytree(FIXTURE, self.source)
        self.registry = ProjectRegistry(self.root / "registry.sqlite", self.root / "projects")
        self.project = self.registry.register(self.source, "Fixture")
        self.policy_store = ProjectPolicyStore(self.registry)
        self.policy_store.update(self.project["id"], default_policy() | {
            "allowed_workspace_paths": ["app"],
            "validation_profiles": ["test"],
        })
        self.ledger = WorkLedger(self.project["id"], self.registry)
        task = self.ledger.create_task("Fixture patch", "Exercise the Phase 5 worker")
        plan = self.ledger.create_plan(task["id"], "Validate a fixture-only change")
        files = ["app/src/main/java/com/example/fixture/Greeting.kt",
                 "app/src/test/java/com/example/fixture/GreetingTest.kt"]
        step = self.ledger.add_step(plan["id"], description="Change the greeting", files=files,
                                    risks="unit-test regression", validation="offline Gradle test",
                                    rollback="discard temporary validation copy")
        self.ledger.approve_plan(plan["id"])
        self.step_id = step["id"]
        self.temp_root = self.root / "worker-tmp"
        self.temp_root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def submit(self, diff):
        patch = self.ledger.record_patch(self.step_id, diff)
        self.ledger.record_review(patch["id"], "approved", "fixture test and scope reviewed")
        self.ledger.approve_patch(patch["id"], patch["sha256"])
        return patch

    def worker(self):
        return ValidationWorker(registry=self.registry,
                                executor=DockerSandboxExecutor(CapabilityPolicy(), "validated_execution"),
                                temp_root=self.temp_root, policy_store=self.policy_store)

    def greeting_diff(self):
        main_path = "app/src/main/java/com/example/fixture/Greeting.kt"
        test_path = "app/src/test/java/com/example/fixture/GreetingTest.kt"
        main = (self.source / main_path).read_text(encoding="utf-8")
        test = (self.source / test_path).read_text(encoding="utf-8")
        return file_diff(main_path, main, main.replace("Hello, $name", "Hi, $name")) + file_diff(
            test_path, test, test.replace("Hello, Docker", "Hi, Docker"))

    def test_approved_positive_patch_passes_and_original_fixture_is_unchanged(self):
        patch = self.submit(self.greeting_diff())
        original = source_bytes(self.source)
        report = self.worker().run(self.project["id"], patch["id"], profile="test")
        self.assertEqual(report["status"], "validated", report["stderr"])
        self.assertEqual(report["patch_sha256"], patch["sha256"])
        self.assertEqual(report["executor"], "docker")
        self.assertTrue(report["executor_image_digest"].startswith("sha256:"))
        self.assertTrue(report["temporary_copy_only"])
        self.assertEqual(source_bytes(self.source), original)
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_compile_error_patch_is_rejected_by_docker(self):
        path = "app/src/main/java/com/example/fixture/Greeting.kt"
        original = (self.source / path).read_text(encoding="utf-8")
        broken = original.replace('fun message(name: String): String = "Hello, $name"',
                                  'fun message(name: String): String = (')
        patch = self.submit(file_diff(path, original, broken))
        report = self.worker().run(self.project["id"], patch["id"])
        self.assertEqual(report["status"], "rejected")
        self.assertNotEqual(report["exit_code"], 0)

    def test_failing_unit_test_patch_is_rejected_by_docker(self):
        path = "app/src/test/java/com/example/fixture/GreetingTest.kt"
        original = (self.source / path).read_text(encoding="utf-8")
        broken = original.replace("Hello, Docker", "Wrong result")
        patch = self.submit(file_diff(path, original, broken))
        report = self.worker().run(self.project["id"], patch["id"])
        self.assertEqual(report["status"], "rejected")
        self.assertNotEqual(report["exit_code"], 0)

    def test_missing_wrapper_blocks_and_invalid_patch_never_reaches_docker(self):
        (self.source / "gradlew").unlink()
        patch = self.submit(self.greeting_diff())
        report = self.worker().run(self.project["id"], patch["id"])
        self.assertIn(report["status"], {"rejected", "blocked"})
        self.assertNotEqual(report["exit_code"], 0)

        task = self.ledger.create_task("Invalid patch", "Fail closed")
        plan = self.ledger.create_plan(task["id"], "Invalid patch scope")
        step = self.ledger.add_step(plan["id"], description="Edit source", files=["app/src/main/java/com/example/fixture/Greeting.kt"],
                                    risks="none", validation="none", rollback="discard")
        self.ledger.approve_plan(plan["id"])
        invalid = self.ledger.record_patch(step["id"], file_diff(
            "app/src/main/java/com/example/fixture/Greeting.kt", "x", "y"))
        self.ledger.record_review(invalid["id"], "approved", "test")
        self.ledger.approve_patch(invalid["id"], invalid["sha256"])
        db = self.registry.state_dir(self.project["id"]) / "runs/work_ledger.sqlite"
        import sqlite3
        connection = sqlite3.connect(db)
        try:
            connection.execute("UPDATE patches SET diff = ? WHERE id = ?", ("invalid", invalid["id"]))
            connection.commit()
        finally:
            connection.close()
        with self.assertRaises(ValidationRejected):
            self.worker().run(self.project["id"], invalid["id"])


if __name__ == "__main__":
    unittest.main()
