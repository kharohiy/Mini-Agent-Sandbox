import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import runner
from regulator_policy import evaluate_regulator_response
from telemetry_aggregator import aggregate_telemetry


REPORT = {
    "total_records": 10,
    "evidence": [{
        "id": "evt-one", "kind": "guardrail_triggered",
        "affected_rule": "guardrail.aws_key", "timestamp": "2026-10-02T00:00:00Z",
        "layer": "regex", "status": "",
    }],
}


class RegulatorPolicyTests(unittest.TestCase):
    def test_structured_evidence_bound_proposal_is_advisory_only(self):
        raw = json.dumps({
            "proposal": "Review the AWS key detector threshold.",
            "confidence": 0.8,
            "evidence": ["evt-one"],
            "affected_rule": "guardrail.aws_key",
        })
        decision = evaluate_regulator_response(raw, REPORT)
        self.assertEqual(decision["status"], "accepted_for_human_review")
        self.assertFalse(decision["auto_apply"])
        self.assertEqual(decision["proposal"]["evidence"], ["evt-one"])

    def test_unknown_evidence_extra_fields_and_rule_mismatch_fail_closed(self):
        base = {
            "proposal": "Change a rule", "confidence": 1,
            "evidence": ["missing"], "affected_rule": "guardrail.other",
        }
        for payload in (base, base | {"apply": True}, base | {"confidence": "high"}):
            with self.subTest(payload=payload):
                decision = evaluate_regulator_response(json.dumps(payload), REPORT)
                self.assertEqual(decision["status"], "rejected")
                self.assertFalse(decision["auto_apply"])

    def test_aggregator_emits_payload_free_evidence_and_rejects_path_ids(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            user_dir = root / "alice"
            user_dir.mkdir()
            secret = "synthetic-secret-value"
            (user_dir / "telemetry.json").write_text(json.dumps([{
                "timestamp": "2026-10-02T00:00:00Z", "event": "guardrail_triggered",
                "rule": "AWS_KEY", "layer": "regex", "matched_length": len(secret),
            }]), encoding="utf-8")
            report = aggregate_telemetry("alice", root)
            written = (user_dir / "incident_summary.json").read_text(encoding="utf-8")
        self.assertEqual(report["evidence"][0]["affected_rule"], "guardrail.aws_key")
        self.assertNotIn(secret, written)
        with self.assertRaises(ValueError):
            aggregate_telemetry("../alice", "data")

    def test_trigger_regulator_admits_only_for_review_without_tools_or_mutation(self):
        raw = json.dumps({
            "proposal": "Review the AWS key detector threshold.", "confidence": 0.8,
            "evidence": ["evt-one"], "affected_rule": "guardrail.aws_key",
        })
        response = SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=raw))])
        roles_before = Path("roles.json").read_bytes()
        capabilities_before = Path("capabilities.json").read_bytes()
        with patch("runner.aggregate_telemetry", return_value=REPORT), patch(
            "runner.safe_llm_completion", return_value=response
        ) as completion:
            decision = runner.trigger_regulator("alice")
        self.assertEqual(decision["status"], "accepted_for_human_review")
        self.assertFalse(decision["auto_apply"])
        self.assertIsNone(completion.call_args.kwargs["tools"])
        self.assertEqual(Path("roles.json").read_bytes(), roles_before)
        self.assertEqual(Path("capabilities.json").read_bytes(), capabilities_before)

    def test_trigger_regulator_skips_model_when_no_actionable_evidence(self):
        with patch("runner.aggregate_telemetry", return_value={
            "total_records": 10, "evidence": [],
        }), patch("runner.safe_llm_completion") as completion:
            self.assertIsNone(runner.trigger_regulator("alice"))
        completion.assert_not_called()


if __name__ == "__main__":
    unittest.main()
