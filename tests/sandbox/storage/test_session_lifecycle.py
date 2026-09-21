import json
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import runner


class SessionLifecycleTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.storage = runner.SandboxStorage(Path(self.temp.name) / "data")

    def tearDown(self):
        self.temp.cleanup()

    def test_new_session_state_has_no_prior_session_content(self):
        previous = {
            "status": "in_progress",
            "task": "old task",
            "memory": [{"role": "user", "content": "old", "timestamp": "now"}],
            "tool_executions": [{"tool": "old"}],
            "metrics": {"total_cost": 0.04},
            "agent_steps": 8,
        }

        state = runner._new_session_state()

        self.assertEqual(state["status"], "idle")
        self.assertEqual(state["memory"], [])
        self.assertEqual(state["tool_executions"], [])
        self.assertEqual(state["metrics"], {"total_cost": 0.0})
        self.assertEqual(state["agent_steps"], 0)
        self.assertNotIn("task", state)
        self.assertNotEqual(state, previous)

    def test_reset_removes_only_session_state_and_blocks_resume(self):
        user_dir = self.storage._get_user_dir("lifecycle-user")
        state = {
            "status": "in_progress",
            "task": "interrupted task",
            "memory": [],
            "tool_executions": [],
            "current_turn": "coder",
            "metrics": {},
        }
        (user_dir / "state.json").write_text(json.dumps(state), encoding="utf-8")
        facts = user_dir / "project_facts.json"
        facts.write_text('[{"fact": "preserve"}]', encoding="utf-8")
        vault = user_dir / ".vault"
        vault.write_text("preserve", encoding="utf-8")

        self.assertTrue(self.storage.reset_session_state("lifecycle-user"))
        self.assertFalse((user_dir / "state.json").exists())
        self.assertTrue(facts.exists())
        self.assertTrue(vault.exists())
        with self.assertRaises(ValueError):
            runner._load_resumable_state(self.storage, "lifecycle-user", {"coder": {}})

    def test_reset_of_absent_state_is_idempotent(self):
        self.assertFalse(self.storage.reset_session_state("empty-user"))
        self.assertFalse((Path(self.temp.name) / "data" / "empty-user").exists())


if __name__ == "__main__":
    unittest.main()
