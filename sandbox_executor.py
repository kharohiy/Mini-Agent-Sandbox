from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from threading import Thread
import shutil
import subprocess
import tempfile
import os
import re

from capability_policy import CapabilityPolicy


DOCKER_SECURITY_SETTINGS = {
    "network": "none",
    "read_only_root": True,
    "user": "1000:1000",
    "cap_drop": ["ALL"],
    "no_new_privileges": True,
    "pids_limit": 512,
    "memory": "2g",
    "cpus": 2,
    "timeout_seconds": 180,
    "tmpfs": "/tmp:rw,nosuid,size=768m",
    "workspace_mount": "temporary-copy:/workspace:rw",
}
MAX_CAPTURE_BYTES = 65_536


def _read_tail(pipe, destination: bytearray) -> None:
    while True:
        chunk = pipe.read(8192)
        if not chunk:
            return
        destination.extend(chunk)
        if len(destination) > MAX_CAPTURE_BYTES:
            del destination[:-MAX_CAPTURE_BYTES]


def _run_docker_bounded(command: list[str]):
    """Drain both pipes continuously while retaining only bounded tails."""
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = bytearray(), bytearray()
    readers = [Thread(target=_read_tail, args=(process.stdout, stdout), daemon=True),
               Thread(target=_read_tail, args=(process.stderr, stderr), daemon=True)]
    for reader in readers:
        reader.start()
    timed_out = False
    try:
        return_code = process.wait(timeout=DOCKER_SECURITY_SETTINGS["timeout_seconds"])
    except subprocess.TimeoutExpired:
        timed_out = True
        process.kill()
        return_code = process.wait()
    finally:
        for reader in readers:
            reader.join()
        if process.stdout:
            process.stdout.close()
        if process.stderr:
            process.stderr.close()
    return (return_code, bytes(stdout).decode("utf-8", errors="replace"),
            bytes(stderr).decode("utf-8", errors="replace"), timed_out)


def _stop_timed_out_container(docker_binary: str, cid_file: Path) -> bool:
    """Stop a detached container if the CLI was killed at its wall-clock limit."""
    try:
        container_id = cid_file.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError):
        return False
    if not re.fullmatch(r"[0-9a-f]{12,64}", container_id):
        return False
    try:
        stopped = subprocess.run([docker_binary, "stop", "--time", "1", container_id],
                                 capture_output=True, timeout=10, check=False)
        if stopped.returncode == 0:
            return True
        removed = subprocess.run([docker_binary, "rm", "--force", container_id],
                                 capture_output=True, timeout=10, check=False)
        detail = (removed.stderr or b"").decode("utf-8", errors="replace").casefold()
        return removed.returncode == 0 or "no such container" in detail
    except (OSError, subprocess.TimeoutExpired):
        return False
    return True


@dataclass(frozen=True)
class ExecutionRequest:
    workspace: str
    command: list[str]


@dataclass(frozen=True)
class ExecutionReport:
    allowed: bool
    reason: str
    exit_code: int | None = None
    stdout: str = ""
    stderr: str = ""
    timed_out: bool = False


class SandboxExecutor(ABC):
    @abstractmethod
    def execute(self, request: ExecutionRequest) -> ExecutionReport:
        """Run only inside a real isolated backend; never on the host directly."""


class DockerSandboxExecutor(SandboxExecutor):
    """Runs validation against an ephemeral workspace copy in a locked-down container."""

    def __init__(self, policy: CapabilityPolicy, mode="plan_only", image="mini-agent-sandbox-executor:latest"):
        self.policy = policy
        self.mode = mode
        self.image = image

    @staticmethod
    def _safe_workspace(path: str) -> Path:
        workspace = Path(path).resolve()
        if not workspace.is_dir():
            raise ValueError("Security Error: workspace must be an existing directory.")
        if workspace.is_symlink():
            raise ValueError("Security Error: workspace cannot be a symlink.")
        if any(entry.is_symlink() for entry in workspace.rglob("*")):
            raise ValueError("Security Error: workspace cannot contain symlinks.")
        return workspace

    @staticmethod
    def _safe_command(command: list[str]) -> list[str]:
        if not command or not all(isinstance(item, str) and item for item in command):
            raise ValueError("Security Error: command must be a non-empty string list.")
        if any("\x00" in item for item in command):
            raise ValueError("Security Error: command cannot contain NUL bytes.")
        return command

    @staticmethod
    def _docker_binary() -> str:
        """Resolve Docker only for the trusted worker process, never the API."""
        configured = os.environ.get("DOCKER_BIN")
        if configured:
            return configured
        discovered = shutil.which("docker")
        if discovered:
            return discovered
        docker_desktop = Path(
            r"C:\Users\AlSaintUk\AppData\Local\Programs\DockerDesktop\resources\bin\docker.exe"
        )
        if docker_desktop.is_file():
            return str(docker_desktop)
        return "docker"

    def execute(self, request: ExecutionRequest) -> ExecutionReport:
        self.policy.require(self.mode, "build_test")
        workspace = self._safe_workspace(request.workspace)
        command = self._safe_command(request.command)

        timeout_cleanup_ok = False
        try:
            with tempfile.TemporaryDirectory(prefix="mini-agent-sandbox-") as temporary_root:
                copied_workspace = Path(temporary_root) / "workspace"
                cid_file = Path(temporary_root) / "container.id"
                shutil.copytree(workspace, copied_workspace, symlinks=False)
                docker_binary = self._docker_binary()
                docker_command = [
                    docker_binary, "run", "--rm", "--cidfile", str(cid_file),
                    "--network", DOCKER_SECURITY_SETTINGS["network"],
                    "--read-only", "--user", DOCKER_SECURITY_SETTINGS["user"],
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges:true",
                    "--pids-limit", str(DOCKER_SECURITY_SETTINGS["pids_limit"]),
                    "--memory", DOCKER_SECURITY_SETTINGS["memory"], "--cpus", str(DOCKER_SECURITY_SETTINGS["cpus"]),
                    "--tmpfs", DOCKER_SECURITY_SETTINGS["tmpfs"],
                    "--volume", f"{copied_workspace}:/workspace:rw", "--workdir", "/workspace",
                    self.image, *command,
                ]
                return_code, stdout, stderr, timed_out = _run_docker_bounded(docker_command)
                if timed_out:
                    timeout_cleanup_ok = _stop_timed_out_container(docker_binary, cid_file)
        except FileNotFoundError:
            return ExecutionReport(False, "Docker CLI is unavailable; host execution remains denied.")
        except subprocess.TimeoutExpired as exc:
            return ExecutionReport(False, "Docker validation timed out.", stdout=exc.stdout or "", stderr=exc.stderr or "", timed_out=True)
        except (OSError, ValueError) as exc:
            return ExecutionReport(False, str(exc))

        if timed_out:
            reason = "Docker validation timed out; container stopped." if timeout_cleanup_ok else (
                "Docker validation timed out; container stop could not be confirmed.")
            return ExecutionReport(False, reason, stdout=stdout, stderr=stderr, timed_out=True)
        return ExecutionReport(return_code == 0,
            "Validation completed in Docker." if return_code == 0 else "Docker validation failed.",
            exit_code=return_code, stdout=stdout, stderr=stderr)
