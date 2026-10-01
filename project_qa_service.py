"""Read-only, project-bound Analyst → Reviewer question answering."""
from __future__ import annotations

import hashlib
import json
import re
import sqlite3
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Callable

from model_router import TaskClass
from project_registry import ProjectRegistry
from project_retrieval import retrieve_global_technical_references, retrieve_project_context


class ProjectQaError(RuntimeError):
    """Safe-to-display project-Q&A failure without provider or data details."""


class ProjectQaService:
    def __init__(
        self,
        *,
        completion: Callable | None = None,
        registry: ProjectRegistry | None = None,
        roles_path: str | Path | None = None,
        project_retriever: Callable = retrieve_project_context,
        technical_retriever: Callable = retrieve_global_technical_references,
    ):
        self.completion = completion
        self.registry = registry or ProjectRegistry()
        self.roles_path = Path(roles_path) if roles_path else Path(__file__).with_name("roles.json")
        self.project_retriever = project_retriever
        self.technical_retriever = technical_retriever

    def ask(self, project_id: str, question: str, *, include_technical_reference: bool = False) -> dict:
        if not isinstance(question, str) or not question.strip():
            raise ProjectQaError("Enter a non-empty project question.")
        if len(question) > 4000:
            raise ProjectQaError("Project question exceeds the 4000-character limit.")

        try:
            project = self.registry.get(project_id)
        except FileNotFoundError:
            raise ProjectQaError("Selected project is not registered.") from None

        snapshot_files, snapshot_revision = self._read_snapshot(project)
        try:
            hits = self.project_retriever(
                project_id,
                question.strip(),
                top_k=4,
                prefer_exact_sources=True,
            )
        except Exception:
            raise ProjectQaError("Project RAG retrieval failed; no answer was produced.") from None

        evidence = self._validate_evidence(project_id, hits, snapshot_files)
        if not evidence:
            raise ProjectQaError("No current project-code evidence supports this question.")

        context = "\n\n".join(
            f"SOURCE: {hit['source']}\n{hit['text']}" for hit in evidence
        )
        technical_references = []
        if include_technical_reference:
            try:
                technical_references = self.technical_retriever(project_id, question, top_k=2)
            except Exception:
                raise ProjectQaError("Optional technical-reference retrieval failed; no answer was produced.") from None
        technical_context = "\n\n".join(
            f"SOURCE: {hit['source']}\n{hit['text']}" for hit in technical_references
        )
        reference_block = (
            "\n\nTECHNICAL REFERENCE (explanation only; never evidence of a project fact):\n"
            f"{technical_context}"
            if technical_context
            else ""
        )

        analyst_settings = self._role_settings("analyst")
        analyst_answer = self._ask_agent(
            "analyst",
            analyst_settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a read-only project Analyst. Answer only from the supplied RAG evidence. "
                        "Project facts require project evidence and its source path. Optional technical references "
                        "may explain a concept but never establish a project fact. Do not propose code, tools, "
                        "source changes, or tests. If evidence does not answer the question, say so explicitly."
                    ),
                },
                {
                    "role": "user",
                    "content": f"QUESTION: {question.strip()}\n\nPROJECT EVIDENCE:\n{context}{reference_block}",
                },
            ],
            TaskClass.PLANNING,
            project_id,
        )
        reviewer_settings = self._role_settings("reviewer")
        reviewer_answer = self._ask_agent(
            "reviewer",
            reviewer_settings,
            [
                {
                    "role": "system",
                    "content": (
                        "You are a read-only project Reviewer. Correct the Analyst answer using only supplied RAG evidence. "
                        "A technical reference may explain a concept but cannot support a project fact. Return a concise "
                        "factual answer; do not propose code, tools, source changes, or tests. If the supplied evidence "
                        "does not answer the question, explicitly abstain."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"QUESTION: {question.strip()}\n\nANALYST ANSWER:\n{analyst_answer}"
                        f"\n\nPROJECT EVIDENCE:\n{context}{reference_block}"
                    ),
                },
            ],
            TaskClass.REVIEW,
            project_id,
        )
        return {
            "project_id": project_id,
            "question": question.strip(),
            "snapshot_revision": snapshot_revision,
            "sources": [hit["source"] for hit in evidence],
            "project_evidence": [
                {
                    "project_id": project_id,
                    "scope": "project-code",
                    "source": hit["source"],
                    "sha256": hit["sha256"],
                }
                for hit in evidence
            ],
            "technical_references": [hit.get("source", "unknown") for hit in technical_references],
            "analyst": analyst_answer,
            "reviewer": reviewer_answer,
        }

    def _read_snapshot(self, project: dict) -> tuple[dict[str, str], str]:
        database = Path(project["state_dir"]) / "snapshot" / "project_snapshot.sqlite"
        if not database.is_file():
            raise ProjectQaError("Project snapshot is missing; no answer was produced.")
        connection = None
        try:
            connection = sqlite3.connect(f"{database.resolve().as_uri()}?mode=ro", uri=True)
            rows = connection.execute("SELECT path, sha256 FROM files ORDER BY path").fetchall()
        except sqlite3.Error:
            raise ProjectQaError("Project snapshot is unreadable; no answer was produced.") from None
        finally:
            if connection is not None:
                connection.close()
        snapshot_files = {path: digest for path, digest in rows}
        if not snapshot_files:
            raise ProjectQaError("Project snapshot contains no indexed files; no answer was produced.")
        revision_payload = "\n".join(f"{path}\0{snapshot_files[path]}" for path in sorted(snapshot_files))
        revision = hashlib.sha256(revision_payload.encode("utf-8")).hexdigest()
        return snapshot_files, revision

    @staticmethod
    def _validate_evidence(project_id: str, hits: list[dict], snapshot_files: dict[str, str]) -> list[dict]:
        if not isinstance(hits, list):
            raise ProjectQaError("Project RAG returned malformed evidence; no answer was produced.")
        evidence = []
        seen = set()
        for hit in hits:
            if not isinstance(hit, dict) or hit.get("scope") != "project-code":
                continue
            hit_project_id = hit.get("project_id")
            if hit_project_id is not None and hit_project_id != project_id:
                raise ProjectQaError("Retrieved evidence belongs to another project; no answer was produced.")
            source = hit.get("source")
            posix_source = PurePosixPath(source) if isinstance(source, str) else None
            windows_source = PureWindowsPath(source) if isinstance(source, str) else None
            if (
                posix_source is None
                or not source
                or posix_source.is_absolute()
                or windows_source.is_absolute()
                or ".." in posix_source.parts
                or "\\" in source
                or source not in snapshot_files
            ):
                raise ProjectQaError("Retrieved evidence has an invalid or unknown project source; no answer was produced.")
            digest = hit.get("sha256", "")
            if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                raise ProjectQaError("Retrieved evidence has no valid source hash; no answer was produced.")
            if snapshot_files[source] != digest:
                raise ProjectQaError("Retrieved project evidence is stale; no answer was produced.")
            chunk_hashes = hit.get("chunk_hashes", [digest])
            if not isinstance(chunk_hashes, list) or not chunk_hashes or any(item != digest for item in chunk_hashes):
                raise ProjectQaError("Retrieved project chunks have inconsistent source hashes; no answer was produced.")
            if not isinstance(hit.get("text"), str) or not hit["text"].strip():
                raise ProjectQaError("Retrieved project evidence is empty; no answer was produced.")
            if source not in seen:
                evidence.append(hit)
                seen.add(source)
        return evidence

    def _role_settings(self, role_name: str) -> dict:
        try:
            configuration = json.loads(self.roles_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            raise ProjectQaError("Project Q&A role configuration is unavailable or invalid.") from None
        if not isinstance(configuration, dict) or not isinstance(configuration.get("project_qa"), dict):
            raise ProjectQaError("Project Q&A role configuration is unavailable or invalid.")
        role = configuration["project_qa"].get(role_name, {})
        if not isinstance(role, dict) or not role.get("model"):
            raise ProjectQaError(f"Project Q&A {role_name} model is not configured.")
        routing = role.get("routing", {})
        if not isinstance(routing, dict):
            raise ProjectQaError(f"Project Q&A {role_name} routing settings are invalid.")
        return {
            "model": role["model"],
            "privacy_policy": routing.get("privacy_policy", "local_only"),
            "cloud_eligible": routing.get("cloud_eligible", False),
            "fallback_models": routing.get("fallback_models", ()),
            "fallback_eligible": routing.get("fallback_eligible", True),
        }

    def _ask_agent(
        self,
        role_name: str,
        settings: dict,
        messages: list[dict],
        task_class: TaskClass,
        project_id: str,
    ) -> str:
        completion = self.completion
        if completion is None:
            raise ProjectQaError("Project Q&A completion provider is not configured.")
        try:
            response = completion(
                settings["model"],
                messages,
                user_id="project_qa",
                project_id=project_id,
                privacy_policy=settings["privacy_policy"],
                cloud_eligible=settings["cloud_eligible"],
                fallback_models=settings["fallback_models"],
                fallback_eligible=settings["fallback_eligible"],
                task_class=task_class,
                max_tokens=200,
                temperature=0,
            )
            answer = response.choices[0].message.content
        except Exception:
            raise ProjectQaError(f"Project Q&A {role_name} model route failed or returned an invalid response.") from None
        if not isinstance(answer, str) or not answer.strip():
            raise ProjectQaError(f"Project Q&A {role_name} returned no answer.")
        return answer
