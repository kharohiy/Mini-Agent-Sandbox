import unittest
import tempfile
import io
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

from capability_policy import CapabilityDenied, CapabilityPolicy
from sandbox_executor import (MAX_CAPTURE_BYTES, DockerSandboxExecutor, ExecutionRequest,
                              _run_docker_bounded, _stop_timed_out_container)


class CapabilityPolicyTests(unittest.TestCase):
    def setUp(self):
        self.policy = CapabilityPolicy()

    def test_unknown_capability_is_denied_by_default(self):
        self.assertFalse(self.policy.is_allowed("plan_only", "unknown_tool"))
        with self.assertRaises(CapabilityDenied):
            self.policy.require("plan_only", "unknown_tool")

    def test_unknown_capability_stays_denied_even_if_manifest_default_allows(self):
        self.policy.manifest["default"] = "allow"
        self.assertFalse(self.policy.is_allowed("validated_execution", "unknown_tool"))

    def test_plan_only_denies_build_execution(self):
        executor = DockerSandboxExecutor(self.policy, "plan_only")
        with self.assertRaises(CapabilityDenied):
            executor.execute(ExecutionRequest("data/alice", ["gradlew", "test"]))

    @patch("sandbox_executor._run_docker_bounded")
    def test_validated_execution_uses_locked_down_docker_command(self, run):
        run.return_value = (0, "ok", "", False)
        with tempfile.TemporaryDirectory() as workspace:
            Path(workspace, "main.py").write_text("print('ok')", encoding="utf-8")
            report = DockerSandboxExecutor(self.policy, "validated_execution").execute(
                ExecutionRequest(workspace, ["python", "-m", "ruff", "check", "."])
            )

        command = run.call_args.args[0]
        self.assertTrue(report.allowed)
        self.assertIn("--network", command)
        self.assertIn("none", command)
        self.assertIn("--read-only", command)
        self.assertIn("--cap-drop", command)
        self.assertIn("--pids-limit", command)
        self.assertIn("--memory", command)
        self.assertIn("no-new-privileges:true", command)
        self.assertIn("--user", command)
        self.assertIn("1000:1000", command)

    @patch("sandbox_executor._run_docker_bounded", side_effect=FileNotFoundError)
    def test_missing_docker_cli_fails_closed(self, _run):
        with tempfile.TemporaryDirectory() as workspace:
            report = DockerSandboxExecutor(self.policy, "validated_execution").execute(
                ExecutionRequest(workspace, ["python", "-m", "ruff", "check", "."])
            )
        self.assertFalse(report.allowed)
        self.assertIn("Docker CLI is unavailable", report.reason)

    @patch("sandbox_executor.subprocess.Popen")
    def test_executor_drains_output_but_retains_only_bounded_tails(self, popen):
        process = MagicMock()
        process.stdout = io.BytesIO(b"x" * (MAX_CAPTURE_BYTES + 100))
        process.stderr = io.BytesIO(b"y" * (MAX_CAPTURE_BYTES + 200))
        process.wait.return_value = 0
        popen.return_value = process
        _code, stdout, stderr, timed_out = _run_docker_bounded(["docker", "run"])
        self.assertFalse(timed_out)
        self.assertEqual(len(stdout), MAX_CAPTURE_BYTES)
        self.assertEqual(len(stderr), MAX_CAPTURE_BYTES)

    @patch("sandbox_executor.subprocess.run")
    def test_timeout_cleanup_stops_container_using_only_cid_file(self, run):
        run.return_value = subprocess.CompletedProcess([], 0, b"", b"")
        with tempfile.TemporaryDirectory() as directory:
            cid_file = Path(directory) / "container.id"
            cid_file.write_text("a" * 64, encoding="ascii")
            self.assertTrue(_stop_timed_out_container("docker", cid_file))
        self.assertEqual(run.call_args.args[0], ["docker", "stop", "--time", "1", "a" * 64])


if __name__ == "__main__":
    unittest.main()
