"""Opt-in end-to-end offline check; uses only the already-running local Ollama."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import chromadb
from chromadb.api.types import Documents, EmbeddingFunction, Embeddings

from model_router import (
    EmbeddingRequest,
    LiteLLMAdapter,
    ModelRequest,
    ModelRouter,
    PrivacyPolicy,
    TaskClass,
)
from project_registry import ProjectRegistry
from work_ledger import WorkLedger


class RecordingLiteLLMAdapter(LiteLLMAdapter):
    def __init__(self):
        super().__init__()
        self.completion_models: list[str] = []
        self.embedding_models: list[str] = []

    def complete(self, model, messages, **kwargs):
        self.completion_models.append(model)
        return super().complete(model, messages, **kwargs)

    def embed(self, model, inputs):
        self.embedding_models.append(model)
        return super().embed(model, inputs)


class RouterEmbeddingFunction(EmbeddingFunction):
    def __init__(self, router: ModelRouter):
        self.router = router

    def __call__(self, input: Documents) -> Embeddings:
        result = self.router.embed(EmbeddingRequest(inputs=list(input)))
        data = result["data"] if isinstance(result, dict) else result.data
        return [item["embedding"] for item in data]

    def name(self) -> str:
        return "offline-model-router-embedding"

    def get_config(self) -> dict:
        return {}


@unittest.skipUnless(
    os.getenv("MINI_AGENT_RUN_OFFLINE_INTEGRATION") == "1",
    "set MINI_AGENT_RUN_OFFLINE_INTEGRATION=1 to call the installed local Ollama models",
)
class OfflineLocalIntegrationTests(unittest.TestCase):
    def test_persisted_task_resumes_with_local_chroma_and_ollama_only(self):
        adapter = RecordingLiteLLMAdapter()
        router = ModelRouter(adapter, local_fallback="ollama/qwen2.5:7b", offline_mode=True)

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source = root / "source"
            source.mkdir()
            registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
            project = registry.register(source, "Offline fixture")

            ledger = WorkLedger(project["id"], registry)
            task = ledger.create_task(
                "Repair navigation route",
                "Continue interrupted task: route parameter is not preserved on back navigation.",
            )
            plan = ledger.create_plan(task["id"], "Inspect the existing route and propose a minimal fix")
            ledger.add_step(
                plan["id"], description="Inspect route handling", files=["app/Nav.kt"],
                risks="navigation regression", validation="Docker unit test", rollback="revert the diff",
            )
            ledger.approve_plan(plan["id"])
            ledger.record_run(task["id"], "running", "Interrupted before local continuation")

            restored = WorkLedger(project["id"], registry).task(task["id"])
            self.assertEqual(restored["plans"][0]["objective"], plan["objective"])
            self.assertEqual(restored["runs"][-1]["status"], "running")

            chroma = chromadb.EphemeralClient()
            collection = chroma.get_or_create_collection(
                name="offline_resume_fixture",
                embedding_function=RouterEmbeddingFunction(router),
            )
            collection.add(
                ids=["nav-source-1"],
                documents=["Navigation route parameters must be restored when returning from a detail screen."],
                metadatas=[{"source": "app/Nav.kt", "scope": "project-code"}],
            )
            retrieved = collection.query(
                query_texts=[restored["description"]], n_results=1
            )["documents"][0][0]
            self.assertIn("route parameters", retrieved)

            result = router.complete(ModelRequest(
                model="gemini/gemini-2.5-flash",
                messages=[
                    {"role": "system", "content": "Continue the saved engineering task. Answer with a short next-step summary."},
                    {"role": "user", "content": f"Task: {restored['description']}\nPlan: {restored['plans'][0]['objective']}\nRetrieved local evidence: {retrieved}"},
                ],
                task_class=TaskClass.PLANNING,
                privacy_policy=PrivacyPolicy.CLOUD_ALLOWED,
                cloud_eligible=True,
                budget_usd=1.0,
                max_retries=0,
                extra_kwargs={"max_tokens": 120, "temperature": 0.1},
            ))

            answer = result.response.choices[0].message.content
            self.assertTrue(answer and answer.strip())
            self.assertEqual(result.provider, "ollama")
            self.assertTrue(adapter.completion_models)
            self.assertTrue(all(model.startswith("ollama/") for model in adapter.completion_models))
            self.assertGreaterEqual(len(adapter.embedding_models), 2)
            self.assertTrue(all(model == "ollama/nomic-embed-text" for model in adapter.embedding_models))

            still_unvalidated = WorkLedger(project["id"], registry).task(task["id"])
            self.assertEqual(still_unvalidated["status"], "approved")


if __name__ == "__main__":
    unittest.main()
