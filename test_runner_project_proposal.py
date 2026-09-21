import tempfile
import unittest
import json
from pathlib import Path

from project_policy import ProjectPolicyStore, default_policy
from project_registry import ProjectRegistry
from runner import (
    agent_tools_for_task_mode,
    project_patch_context,
    record_project_patch_proposal,
    record_project_patch_response,
    recover_project_patch_response,
)
from work_ledger import WorkLedger


DIFF = """diff --git a/app/Main.kt b/app/Main.kt
--- a/app/Main.kt
+++ b/app/Main.kt
@@ -1 +1 @@
-old
+new
"""


class RunnerProjectProposalTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        source = root / "source"
        (source / "app").mkdir(parents=True)
        (source / "app" / "Main.kt").write_text("old\n", encoding="utf-8")
        self.registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        self.project = self.registry.register(source, "Demo")
        ProjectPolicyStore(self.registry).update(
            self.project["id"], default_policy() | {"allowed_workspace_paths": ["app"]}
        )
        self.ledger = WorkLedger(self.project["id"], self.registry)
        task = self.ledger.create_task("Change greeting", "Create a bounded patch proposal")
        self.task_id = task["id"]
        plan = self.ledger.create_plan(self.task_id, "Change Main")
        self.step = self.ledger.add_step(
            plan["id"], description="Edit Main", files=["app/Main.kt"],
            risks="regression", validation="test", rollback="revert",
        )
        self.ledger.approve_plan(plan["id"])

    def tearDown(self):
        self.temporary.cleanup()

    def test_project_patch_mode_exposes_only_proposal_tool_and_persists_no_source_write(self):
        tools = agent_tools_for_task_mode("code", "coder", self.step["id"])
        self.assertEqual([tool["function"]["name"] for tool in tools], ["propose_patch"])
        before = (Path(self.project["source_path"]) / "app/Main.kt").read_bytes()

        patch = record_project_patch_proposal(
            self.project["id"], self.step["id"], DIFF, registry=self.registry
        )

        self.assertEqual(patch["status"], "proposed")
        self.assertEqual((Path(self.project["source_path"]) / "app/Main.kt").read_bytes(), before)

    def test_project_patch_context_is_limited_to_the_approved_step_files(self):
        self.assertEqual(
            project_patch_context(self.project["id"], self.step["id"], registry=self.registry),
            ["app/Main.kt"],
        )

    def test_project_patch_proposal_is_rejected_before_persistence_when_policy_scope_fails(self):
        blocked = DIFF.replace("app/Main.kt", "outside.kt")

        with self.assertRaisesRegex(ValueError, "scope|allowed|declared"):
            record_project_patch_proposal(
                self.project["id"], self.step["id"], blocked, registry=self.registry
            )

        self.assertEqual(self.ledger.task(self.task_id)["plans"][0]["steps"][0]["patches"], [])

    def test_structured_model_response_with_omitted_git_line_is_normalized_and_recorded(self):
        raw_response = json.dumps({"diff": DIFF.split("\n", 1)[1]})

        patch = record_project_patch_response(
            self.project["id"], self.step["id"], raw_response, registry=self.registry
        )

        self.assertEqual(patch["status"], "proposed")
        self.assertTrue(patch["diff"].startswith("diff --git a/app/Main.kt b/app/Main.kt\n"))

    def test_structured_model_response_cannot_normalize_an_out_of_scope_path(self):
        raw_response = json.dumps({"diff": DIFF.split("\n", 1)[1].replace("app/Main.kt", "outside.kt")})

        with self.assertRaisesRegex(ValueError, "outside the approved step"):
            record_project_patch_response(
                self.project["id"], self.step["id"], raw_response, registry=self.registry
            )

    def test_serialized_tool_envelope_is_recovered_through_the_same_policy_boundary(self):
        state = {
            "proposal_step_id": self.step["id"],
            "memory": [{
                "role": "coder",
                "content": json.dumps({"name": "propose_patch", "arguments": {"diff": DIFF}}),
            }],
        }

        patch = recover_project_patch_response(
            state, project_id=self.project["id"], registry=self.registry
        )

        self.assertEqual(patch["status"], "proposed")
        self.assertEqual(state["patch_proposal"]["id"], patch["id"])
        self.assertEqual(state["current_turn"], "reviewer")
        self.assertEqual(state["tool_executions"][-1]["tool_name"], "propose_patch_response_adapter")

    def test_legacy_tool_envelope_with_unescaped_diff_quotes_is_recovered(self):
        escaped_lines = DIFF.replace("\n", "\\n").replace("old", '"old"')
        response = '{"name": "propose_patch", "arguments":{"diff": "' + escaped_lines + '"}}'

        patch = record_project_patch_response(
            self.project["id"], self.step["id"], response, registry=self.registry
        )

        self.assertEqual(patch["status"], "proposed")

    def test_legacy_tool_envelope_with_a_single_outer_closing_brace_is_recovered(self):
        escaped_lines = DIFF.replace("\n", "\\n").replace("old", '"old"')
        response = '{"name": "propose_patch", "arguments":{"diff": "' + escaped_lines + '"}'

        patch = record_project_patch_response(
            self.project["id"], self.step["id"], response, registry=self.registry
        )

        self.assertEqual(patch["status"], "proposed")

    def test_repeated_proposal_returns_the_existing_ledger_record(self):
        first = record_project_patch_proposal(
            self.project["id"], self.step["id"], DIFF, registry=self.registry
        )
        repeated = record_project_patch_proposal(
            self.project["id"], self.step["id"], DIFF, registry=self.registry
        )

        self.assertEqual(repeated["id"], first["id"])
        self.assertEqual(len(self.ledger.task(self.task_id)["plans"][0]["steps"][0]["patches"]), 1)


if __name__ == "__main__":
    unittest.main()
