import unittest
import json
import io
import sqlite3
import tempfile
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import project_qa
import runner
from ollama_runtime import unload_ollama_models
from project_qa_service import ProjectQaError, ProjectQaService
from project_registry import ProjectRegistry
from project_retrieval import AmbiguousProjectFile


class ProjectQaTests(unittest.TestCase):
    def test_truncated_agent_output_stops_without_retry_or_final_answer(self):
        for truncated_role, expected_calls in (("analyst", 1), ("reviewer", 2)):
            with self.subTest(role=truncated_role), tempfile.TemporaryDirectory() as temporary:
                registry, project, roles_path, digest = self.create_project_fixture(Path(temporary))
                responses = [SimpleNamespace(choices=[SimpleNamespace(
                    message=SimpleNamespace(content="partial code"), finish_reason=reason,
                )]) for reason in (["length"] if expected_calls == 1 else ["stop", "length"])]
                completion = Mock(side_effect=responses)
                service = ProjectQaService(
                    completion=completion, registry=registry, roles_path=roles_path,
                    project_retriever=lambda *args, **kwargs: [{
                        "scope": "project-code", "source": "app/MainActivity.kt",
                        "sha256": digest, "text": "fun main() {}",
                    }],
                )
                with self.assertRaisesRegex(ProjectQaError, truncated_role + " response reached the output limit"):
                    service.ask(project["id"], "Show the file and explain it")
                self.assertEqual(completion.call_count, expected_calls)

    def test_ambiguous_filename_is_reported_before_any_model_call(self):
        with tempfile.TemporaryDirectory() as temporary:
            registry, project, roles_path, _ = self.create_project_fixture(Path(temporary))
            completion = Mock()
            service = ProjectQaService(
                completion=completion, registry=registry, roles_path=roles_path,
                project_retriever=Mock(side_effect=AmbiguousProjectFile(
                    "Model.kt matches one/Model.kt, two/Model.kt. Specify the project-relative path."
                )),
            )
            with self.assertRaisesRegex(ProjectQaError, "Specify the project-relative path"):
                service.ask(project["id"], "Explain Model.kt")
            completion.assert_not_called()

    @staticmethod
    def create_project_fixture(root):
        source_root = root / "source"
        source_root.mkdir()
        registry = ProjectRegistry(root / "registry.sqlite", root / "projects")
        project = registry.register(source_root, "Demo")
        snapshot = Path(project["state_dir"]) / "snapshot" / "project_snapshot.sqlite"
        connection = sqlite3.connect(snapshot)
        connection.execute("CREATE TABLE files (path TEXT PRIMARY KEY, sha256 TEXT NOT NULL)")
        digest = "a" * 64
        connection.execute("INSERT INTO files VALUES (?, ?)", ("app/MainActivity.kt", digest))
        connection.commit()
        connection.close()
        roles_path = root / "roles.json"
        roles_path.write_text(json.dumps({"project_qa": {
            "analyst": {"model": "ollama/analyst", "routing": {"privacy_policy": "local_only"}},
            "reviewer": {"model": "ollama/reviewer", "routing": {"privacy_policy": "local_only"}},
        }}), encoding="utf-8")
        return registry, project, roles_path, digest

    def test_runner_project_selector_binds_question_to_selected_registered_project(self):
        projects = [
            {"id": "alpha--11111111", "display_name": "Alpha", "source_path": "C:/alpha", "state_dir": "C:/state/alpha"},
            {"id": "gta-cheats--cc0fe5de", "display_name": "GTA Cheats", "source_path": "C:/gta", "state_dir": "C:/state/gta"},
        ]
        expected = {"project_id": "gta-cheats--cc0fe5de", "analyst": "answer"}
        with patch("runner.ProjectRegistry") as registry:
            registry.return_value.list.return_value = projects
            with patch("builtins.input", side_effect=["2", "What is the manifest target API?"]):
                with patch("runner.ask_registered_project", return_value=expected) as ask:
                    output = io.StringIO()
                    with redirect_stdout(output):
                        result = runner.run_project_qa_interactive()

        self.assertEqual(result, expected)
        ask.assert_called_once_with("gta-cheats--cc0fe5de", "What is the manifest target API?")
        self.assertIn("2. GTA Cheats (gta-cheats--cc0fe5de)", output.getvalue())

    def test_runner_project_selector_rejects_unregistered_selection(self):
        with patch("runner.ProjectRegistry") as registry:
            registry.return_value.list.return_value = [
                {"id": "alpha--11111111", "display_name": "Alpha", "source_path": "C:/alpha", "state_dir": "C:/state/alpha"},
            ]
            with patch("builtins.input", return_value="2"):
                with patch("runner.ask_registered_project") as ask:
                    with self.assertRaisesRegex(ProjectQaError, "No matching registered project"):
                        runner.run_project_qa_interactive()

        ask.assert_not_called()

    def test_project_menu_displays_stored_remote_metadata_without_claiming_readiness(self):
        state = Path("C:/state/demo")
        project = {
            "id": "demo--12345678",
            "display_name": "Demo",
            "description": "Stored project description",
            "source_kind": "git",
            "source_uri": "https://example.invalid/demo.git",
            "source_path": "C:/checkout/demo",
            "state_dir": str(state),
        }
        output = io.StringIO()
        with patch("runner.ProjectRegistry") as registry:
            registry.return_value.list.return_value = [project]
            with patch("builtins.input", side_effect=[project["id"], ""]):
                with redirect_stdout(output):
                    result = runner.run_project_qa_interactive()

        self.assertIsNone(result)
        self.assertIn("Stored project description", output.getvalue())
        self.assertIn("https://example.invalid/demo.git", output.getvalue())
        self.assertIn("Checkout: C:/checkout/demo", output.getvalue())
        self.assertIn("Project RAG:", output.getvalue())
        self.assertIn("not initialized or incomplete", output.getvalue())

    def test_runner_and_compatibility_api_delegate_to_the_same_service(self):
        expected = {"reviewer": "answer"}
        with patch("runner.ProjectQaService") as service:
            service.return_value.ask.return_value = expected
            result = runner.ask_registered_project("demo--12345678", "question")

        self.assertEqual(result, expected)
        service.assert_called_once_with(completion=runner.safe_llm_completion)
        service.return_value.ask.assert_called_once_with("demo--12345678", "question", include_technical_reference=False)

        with patch("runner.safe_llm_completion") as completion, patch("project_qa.ProjectQaService") as service:
            service.return_value.ask.return_value = expected
            result = project_qa.ask_project("demo--12345678", "question")

        self.assertEqual(result, expected)
        service.assert_called_once_with(completion=completion)
        service.return_value.ask.assert_called_once_with(
            "demo--12345678", "question", include_technical_reference=False,
        )

    def test_runner_project_qa_cli_unloads_models_after_query(self):
        expected = {
            "analyst": "draft",
            "reviewer": "answer",
            "snapshot_revision": "c" * 64,
            "sources": ["app/src/main/AndroidManifest.xml"],
            "technical_references": [],
        }
        with patch("runner.run_project_qa_interactive", return_value=expected):
            with patch("runner.unload_ollama_models") as unload:
                self.assertEqual(runner.run_project_qa_cli(), 0)

        unload.assert_called_once_with(announce=False)

    def test_unload_uses_ollama_model_field_and_unloads_completion_and_embedding(self):
        with patch("ollama_runtime.urllib.request.urlopen") as urlopen:
            unload_ollama_models(announce=False)

        payloads = [json.loads(call.args[0].data.decode("utf-8")) for call in urlopen.call_args_list]
        self.assertEqual(payloads, [
            {"model": "nomic-embed-text:latest", "keep_alive": 0},
            {"model": "qwen2.5:14b", "keep_alive": 0},
        ])

    def test_unload_tracks_configured_local_and_fallback_models_only(self):
        with tempfile.TemporaryDirectory() as temporary:
            roles_path = Path(temporary) / "roles.json"
            roles_path.write_text(json.dumps({
                "agents": {
                    "coder": {"model": "ollama/qwen3.5:9b"},
                    "analyst": {"model": "hosted/analyst", "routing": {
                        "fallback_models": ["ollama/local:7b", "hosted/backup"],
                    }},
                },
                "project_qa": {"reviewer": {"model": "ollama/qwen3.5:9b"}},
            }), encoding="utf-8")
            with patch("ollama_runtime.ROLES_FILE", roles_path), patch(
                "ollama_runtime.urllib.request.urlopen"
            ) as urlopen:
                unload_ollama_models(announce=False)

        payloads = [json.loads(call.args[0].data.decode("utf-8")) for call in urlopen.call_args_list]
        self.assertEqual(payloads, [
            {"model": "local:7b", "keep_alive": 0},
            {"model": "nomic-embed-text:latest", "keep_alive": 0},
            {"model": "qwen3.5:9b", "keep_alive": 0},
        ])

    def test_runner_project_qa_cli_prints_readable_answer_and_sources(self):
        expected = {
            "analyst": "Analyst draft.",
            "reviewer": "targetApi is 31.",
            "snapshot_revision": "c" * 64,
            "sources": ["app/src/main/AndroidManifest.xml"],
            "technical_references": [],
        }
        output = io.StringIO()
        with patch("runner.run_project_qa_interactive", return_value=expected):
            with patch("runner.unload_ollama_models"):
                with redirect_stdout(output):
                    code = runner.run_project_qa_cli()

        self.assertEqual(code, 0)
        self.assertIn("Analyst answer:\nAnalyst draft.", output.getvalue())
        self.assertIn("Answer:\ntargetApi is 31.", output.getvalue())
        self.assertIn("- app/src/main/AndroidManifest.xml", output.getvalue())

    def test_project_qa_rejects_an_empty_analyst_answer(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, digest = self.create_project_fixture(root)
            evidence = [{
                "scope": "project-code", "source": "app/MainActivity.kt", "sha256": digest,
                "text": "fun main() {}",
            }]
            def completion(*args, **kwargs):
                return SimpleNamespace(
                    choices=[SimpleNamespace(message=SimpleNamespace(content="  "))]
                )
            service = ProjectQaService(
                completion=completion,
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: evidence,
            )
            with self.assertRaisesRegex(ProjectQaError, "analyst returned no answer"):
                service.ask(project["id"], "Where is main?")

    def test_project_qa_uses_models_configured_for_analyst_and_reviewer_roles(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, digest = self.create_project_fixture(root)
            role_config = {"project_qa": {
                "analyst": {"model": "provider/analyst", "routing": {
                    "privacy_policy": "cloud_allowed", "cloud_eligible": True,
                    "fallback_models": ["ollama/local"],
                }},
                "reviewer": {"model": "ollama/reviewer"},
            }}
            roles_path.write_text(json.dumps(role_config), encoding="utf-8")
            evidence = [{
                "scope": "project-code", "source": "app/MainActivity.kt", "sha256": digest,
                "text": "fun main() {}",
            }]
            calls = []

            def completion(*args, **kwargs):
                calls.append((args, kwargs))
                return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Grounded."))])

            service = ProjectQaService(
                completion=completion,
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: evidence,
            )
            service.ask(project["id"], "Where is main?")

        self.assertEqual(calls[0][0][0], "provider/analyst")
        self.assertEqual(calls[0][1]["privacy_policy"], "cloud_allowed")
        self.assertTrue(calls[0][1]["cloud_eligible"])
        self.assertEqual(calls[0][1]["fallback_models"], ["ollama/local"])
        self.assertEqual(calls[1][0][0], "ollama/reviewer")
        self.assertEqual([call[1]["max_tokens"] for call in calls], [2048, 2048])

    def test_project_qa_rejects_stale_snapshot_evidence_before_model_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, _ = self.create_project_fixture(root)
            service = ProjectQaService(
                completion=lambda *args, **kwargs: self.fail("stale evidence must not reach a model"),
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: [{
                    "scope": "project-code", "source": "app/MainActivity.kt", "sha256": "b" * 64,
                    "text": "stale text",
                }],
            )

            with self.assertRaisesRegex(ProjectQaError, "stale"):
                service.ask(project["id"], "Where is main?")

    def test_project_qa_abstains_when_selected_project_has_no_retrieved_evidence(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, _ = self.create_project_fixture(root)
            service = ProjectQaService(
                completion=lambda *args, **kwargs: self.fail("missing evidence must not reach a model"),
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: [],
            )

            with self.assertRaisesRegex(ProjectQaError, "No current project-code evidence"):
                service.ask(project["id"], "Unanswerable question")

    def test_project_qa_rejects_evidence_labelled_for_another_project(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, digest = self.create_project_fixture(root)
            service = ProjectQaService(
                completion=lambda *args, **kwargs: self.fail("cross-project evidence must not reach a model"),
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: [{
                    "project_id": "other-project--12345678", "scope": "project-code",
                    "source": "app/MainActivity.kt", "sha256": digest, "text": "foreign text",
                }],
            )

            with self.assertRaisesRegex(ProjectQaError, "another project"):
                service.ask(project["id"], "Where is main?")

    def test_project_qa_rejects_mixed_hash_chunks_before_model_calls(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, digest = self.create_project_fixture(root)
            service = ProjectQaService(
                completion=lambda *args, **kwargs: self.fail("mixed hashes must not reach a model"),
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: [{
                    "scope": "project-code", "source": "app/MainActivity.kt", "sha256": digest,
                    "chunk_hashes": [digest, "b" * 64], "text": "mixed-version text",
                }],
            )

            with self.assertRaisesRegex(ProjectQaError, "inconsistent source hashes"):
                service.ask(project["id"], "Where is main?")

    def test_cli_unloads_local_models_after_success_without_polluting_json(self):
        output = io.StringIO()
        with patch("sys.argv", ["project_qa.py", "demo--123", "question"]):
            with patch("project_qa.ask_project", return_value={"answer": "ok"}):
                with patch("project_qa.unload_ollama_models") as unload:
                    with redirect_stdout(output):
                        project_qa.main()

        unload.assert_called_once_with(announce=False)
        self.assertEqual(json.loads(output.getvalue()), {"answer": "ok"})

    def test_cli_unloads_local_models_after_failure(self):
        with patch("sys.argv", ["project_qa.py", "demo--123", "question"]):
            with patch("project_qa.ask_project", side_effect=RuntimeError("failed")):
                with patch("project_qa.unload_ollama_models") as unload:
                    with self.assertRaises(SystemExit) as error:
                        project_qa.main()
                    self.assertEqual(error.exception.code, 1)

        unload.assert_called_once_with(announce=False)

    def test_technical_reference_is_separate_from_project_evidence(self):
        completions = []

        def complete(*args, **kwargs):
            completions.append((args[1], kwargs))
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Grounded answer."))])

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            registry, project, roles_path, digest = self.create_project_fixture(root)
            service = ProjectQaService(
                completion=complete,
                registry=registry,
                roles_path=roles_path,
                project_retriever=lambda *args, **kwargs: [{
                    "scope": "project-code", "source": "app/MainActivity.kt", "sha256": digest,
                    "text": "fun main() {}",
                }],
                technical_retriever=lambda *args, **kwargs: [{
                    "scope": "global-library", "source": "Compose.pdf", "text": "Navigation explanation",
                }],
            )
            answer = service.ask(project["id"], "Where is navigation created?", include_technical_reference=True)

        self.assertEqual(answer["sources"], ["app/MainActivity.kt"])
        self.assertEqual(answer["project_evidence"], [{
            "project_id": project["id"], "scope": "project-code",
            "source": "app/MainActivity.kt", "sha256": "a" * 64,
        }])
        self.assertEqual(answer["technical_references"], ["Compose.pdf"])
        self.assertIn("PROJECT EVIDENCE:\nSOURCE: app/MainActivity.kt", completions[0][0][1]["content"])
        self.assertIn("TECHNICAL REFERENCE (explanation only; never evidence of a project fact):", completions[0][0][1]["content"])
        self.assertIn("Project facts require project evidence", completions[0][0][0]["content"])
        reviewer_prompt = completions[1][0][0]["content"]
        self.assertIn("cover every part", reviewer_prompt)
        self.assertIn("trace relevant method calls and state changes", reviewer_prompt)
        self.assertIn("remove timing, ordering, or guarantee claims", reviewer_prompt)
        self.assertIn("without evaluating or praising the Analyst", reviewer_prompt)
        self.assertEqual([item[1]["project_id"] for item in completions], [project["id"], project["id"]])


if __name__ == "__main__":
    unittest.main()
