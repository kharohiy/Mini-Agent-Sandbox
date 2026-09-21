"""Trusted, host-side Phase 5 worker. Never import this module from FastAPI."""
from __future__ import annotations

import hashlib
import os
import re
import shutil
import sqlite3
import stat
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Callable

from capability_policy import CapabilityPolicy
from patch_policy import validate_unified_diff
from project_policy import ProjectPolicyStore
from project_registry import ProjectRegistry
from project_telemetry import ProjectTelemetryStore
from sandbox_executor import DOCKER_SECURITY_SETTINGS, DockerSandboxExecutor, ExecutionRequest
from work_ledger import WorkLedger

MAX_OUTPUT_CHARS = 16_384
MAX_PATCH_BYTES = 2_000_000
MAX_COPY_FILES = 100_000
DOCKER_SETTINGS = DOCKER_SECURITY_SETTINGS
_SECRET_PATTERNS = (
    re.compile(r"(?i)(\b(?:api[_-]?key|access[_-]?token|secret|password)\b\s*[:=]\s*)([^\s,;]+)"),
    re.compile(r"\b(?:sk-[A-Za-z0-9_-]{12,}|gh[pousr]_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16})\b"),
)
_SKIP_DIRS = {".git", ".gradle", ".idea", "build", "node_modules", ".mini-agent",
              ".vault", ".secrets", ".credentials", "secrets", "credentials"}
_SKIP_FILES = {".vault_key", ".env", "id_rsa", "id_ed25519", "credentials.json",
               "service_account.json"}


class ValidationRejected(ValueError):
    """The persisted candidate or requested validation profile failed closed."""


def _is_link_or_junction(path: Path) -> bool:
    if path.is_symlink():
        return True
    is_junction = getattr(path, "is_junction", None)
    if callable(is_junction) and is_junction():
        return True
    attributes = getattr(path.lstat(), "st_file_attributes", 0)
    reparse_flag = getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0x400)
    return bool(attributes & reparse_flag)


def _redact(text: str) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    elif not isinstance(text, str):
        text = str(text)
    for pattern in _SECRET_PATTERNS:
        if pattern.groups:
            text = pattern.sub(r"\1[REDACTED]", text)
        else:
            text = pattern.sub("[REDACTED]", text)
    return text[-MAX_OUTPUT_CHARS:]


def _modules(registry: ProjectRegistry, project_id: str) -> set[str]:
    database = registry.state_dir(project_id) / "snapshot" / "project_snapshot.sqlite"
    if not database.is_file():
        return set()
    connection = None
    try:
        connection = sqlite3.connect(database)
        return {row[0] for row in connection.execute("SELECT DISTINCT module FROM files WHERE module != ''")}
    except sqlite3.Error:
        return set()
    finally:
        if connection is not None:
            connection.close()


def resolve_validation_command(profile: str, *, module: str | None = None,
                               modules: set[str] | None = None) -> list[str]:
    """Map a small symbolic profile to a fixed offline Gradle command."""
    if not isinstance(profile, str) or (module is not None and not isinstance(module, str)):
        raise ValidationRejected("validation profile and module must be strings")
    if profile == "test" and module is None:
        return ["./gradlew", "--offline", "test"]
    if profile == "lint" and module is None:
        return ["./gradlew", "--offline", "lint"]
    if profile == "module_test" and module and module in (modules or set()):
        if not re.fullmatch(r":(?:[A-Za-z0-9_-]+(?::[A-Za-z0-9_-]+)*)?", module):
            raise ValidationRejected("invalid registered Gradle module")
        task = f"{module}:test" if module != ":" else "test"
        return ["./gradlew", "--offline", task]
    raise ValidationRejected("validation profile is not allowlisted")


def _assert_no_links(source: Path) -> None:
    if _is_link_or_junction(source) or not source.is_dir():
        raise ValidationRejected("registered project source must be a real directory")
    count = 0
    for base, dirs, files in os.walk(source, topdown=True, followlinks=False):
        base_path = Path(base)
        kept_dirs = []
        for name in dirs:
            entry = base_path / name
            if _is_link_or_junction(entry):
                raise ValidationRejected("project contains a symlink or junction")
            count += 1
            if count > MAX_COPY_FILES:
                raise ValidationRejected("project exceeds the bounded copy file limit")
            kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in files:
            entry = base_path / name
            if _is_link_or_junction(entry):
                raise ValidationRejected("project contains a symlink")
            count += 1
            if count > MAX_COPY_FILES:
                raise ValidationRejected("project exceeds the bounded copy file limit")


def _copy_ignore(_directory: str, names: list[str]) -> set[str]:
    ignored = {name for name in names if name.casefold() in _SKIP_DIRS or name.casefold() in _SKIP_FILES}
    ignored.update(name for name in names if name.casefold() == ".env" or name.casefold().startswith(".env."))
    ignored.update(name for name in names if Path(name).suffix.casefold() in {".pem", ".key", ".p12", ".pfx"})
    return ignored


