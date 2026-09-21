from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from capability_policy import CapabilityDenied, CapabilityPolicy
from project_search import list_projects, search_snapshot, snapshot_summary
from knowledge_rag_sync import sync_card
from knowledge_store import KnowledgeStore
from operational_metrics import build_project_metrics
from operations_view import build_operations_view
from project_policy import ProjectPolicyStore
from project_retention import ProjectRetentionPreview
from project_telemetry import ProjectTelemetryStore
from project_document_ingestion import ingest_project_document, list_project_documents, remove_project_document
from work_ledger import WorkLedger

app = FastAPI(title="Mini Agent Sandbox", version="0.1.0")
policy = CapabilityPolicy()
knowledge_store = KnowledgeStore()


class AuthorizationRequest(BaseModel):
    mode: str = "plan_only"
    capability: str


class ExecutionAuthorizationRequest(BaseModel):
    mode: str = "plan_only"
    workspace: str
    command: list[str]


class KnowledgeCardRequest(BaseModel):
    title: str
    problem: str
    decision: str
    rationale: str
    tags: list[str] = []
    affected_modules: list[str] = []


class EvidenceRequest(BaseModel):
    type: str
    reference: str
    description: str = ""


class TaskRequest(BaseModel):
    title: str
    description: str


class PlanRequest(BaseModel):
    objective: str


class PlanStepRequest(BaseModel):
    description: str
    files: list[str]
    risks: str
    validation: str
    rollback: str


class PatchRequest(BaseModel):
    diff: str


class PatchApprovalRequest(BaseModel):
    sha256: str


class ReviewRequest(BaseModel):
    decision: str
    notes: str = ""


class ValidationReportRequest(BaseModel):
    status: str
    report: dict


class RunRequest(BaseModel):
    status: str
    detail: str


class ProjectPolicyRequest(BaseModel):
    schema_version: int
    allowed_workspace_paths: list[str]
    validation_profiles: list[str]
    model_providers: list[str]
    budgets: dict[str, int]
    retention: dict[str, int]
    auto_apply_level: str


class ProjectDocumentRequest(BaseModel):
    source: str
    content: str
    content_type: str = "text/plain"
    confirmed: bool = False


@app.get("/security-contract")
def security_contract():
    return policy.manifest


@app.post("/authorize")
def authorize(request: AuthorizationRequest):
    return {"allowed": policy.is_allowed(request.mode, request.capability)}


@app.post("/execution/authorize")
def authorize_execution(request: ExecutionAuthorizationRequest):
    # This container is deliberately not a Docker control-plane client: it
    # receives no Docker socket or CLI. A trusted host-side worker may invoke
    # DockerSandboxExecutor after this authorization step.
    try:
        policy.require(request.mode, "build_test")
    except CapabilityDenied as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    return {
        "allowed": True,
        "reason": "Authorized for a separate Docker-only validation worker; API never executes commands.",
    }


@app.get("/projects")
def projects():
    return {"projects": list_projects()}


@app.get("/projects/{project_id}/snapshot")
def project_snapshot(project_id: str):
    try:
        return snapshot_summary(project_id)
    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/projects/{project_id}/search")
def project_search(project_id: str, q: str, limit: int = 20):
    try:
        return {"results": search_snapshot(project_id, q, limit)}
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@app.get("/projects/{project_id}/documents")
def project_documents(project_id: str):
    """Metadata-only inventory of explicitly ingested supplemental documents."""
    return _knowledge_error(lambda: {"documents": list_project_documents(project_id)})


@app.post("/projects/{project_id}/documents")
def ingest_document(project_id: str, request: ProjectDocumentRequest):
    """Explicit request-body ingestion; this endpoint never reads a disk path."""
    return _knowledge_error(
        lambda: ingest_project_document(project_id, **request.model_dump())
    )


@app.delete("/projects/{project_id}/documents/{source}")
def delete_document(project_id: str, source: str, confirmed: bool = False):
    return _knowledge_error(
        lambda: remove_project_document(project_id, source, confirmed=confirmed)
    )


