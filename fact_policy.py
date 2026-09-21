"""Deterministic authorization for long-term project facts."""

import re
from dataclasses import dataclass


SECURITY_CRITICAL_TERMS = (
    "security", "secret", "credential", "password", "api key", "token", "vault",
    "guardrail", "authentication", "authorization", "permission", "privilege",
    "access control", "sandbox", "path traversal", "symlink", "shell", "subprocess",
    "network", "exfiltrat", "encryption", "decrypt", "policy",
)

ALLOWED_AGENT_FACT_TERMS = (
    "architecture", "architectural", "code style", "coding style", "dependency",
    "dependencies", "library", "libraries", "framework", "module", "interface",
    "repository", "test", "testing", "validation", "kotlin", "android", "compose",
)


@dataclass(frozen=True)
class FactMutationDecision:
    allowed_new_facts: list[str]
    allowed_retire_facts: list[str]
    denied_facts: list[str]


class FactPolicy:
    """Treat LLMs as untrusted fact-mutation callers."""

    @staticmethod
    def _normalize(fact) -> str | None:
        if not isinstance(fact, str):
            return None
        normalized = re.sub(r"\s+", " ", fact).strip()
        return normalized or None

    @classmethod
    def is_security_critical(cls, fact) -> bool:
        normalized = cls._normalize(fact)
        return bool(normalized and any(term in normalized.lower() for term in SECURITY_CRITICAL_TERMS))

    @classmethod
    def is_allowed_agent_fact(cls, fact) -> bool:
        normalized = cls._normalize(fact)
        return bool(normalized and any(term in normalized.lower() for term in ALLOWED_AGENT_FACT_TERMS))

    @classmethod
    def authorize_agent_mutation(cls, new_facts, retire_facts) -> FactMutationDecision:
        allowed_new, allowed_retire, denied = [], [], []
        new_facts = new_facts if isinstance(new_facts, (list, tuple)) else [new_facts]
        retire_facts = retire_facts if isinstance(retire_facts, (list, tuple)) else [retire_facts]

        for fact in new_facts:
            normalized = cls._normalize(fact)
            if normalized is None:
                denied.append(str(fact))
            elif cls.is_security_critical(normalized):
                denied.append(normalized)
            elif cls.is_allowed_agent_fact(normalized):
                allowed_new.append(normalized)
            else:
                denied.append(normalized)

        for fact in retire_facts:
            normalized = cls._normalize(fact)
            if normalized is None or cls.is_security_critical(normalized):
                denied.append(str(fact))
            else:
                allowed_retire.append(normalized)

        return FactMutationDecision(allowed_new, allowed_retire, denied)
