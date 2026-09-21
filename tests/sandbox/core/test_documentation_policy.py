import copy
import json
import tempfile
import unittest
from unittest.mock import patch

import runner
from documentation_policy import (documentation_contract, project_evidence, check_artifact, check_review)

CONTRACT = {'artifact': 'architecture_summary.md',
            'sections': ['Overview', 'Components', 'Relationships', 'Limitations']}
HITS = [{'scope': 'project-code', 'trust': 'project code', 'source': 'app/Main.kt', 'module': ':app',
         'text': 'class MainActivity : Activity() { val repository = Repository() }'},
        {'scope': 'project-code', 'trust': 'project code', 'source': 'data/Repository.kt', 'module': ':data',
         'text': 'class Repository { fun load() = service.fetch() }'}]
DOC = '''# Architecture summary
## Overview
MainActivity is an Activity. Source: `app/Main.kt`.
## Components
Repository loads data by calling service.fetch(). Source: `data/Repository.kt`.
## Relationships
MainActivity constructs a Repository. Source: `app/Main.kt`.
## Limitations
The retrieved excerpts do not establish navigation behavior or thread scheduling.
'''


def good_review():
    return {'decision': 'APPROVE', 'reason': 'The requested components and relationships are supported by retrieved code; missing navigation detail is explicitly disclosed.'}



class DocumentationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.storage = runner.SandboxStorage(self.temp.name)
        self.path = self.storage.resolve_workspace_path('docs', CONTRACT['artifact'])
        self.path.write_text(DOC, encoding='utf-8')
        self.evidence = project_evidence('demo', HITS)

    def check(self):
        return check_artifact(self.storage, 'docs', CONTRACT, self.evidence)

    def test_valid_artifact_and_evidence_bound_review(self):
        check = self.check()
        self.assertEqual(check.citations, ['app/Main.kt', 'data/Repository.kt'])
        self.assertEqual(check_review(json.dumps(good_review()))['decision'], 'APPROVE')

    def test_missing_citations_rejected(self):
        self.path.write_text(DOC.replace('app/Main.kt', 'MainActivity').replace('data/Repository.kt', 'Repository'))
        with self.assertRaisesRegex(ValueError, 'Cite exact'):
            self.check()

    def test_invented_path_rejected_even_with_valid_citations(self):
        for path in ('other/Invented.kt', 'scripts/fake.py', 'config/fake.yaml'):
            self.path.write_text(DOC + '\nUses `' + path + '`.')
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, 'not present'):
                self.check()

    def test_reference_list_is_accepted_for_semantic_review(self):
        self.path.write_text(DOC.replace('Source: `app/Main.kt`.', '').replace('Source: `data/Repository.kt`.', '')
                             + '\n## References\n`app/Main.kt` and `data/Repository.kt`')
        self.assertEqual(self.check().citations, ['app/Main.kt', 'data/Repository.kt'])

    def test_missing_architecture_section_rejected(self):
        self.path.write_text(DOC.replace('## Relationships', '## DTO details'))
        with self.assertRaisesRegex(ValueError, 'required section: Relationships'):
            self.check()

    def test_missing_artifact_and_extra_files_rejected(self):
        self.path.rename(self.path.with_name('other.md'))
        with self.assertRaisesRegex(ValueError, 'Unexpected file'):
            self.check()
        self.path.with_name('other.md').rename(self.path)
        for name in ('other.md', 'Injected.kt', 'project_facts.json'):
            extra = self.path.with_name(name)
            extra.write_text('extra')
            with self.assertRaisesRegex(ValueError, 'Unexpected file'):
                self.check()
            extra.unlink()

    def test_no_evidence_or_cross_project_evidence_rejected(self):
        self.evidence['hits'] = []
        with self.assertRaisesRegex(ValueError, 'No project evidence'):
            self.check()
        hits = copy.deepcopy(HITS)
        hits[0]['metadata'] = {'project_id': 'different'}
        with self.assertRaisesRegex(ValueError, 'different project'):
            project_evidence('demo', hits)

    def test_contract_rejects_escaping_or_ambiguous_artifacts(self):
        for artifact in ('../escape.md', '/escape.md', 'C:/escape.md', 'a/../escape.md'):
            with self.assertRaises(ValueError):
                documentation_contract({'task': 'write a summary', 'documentation_contract': {**CONTRACT, 'artifact': artifact}})
        with self.assertRaises(ValueError):
            documentation_contract({'task': 'write a summary'})

    def test_bare_approve_cannot_complete(self):
        with self.assertRaises(ValueError):
            check_review('{"decision":"APPROVE"}')

    def test_review_requires_an_explanation_and_explicit_acceptance(self):
        for review in ({'decision': 'APPROVE', 'reason': ''},
                       {'decision': 'REJECTED', 'reason': 'Unsupported relationship'},
                       {'decision': 'MAYBE', 'reason': 'The model is uncertain about the architecture.'}):
            with self.subTest(review=review), self.assertRaises(ValueError):
                check_review(json.dumps(review))


