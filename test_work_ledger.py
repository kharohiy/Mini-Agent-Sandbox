import tempfile
import unittest
from pathlib import Path

from project_registry import ProjectRegistry
from project_policy import ProjectPolicyStore, default_policy
from work_ledger import WorkLedger


def unified_diff(path="app/Nav.kt"):
    return f"diff --git a/{path} b/{path}\n--- a/{path}\n+++ b/{path}\n@@ -1 +1 @@\n-old\n+new\n"


def allow_workspace_paths(registry, project_id, paths):
    ProjectPolicyStore(registry).update(
        project_id, default_policy() | {"allowed_workspace_paths": paths}
    )


class WorkLedgerTests(unittest.TestCase):
    def test_task_plan_is_persistent_and_requires_inspectable_step_details(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Fix navigation", "Repair route handling")
            plan = ledger.create_plan(task["id"], "Make the minimal route fix")
            with self.assertRaises(ValueError):
                ledger.approve_plan(plan["id"])
            ledger.add_step(plan["id"], description="Update route", files=["app/Nav.kt"], risks="route regression", validation="Docker unit test", rollback="revert patch")
            approved = ledger.approve_plan(plan["id"])
            restored = WorkLedger(project["id"], registry).task(task["id"])
            self.assertEqual(approved["status"], "approved")
            self.assertEqual(restored["status"], "approved")
            self.assertEqual(restored["plans"][0]["steps"][0]["files"], ["app/Nav.kt"])

    def test_patch_requires_review_before_validation_and_records_audit_chain(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Fix route", "Repair routing")
            plan = ledger.create_plan(task["id"], "Minimal fix")
            step = ledger.add_step(plan["id"], description="Edit navigation", files=["app/Nav.kt"], risks="route regression", validation="Docker test", rollback="revert")
            ledger.approve_plan(plan["id"])
            allow_workspace_paths(registry, project["id"], ["app"])
            patch = ledger.record_patch(step["id"], unified_diff())
            with self.assertRaises(ValueError):
                ledger.record_validation(patch["id"], "validated", {"exit_code": 0})
            ledger.record_review(patch["id"], "approved", "scope is minimal")
            with self.assertRaises(ValueError):
                ledger.record_validation(patch["id"], "validated", {"exit_code": 0})
            ledger.approve_patch(patch["id"], patch["sha256"])
            report = ledger.record_validation(patch["id"], "validated", {"executor": "docker", "exit_code": 0})
            run = ledger.record_run(task["id"], "validated", "Docker validation passed")
            self.assertEqual(report["status"], "validated")
            self.assertEqual(run["status"], "validated")
            restored = WorkLedger(project["id"], registry).task(task["id"])
            self.assertEqual(restored["status"], "validated")
            self.assertEqual(restored["runs"][0]["id"], run["id"])
            restored_patch = restored["plans"][0]["steps"][0]["patches"][0]
            self.assertEqual(restored_patch["reviews"][0]["decision"], "approved")
            self.assertEqual(restored_patch["user_approval"]["patch_sha256"], restored_patch["sha256"])
            self.assertEqual(restored_patch["validation_reports"][0]["report"]["executor"], "docker")
            self.assertEqual(ledger.list_tasks("validated")[0]["id"], task["id"])

    def test_patch_requires_exact_plan_scope_and_explicit_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary); source = root / "source"; source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Fix route", "Repair routing")
            plan = ledger.create_plan(task["id"], "Minimal fix")
            step = ledger.add_step(plan["id"], description="Edit navigation", files=["app/Nav.kt"], risks="route regression", validation="Docker test", rollback="revert")
            ledger.approve_plan(plan["id"])
            allow_workspace_paths(registry, project["id"], ["app"])
            for unsafe in (
                unified_diff("app/Other.kt"),
                unified_diff("../outside.kt"),
                unified_diff(".vault/secret.kt"),
                "APPROVE\n",
            ):
                with self.assertRaises(ValueError):
                    ledger.record_patch(step["id"], unsafe)
            patch = ledger.record_patch(step["id"], unified_diff())
            with self.assertRaises(ValueError):
                ledger.approve_patch(patch["id"], patch["sha256"])
            ledger.record_review(patch["id"], "approved", "scope and tests look good")
            self.assertEqual(ledger.patch(patch["id"])["status"], "review_approved")
            with self.assertRaises(ValueError):
                ledger.approve_patch(patch["id"], "0" * 64)
            with self.assertRaises(ValueError):
                ledger.record_review(patch["id"], "rejected", "cannot overwrite review")
            approved = ledger.approve_patch(patch["id"], patch["sha256"])
            self.assertEqual(ledger.patch(patch["id"])["status"], "approved")
            self.assertEqual(approved["user_approval"]["patch_sha256"], patch["sha256"])
            restored = WorkLedger(project["id"], registry).patch(patch["id"])
            self.assertEqual(restored["status"], "approved")
            self.assertEqual(restored["user_approval"]["patch_sha256"], patch["sha256"])

    def test_patch_workspace_policy_is_default_deny_and_blocks_before_persistence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Fix route", "Repair routing")
            plan = ledger.create_plan(task["id"], "Minimal fix")
            step = ledger.add_step(plan["id"], description="Edit navigation", files=["app/Nav.kt"], risks="route regression", validation="Docker test", rollback="revert")
            ledger.approve_plan(plan["id"])
            with self.assertRaisesRegex(ValueError, "does not allow"):
                ledger.record_patch(step["id"], unified_diff())
            self.assertEqual(ledger.task(task["id"])["plans"][0]["steps"][0]["patches"], [])

            allow_workspace_paths(registry, project["id"], ["docs"])
            with self.assertRaisesRegex(ValueError, "not allowed"):
                ledger.record_patch(step["id"], unified_diff())
            self.assertEqual(ledger.task(task["id"])["plans"][0]["steps"][0]["patches"], [])


if __name__ == "__main__":
    unittest.main()
