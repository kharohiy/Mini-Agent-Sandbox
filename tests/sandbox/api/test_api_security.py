import unittest
from unittest.mock import patch
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient

from api import app
from knowledge_store import KnowledgeStore
from project_policy import ProjectPolicyStore, default_policy
from project_retention import ProjectRetentionPreview
from project_registry import ProjectRegistry
from project_telemetry import ProjectTelemetryStore


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_plan_only_build_authorization_is_denied(self):
        response = self.client.post("/authorize", json={"mode": "plan_only", "capability": "build_test"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"allowed": False})

    def test_plan_only_execution_authorization_is_forbidden(self):
        response = self.client.post(
            "/execution/authorize",
            json={"mode": "plan_only", "workspace": "/untrusted", "command": ["echo", "no"]},
        )
        self.assertEqual(response.status_code, 403)

    def test_validated_authorization_never_executes_from_api(self):
        response = self.client.post(
            "/execution/authorize",
            json={"mode": "validated_execution", "workspace": "/untrusted", "command": ["echo", "no"]},
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["allowed"])
        self.assertIn("API never executes commands", response.json()["reason"])

    @patch("api.list_projects", return_value=["demo"])
    def test_projects_endpoint_only_lists_snapshots(self, _list_projects):
        response = self.client.get("/projects")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"projects": ["demo"]})

    @patch("api.snapshot_summary", return_value={"id": "demo", "modules": [":app"]})
    def test_snapshot_endpoint_is_read_only(self, _snapshot_summary):
        response = self.client.get("/projects/demo/snapshot")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["modules"], [":app"])

    @patch("api.search_snapshot", return_value=[{"path": "app/Main.kt"}])
    def test_search_endpoint_returns_snapshot_metadata_only(self, _search_snapshot):
        response = self.client.get("/projects/demo/search?q=Main")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["results"], [{"path": "app/Main.kt"}])

    @patch("api.list_project_documents", return_value=[{"source": "notes.md", "status": "active"}])
    @patch("api.ingest_project_document", return_value={"action": "indexed", "document": {"source": "notes.md"}})
    @patch("api.remove_project_document", return_value={"action": "removed", "document": {"source": "notes.md"}})
    def test_project_document_api_uses_explicit_request_content_not_a_disk_path(self, remove, ingest, list_documents):
        listed = self.client.get("/projects/demo--1234abcd/documents")
        created = self.client.post(
            "/projects/demo--1234abcd/documents",
            json={"source": "notes.md", "content": "owner supplied text", "confirmed": True},
        )
        removed = self.client.delete("/projects/demo--1234abcd/documents/notes.md?confirmed=true")
        self.assertEqual(listed.status_code, 200)
        self.assertEqual(created.status_code, 200)
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(ingest.call_args.kwargs["content"], "owner supplied text")
        self.assertNotIn("path", ingest.call_args.kwargs)
        self.assertTrue(remove.call_args.kwargs["confirmed"])
        self.assertEqual(list_documents.call_args.args, ("demo--1234abcd",))

    def test_knowledge_api_preserves_evidence_and_syncs_only_after_verify(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            store = KnowledgeStore(registry, root / "global")
            with patch("api.knowledge_store", store), patch("api.sync_card", return_value={"action": "indexed"}) as sync:
                created = self.client.post("/knowledge/global/cards", json={"title": "Docker", "problem": "Safety", "decision": "Isolate", "rationale": "Containment"})
                self.assertEqual(created.status_code, 200)
                card_id = created.json()["id"]
                self.assertEqual(self.client.post(f"/knowledge/global/cards/{card_id}/verify").status_code, 422)
                evidence = self.client.post(f"/knowledge/global/cards/{card_id}/evidence", json={"type": "policy", "reference": "contract", "description": "rule"})
                self.assertEqual(evidence.status_code, 200)
                verified = self.client.post(f"/knowledge/global/cards/{card_id}/verify")
                self.assertEqual(verified.status_code, 200)
                self.assertEqual(verified.json()["sync"]["action"], "indexed")
                self.assertEqual(sync.call_count, 1)

    def test_patch_api_requires_reviewer_then_explicit_user_approval(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ProjectPolicyStore(registry).update(
                project["id"], default_policy() | {"allowed_workspace_paths": ["app"]}
            )
            from work_ledger import WorkLedger
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Fix route", "Repair routing")
            plan = ledger.create_plan(task["id"], "Minimal fix")
            step = ledger.add_step(plan["id"], description="Edit route", files=["app/Nav.kt"], risks="regression", validation="Docker test", rollback="revert")
            ledger.approve_plan(plan["id"])
            diff = "diff --git a/app/Nav.kt b/app/Nav.kt\n--- a/app/Nav.kt\n+++ b/app/Nav.kt\n@@ -1 +1 @@\n-old\n+new\n"
            candidate = ledger.record_patch(step["id"], diff)
            with patch("api._ledger", return_value=ledger):
                before_review = self.client.post(
                    f"/projects/{project['id']}/patches/{candidate['id']}/approve",
                    json={"sha256": candidate["sha256"]},
                )
                self.assertEqual(before_review.status_code, 422)
                review = self.client.post(
                    f"/projects/{project['id']}/patches/{candidate['id']}/reviews",
                    json={"decision": "approved", "notes": "scope and tests checked"},
                )
                self.assertEqual(review.status_code, 200)
                self.assertEqual(review.json()["decision"], "approved")
                premature_validation = self.client.post(
                    f"/projects/{project['id']}/patches/{candidate['id']}/validation-reports",
                    json={"status": "validated", "report": {"exit_code": 0}},
                )
                self.assertEqual(premature_validation.status_code, 422)
                approval = self.client.post(
                    f"/projects/{project['id']}/patches/{candidate['id']}/approve",
                    json={"sha256": candidate["sha256"]},
                )
                self.assertEqual(approval.status_code, 200)
                self.assertEqual(approval.json()["status"], "approved")
                self.assertEqual(approval.json()["user_approval"]["patch_sha256"], candidate["sha256"])

    def test_operations_view_is_bounded_redacted_and_read_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            ProjectPolicyStore(registry).update(
                project["id"], default_policy() | {"allowed_workspace_paths": ["app"]}
            )
            from work_ledger import WorkLedger
            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task("Secret title", "PROMPT_SECRET")
            plan = ledger.create_plan(task["id"], "PLAN_SECRET")
            step = ledger.add_step(plan["id"], description="STEP_SECRET", files=["app/Nav.kt"], risks="RISK_SECRET", validation="VALIDATION_SECRET", rollback="ROLLBACK_SECRET")
            ledger.approve_plan(plan["id"])
            candidate = ledger.record_patch(step["id"], "diff --git a/app/Nav.kt b/app/Nav.kt\n--- a/app/Nav.kt\n+++ b/app/Nav.kt\n@@ -1 +1 @@\n-old\n+DIFF_SECRET\n")
            ledger.record_review(candidate["id"], "approved", "REVIEW_SECRET")
            ledger.approve_patch(candidate["id"], candidate["sha256"])
            ledger.record_validation(candidate["id"], "validated", {"output": "REPORT_SECRET"})
            store = KnowledgeStore(registry, root / "global")
            card = store.create(scope="project", project_id=project["id"], title="CARD_SECRET", problem="problem", decision="decision", rationale="rationale")
            store.add_evidence("project", card["id"], {"type": "policy", "reference": "contract"}, project["id"])
            store.verify("project", card["id"], project["id"])

            with patch("api._ledger", return_value=ledger), patch("api.knowledge_store", store):
                response = self.client.get(f"/projects/{project['id']}/operations")

            self.assertEqual(response.status_code, 200)
            view = response.json()
            self.assertEqual(view["project"]["id"], project["id"])
            patch_view = view["tasks"][0]["plans"][0]["steps"][0]["patches"][0]
            self.assertEqual(patch_view["sha256"], candidate["sha256"])
            self.assertEqual(patch_view["validation_reports"][0]["status"], "validated")
            self.assertEqual(view["knowledge_candidates"][0]["id"], card["id"])
            serialized = response.text
            for secret in ("PROMPT_SECRET", "PLAN_SECRET", "STEP_SECRET", "RISK_SECRET", "VALIDATION_SECRET", "ROLLBACK_SECRET", "DIFF_SECRET", "REVIEW_SECRET", "REPORT_SECRET", "CARD_SECRET"):
                self.assertNotIn(secret, serialized)

    def test_project_policy_api_defaults_to_deny_and_keeps_audit_redacted(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            store = ProjectPolicyStore(registry)
            policy = default_policy() | {"model_providers": ["ollama"]}

            with patch("api._project_policy", return_value=store):
                initial = self.client.get(f"/projects/{project['id']}/policy")
                updated = self.client.put(f"/projects/{project['id']}/policy", json=policy)
                audit = self.client.get(f"/projects/{project['id']}/policy/audit")

            self.assertEqual(initial.status_code, 200)
            self.assertEqual(initial.json()["auto_apply_level"], "never")
            self.assertEqual(updated.status_code, 200)
            self.assertEqual(updated.json()["model_providers"], ["ollama"])
            self.assertEqual(audit.status_code, 200)
            self.assertEqual(set(audit.json()["events"][0]), {"action", "schema_version", "sha256", "created_at"})

    def test_retention_preview_api_is_metadata_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            preview = ProjectRetentionPreview(registry)

            with patch("api._project_retention", return_value=preview):
                response = self.client.get(f"/projects/{project['id']}/retention/preview")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json(), {
                "project_id": project["id"],
                "categories": [
                    {"category": "telemetry", "retention_days": 30, "total_events": 0, "expired_events": 0},
                    {"category": "audit", "retention_days": 30, "total_events": 0, "expired_events": 0},
                ],
            })

    def test_metrics_api_exposes_only_aggregates_and_marks_missing_sources(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Demo")
            from work_ledger import WorkLedger
            ledger = WorkLedger(project["id"], registry)
            ledger.create_task("SECRET_TASK", "SECRET_PROMPT")
            store = KnowledgeStore(registry, root / "global")
            store.create(scope="project", project_id=project["id"], title="SECRET_CARD", problem="problem", decision="decision", rationale="rationale")
            telemetry = ProjectTelemetryStore(registry)
            telemetry.record(project["id"], event="model", outcome="success", provider="ollama", tokens=25)

            with patch("api._ledger", return_value=ledger), patch("api.knowledge_store", store), patch("api._project_telemetry", return_value=telemetry):
                response = self.client.get(f"/projects/{project['id']}/metrics")

            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["task_outcomes"], {"total": 1, "by_status": {"proposed": 1}})
            self.assertEqual(response.json()["knowledge"], {"total": 1, "by_status": {"draft": 1}})
            self.assertEqual(response.json()["retrieval_quality"]["availability"], "not_recorded")
            self.assertEqual(response.json()["telemetry"]["tokens"], 25)
            self.assertNotIn("SECRET_TASK", response.text)
            self.assertNotIn("SECRET_PROMPT", response.text)
            self.assertNotIn("SECRET_CARD", response.text)


if __name__ == "__main__":
    unittest.main()