class DocumentationCompletionGateTests(unittest.TestCase):
    def run_review(self, document=DOC, verdict=None, mutate=False):
        from tests.sandbox.core.test_documentation_transition import response
        with tempfile.TemporaryDirectory() as temp:
            storage = runner.SandboxStorage(temp)
            path = storage.resolve_workspace_path('docs', CONTRACT['artifact'])
            path.write_text(document)
            storage.save_state('docs', {'status': 'in_progress', 'task_mode': 'documentation',
                'task': 'Review architecture_summary.md', 'documentation_contract': CONTRACT,
                'project_id': 'demo', 'current_turn': 'reviewer',
                'memory': [{'role': 'reviewer', 'content': 'STALE_REJECTION: the old file lacked citations'}],
                'metrics': {}, 'agent_steps': 0})
            def complete(**kwargs):
                self.assertNotIn('STALE_REJECTION', str(kwargs['messages']))
                self.assertIn('USER TASK: Review architecture_summary.md', kwargs['messages'][0]['content'])
                if mutate:
                    path.write_text(DOC + '\nChanged after review started.')
                return response(json.dumps(verdict if verdict is not None else good_review()))
            with patch('runner.SandboxStorage', return_value=storage), \
                 patch('runner.load_json', return_value={'agents': {'reviewer': {'name': 'Reviewer'}}}), \
                 patch('runner.retrieve_project_context', return_value=HITS), \
                 patch('runner.safe_llm_completion', side_effect=complete) as llm, \
                 patch.object(storage, 'ingest_and_extract_facts', side_effect=AssertionError('no fact promotion')), \
                 patch('runner.trigger_regulator'), patch('runner.MAX_AGENT_STEPS', 1), patch('builtins.print'):
                runner.run_agent_loop('docs', resume=True)
            return storage.get_current_state('docs'), llm.call_count

    def test_real_artifact_and_substantive_review_complete_without_fact_promotion(self):
        state, calls = self.run_review()
        self.assertEqual(state['status'], 'completed')
        self.assertEqual(calls, 1)
        self.assertEqual(state['documentation_review']['sources'], ['app/Main.kt', 'data/Repository.kt'])
        self.assertFalse(any('approval' in k or 'validation' in k for k in state))

    def test_uncited_document_blocks_even_an_approving_reviewer(self):
        state, calls = self.run_review(DOC.replace('app/Main.kt', 'App').replace('data/Repository.kt', 'Repository'))
        self.assertEqual(state['status'], 'in_progress')
        self.assertEqual(state['current_turn'], 'coder')
        self.assertEqual(calls, 0)

    def test_unjustified_approve_returns_to_coder(self):
        state, _ = self.run_review(verdict={'decision': 'APPROVE'})
        self.assertEqual(state['status'], 'in_progress')
        self.assertEqual(state['current_turn'], 'coder')

    def test_artifact_change_during_review_requires_fresh_review(self):
        state, _ = self.run_review(mutate=True)
        self.assertEqual(state['status'], 'in_progress')
        self.assertIn('changed during review', state['memory'][-1]['content'])

    def test_reviewer_reports_unsupported_architecture_and_cannot_complete(self):
        state, _ = self.run_review(verdict={'decision': 'REJECTED', 'reason': 'Relationship is not supported by the excerpt.'})
        self.assertEqual(state['status'], 'in_progress')
        self.assertIn('not supported', state['memory'][-1]['content'])