def _knowledge_error(action):
    try:
        return action()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


def _knowledge_context(project_id: str | None):
    return ("project", project_id) if project_id else ("global", None)


@app.get("/knowledge/global")
def global_knowledge(q: str | None = None, status: str | None = None):
    return _knowledge_error(lambda: {"cards": knowledge_store.search("global", q) if q else knowledge_store.list("global", status=status)})


@app.get("/projects/{project_id}/knowledge")
def project_knowledge(project_id: str, q: str | None = None, status: str | None = None):
    return _knowledge_error(lambda: {"cards": knowledge_store.search("project", q, project_id) if q else knowledge_store.list("project", project_id, status)})


@app.post("/knowledge/global/cards")
def create_global_card(request: KnowledgeCardRequest):
    return _knowledge_error(lambda: knowledge_store.create(scope="global", **request.model_dump()))


@app.post("/projects/{project_id}/knowledge/cards")
def create_project_card(project_id: str, request: KnowledgeCardRequest):
    return _knowledge_error(lambda: knowledge_store.create(scope="project", project_id=project_id, **request.model_dump()))


@app.post("/knowledge/global/cards/{card_id}/evidence")
def add_global_evidence(card_id: str, request: EvidenceRequest):
    return _knowledge_error(lambda: knowledge_store.add_evidence("global", card_id, request.model_dump()))


@app.post("/projects/{project_id}/knowledge/cards/{card_id}/evidence")
def add_project_evidence(project_id: str, card_id: str, request: EvidenceRequest):
    return _knowledge_error(lambda: knowledge_store.add_evidence("project", card_id, request.model_dump(), project_id))


def _verify_and_sync(scope: str, card_id: str, project_id: str | None):
    card = knowledge_store.verify(scope, card_id, project_id)
    sync = sync_card(card_id, scope=scope, project_id=project_id, store=knowledge_store)
    return {"card": card, "sync": sync}


@app.post("/knowledge/global/cards/{card_id}/verify")
def verify_global(card_id: str):
    return _knowledge_error(lambda: _verify_and_sync("global", card_id, None))


@app.post("/projects/{project_id}/knowledge/cards/{card_id}/verify")
def verify_project(project_id: str, card_id: str):
    return _knowledge_error(lambda: _verify_and_sync("project", card_id, project_id))


def _retire_and_sync(scope: str, card_id: str, status: str, project_id: str | None):
    card = knowledge_store.set_status(scope, card_id, status, project_id)
    return {"card": card, "sync": sync_card(card_id, scope=scope, project_id=project_id, store=knowledge_store)}


@app.post("/knowledge/global/cards/{card_id}/{status}")
def retire_global(card_id: str, status: str):
    return _knowledge_error(lambda: _retire_and_sync("global", card_id, status, None))


@app.post("/projects/{project_id}/knowledge/cards/{card_id}/{status}")
def retire_project(project_id: str, card_id: str, status: str):
    return _knowledge_error(lambda: _retire_and_sync("project", card_id, status, project_id))


@app.get("/knowledge/global/cards/{card_id}/history")
def global_history(card_id: str):
    return _knowledge_error(lambda: {"versions": knowledge_store.versions("global", card_id), "audit": knowledge_store.audit("global", card_id)})


@app.get("/projects/{project_id}/knowledge/cards/{card_id}/history")
def project_history(project_id: str, card_id: str):
    return _knowledge_error(lambda: {"versions": knowledge_store.versions("project", card_id, project_id), "audit": knowledge_store.audit("project", card_id, project_id)})


def _ledger(project_id: str) -> WorkLedger:
    return WorkLedger(project_id)


def _project_policy() -> ProjectPolicyStore:
    return ProjectPolicyStore()


def _project_telemetry() -> ProjectTelemetryStore:
    return ProjectTelemetryStore()


def _project_retention() -> ProjectRetentionPreview:
    return ProjectRetentionPreview()


