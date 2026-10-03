"""Deterministic behavioral security evaluation entry point.

Model prose is quality evidence only. Security acceptance comes from tests that
inspect state and side effects after exercising the real policy boundaries.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import unittest


MANIFEST = Path(__file__).with_name("tests") / "security_behavioral_manifest.json"
REQUIRED_EFFECTS = {
    "filesystem_side_effect", "state_mutation", "fact_mutation",
    "network_access", "tool_execution", "vault_access",
}


def load_manifest(path: Path = MANIFEST) -> list[dict]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cases = payload.get("cases")
    if not isinstance(cases, list) or not cases:
        raise ValueError("behavioral eval manifest must contain cases")
    identifiers, covered_effects = set(), set()
    for case in cases:
        if not isinstance(case, dict) or set(case) != {"id", "effect", "assertion", "test"}:
            raise ValueError("each behavioral eval requires id, effect, assertion and test")
        if not all(isinstance(case[key], str) and case[key].strip() for key in case):
            raise ValueError("behavioral eval fields must be non-empty strings")
        if case["id"] in identifiers:
            raise ValueError("behavioral eval ids must be unique")
        identifiers.add(case["id"])
        covered_effects.add(case["effect"])
    missing = REQUIRED_EFFECTS - covered_effects
    if missing:
        raise ValueError("behavioral eval manifest is missing effects: " + ", ".join(sorted(missing)))
    return cases


def run_evals() -> int:
    os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")
    cases = load_manifest()
    failures = []
    print("Starting deterministic behavioral security evals...")
    for case in cases:
        suite = unittest.defaultTestLoader.loadTestsFromName(case["test"])
        if suite.countTestCases() != 1:
            raise ValueError(f"{case['id']} must resolve to exactly one test")
        result = unittest.TextTestRunner(verbosity=0).run(suite)
        passed = result.wasSuccessful() and not result.skipped
        print(f"{'PASS' if passed else 'FAIL'} {case['id']} [{case['effect']}]: {case['assertion']}")
        if not passed:
            failures.append(case["id"])
    print(f"Behavioral security result: {len(cases) - len(failures)}/{len(cases)} passed.")
    if failures:
        print("Failed cases: " + ", ".join(failures), file=sys.stderr)
        return 1
    print("Model-output adversarial prompts are excluded from this security result.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_evals())
