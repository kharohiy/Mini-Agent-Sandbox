"""Deterministic, local-only secret and PII finding primitives."""

from __future__ import annotations

from dataclasses import dataclass
from math import log2
import re
from typing import Pattern


@dataclass(frozen=True)
class SecretFinding:
    """A redaction candidate that deliberately contains no plaintext value."""

    kind: str
    detector: str
    confidence: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class DetectorRule:
    kind: str
    detector: str
    pattern: Pattern[str]
    confidence: str = "high"
    value_group: str | int | None = None


_CREDENTIAL_WORDS = re.compile(
    r"\b(?:api[_-]?key|access[_-]?key|auth(?:orization)?|credential|"
    r"pass(?:word|wd)?|secret|token)\b",
    re.IGNORECASE,
)
_GENERIC_ASSIGNMENT = re.compile(
    r"\b(?:api[_-]?key|access[_-]?key|auth(?:orization)?|credential|"
    r"pass(?:word|wd)?|secret|token)\b\s*(?:=|:)\s*"
    r"(?:[\"'](?P<quoted>[A-Za-z0-9_./+=-]{12,200})[\"']|"
    r"(?P<bare>[A-Za-z0-9_./+=-]{12,200}))",
    re.IGNORECASE,
)
_HIGH_ENTROPY_CANDIDATE = re.compile(r"[A-Za-z0-9_./+=-]{20,200}")
_SAFE_PLACEHOLDERS = {
    "changeme", "dummy", "example", "notasecret", "placeholder", "replace-me", "test", "your-token-here",
}


class SecretScanner:
    """Produces stable spans for provider secrets, PII and generic credentials."""

    def __init__(self, extra_rules: list[DetectorRule] | None = None):
        self.rules = [
            DetectorRule("PRIVATE_KEY", "private-key-header", re.compile(
                r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----[\s\S]+?"
                r"-----END (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"
            )),
            DetectorRule("AWS_KEY", "aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
            DetectorRule("API_KEY", "openai-style-key", re.compile(r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,200}\b")),
            DetectorRule("GITHUB_TOKEN", "github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,255}\b")),
            DetectorRule("GITLAB_TOKEN", "gitlab-token", re.compile(r"\bglpat-[A-Za-z0-9_-]{20,255}\b")),
            DetectorRule("SLACK_TOKEN", "slack-token", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{20,255}\b")),
            DetectorRule("STRIPE_KEY", "stripe-key", re.compile(r"\b[rs]k_(?:live|test)_[A-Za-z0-9]{16,255}\b")),
            DetectorRule("EMAIL", "email", re.compile(r"[A-Za-z0-9_.+-]+@[A-Za-z0-9-]+\.[A-Za-z0-9-.]+"), "medium"),
            DetectorRule("IPV4", "ipv4", re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"), "medium"),
        ]
        if extra_rules:
            self.rules.extend(extra_rules)

    @staticmethod
    def shannon_entropy(value: str) -> float:
        if not value:
            return 0.0
        return -sum((count / len(value)) * log2(count / len(value)) for count in (value.count(char) for char in set(value)))

    @staticmethod
    def _contains_letter_and_number(value: str) -> bool:
        return any(char.isalpha() for char in value) and any(char.isdigit() for char in value)

    @staticmethod
    def _credential_context(text: str, start: int) -> bool:
        line_start = text.rfind("\n", 0, start) + 1
        return bool(_CREDENTIAL_WORDS.search(text[max(line_start, start - 80):start]))

    @staticmethod
    def _non_overlapping(findings: list[SecretFinding]) -> list[SecretFinding]:
        accepted: list[SecretFinding] = []
        generic_kinds = {"GENERIC_CREDENTIAL", "HIGH_ENTROPY_CREDENTIAL"}
        for finding in sorted(
            findings,
            key=lambda item: (item.start, item.kind in generic_kinds, -item.length, item.detector),
        ):
            if all(finding.end <= known.start or finding.start >= known.end for known in accepted):
                accepted.append(finding)
        return accepted

    def scan(self, text: str) -> list[SecretFinding]:
        if not text:
            return []
        findings: list[SecretFinding] = []
        for rule in self.rules:
            for match in rule.pattern.finditer(text):
                start, end = match.span(rule.value_group) if rule.value_group else match.span()
                findings.append(SecretFinding(rule.kind, rule.detector, rule.confidence, start, end))
        for match in _GENERIC_ASSIGNMENT.finditer(text):
            group = "quoted" if match.group("quoted") is not None else "bare"
            start, end = match.span(group)
            if text[start:end].lower() not in _SAFE_PLACEHOLDERS:
                findings.append(SecretFinding("GENERIC_CREDENTIAL", "credential-assignment", "medium", start, end))
        for match in _HIGH_ENTROPY_CANDIDATE.finditer(text):
            value = match.group(0)
            if (value.lower() not in _SAFE_PLACEHOLDERS and self._contains_letter_and_number(value)
                    and self._credential_context(text, match.start()) and self.shannon_entropy(value) >= 3.5):
                findings.append(SecretFinding("HIGH_ENTROPY_CREDENTIAL", "entropy-with-credential-context", "medium", match.start(), match.end()))
        return self._non_overlapping(findings)
