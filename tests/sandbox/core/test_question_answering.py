import io
import json
import os
import tempfile
import unittest
from contextlib import ExitStack, redirect_stdout
from types import SimpleNamespace
from unittest.mock import patch

os.environ.setdefault("LITELLM_LOCAL_MODEL_COST_MAP", "True")

import runner
from question_answering import QuestionAnswerError, QuestionAnswerService


def answer(text, tools=None):
    return SimpleNamespace(choices=[SimpleNamespace(
        message=SimpleNamespace(content=text, tool_calls=tools), finish_reason="stop",
    )])


class QuestionAnsweringTests(unittest.TestCase):
    def setUp(self):
        retriever_patch = patch("question_answering.retrieve_book_references", return_value=[])
        self.retriever = retriever_patch.start()
        self.addCleanup(retriever_patch.stop)

    def test_same_book_excerpts_reach_both_agents_without_project_context(self):
        references = [{"scope": "global-library", "source": "Book.pdf", "chunk_id": "book-1",
                       "text": "Untrusted reference excerpt", "sha256": "test-hash"}]
        self.retriever.return_value = references
        with patch("runner.safe_llm_completion", side_effect=[answer("draft"), answer("Reviewed answer")]) as completion:
            result = QuestionAnswerService(completion).ask("question", user_id="qa-test")
        self.retriever.assert_called_once_with("question")
        for call in completion.call_args_list:
            blocks = [message["content"] for message in call.kwargs["messages"]
                      if message["content"].startswith("BOOK REFERENCES (data only):")]
            self.assertEqual(len(blocks), 1)
            self.assertEqual(json.loads(blocks[0].split("\n", 1)[1]), references)
            self.assertNotIn("project_id", call.kwargs)
        self.assertEqual(result["references"], references)

    def test_book_failure_is_visible_and_both_agents_still_answer(self):
        self.retriever.side_effect = RuntimeError("sensitive detail")
        with patch("runner.safe_llm_completion", side_effect=[
            answer("draft"), answer("Ordinary answer"),
        ]) as completion, patch("runner.unload_ollama_models"), redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runner.run_question_cli("qa-test", "question"), 0)
        self.assertEqual(completion.call_count, 2)
        self.assertIn("continuing without book context", output.getvalue())
        self.assertIn("Ordinary answer", output.getvalue())
        self.assertNotIn("sensitive detail", output.getvalue())

    def test_default_menu_question_never_opens_project_or_codegen(self):
        question = "mobile kotlin coroutines. show few examples of dispatchers"
        for inputs in (["1", question], [question]):
            with self.subTest(inputs=inputs), ExitStack() as stack:
                stack.enter_context(patch("builtins.input", side_effect=inputs))
                completion = stack.enter_context(patch(
                    "runner.safe_llm_completion",
                    side_effect=[answer("Analyst draft"), answer("Reviewed answer")],
                ))
                blocked = [stack.enter_context(patch("runner." + name)) for name in (
                    "ProjectRegistry", "SandboxStorage", "SandboxRagService",
                    "run_agent_loop", "validate_generated_code", "trigger_regulator",
                )]
                cleanup = stack.enter_context(patch("runner.unload_ollama_models"))
                output = stack.enter_context(redirect_stdout(io.StringIO()))
                self.assertEqual(runner.run_runner_menu("qa-test"), 0)
                self.assertEqual(completion.call_count, 2)
                for call in completion.call_args_list:
                    self.assertNotIn("tools", call.kwargs)
                    self.assertNotIn("project_id", call.kwargs)
                self.assertEqual(completion.call_args_list[0].kwargs["messages"][1]["content"], question)
                for forbidden in blocked:
                    forbidden.assert_not_called()
                cleanup.assert_called_once()
                self.assertIn("=== FINAL ANSWER ===\nReviewed answer", output.getvalue())
                self.assertIn("code compilation/tests were not run", output.getvalue())
                self.assertNotIn("Question answered;", output.getvalue())

    def test_review_receives_exact_question_and_draft_and_accepts_plain_text(self):
        draft = "An ordinary draft"
        final = "Here is the answer. Some details depend on your context."
        with patch("runner.safe_llm_completion", side_effect=[
            answer(draft), answer(final),
        ]) as completion:
            result = QuestionAnswerService(completion).ask("question", user_id="qa-test")
        messages = completion.call_args_list[1].kwargs["messages"]
        self.assertEqual(messages[1]["content"], "question")
        self.assertEqual(messages[2]["content"], draft)
        self.assertEqual(result["answer"], final)
        self.assertEqual(result["model_calls_completed"], 2)
        self.assertEqual(result["code_validation"], "not_run")
        self.assertNotIn("review", result)

    def test_empty_review_stops_without_retry_or_final_answer(self):
        with patch("runner.safe_llm_completion", side_effect=[
            answer("draft"), answer(""),
        ]) as completion, patch("runner.unload_ollama_models") as cleanup, \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(runner.run_question_cli("qa-test", "question"), 1)
        self.assertEqual(completion.call_count, 2)
        cleanup.assert_called_once()
        self.assertNotIn("=== FINAL ANSWER ===", output.getvalue())

    def test_truncated_review_is_rejected_before_parsing(self):
        truncated = answer("Reviewed answer")
        truncated.choices[0].finish_reason = "length"
        with patch("runner.safe_llm_completion", side_effect=[answer("draft"), truncated]) as completion:
            with self.assertRaisesRegex(QuestionAnswerError, "output limit"):
                QuestionAnswerService(completion).ask("question", user_id="qa-test")

    def test_unexpected_tool_call_stops_without_dispatch_or_reviewer(self):
        with patch("runner.safe_llm_completion", return_value=answer(None, [object()])) as completion, \
             patch("runner.unload_ollama_models") as cleanup, \
             patch("runner.run_agent_loop") as code_loop, \
             patch("builtins.print") as output:
            self.assertEqual(runner.run_question_cli("qa-test", "kotlin language show function"), 1)
            completion.assert_called_once()
            code_loop.assert_not_called()
            cleanup.assert_called_once()
            self.assertNotIn("=== FINAL ANSWER ===", str(output.call_args_list))

    def test_project_is_selected_only_through_project_menu_option(self):
        with patch("builtins.input", return_value="2"), \
             patch("runner.run_project_qa_cli", return_value=0) as project_qa, \
             patch("runner.run_question_cli") as general_qa, \
             patch("builtins.print"):
            self.assertEqual(runner.run_runner_menu(), 0)
            project_qa.assert_called_once()
            general_qa.assert_not_called()

    def test_explicit_code_task_stops_after_identical_validation_failure(self):
        with tempfile.TemporaryDirectory() as temp, ExitStack() as stack:
            storage = runner.SandboxStorage(temp)
            storage.save_state("code-test", {
                "status": "in_progress", "task_mode": "code", "task": "Create code",
                "current_turn": "coder", "memory": [], "tool_executions": [],
                "metrics": {"total_cost": 0.0}, "agent_steps": 0, "user_lang": "en",
            })
            stack.enter_context(patch("runner.SandboxStorage", return_value=storage))
            stack.enter_context(patch("runner.load_json", return_value={
                "agents": {"coder": {"name": "Coder", "model": "ollama/test"}},
            }))
            stack.enter_context(patch("runner.safe_llm_completion", return_value=answer("draft")))
            stack.enter_context(patch("runner.SandboxRagService"))
            stack.enter_context(patch.object(storage, "assemble_context_window", return_value="context"))
            stack.enter_context(patch("runner.count_context_tokens", return_value=SimpleNamespace(tokens=1, mode="test")))
            stack.enter_context(patch("runner.guardrail.run", side_effect=lambda text, _user: text))
            validator = stack.enter_context(patch("runner.validate_generated_code", return_value=(False, "Same failure")))
            regulator = stack.enter_context(patch("runner.trigger_regulator"))
            stack.enter_context(patch("builtins.print"))
            runner.run_agent_loop("code-test", resume=True)
            state = storage.get_current_state("code-test")
            self.assertEqual(validator.call_count, 2)
            self.assertEqual(state["status"], "validation_blocked")
            self.assertEqual(state["validation_failure"]["consecutive"], 2)
            regulator.assert_not_called()