def _apply_diff(workspace: Path, diff: str) -> None:
    # git apply parses data only; Gradle and project code are never invoked on the host.
    environment = {"PATH": os.environ.get("PATH", ""), "GIT_CONFIG_NOSYSTEM": "1",
                   "GIT_CONFIG_GLOBAL": os.devnull, "GIT_TERMINAL_PROMPT": "0"}
    for check in (True, False):
        args = ["git", "apply"] + (["--check"] if check else []) + ["--whitespace=nowarn", "-"]
        try:
            result = subprocess.run(args, cwd=workspace, input=diff.encode("utf-8"), text=False,
                                    capture_output=True, timeout=15, check=False, env=environment)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ValidationRejected("could not safely apply the patch to the temporary copy") from exc
        if result.returncode:
            detail = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace").strip()[-512:]
            raise ValidationRejected("patch does not apply cleanly to the registered project snapshot" +
                                     (f": {detail}" if detail else ""))


class ValidationWorker:
    """Run an approved patch against an isolated copy using the Docker executor."""

    def __init__(self, *, registry: ProjectRegistry | None = None,
                 executor=None, temp_root: str | Path | None = None,
                 output_limit: int = MAX_OUTPUT_CHARS,
                 ledger_factory: Callable[..., WorkLedger] = WorkLedger,
                 policy_store: ProjectPolicyStore | None = None,
                 telemetry_store: ProjectTelemetryStore | None = None):
        self.registry = registry or ProjectRegistry()
        policy_path = Path(__file__).with_name("capabilities.json")
        self.executor = executor or DockerSandboxExecutor(
            CapabilityPolicy(policy_path), "validated_execution")
        self.temp_root = Path(temp_root) if temp_root else None
        self.output_limit = max(256, min(int(output_limit), MAX_OUTPUT_CHARS))
        self.ledger_factory = ledger_factory
        self.policy_store = policy_store or ProjectPolicyStore(self.registry)
        self.telemetry_store = telemetry_store or ProjectTelemetryStore(self.registry)

    def _approved_bundle(self, ledger: WorkLedger, patch_id: str) -> dict:
        bundle = ledger.validation_bundle(patch_id)
        patch = bundle["patch"]
        if patch["status"] in {"rejected", "superseded", "validated", "blocked", "running"}:
            raise ValidationRejected("candidate is rejected, superseded, or no longer eligible")
        if patch["status"] != "approved":
            raise ValidationRejected("candidate does not have explicit user approval")
        if bundle["plan_status"] != "approved":
            raise ValidationRejected("candidate plan is not approved")
        digest = hashlib.sha256(patch["diff"].encode("utf-8")).hexdigest()
        if digest != patch["sha256"]:
            raise ValidationRejected("candidate content hash changed after approval")
        review = bundle["review"]
        if not review or review["decision"] != "approved":
            raise ValidationRejected("candidate lacks a positive persisted reviewer decision")
        approval = bundle["user_approval"]
        if not approval or approval["patch_sha256"] != digest:
            raise ValidationRejected("user approval is missing or does not match the current patch hash")
        if len(patch["diff"].encode("utf-8")) > MAX_PATCH_BYTES:
            raise ValidationRejected("candidate patch exceeds the size limit")
        try:
            validate_unified_diff(patch["diff"], bundle["step"]["files"])
        except ValueError as exc:
            raise ValidationRejected(f"candidate diff failed policy validation: {exc}") from exc
        return bundle

    @staticmethod
    def _image_digest(executor) -> str | None:
        image = getattr(executor, "image", None)
        if not isinstance(executor, DockerSandboxExecutor) or not image:
            return None
        if "@sha256:" in image:
            return image.rsplit("@", 1)[-1]
        try:
            result = subprocess.run(
                [executor._docker_binary(), "image", "inspect", "--format", "{{.Id}}", image],
                capture_output=True, text=True, timeout=10, check=False,
            )
        except (OSError, subprocess.TimeoutExpired):
            return None
        value = (result.stdout or "").strip()
        return value if result.returncode == 0 and value.startswith("sha256:") else None

    def run(self, project_id: str, patch_id: str, *, profile: str | list[str] = "test",
            module: str | None = None) -> dict:
        # Reject arbitrary commands before touching the ledger, source, or temp filesystem.
        if isinstance(profile, str):
            profiles = [profile]
        elif isinstance(profile, (list, tuple)):
            profiles = list(profile)
        else:
            raise ValidationRejected("validation profile must be a symbolic profile or bounded profile list")
        if (not profiles or len(profiles) > 3 or not all(isinstance(item, str) for item in profiles)
                or len(set(profiles)) != len(profiles)):
            raise ValidationRejected("staged validation requires one to three unique allowlisted profiles")
        allowed_profiles = self.policy_store.get(project_id)["validation_profiles"]
        if any(profile not in allowed_profiles for profile in profiles):
            raise ValidationRejected("validation profile is not allowed by the project policy")
        registered_modules = _modules(self.registry, project_id)
        commands = [resolve_validation_command(item, module=module, modules=registered_modules)
                    for item in profiles]
        ledger = self.ledger_factory(project_id, self.registry)
        bundle = self._approved_bundle(ledger, patch_id)
        project = self.registry.get(project_id)
        source = Path(project["source_path"])
        _assert_no_links(source)
        source_root = source.resolve()
        configured_temp = self.temp_root.resolve() if self.temp_root else Path(tempfile.gettempdir()).resolve()
        try:
            configured_common = os.path.commonpath([str(source_root), str(configured_temp)])
        except ValueError:
            configured_common = None
        if configured_common == str(source_root):
            raise ValidationRejected("temporary validation root cannot be inside the registered project")
        started = time.monotonic()
        executor_image = getattr(self.executor, "image", None) or getattr(self.executor, "image_identifier", None)
        executor_image_digest = self._image_digest(self.executor)
        with tempfile.TemporaryDirectory(prefix="mini-agent-validation-", dir=self.temp_root) as temporary:
            temp_base = Path(temporary).resolve()
            try:
                common = os.path.commonpath([str(source.resolve()), str(temp_base)])
            except ValueError:
                common = ""
            if common in {str(source.resolve()), str(temp_base)}:
                raise ValidationRejected("temporary validation directory overlaps the registered project")
            copied = temp_base / "project"
            shutil.copytree(source, copied, ignore=_copy_ignore, symlinks=False)
            _apply_diff(copied, bundle["patch"]["diff"])
            # Re-read the approvals after copy/apply and immediately before execution.
            current = self._approved_bundle(ledger, patch_id)
            if current["patch"]["sha256"] != bundle["patch"]["sha256"]:
                raise ValidationRejected("candidate approval changed during workspace preparation")
            if Path(project["source_path"]).resolve() == copied.resolve():
                raise ValidationRejected("refusing to mount the registered source directory")
            stage_results = []
            for stage_profile, command in zip(profiles, commands):
                # Each stage rechecks the persisted gates immediately before Docker.
                current = self._approved_bundle(ledger, patch_id)
                if current["patch"]["sha256"] != bundle["patch"]["sha256"]:
                    raise ValidationRejected("candidate approval changed during staged validation")
                execution = self.executor.execute(ExecutionRequest(str(copied), command))
                stage_status = ("validated" if execution.allowed else
                                "rejected" if getattr(execution, "exit_code", None) is not None else "blocked")
                stage_results.append({
                    "profile": stage_profile,
                    "command": command,
                    "status": stage_status,
                    "exit_code": getattr(execution, "exit_code", None),
                    "timed_out": bool(getattr(execution, "timed_out", False)),
                    "stdout": _redact(getattr(execution, "stdout", "") or ""),
                    "stderr": _redact(getattr(execution, "stderr", "") or ""),
                    "reason": _redact(getattr(execution, "reason", ""))[-1024:],
                })
                if not execution.allowed:
                    break
        duration = round(time.monotonic() - started, 3)
        report_status = stage_results[-1]["status"]
        command_evidence = commands[0] if len(commands) == 1 else commands
        raw_stdout = "\n".join(stage["stdout"] for stage in stage_results)
        raw_stderr = "\n".join(stage["stderr"] for stage in stage_results)
        reason = "\n".join(stage["reason"] for stage in stage_results if stage["reason"])
        report = {
            "patch_sha256": bundle["patch"]["sha256"],
            "command": command_evidence,
            "status": report_status,
            "exit_code": stage_results[-1]["exit_code"],
            "timed_out": any(stage["timed_out"] for stage in stage_results),
            "duration_seconds": duration,
            "stdout": _redact(raw_stdout)[-self.output_limit:],
            "stderr": _redact(raw_stderr)[-self.output_limit:],
            "stages": stage_results,
            "executor": "docker",
            "executor_image": executor_image,
            "executor_image_digest": executor_image_digest,
            "docker_settings": DOCKER_SETTINGS,
            "temporary_copy_only": True,
            "reason": _redact(reason)[-1024:],
        }
        ledger.record_validation(patch_id, report_status, report)
        self.telemetry_store.record(project_id, event="validation", outcome=report_status)
        return report


def run_validation(project_id: str, patch_id: str, *, profile: str | list[str] = "test",
                   module: str | None = None) -> dict:
    """Convenience entry point for a separate trusted worker process."""
    return ValidationWorker().run(project_id, patch_id, profile=profile, module=module)
