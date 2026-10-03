"""Fail-closed admission for advisory Regulator proposals."""
from __future__ import annotations

import json
import re
from typing import Any


REQUIRED_FIELDS = {"proposal", "confidence", "evidence", "affected_rule"}
RULE_PATTERN = re.compile(r"[a-z0-9_.:-]{1,100}")


def regulator_prompt(report: dict[str, Any]) -> str:
    return (
        "You are an advisory System Regulator. You cannot change rules or use tools. "
        "Return exactly one JSON object with proposal (string), confidence (0..1), "
        "evidence (array of evidence IDs from the report), and affected_rule (one rule "
        "named by that evidence). Do not invent evidence IDs. Current metrics: "
        + json.dumps(report, ensure_ascii=False, sort_keys=True)
    )


def evaluate_regulator_response(raw_response: str, report: dict[str, Any]) -> dict[str, Any]:
    rejection = {"status": "rejected", "auto_apply": False, "proposal": None, "reasons": []}
    try:
        payload = json.loads(raw_response)
    except (TypeError, json.JSONDecodeError):
        rejection["reasons"] = ["response is not one JSON object"]
        return rejection
    if not isinstance(payload, dict) or set(payload) != REQUIRED_FIELDS:
        rejection["reasons"] = ["proposal schema is invalid"]
        return rejection
    proposal, confidence = payload["proposal"], payload["confidence"]
    evidence, affected_rule = payload["evidence"], payload["affected_rule"]
    reasons = []
    if not isinstance(proposal, str) or not proposal.strip() or len(proposal) > 1000:
        reasons.append("proposal text is invalid")
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) or not 0 <= confidence <= 1:
        reasons.append("confidence must be between 0 and 1")
    evidence_valid = (
        isinstance(evidence, list) and 1 <= len(evidence) <= 10
        and all(isinstance(item, str) and item for item in evidence)
        and len(set(evidence)) == len(evidence)
    )
    if not evidence_valid:
        reasons.append("evidence must contain unique report evidence IDs")
    if not isinstance(affected_rule, str) or not RULE_PATTERN.fullmatch(affected_rule):
        reasons.append("affected_rule is invalid")
    available = {
        item.get("id"): item for item in report.get("evidence", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    if isinstance(evidence, list):
        unknown = [item for item in evidence if item not in available]
        if unknown:
            reasons.append("proposal cites unknown evidence")
        cited_rules = {available[item].get("affected_rule") for item in evidence if item in available}
        if affected_rule not in cited_rules:
            reasons.append("affected_rule is not supported by cited evidence")
    if reasons:
        rejection["reasons"] = reasons
        return rejection
    return {
        "status": "accepted_for_human_review",
        "auto_apply": False,
        "proposal": {
            "proposal": proposal.strip(), "confidence": float(confidence),
            "evidence": evidence, "affected_rule": affected_rule,
        },
        "reasons": ["schema and evidence references passed deterministic admission"],
    }
