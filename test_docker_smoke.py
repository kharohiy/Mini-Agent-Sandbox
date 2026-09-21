"""Docker-backed safety checks; skipped only when Docker is genuinely unavailable."""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from capability_policy import CapabilityPolicy
from sandbox_executor import DockerSandboxExecutor, ExecutionRequest


DOCKER = os.environ.get("DOCKER_BIN") or shutil.which("docker")


def docker_available():
    if not DOCKER:
        return False
    return subprocess.run([DOCKER, "info"], capture_output=True).returncode == 0


@unittest.skipUnless(docker_available(), "Docker CLI or daemon is unavailable")
class DockerSmokeTests(unittest.TestCase):
    image = "mini-agent-sandbox-executor:latest"

    def test_executor_image_exists(self):
            self.assertEqual(subprocess.run([DOCKER, "image", "inspect", self.image]).returncode, 0)

    def test_executor_constructs_locked_down_docker_command(self):
        """This unit test runs without Docker and protects the invocation contract."""
        with tempfile.TemporaryDirectory() as source, patch("sandbox_executor._run_docker_bounded") as run:
            run.return_value = (0, "", "", False)
            report = DockerSandboxExecutor(CapabilityPolicy(), "validated_execution").execute(
                ExecutionRequest(source, ["python3", "-c", "pass"])
            )
        self.assertTrue(report.allowed)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--network") + 1], "none")
        self.assertIn("--read-only", command)
        self.assertEqual(command[command.index("--cap-drop") + 1], "ALL")
        self.assertIn("no-new-privileges:true", command)
        self.assertEqual(command[command.index("--pids-limit") + 1], "512")
        self.assertEqual(command[command.index("--memory") + 1], "2g")
        self.assertEqual(command[command.index("--cpus") + 1], "2")
        self.assertIn("/tmp:rw,nosuid,size=768m", command)
        mount = command[command.index("--volume") + 1]
        self.assertIn(":/workspace:rw", mount)
        self.assertNotIn(source, mount)

    def test_isolated_executor_has_no_network_and_keeps_source_unchanged(self):
        with tempfile.TemporaryDirectory() as source:
            source_path = Path(source)
            marker = source_path / "source-marker.txt"
            marker.write_text("unchanged", encoding="utf-8")
            report = DockerSandboxExecutor(CapabilityPolicy(), "validated_execution").execute(
                ExecutionRequest(source, ["python3", "-c", "from pathlib import Path; Path('result').write_text('ok')"])
            )
            self.assertTrue(report.allowed, report.stderr)
            self.assertEqual(marker.read_text(encoding="utf-8"), "unchanged")
            self.assertFalse((source_path / "result").exists())

    def test_container_security_settings_are_present(self):
        container_id = subprocess.check_output([
            DOCKER, "create", "--network", "none", "--read-only", "--user", "1000:1000",
            "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true", "--pids-limit", "512",
            "--memory", "2g", "--cpus", "2", "--tmpfs", "/tmp:rw,nosuid,size=512m", self.image,
            "python", "-c", "pass",
        ], text=True).strip()
        try:
            info = json.loads(subprocess.check_output([DOCKER, "inspect", container_id], text=True))[0]
            host = info["HostConfig"]
            self.assertEqual(host["NetworkMode"], "none")
            self.assertTrue(host["ReadonlyRootfs"])
            self.assertEqual(host["PidsLimit"], 512)
            self.assertEqual(host["Memory"], 2 * 1024 * 1024 * 1024)
            self.assertIn("ALL", host["CapDrop"])
            self.assertIn("no-new-privileges:true", host["SecurityOpt"])
        finally:
            subprocess.run([DOCKER, "rm", "-f", container_id], check=False)


if __name__ == "__main__":
    unittest.main()
