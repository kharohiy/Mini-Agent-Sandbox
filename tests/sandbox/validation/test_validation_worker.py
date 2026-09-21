import hashlib
import sqlite3
import difflib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from project_registry import ProjectRegistry
from project_policy import ProjectPolicyStore, default_policy
from validation_worker import ValidationRejected, ValidationWorker
from work_ledger import WorkLedger


def make_diff(old="app/Main.kt", before="old", after="new"):
    old_text = f"package test\nval value = {before}\nend\n"
    new_text = f"package test\nval value = {after}\nend\n"
    body = list(difflib.unified_diff(old_text.splitlines(), new_text.splitlines(),
                                     fromfile=f"a/{old}", tofile=f"b/{old}", n=3,
                                     lineterm=""))
    return f"diff --git a/{old} b/{old}\n" + "\n".join(body) + "\n"


class FakeExecutor:
    image = "fake-image:test"

    def __init__(self, stdout="ok", stderr="", exit_code=0, raises=False, timed_out=False):
        self.stdout, self.stderr, self.exit_code, self.raises = stdout, stderr, exit_code, raises
        self.timed_out = timed_out
        self.requests = []
        self.source_text = None
        self.vault_was_copied = None
        self.env_was_copied = None

    def execute(self, request):
        self.requests.append(request)
        self.source_text = (Path(request.workspace) / "app/Main.kt").read_text(encoding="utf-8")
        self.vault_was_copied = (Path(request.workspace) / ".vault").exists()
        self.env_was_copied = (Path(request.workspace) / ".ENV").exists()
        if self.raises:
            raise RuntimeError("executor failure")
        return SimpleNamespace(allowed=self.exit_code == 0, reason="done", exit_code=self.exit_code,
                               stdout=self.stdout, stderr=self.stderr, timed_out=self.timed_out)


class ValidationWorkerTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.source = self.root / "source"
        (self.source / "app").mkdir(parents=True)
        (self.source / "app/Main.kt").write_bytes(b"package test\nval value = old\nend\n")
        (self.source / ".vault").mkdir()
        (self.source / ".vault/secret.txt").write_text("do not copy", encoding="utf-8")
        (self.source / ".ENV").write_text("API_KEY=private", encoding="utf-8")
        self.registry = ProjectRegistry(self.root / "registry.sqlite", self.root / "projects")
        self.project = self.registry.register(self.source, "Demo")
        self.policy_store = ProjectPolicyStore(self.registry)
        self.policy_store.update(self.project["id"], default_policy() | {
            "allowed_workspace_paths": ["app"],
            "validation_profiles": ["test", "lint", "module_test"],
        })
        self.ledger = WorkLedger(self.project["id"], self.registry)
        task = self.ledger.create_task("Change", "Test change")
        self.task_id = task["id"]
        plan = self.ledger.create_plan(task["id"], "Change source")
        step = self.ledger.add_step(plan["id"], description="Edit source", files=["app/Main.kt"],
                                    risks="regression", validation="offline tests", rollback="revert diff")
        self.ledger.approve_plan(plan["id"])
        self.patch = self.ledger.record_patch(step["id"], make_diff())
        self.ledger.record_review(self.patch["id"], "approved", "reviewed")
        self.ledger.approve_patch(self.patch["id"], self.patch["sha256"])
        self.temp_root = self.root / "worker-temp"
        self.temp_root.mkdir()

    def tearDown(self):
        self.temporary.cleanup()

    def worker(self, executor):
        return ValidationWorker(registry=self.registry, executor=executor, temp_root=self.temp_root,
                                policy_store=self.policy_store)

    def sql(self, statement, values):
        db_path = self.registry.state_dir(self.project["id"]) / "runs/work_ledger.sqlite"
        db = sqlite3.connect(db_path)
        try:
            db.execute(statement, values)
            db.commit()
        finally:
            db.close()

    def test_patch_is_applied_only_to_copy_and_audited(self):
        before = (self.source / "app/Main.kt").read_bytes()
        executor = FakeExecutor()
        report = self.worker(executor).run(self.project["id"], self.patch["id"])
        self.assertEqual(report["status"], "validated")
        self.assertEqual(executor.source_text, "package test\nval value = new\nend\n")
        self.assertFalse(executor.vault_was_copied)
        self.assertFalse(executor.env_was_copied)
        self.assertEqual((self.source / "app/Main.kt").read_bytes(), before)
        self.assertEqual(list(self.temp_root.iterdir()), [])
        persisted = self.ledger.task(self.task_id)
        # Reports are attached to the task via the plan/step/patch audit chain.
        self.assertEqual(persisted["plans"][0]["steps"][0]["patches"][0]["validation_reports"][0]["status"], "validated")

    def assert_refused_before_execution(self, executor):
        with self.assertRaises(ValidationRejected):
            self.worker(executor).run(self.project["id"], self.patch["id"])
        self.assertEqual(executor.requests, [])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_reviewer_rejection_and_missing_user_approval_fail_closed(self):
        # A separate rejected candidate exercises the persisted rejection gate.
        task = self.ledger.create_task("Reject", "test")
        plan = self.ledger.create_plan(task["id"], "reject")
        step = self.ledger.add_step(plan["id"], description="edit", files=["app/Main.kt"], risks="risk", validation="test", rollback="revert")
        self.ledger.approve_plan(plan["id"])
        rejected = self.ledger.record_patch(step["id"], make_diff())
        self.ledger.record_review(rejected["id"], "rejected", "unsafe")
        self.patch = rejected
        self.assert_refused_before_execution(FakeExecutor())

        task = self.ledger.create_task("No approval", "test")
        plan = self.ledger.create_plan(task["id"], "no user gate")
        step = self.ledger.add_step(plan["id"], description="edit", files=["app/Main.kt"], risks="risk", validation="test", rollback="revert")
        self.ledger.approve_plan(plan["id"])
        missing = self.ledger.record_patch(step["id"], make_diff())
        self.ledger.record_review(missing["id"], "approved", "reviewed")
        self.patch = missing
        self.assert_refused_before_execution(FakeExecutor())

    def test_wrong_approval_hash_and_changed_patch_fail_closed(self):
        self.sql("UPDATE patch_approvals SET patch_sha256 = ? WHERE patch_id = ?", ("0" * 64, self.patch["id"]))
        self.assert_refused_before_execution(FakeExecutor())
        self.sql("UPDATE patch_approvals SET patch_sha256 = ? WHERE patch_id = ?", (self.patch["sha256"], self.patch["id"]))
        self.sql("UPDATE patches SET diff = ? WHERE id = ?", (make_diff(after="tampered"), self.patch["id"]))
        self.assert_refused_before_execution(FakeExecutor())

    def test_malformed_patch_and_path_escape_fail_closed(self):
        for diff in ("not a diff\n", make_diff("../outside.kt")):
            digest = hashlib.sha256(diff.encode()).hexdigest()
            self.sql("UPDATE patches SET diff = ?, sha256 = ? WHERE id = ?", (diff, digest, self.patch["id"]))
            self.sql("UPDATE patch_approvals SET patch_sha256 = ? WHERE patch_id = ?", (digest, self.patch["id"]))
            self.assert_refused_before_execution(FakeExecutor())

    def test_disallowed_profile_is_refused_and_output_is_bounded_and_redacted(self):
        executor = FakeExecutor(stdout="api_key=supersecret " + "x" * 2000)
        with self.assertRaises(ValidationRejected):
            self.worker(executor).run(self.project["id"], self.patch["id"], profile="clean")
        self.assertEqual(executor.requests, [])
        worker = ValidationWorker(registry=self.registry, executor=executor,
                                  temp_root=self.temp_root, output_limit=256,
                                  policy_store=self.policy_store)
        report = worker.run(self.project["id"], self.patch["id"])
        self.assertLessEqual(len(report["stdout"]), 256)
        self.assertNotIn("supersecret", report["stdout"])

    def test_module_profile_is_resolved_only_from_registered_snapshot(self):
        snapshot = self.registry.state_dir(self.project["id"]) / "snapshot/project_snapshot.sqlite"
        connection = sqlite3.connect(snapshot)
        try:
            connection.execute("CREATE TABLE files (path TEXT, module TEXT)")
            connection.execute("INSERT INTO files VALUES (?, ?)", ("app/Main.kt", ":app"))
            connection.commit()
        finally:
            connection.close()
        executor = FakeExecutor()
        self.worker(executor).run(self.project["id"], self.patch["id"],
                                  profile="module_test", module=":app")
        self.assertEqual(executor.requests[0].command, ["./gradlew", "--offline", ":app:test"])
        with self.assertRaises(ValidationRejected):
            self.worker(FakeExecutor()).run(self.project["id"], self.patch["id"],
                                            profile="module_test", module=":unregistered")

    def test_temp_copy_is_removed_when_executor_raises(self):
        with self.assertRaisesRegex(RuntimeError, "executor failure"):
            self.worker(FakeExecutor(raises=True)).run(self.project["id"], self.patch["id"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_temp_copy_is_removed_after_executor_timeout(self):
        report = self.worker(FakeExecutor(exit_code=None, timed_out=True)).run(
            self.project["id"], self.patch["id"])
        self.assertEqual(report["status"], "blocked")
        self.assertTrue(report["timed_out"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_staged_profiles_share_one_copy_and_persist_stage_evidence(self):
        executor = FakeExecutor(stdout="stage ok")
        report = self.worker(executor).run(self.project["id"], self.patch["id"],
                                           profile=["test", "lint"])
        self.assertEqual(report["status"], "validated")
        self.assertEqual([stage["profile"] for stage in report["stages"]], ["test", "lint"])
        self.assertEqual(len(executor.requests), 2)
        self.assertEqual(executor.requests[0].workspace, executor.requests[1].workspace)
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_staged_validation_stops_after_first_failed_stage(self):
        executor = FakeExecutor(exit_code=1, stdout="failed")
        report = self.worker(executor).run(self.project["id"], self.patch["id"],
                                           profile=["test", "lint"])
        self.assertEqual(report["status"], "rejected")
        self.assertEqual(len(executor.requests), 1)
        self.assertEqual([stage["profile"] for stage in report["stages"]], ["test"])
        self.assertEqual(list(self.temp_root.iterdir()), [])

    def test_temp_root_inside_project_is_rejected_before_directory_creation(self):
        unsafe_root = self.source / "worker-temp"
        with self.assertRaises(ValidationRejected):
            ValidationWorker(registry=self.registry, executor=FakeExecutor(),
                             temp_root=unsafe_root).run(self.project["id"], self.patch["id"])
        self.assertFalse(unsafe_root.exists())

    def test_missing_or_nonmatching_project_policy_blocks_before_execution(self):
        self.policy_store._policy_path(self.project["id"]).unlink()
        self.assert_refused_before_execution(FakeExecutor())
        self.policy_store.update(self.project["id"], default_policy() | {
            "validation_profiles": ["lint"],
        })
        self.assert_refused_before_execution(FakeExecutor())


if __name__ == "__main__":
    unittest.main()
