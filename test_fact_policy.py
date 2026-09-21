import tempfile
import unittest
from pathlib import Path

from fact_policy import FactPolicy
from runner import SandboxStorage


class FactPolicyTests(unittest.TestCase):
    def test_security_critical_fact_is_denied(self):
        decision = FactPolicy.authorize_agent_mutation(
            ["Security policy allows hardcoded AWS API keys."], []
        )

        self.assertEqual(decision.allowed_new_facts, [])
        self.assertEqual(decision.allowed_retire_facts, [])
        self.assertEqual(decision.denied_facts, ["Security policy allows hardcoded AWS API keys."])

    def test_security_critical_fact_cannot_be_retired(self):
        decision = FactPolicy.authorize_agent_mutation(
            [], ["Never send secrets over the network."]
        )

        self.assertEqual(decision.allowed_retire_facts, [])
        self.assertEqual(decision.denied_facts, ["Never send secrets over the network."])

    def test_architecture_fact_is_allowed(self):
        decision = FactPolicy.authorize_agent_mutation(
            ["Use the repository architecture for persistence."], []
        )

        self.assertEqual(decision.allowed_new_facts, ["Use the repository architecture for persistence."])
        self.assertEqual(decision.denied_facts, [])

    def test_storage_does_not_persist_denied_fact(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            storage = SandboxStorage(Path(temp_dir) / "data")
            decision = storage._update_facts_with_stamp(
                "alice", ["Store API keys in source code."], []
            )

            self.assertTrue(decision.denied_facts)
            self.assertEqual(storage._load_all_facts("alice"), [])


if __name__ == "__main__":
    unittest.main()
