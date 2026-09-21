"""Real Android/Kotlin validation. Gradle is invoked only by DockerSandboxExecutor."""
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from capability_policy import CapabilityPolicy
from sandbox_executor import DockerSandboxExecutor, ExecutionRequest


DOCKER = os.environ.get("DOCKER_BIN") or shutil.which("docker")
FIXTURE = Path(__file__).parent / "tests" / "fixtures" / "kotlin-android"


def docker_available():
    return bool(DOCKER) and subprocess.run([DOCKER, "info"], capture_output=True).returncode == 0


@unittest.skipUnless(docker_available(), "Docker CLI or daemon is unavailable")
class KotlinAndroidExecutorIntegrationTests(unittest.TestCase):
    def execute(self, workspace: Path):
        return DockerSandboxExecutor(CapabilityPolicy(), "validated_execution").execute(
            ExecutionRequest(str(workspace), ["./gradlew", "--offline", "test"])
        )

    def fixture_copy(self):
        temporary = tempfile.TemporaryDirectory()
        workspace = Path(temporary.name) / "fixture"
        shutil.copytree(FIXTURE, workspace)
        return temporary, workspace

    def test_valid_fixture_passes_only_in_docker_and_source_is_unchanged(self):
        original = (FIXTURE / "app/src/main/java/com/example/fixture/Greeting.kt").read_text(encoding="utf-8")
        temporary, workspace = self.fixture_copy()
        with temporary:
            report = self.execute(workspace)
        self.assertTrue(report.allowed, report.stderr)
        self.assertIn("BUILD SUCCESSFUL", report.stdout)
        self.assertEqual(
            (FIXTURE / "app/src/main/java/com/example/fixture/Greeting.kt").read_text(encoding="utf-8"),
            original,
        )
        self.assertFalse((FIXTURE / "app/build").exists())

    def test_kotlin_compile_error_blocks_validation(self):
        temporary, workspace = self.fixture_copy()
        with temporary:
            source = workspace / "app/src/main/java/com/example/fixture/Greeting.kt"
            source.write_text("package com.example.fixture\nfun broken( = 1\n", encoding="utf-8")
            report = self.execute(workspace)
        self.assertFalse(report.allowed)
        self.assertNotEqual(report.exit_code, 0)

    def test_failing_unit_test_blocks_validation(self):
        temporary, workspace = self.fixture_copy()
        with temporary:
            test = workspace / "app/src/test/java/com/example/fixture/GreetingTest.kt"
            test.write_text(test.read_text(encoding="utf-8").replace("Hello, Docker", "Wrong result"), encoding="utf-8")
            report = self.execute(workspace)
        self.assertFalse(report.allowed)
        self.assertNotEqual(report.exit_code, 0)

    def test_missing_gradle_wrapper_blocks_validation(self):
        temporary, workspace = self.fixture_copy()
        with temporary:
            (workspace / "gradlew").unlink()
            report = self.execute(workspace)
        self.assertFalse(report.allowed)
        self.assertNotEqual(report.exit_code, 0)


if __name__ == "__main__":
    unittest.main()