@app.get("/projects/{project_id}/operations")
def project_operations(project_id: str):
    """Read-only Phase 8 overview; it cannot invoke validation or Docker."""
    def view():
        ledger = _ledger(project_id)
        project = ledger.registry.get(project_id)
        cards = knowledge_store.list("project", project_id, status="verified")
        return build_operations_view(project, ledger.list_tasks(), cards)

    return _knowledge_error(view)


@app.get("/projects/{project_id}/policy")
def get_project_policy(project_id: str):
    return _knowledge_error(lambda: _project_policy().get(project_id))


@app.put("/projects/{project_id}/policy")
def update_project_policy(project_id: str, request: ProjectPolicyRequest):
    return _knowledge_error(lambda: _project_policy().update(project_id, request.model_dump()))


@app.get("/projects/{project_id}/policy/audit")
def project_policy_audit(project_id: str):
    return _knowledge_error(lambda: {"events": _project_policy().audit(project_id)})


@app.get("/projects/{project_id}/retention/preview")
def project_retention_preview(project_id: str):
    """Explicit read-only retention calculation; it never performs cleanup."""
    return _knowledge_error(lambda: _project_retention().preview(project_id))


@app.get("/projects/{project_id}/metrics")
def project_metrics(project_id: str):
    def metrics():
        ledger = _ledger(project_id)
        ledger.registry.get(project_id)
        return build_project_metrics(ledger.list_tasks(), knowledge_store.list("project", project_id)) | {
            "telemetry": _project_telemetry().summary(project_id),
        }

    return _knowledge_error(metrics)


@app.post("/projects/{project_id}/tasks")
def create_task(project_id: str, request: TaskRequest):
    return _knowledge_error(lambda: _ledger(project_id).create_task(**request.model_dump()))


@app.get("/projects/{project_id}/tasks")
def list_tasks(project_id: str, status: str | None = None):
    return _knowledge_error(lambda: {"tasks": _ledger(project_id).list_tasks(status)})


@app.get("/projects/{project_id}/tasks/{task_id}")
def inspect_task(project_id: str, task_id: str):
    return _knowledge_error(lambda: _ledger(project_id).task(task_id))


@app.post("/projects/{project_id}/tasks/{task_id}/plans")
def create_plan(project_id: str, task_id: str, request: PlanRequest):
    return _knowledge_error(lambda: _ledger(project_id).create_plan(task_id, request.objective))


@app.post("/projects/{project_id}/plans/{plan_id}/steps")
def add_plan_step(project_id: str, plan_id: str, request: PlanStepRequest):
    return _knowledge_error(lambda: _ledger(project_id).add_step(plan_id, **request.model_dump()))


@app.post("/projects/{project_id}/plans/{plan_id}/approve")
def approve_plan(project_id: str, plan_id: str):
    return _knowledge_error(lambda: _ledger(project_id).approve_plan(plan_id))


@app.post("/projects/{project_id}/steps/{step_id}/patches")
def record_patch(project_id: str, step_id: str, request: PatchRequest):
    return _knowledge_error(lambda: _ledger(project_id).record_patch(step_id, request.diff))


@app.post("/projects/{project_id}/patches/{patch_id}/reviews")
def record_review(project_id: str, patch_id: str, request: ReviewRequest):
    return _knowledge_error(lambda: _ledger(project_id).record_review(patch_id, request.decision, request.notes))


@app.post("/projects/{project_id}/patches/{patch_id}/approve")
def approve_patch(project_id: str, patch_id: str, request: PatchApprovalRequest):
    return _knowledge_error(lambda: _ledger(project_id).approve_patch(patch_id, request.sha256))


@app.post("/projects/{project_id}/patches/{patch_id}/validation-reports")
def record_validation(project_id: str, patch_id: str, request: ValidationReportRequest):
    return _knowledge_error(lambda: _ledger(project_id).record_validation(patch_id, request.status, request.report))


@app.post("/projects/{project_id}/tasks/{task_id}/runs")
def record_run(project_id: str, task_id: str, request: RunRequest):
    return _knowledge_error(lambda: _ledger(project_id).record_run(task_id, request.status, request.detail))
