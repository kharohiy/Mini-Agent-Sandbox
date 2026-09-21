"""Validate unified diffs against the exact files approved in a plan step."""
from __future__ import annotations

import re

_GIT_HEADER = re.compile(r"^diff --git a/(.+) b/(.+)$")
_HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+\d+(?:,\d+)? @@(?: .*)?$")
_ALLOWED_SUFFIXES = {".kt", ".java", ".gradle", ".kts", ".xml", ".md"}
_ALLOWED_NAMES = {"settings.gradle", "settings.gradle.kts", "gradle.properties"}
_FORBIDDEN_PARTS = {".git", ".gradle", ".idea", "build", "node_modules", ".mini-agent", ".vault", ".vault_key"}


def _path(value: str) -> str | None:
    if value == "/dev/null":
        return None
    if not value or "\x00" in value or "\\" in value or value.startswith("/"):
        raise ValueError("diff contains an unsafe file path")
    if value.startswith(("a/", "b/")):
        value = value[2:]
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        raise ValueError("diff contains an unsafe file path")
    if any(part.casefold() in _FORBIDDEN_PARTS for part in parts[:-1]):
        raise ValueError("diff targets an excluded project directory")
    name = parts[-1]
    if name in {".vault", ".vault_key", "state.json"}:
        raise ValueError("diff targets a protected project file")
    if name not in _ALLOWED_NAMES and not any(name.casefold().endswith(suffix) for suffix in _ALLOWED_SUFFIXES):
        raise ValueError("diff target is outside the project source-file policy")
    return "/".join(parts)


def validate_unified_diff(diff: str, declared_files: list[str]) -> list[str]:
    """Return changed paths or reject malformed, unsafe, or out-of-scope diffs."""
    if not isinstance(diff, str) or not diff.strip() or "\x00" in diff:
        raise ValueError("a non-empty text unified diff is required")
    declared = {_path(item) for item in declared_files}
    if None in declared or not declared:
        raise ValueError("approved plan step contains invalid file paths")

    lines = diff.splitlines()
    changed: set[str] = set()
    i = 0
    while i < len(lines):
        match = _GIT_HEADER.fullmatch(lines[i]) if lines[i].startswith("diff --git ") else None
        if not match:
            raise ValueError("patch must contain standard diff --git headers")
        old_git = _path("a/" + match.group(1))
        new_git = _path("b/" + match.group(2))
        i += 1
        while i < len(lines) and not lines[i].startswith("--- "):
            if lines[i].startswith(("diff --git ", "GIT binary patch", "Binary files ")):
                raise ValueError("binary and header-only patches are not supported")
            i += 1
        if i + 1 >= len(lines) or not lines[i].startswith("--- ") or not lines[i + 1].startswith("+++ "):
            raise ValueError("each diff must include --- and +++ file headers")
        old = _path(lines[i][4:].split("\t", 1)[0])
        new = _path(lines[i + 1][4:].split("\t", 1)[0])
        git_old_matches = old_git == (old if old is not None else new)
        git_new_matches = new_git == (new if new is not None else old)
        if not git_old_matches or not git_new_matches or (old is None and new is None):
            raise ValueError("diff header paths do not match file headers")
        if (old is not None and old not in declared) or (new is not None and new not in declared):
            raise ValueError("diff modifies a file not declared by the approved plan step")
        i += 2
        has_hunk = False
        while i < len(lines) and not lines[i].startswith("diff --git "):
            if lines[i].startswith("@@"):
                if not _HUNK_HEADER.fullmatch(lines[i]):
                    raise ValueError("patch contains a malformed hunk header")
                has_hunk = True
            elif lines[i].startswith(("GIT binary patch", "Binary files ")):
                raise ValueError("binary patches are not supported")
            i += 1
        if not has_hunk:
            raise ValueError("each diff must contain at least one text hunk")
        changed.update(path for path in (old, new) if path)
    if not changed:
        raise ValueError("patch contains no file changes")
    return sorted(changed)
