import json
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import runner
from tests.sandbox.core.test_documentation_policy import CONTRACT, DOC, HITS, good_review


def response(content=None, calls=None):
    message = SimpleNamespace(content=content, tool_calls=calls)
    message.model_dump = lambda: {'role': 'assistant', 'content': content}
    return SimpleNamespace(choices=[SimpleNamespace(message=message)])


def write_call(path, content):
    return SimpleNamespace(id=path, function=SimpleNamespace(
        name='create_file', arguments=json.dumps({'filepath': path, 'content': content})))


class DocumentationTransitionTests(unittest.TestCase):
    def test_invalid_documentation_write_preserves_file_and_step_before_model_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            storage.save_state('docs', {
                'status': 'in_progress', 'task_mode': 'documentation',
                'task': 'Create architecture_summary.md', 'documentation_contract': CONTRACT,
                'project_id': 'demo', 'current_turn': 'coder', 'memory': [],
                'tool_executions': [], 'metrics': {}, 'agent_steps': 4,
            })
            invalid = '# Overview\nToo short\n\n## Components\nToo short\n'
            with patch('runner.SandboxStorage', return_value=storage), \
                 patch('runner.load_json', return_value={'agents': {'coder': {'name': 'coder', 'model': 'ollama/test'}}}), \
                 patch('runner.safe_llm_completion', side_effect=[response(calls=[write_call('architecture_summary.md', invalid)]), ConnectionError('stop after rejected dispatch')]), \
                 patch('runner.retrieve_project_context', return_value=HITS), \
                 patch('runner.format_retrieval_context', return_value='evidence'), \
                 patch('runner.trigger_regulator'), \
                 patch('builtins.print'):
                runner.run_agent_loop('docs', resume=True)
            state = storage.get_current_state('docs')
            self.assertEqual(state['agent_steps'], 4)
            self.assertFalse((Path(temp) / 'docs' / 'architecture_summary.md').exists())

    def test_unavailable_local_model_preserves_interrupted_state(self):
        self._assert_stopped_state(0, 0.0, failure=True)

    def test_step_limit_does_not_complete_task(self):
        self._assert_stopped_state(runner.MAX_AGENT_STEPS, 0.0)

    def test_budget_limit_does_not_complete_task(self):
        self._assert_stopped_state(0, 0.06)

    def _assert_stopped_state(self, steps, cost, failure=False):
        from model_router import ModelRouter
        calls = []
        class FailingAdapter:
            def complete(self, model, messages, **kwargs):
                calls.append(model)
                raise ConnectionError('local model unavailable')
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            storage.save_state('docs', {
                'status': 'in_progress', 'task_mode': 'documentation',
                'task': 'Create architecture_summary.md', 'documentation_contract': CONTRACT, 'current_turn': 'coder',
                'project_id': 'demo', 'memory': [],
                'metrics': {'total_cost': cost}, 'agent_steps': steps,
            })
            roles = {'agents': {'coder': {'name': 'coder', 'model': 'ollama/test'}}}
            with patch('runner.SandboxStorage', return_value=storage), \
                 patch('runner.load_json', return_value=roles), \
                 patch('runner.MODEL_ROUTER', ModelRouter(FailingAdapter(), offline_mode=True, sleeper=lambda _: None)), \
                 patch('runner.project_model_policy', return_value={'model_providers': ['ollama'], 'budgets': {}}), \
                 patch('runner.guardrail.run', side_effect=lambda text, user: text), \
                 patch('runner.get_user_vault'), \
                 patch('runner.log_prediction_telemetry'), \
                 patch('runner.retrieve_project_context', return_value=HITS), \
                 patch('runner.trigger_regulator'), patch('builtins.print'):
                runner.run_agent_loop('docs', resume=True)
            state = storage.get_current_state('docs')
            self.assertEqual(state['status'], 'in_progress')
            self.assertEqual(state['current_turn'], 'coder')
            self.assertFalse(any('approval' in key or 'validation' in key for key in state))
            self.assertEqual(bool(calls), failure)
            self.assertTrue(all(model.startswith('ollama/') for model in calls))

    def test_first_write_advances_and_reviewer_cannot_write(self):
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            storage.save_state('docs', {
                'status': 'in_progress', 'task_mode': 'documentation',
                'task': 'Create architecture_summary.md', 'documentation_contract': CONTRACT, 'user_lang': 'en',
                'project_id': 'demo', 'current_turn': 'coder',
                'memory': [], 'metrics': {}, 'agent_steps': 4,
            })
            turns = []
            def complete(*args, **kwargs):
                tools = kwargs.get('tools')
                if not tools:
                    return response('summary')
                turns.append({t['function']['name'] for t in tools})
                if len(turns) == 1:
                    return response(calls=[write_call('architecture_summary.md', DOC),
                                           write_call('extra.md', 'unwanted')])
                if len(turns) == 2:
                    self.assertIn('# Architecture summary', kwargs['messages'][-1]['content'])
                    return response(calls=[write_call('architecture_summary.md', 'overwrite')])
                return response(json.dumps(good_review()))
            roles = {'agents': {name: {'name': name, 'model': 'ollama/test'}
                                for name in ('coder', 'reviewer')}}
            with patch('runner.SandboxStorage', return_value=storage), \
                 patch('runner.load_json', return_value=roles), \
                 patch('runner.safe_llm_completion', side_effect=complete), \
                 patch('runner.retrieve_project_context', return_value=HITS), \
                 patch('runner.format_retrieval_context', return_value='evidence'), \
                 patch('runner.trigger_regulator'), \
                 patch('runner.reverse_language_gateway', side_effect=lambda text, lang: text), \
                 patch('builtins.print'):
                runner.run_agent_loop('docs', resume=True)
            state = storage.get_current_state('docs')
            self.assertEqual(state['status'], 'completed')
            self.assertEqual(state['agent_steps'], 6)
            self.assertEqual(len(turns), 3)
            self.assertNotIn('create_file', turns[1])
            self.assertNotIn('create_file', turns[2])
            self.assertEqual((Path(temp)/'docs/architecture_summary.md').read_text(), DOC)
            self.assertFalse((Path(temp)/'docs/extra.md').exists())
            self.assertFalse((Path(temp)/'docs/project_facts.json').exists())
            self.assertEqual([m['role'] for m in state['memory']], ['coder', 'reviewer'])
